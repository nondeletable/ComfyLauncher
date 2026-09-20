import os
from datetime import datetime

from utils.platform_paths import app_dir


def _get_log_dir():
    """Returns the path to the log directory in the user profile.

    Uses the same per-user directory as the rest of the app data
    (``%APPDATA%/ComfyLauncher`` on Windows, ``~/.config/ComfyLauncher`` on
    Linux). It used to resolve the base itself and fell through to ``~`` off
    Windows, dropping logs into a bare ``~/ComfyLauncher/logs``.
    """
    log_dir = os.path.join(app_dir(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


LOG_DIR = _get_log_dir()
LOG_FILE = os.path.join(LOG_DIR, "launcher.log")


def log_event(message: str):
    """Writes an event to the console and log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    # Console output is best-effort: a non-UTF-8 stdout (cp1251/cp1252 console,
    # a redirected file) can't encode the emoji in these messages and raises
    # UnicodeEncodeError. That must never take the app down, so swallow it —
    # the log file below is UTF-8 and keeps the full record.
    try:
        print(formatted)
    except (UnicodeEncodeError, OSError):
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception as e:
        try:
            print(f"[LOGGER ERROR] {e}")
        except (UnicodeEncodeError, OSError):
            pass
