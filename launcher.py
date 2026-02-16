import subprocess
from subprocess import TimeoutExpired
import socket
import time
import psutil
import os
import shutil
import re
import hashlib
import threading
from datetime import datetime
from utils.console_buffer import ConsoleBuffer
from utils.logger import log_event
from config import (
    COMFYUI_PORT,
    CHECK_INTERVAL,
    MAX_WAIT_TIME,
    load_user_config,
    save_user_config,
)

_comfy_process: subprocess.Popen | None = None


def comfy_exists(path):
    """Checks that the folder contains main.py"""
    return os.path.exists(os.path.join(path, "main.py"))


def is_port_open(port):
    """Checks if the specified port is open"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_for_server():
    """Waiting for ComfyUI to load"""
    start = time.time()
    while time.time() - start < MAX_WAIT_TIME:
        if is_port_open(COMFYUI_PORT):
            log_event("ComfyUI started.")
            return True
        time.sleep(CHECK_INTERVAL)
    log_event("Failed to connect to the server.")
    return False


def get_listening_pids(port: int) -> set[int]:
    pids: set[int] = set()
    try:
        for c in psutil.net_connections(kind="inet"):
            if c.laddr and c.laddr.port == port and c.status == psutil.CONN_LISTEN:
                if c.pid:
                    pids.add(c.pid)
    except Exception:
        pass
    return pids


def is_cuda_available():
    """Checks for the presence of an NVIDIA GPU via nvidia-smi"""
    # Checks that nvidia-smi even exists
    if not shutil.which("nvidia-smi"):
        return False

    try:
        result = subprocess.run(
            ["nvidia-smi"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,  # таймаут на случай зависания
        )
        return result.returncode == 0
    except (OSError, TimeoutExpired):
        return False


# =====================================================================
# 🔹 Auxiliary functions
# =====================================================================


def get_file_hash(path: str) -> str:
    """Returns a short MD5 hash of the file for change tracking."""
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, IOError):
        return ""


def disable_browser_auto_launch(comfy_path: str):
    """
    Checks main.py and comments out webbrowser.open(...) if it's not already commented out.
    Returns (patched: bool, file_hash: str)
    """
    main_py = os.path.join(comfy_path, "main.py")
    if not os.path.exists(main_py):
        log_event("⚠️ main.py not found — skip browser patch.")
        return False, ""

    file_hash = get_file_hash(main_py)

    try:
        with open(main_py, "r", encoding="utf-8") as f:
            content = f.read()

        if "# webbrowser.open(" in content:
            log_event("🧩 Browser auto-launch already disabled.")
            return True, file_hash

        pattern = re.compile(r"^\s*webbrowser\.open\(.*\)$", re.MULTILINE)
        if pattern.search(content):
            patched = pattern.sub(r"# \g<0>  # patched by ComfyLauncher", content)
            backup = main_py + ".bak"
            if not os.path.exists(backup):
                shutil.copy2(main_py, backup)
            with open(main_py, "w", encoding="utf-8") as f:
                f.write(patched)
            log_event("🧩 Browser auto-launch disabled (via patch).")
            return True, get_file_hash(main_py)
        else:
            log_event("ℹ️ No webbrowser.open() found — nothing to patch.")
            return False, file_hash
    except Exception as e:
        log_event(f"❌ Failed to patch browser launch: {e}")
        return False, file_hash


def update_browser_patch_registry(comfy_path: str, patched: bool, file_hash: str):
    """Saves the patch state in user_config.json."""
    cfg = load_user_config()
    registry = cfg.get("browser_patch_registry", {})

    registry[comfy_path] = {
        "patched": patched,
        "file_hash": file_hash,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    cfg["browser_patch_registry"] = registry
    save_user_config(cfg)


def resolve_python_exe(base_dir: str) -> str:
    """
    Returns the path to the embedded Python inside the portable build, if present.
    Supports both spellings: python_embeded / python_embedded.
    Otherwise, it uses 'python' (the system interpreter).
    """
    cand = os.path.join(base_dir, "python_embeded", "python.exe")
    if os.path.exists(cand):
        return cand
    cand = os.path.join(base_dir, "python_embedded", "python.exe")
    if os.path.exists(cand):
        return cand
    return "python"


def ensure_comfyui_running(comfy_path: str, port: int = 8188):
    """
    1) Checks if the server is running.
    2) Checks if main.py is patched (auto-browser is disabled).
    3) If necessary, patches and updates user_config.json.
    4) Launches ComfyUI (via bat or directly).
    """
    global _comfy_process

    # --- Browser Check and Patch -------------------------------------
    main_py = os.path.join(comfy_path, "main.py")
    file_hash = get_file_hash(main_py)

    cfg = load_user_config()
    show_cmd = cfg.get("show_cmd", True)
    use_internal_console = not show_cmd

    registry = cfg.get("browser_patch_registry", {})
    entry = registry.get(comfy_path, {})

    need_patch = (
        not entry
        or entry.get("file_hash") != file_hash
        or not entry.get("patched", False)
    )

    if need_patch:
        patched, new_hash = disable_browser_auto_launch(comfy_path)
        update_browser_patch_registry(comfy_path, patched, new_hash)
    else:
        log_event("✅ Browser patch check skipped — already up to date.")

    # Is there a live process already?
    if _comfy_process and _comfy_process.poll() is None:
        log_event("⚠️ ComfyUI process is already running, skip start.")
        return

    # Port busy - Comfy is already running
    if is_port_open(port):
        log_event("✅ ComfyUI already launched.")
        return

    # --- GPU / CPU select ---------------------------------------------
    try:
        cuda_available = is_cuda_available()
    except Exception:
        cuda_available = False

    cfg = load_user_config()
    active_build = _get_active_build(cfg)
    startup_mode = (active_build or {}).get("startup_mode", "auto")

    bat_name, mode = _resolve_bat_name(str(startup_mode), cuda_available)
    log_event(f"🚀 Starting ComfyUI in {mode} mode...")

    base_dir = os.path.dirname(comfy_path)
    bat_file = os.path.join(base_dir, bat_name)

    # --- BAT mode ----------------------------------------------------
    sm = str(startup_mode).lower()

    # downgrade chain for missing bats
    if not os.path.exists(bat_file):
        if sm == "cpu":
            log_event("⚠️ run_cpu.bat not found → fallback to Python mode")
        elif sm == "fast_fp16":
            log_event(f"⚠️ Selected bat not found: {bat_name} → fallback to GPU bat")
            bat_name, mode = "run_nvidia_gpu.bat", "GPU"
            bat_file = os.path.join(base_dir, bat_name)

            if not os.path.exists(bat_file):
                log_event("⚠️ GPU bat not found either → fallback to AUTO")
                bat_name, mode = _resolve_bat_name("auto", cuda_available)
                bat_file = os.path.join(base_dir, bat_name)

        elif sm == "gpu":
            log_event(f"⚠️ Selected bat not found: {bat_name} → fallback to AUTO")
            bat_name, mode = _resolve_bat_name("auto", cuda_available)
            bat_file = os.path.join(base_dir, bat_name)

    if os.path.exists(bat_file):
        log_event(f"🚀 Starting ComfyUI via {bat_name} ({mode})")
    else:
        log_event(f"🚀 Starting ComfyUI in Python mode ({mode})")

    if os.path.exists(bat_file):

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        if show_cmd:
            # 🔹 MODE: SHOW CMD (REAL)
            _comfy_process = subprocess.Popen(
                ["cmd.exe", "/k", bat_file],
                cwd=base_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )

        else:
            # 🔹 MODE: HIDDEN CONSOLE (PIPE)
            _comfy_process = subprocess.Popen(
                ["cmd.exe", "/d", "/c", bat_file],  # бат выполняем через cmd корректно
                cwd=base_dir,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # один поток → без зависаний/пачек
                text=True,
                bufsize=1,
            )

    # --- Python mode -------------------------------------------------
    else:
        python_exe = resolve_python_exe(base_dir)

        args = [
            python_exe,
            "-u",  # realtime
            os.path.join(comfy_path, "main.py"),
            "--windows-standalone-build",
        ]
        if not cuda_available:
            args.append("--cpu")

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONHOME"] = os.path.join(base_dir, "python_embeded")
        env["PYTHONPATH"] = comfy_path
        env["PATH"] = env["PYTHONHOME"] + ";" + env["PATH"]
        env["PYTHONIOENCODING"] = "utf-8"

        if show_cmd:
            _comfy_process = subprocess.Popen(
                ["cmd.exe", "/k"] + args,
                cwd=comfy_path,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        else:
            _comfy_process = subprocess.Popen(
                args,
                cwd=comfy_path,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

    # We read the output ONLY in the built-in console mode
    if use_internal_console and _comfy_process:
        threading.Thread(
            target=_read_process_output, args=(_comfy_process,), daemon=True
        ).start()

    log_event(f"🟢 ComfyUI started (PID {_comfy_process.pid}) in mode {mode}.")


def kill_process_tree(pid):
    """Kills the process and all its descendants"""
    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return

    for child in parent.children(recursive=True):
        try:
            log_event(f"💀 Killing child PID {child.pid}: {child.name()}")
            child.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    log_event(f"💀 Killing parent PID {pid}: {parent.name()}")
    try:
        parent.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass


def stop_comfyui_hard(_grace_period=5):
    """Completely completes ComfyUI (bat file + python descendants)."""
    global _comfy_process
    log_event("⏹ Completing ComfyUI...")

    killed = False

    # 1️⃣ Let's try to kill the running .bat
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            # safely get the command line
            cmdline = proc.info.get("cmdline") or []
            if not cmdline:
                continue
            cmdline_joined = " ".join(cmdline).lower()

            if (
                "run_cpu.bat" in cmdline_joined
                or "run_nvidia_gpu.bat" in cmdline_joined
                or "run_nvidia_gpu_fast_fp16.bat" in cmdline_joined
            ):
                log_event(
                    f"💀 We are finishing the bat file and all its descendants (PID {proc.pid})"
                )
                time.sleep(1)
                kill_process_tree(proc.pid)
                # To be on the safe side, we'll additionally check for descendants after kill.
                time.sleep(0.5)
                for child in psutil.process_iter(["pid", "ppid", "name"]):
                    if child.info["ppid"] == proc.pid:
                        log_event(
                            f"⚠️ Descendant {child.pid} ({child.info['name']}) still alive - kill directly"
                        )
                        child.kill()
                killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # 2️⃣ If the batch file is not found, fallback: look for python main.py
    if not killed:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmd = " ".join(proc.info["cmdline"]).lower()
                if "comfyui" in cmd or "main.py" in cmd:
                    log_event(f"💀 Force quit ComfyUI (PID {proc.pid})")
                    proc.kill()
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    if killed:
        # 3️⃣ Confirm state
        if not is_port_open(COMFYUI_PORT):
            log_event("🟢 Port 8188 closed — server fully stopped.")
        else:
            log_event("⚠️ Port still busy — possible residual process.")
        log_event("✅ ComfyUI stopped completely.")
    else:
        log_event("⚠️ No ComfyUI process found to stop.")

    deadline = time.time() + _grace_period
    while time.time() < deadline and is_port_open(COMFYUI_PORT):
        pids = get_listening_pids(COMFYUI_PORT)
        if not pids:
            time.sleep(0.2)
            continue

        for pid in pids:
            log_event(f"💀 Killing listener on port {COMFYUI_PORT}: PID {pid}")
            kill_process_tree(pid)

        time.sleep(0.3)

    if not is_port_open(COMFYUI_PORT):
        log_event("🟢 Port 8188 closed — server fully stopped.")
    else:
        log_event("⚠️ Port still busy — residual process remains.")

    _comfy_process = None


def _read_process_output(proc: subprocess.Popen):
    """Reads stdout of ComfyUI process and writes to ConsoleBuffer."""
    try:
        if proc.stdout:
            for line in proc.stdout:
                ConsoleBuffer.add(line)
    except Exception as e:
        ConsoleBuffer.add(f"[Console reader error] {e}\n")


def _get_active_build(cfg: dict) -> dict | None:
    bid = str(cfg.get("last_used_build_id", "")).strip()
    for b in cfg.get("builds", []) or []:
        if str(b.get("id", "")) == bid:
            return b
    return None


def _resolve_bat_name(startup_mode: str, cuda_available: bool) -> tuple[str, str]:
    """
    Returns (bat_name, mode_label)
    startup_mode: cpu | gpu | fast_fp16 | auto
    """
    sm = (startup_mode or "auto").lower()

    if sm == "cpu":
        return "run_cpu.bat", "CPU"
    if sm == "gpu":
        return "run_nvidia_gpu.bat", "GPU"
    if sm == "fast_fp16":
        return "run_nvidia_gpu_fast_fp16.bat", "GPU (fast fp16)"

    # auto
    return ("run_nvidia_gpu.bat", "GPU") if cuda_available else ("run_cpu.bat", "CPU")


__all__ = [
    "is_port_open",
    "ensure_comfyui_running",
    "stop_comfyui_hard",
    "comfy_exists",
    "kill_process_tree",
]
