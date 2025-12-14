import os
from datetime import datetime


def _get_log_dir():
    """Returns the path to the log directory in the user profile."""
    base = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
    log_dir = os.path.join(base, "ComfyLauncher", "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


LOG_DIR = _get_log_dir()
LOG_FILE = os.path.join(LOG_DIR, "launcher.log")


def log_event(message: str):
    """Writes an event to the console and log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception as e:
        print(f"[LOGGER ERROR] {e}")
