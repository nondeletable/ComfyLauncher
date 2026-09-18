"""Cross-platform user paths and OS integration helpers.

The single facade for per-user directories and "open in file manager" actions,
so the rest of the app never hardcodes a Windows path or ``os.startfile``.

Design rule: **Windows behavior is unchanged.** ``app_dir()`` on Windows returns
exactly the previous ``%APPDATA%/ComfyLauncher`` location, so existing installs
keep their config and themes with no migration. Linux/macOS branches are added
alongside, they never alter the Windows path.
"""

from __future__ import annotations

import os
import sys
import subprocess


APP_NAME = "ComfyLauncher"


def app_dir(app_name: str = APP_NAME) -> str:
    """Single per-user directory for this app's config and data.

    - Windows: ``%APPDATA%/ComfyLauncher`` (unchanged — existing installs keep working)
    - macOS:   ``~/Library/Application Support/ComfyLauncher``
    - Linux:   ``$XDG_CONFIG_HOME/ComfyLauncher`` or ``~/.config/ComfyLauncher``

    Returns the path only; the directory is created by callers when they write,
    exactly as before. No side effects on import.
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config"
        )
    return os.path.join(base, app_name)


def open_in_file_manager(path: str) -> None:
    """Open a folder in the OS file manager. Best-effort — never raises.

    Replaces the previous bare ``os.startfile`` calls with a platform dispatch:
    ``os.startfile`` on Windows, ``open`` on macOS, ``xdg-open`` on Linux.
    """
    try:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]  # Windows-only
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        # Imported here, not at module level: utils.logger asks this module for
        # the app directory, and a module-level import would be circular.
        from utils.logger import log_event

        log_event(f"⚠️ Failed to open path in file manager: {path} ({e})")
