"""Measures how well each available web engine renders a ComfyUI-shaped canvas.

Why this exists: the launcher has to pick an engine per platform, and the
argument has always been about frame rate on a big node graph versus memory
use. This runs the identical scripted zoom/pan over the identical canvas in
every engine available on the machine and prints the two numbers side by side.

    python tools/webview_bench/run.py --all
    python tools/webview_bench/run.py --engine webview2 --nodes 600 --repeat 3
    python tools/webview_bench/run.py --bootstrap C:\\tmp\\qt611   # see README

Engines: webview2 (Windows, what ships today), qtwebengine (the candidate,
needs PyQt6-WebEngine), and whichever of edge/chrome/chromium/firefox is
installed, as a reference point for "a real browser".
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psutil

sys.path.insert(0, str(Path(__file__).parent))
from server import BenchServer  # noqa: E402

HERE = Path(__file__).parent
HOST = HERE / "_host.py"

# Pinned as a set: pip resolves the two "-Qt6" packages independently of each
# other, and a mismatch fails at import with a missing libQt6Qml*.so / DLL.
QT_PINS = [
    "PyQt6==6.11.0",
    "PyQt6-Qt6==6.11.0",
    "PyQt6-WebEngine==6.11.0",
    "PyQt6-WebEngine-Qt6==6.11.0",
    "psutil",
]

WINDOWS_BROWSERS = {
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
}


def find_browser(name: str) -> str | None:
    for candidate in WINDOWS_BROWSERS.get(name, []):
        if Path(candidate).exists():
            return candidate
    return shutil.which(name) or shutil.which(f"{name}-browser")


def browser_command(name: str, exe: str, url: str, profile: Path) -> list[str]:
    """A throwaway profile is what makes the measurement possible at all.

    Without it the launch hands the URL to an already-running browser and
    exits, so there is no process tree left to measure.
    """
    if name == "firefox":
        return [
            exe,
            "-profile",
            str(profile),
            "-no-remote",
            "-width",
            "1400",
            "-height",
            "900",
            url,
        ]
    return [
        exe,
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1400,900",
        url,
    ]


def engine_command(engine: str, url: str, profile: Path) -> list[str] | None:
    if engine in ("webview2", "qtwebengine"):
        return [sys.executable, str(HOST), engine, url]
    exe = find_browser(engine)
    return browser_command(engine, exe, url, profile) if exe else None


PROFILE_ROOT = Path.home() / "comfylauncher-bench-profiles"


def profile_dir() -> Path:
    """A throwaway profile, in a plain visible folder inside HOME.

    Not the system temp dir and not a dotted folder: a snap-packaged browser
    (Firefox, Chromium on Ubuntu) sees a private /tmp and is denied hidden
    directories under HOME, and quits instead of starting.
    """
    PROFILE_ROOT.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(dir=PROFILE_ROOT))


def tree_rss(proc: psutil.Process) -> int:
    total = 0
    for p in [proc, *proc.children(recursive=True)]:
        try:
            total += p.memory_info().rss
        except psutil.Error:
            pass
    return total


def detached_rss(exe: str, started_after: float) -> tuple[int, list[psutil.Process]]:
    """Memory of processes this run spawned when the launcher forked away.

    Matched by executable and start time so an already-running browser of the
    same brand is neither measured nor, later, killed.
    """
    name = Path(exe).name.lower()
    found = []
    total = 0
    for p in psutil.process_iter(["name", "create_time"]):
        try:
            if name.startswith(
                str(p.info["name"]).lower().removesuffix(".exe")[:8]
            ) or str(p.info["name"]).lower().startswith(name.removesuffix(".exe")[:8]):
                if p.info["create_time"] >= started_after:
                    total += p.memory_info().rss
                    found.append(p)
        except psutil.Error:
            pass
    return total, found


def kill_tree(proc: psutil.Process) -> None:
    for p in [*proc.children(recursive=True), proc]:
        try:
            p.terminate()
        except psutil.Error:
            pass
    _, alive = psutil.wait_procs([proc, *proc.children(recursive=True)], timeout=8)
    for p in alive:
        try:
            p.kill()
        except psutil.Error:
            pass


def run_once(engine: str, nodes: int, frames: int, timeout: int) -> dict:
    profile = profile_dir()
    try:
        with BenchServer() as server:
            url = server.url(f"nodes={nodes}&frames={frames}")
            cmd = engine_command(engine, url, profile)
            if cmd is None:
                return {"engine": engine, "error": "not installed"}

            launched_at = time.time() - 1
            child = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            try:
                proc = psutil.Process(child.pid)
            except psutil.Error:
                proc = None

            peak, strays = 0, []
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if server.wait(0.5) is not None:
                    break
                if proc is not None and child.poll() is None:
                    try:
                        peak = max(peak, tree_rss(proc))
                        continue
                    except psutil.Error:
                        pass
                # The launcher handed off to a background process and exited:
                # keep waiting for the page, and follow what it left running.
                rss, strays = detached_rss(cmd[0], launched_at)
                peak = max(peak, rss)
                if not strays and child.poll() is not None:
                    return {"engine": engine, "error": "engine exited early"}

            result = dict(server.result) or {"error": "timed out"}
            if proc is not None:
                kill_tree(proc)
            for p in strays:
                try:
                    p.terminate()
                except psutil.Error:
                    pass
    finally:
        shutil.rmtree(profile, ignore_errors=True)
        try:
            PROFILE_ROOT.rmdir()  # only when this was the last run
        except OSError:
            pass

    result["engine"] = engine
    result["rss_peak_mb"] = round(peak / 1024 / 1024, 1)
    return result


def engine_build(ua: str) -> str:
    """The browser build behind the numbers — the thing that actually differs."""
    for marker, label in (("Chrome/", "chromium"), ("Firefox/", "gecko")):
        if marker in ua:
            return f"{label} {ua.split(marker)[-1].split('.')[0]}"
    return "-"


def summarize(runs: list[dict]) -> dict:
    ok = [r for r in runs if "fps_mean" in r]
    if not ok:
        return {"engine": runs[0]["engine"], "error": runs[0].get("error", "no data")}

    def med(key):
        return round(statistics.median([r[key] for r in ok]), 1)

    return {
        "engine": ok[0]["engine"],
        "runs": len(ok),
        "fps": med("fps_mean"),
        "draw_ms": med("draw_median_ms"),
        "frame_p95_ms": med("frame_p95_ms"),
        "rss_mb": med("rss_peak_mb"),
        "build": engine_build(ok[0].get("ua", "")),
    }


def print_table(rows: list[dict]) -> None:
    print()
    print(
        f"{'engine':<14}{'runs':>5}{'fps':>8}{'draw ms':>10}"
        f"{'frame p95':>11}{'RSS MB':>9}  notes"
    )
    print("-" * 74)
    for r in rows:
        if "error" in r:
            print(
                f"{r['engine']:<14}{'-':>5}{'-':>8}{'-':>10}{'-':>11}{'-':>9}"
                f"  {r['error']}"
            )
            continue
        print(
            f"{r['engine']:<14}{r['runs']:>5}{r['fps']:>8}{r['draw_ms']:>10}"
            f"{r['frame_p95_ms']:>11}{r['rss_mb']:>9}  chromium {r['chromium']}"
        )
    print()
    print("fps: higher is better, 60 is the vsync ceiling. draw ms: time inside the")
    print("canvas calls. frame p95: worst frames — a multiple of 16.7 means the engine")
    print(
        "is dropping whole frames. RSS: peak memory of the engine's whole process tree."
    )


def bootstrap(target: str) -> int:
    """Builds a throwaway venv with the newest pinned Qt, without touching .venv."""
    target_path = Path(target)
    print(f"creating {target_path} …")
    subprocess.run([sys.executable, "-m", "venv", str(target_path)], check=True)
    py = target_path / (
        "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
    )
    print("installing " + " ".join(QT_PINS) + " …")
    subprocess.run(
        [str(py), "-m", "pip", "install", "--progress-bar", "off", *QT_PINS], check=True
    )
    print(f"\ndone. now run:\n  {py} {Path(__file__)} --engine qtwebengine")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--engine",
        action="append",
        default=[],
        help="webview2 | qtwebengine | edge | chrome | chromium | firefox",
    )
    ap.add_argument(
        "--all", action="store_true", help="every engine found on this machine"
    )
    ap.add_argument("--nodes", type=int, default=600, help="graph size (default 600)")
    ap.add_argument(
        "--frames", type=int, default=240, help="frames per run (default 240)"
    )
    ap.add_argument("--repeat", type=int, default=3, help="runs per engine (default 3)")
    ap.add_argument("--timeout", type=int, default=180, help="seconds per run")
    ap.add_argument("--json", type=str, default="", help="also write raw runs here")
    ap.add_argument(
        "--bootstrap",
        type=str,
        default="",
        help="create a venv with the newest pinned Qt at this path, then exit",
    )
    args = ap.parse_args()

    if args.bootstrap:
        return bootstrap(args.bootstrap)

    engines = list(args.engine)
    if args.all or not engines:
        engines = ["webview2"] if sys.platform == "win32" else []
        engines.append("qtwebengine")
        engines += [
            b for b in ("edge", "chrome", "chromium", "firefox") if find_browser(b)
        ]

    print(
        f"bench: {args.nodes} nodes, {args.frames} frames, "
        f"{args.repeat} run(s) per engine"
    )

    raw, rows = [], []
    for engine in engines:
        runs = []
        for i in range(args.repeat):
            print(f"  {engine} run {i + 1}/{args.repeat} …", flush=True)
            result = run_once(engine, args.nodes, args.frames, args.timeout)
            runs.append(result)
            raw.append(result)
            if "error" in result:
                print(f"    {result['error']}")
                break
        rows.append(summarize(runs))

    print_table(rows)
    if args.json:
        Path(args.json).write_text(
            "\n".join(json.dumps(r) for r in raw), encoding="utf-8"
        )
        print(f"raw runs → {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
