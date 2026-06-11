import sys
import os
import subprocess

IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"


def get_app_data_dir(app_name: str = "ComfyLauncher") -> str:
    """
    Return the application data directory:
    - Windows: %APPDATA%/ComfyLauncher
    - macOS: ~/Library/Application Support/ComfyLauncher
    """
    if IS_WINDOWS:
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif IS_MACOS:
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
    return os.path.join(base, app_name)


def get_log_dir(app_name: str = "ComfyLauncher") -> str:
    """
    Return the log directory:
    - Windows: %APPDATA%/ComfyLauncher/logs
    - macOS: ~/Library/Application Support/ComfyLauncher/logs
    """
    return os.path.join(get_app_data_dir(app_name), "logs")


def open_path_in_explorer(path: str) -> None:
    """
    Open a path in the system file manager:
    - Windows: os.startfile(path)
    - macOS: open path
    """
    if IS_WINDOWS:
        os.startfile(path)  # type: ignore[attr-defined]
    elif IS_MACOS:
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])


# ── Python environment lookup order ──────────────────────────────────

# Candidate venv directory names for macOS/Linux, ordered by priority
_VENV_DIRS = [".venv", "venv"]


def find_venv_python(comfy_path: str) -> str | None:
    """
    Find venv python3 in comfy_path (directory containing main.py) and its parent.
    Search order:
      1. comfy_path/.venv/bin/python3
      2. comfy_path/venv/bin/python3
      3. parent/.venv/bin/python3
      4. parent/venv/bin/python3
      5. parent/standalone-env/bin/python3
    Returns the absolute path to python3 if found, otherwise None.
    """
    parent = os.path.dirname(comfy_path)
    search_roots = [comfy_path, parent]

    for root in search_roots:
        for vdir in _VENV_DIRS:
            cand = os.path.join(root, vdir, "bin", "python3")
            if os.path.exists(cand):
                return cand

    # Fallback: standalone-env (sibling of comfy_path)
    standalone = os.path.join(parent, "standalone-env", "bin", "python3")
    if os.path.exists(standalone):
        return standalone

    return None


def has_venv(comfy_path: str) -> bool:
    """Check if comfy_path has an available venv (uses the same search logic as find_venv_python)."""
    return find_venv_python(comfy_path) is not None


# ── System language detection ─────────────────────────────────────────


def detect_system_language() -> str:
    """
    Detect the OS preferred language and return a BCP-47 tag (e.g. 'zh-CN', 'en').
    - macOS: reads `defaults read -g AppleLocale`
    - Linux: reads the LANG environment variable
    - Windows: not yet supported
    Falls back to 'en'.
    """
    try:
        if IS_MACOS:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleLocale"],
                capture_output=True, text=True, timeout=3,
            )
            if result.returncode == 0:
                raw = result.stdout.strip()
                # AppleLocale format e.g. zh_CN → zh-CN
                return raw.replace("_", "-")
        else:
            # Linux: read from environment variable
            lang = os.environ.get("LANG", "en_US.UTF-8")
            raw = lang.split(".")[0]  # zh_CN.UTF-8 → zh_CN
            return raw.replace("_", "-")
    except Exception:
        pass
    return "en"
