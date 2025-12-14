import json
import os

# ── Base paths ──────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
SPLASH_DIR = os.path.join(ASSETS_DIR, "splash")

COMFYUI_PORT = 8188

# ── Waiting parameters ────────────────────────
CHECK_INTERVAL = 1
MAX_WAIT_TIME = 90

# ── Shared resources ─────────────────────────────
ICON_PATH = os.path.join(ICONS_DIR, "icon.png")
SPLASH_PATH = os.path.join(SPLASH_DIR, "1618x616_qt.mp4")

# ── Set of icons for toolbar ──────────────────
ICON_PATHS = {
    "restart": os.path.join(ICONS_DIR, "restart.svg"),
    "stop": os.path.join(ICONS_DIR, "stop.svg"),
    "open_folder": os.path.join(ICONS_DIR, "open_folder.svg"),
    "open_browser": os.path.join(ICONS_DIR, "open_in_browser.svg"),
    "settings": os.path.join(ICONS_DIR, "settings.svg"),
    "open_output": os.path.join(ICONS_DIR, "output.svg"),
    "refresh": os.path.join(ICONS_DIR, "reload.svg"),
    "terminal": os.path.join(ICONS_DIR, "terminal.svg")
}

# ── Saved builds ─────────────────────────────
SAVED_BUILDS = {
    "active": "",
    "history": [],
}

# ── Set of icons for header bar ──────────────────
HEAD_ICON_PATHS = {
    "minimize": os.path.join(ICONS_DIR, "minimize.svg"),
    "maximize": os.path.join(ICONS_DIR, "maximize.svg"),
    "close": os.path.join(ICONS_DIR, "close.svg"),
}

MESSAGEBOX_ICONS = {
    "info": os.path.join(ICONS_DIR, "messagebox", "info.svg"),
    "warning": os.path.join(ICONS_DIR, "messagebox", "warning.svg"),
    "error": os.path.join(ICONS_DIR, "messagebox", "error.svg"),
    "ask_yes_no": os.path.join(ICONS_DIR, "messagebox", "ask_yes_no.svg"),
}

DONATION_ICONS = {
    "boosty": os.path.join(ICONS_DIR, "donations", "boosty_color.svg"),
    "patreon": os.path.join(ICONS_DIR, "donations", "patreon.svg"),
    "kofi": os.path.join(ICONS_DIR, "donations", "ko-fi.svg"),
    "buymeacoffee": os.path.join(ICONS_DIR, "donations", "buy_me_a_coffee.svg"),
}

CONTACT_ICONS = {
    "github": os.path.join(ICONS_DIR, "contacts", "github.png"),
    "email": os.path.join(ICONS_DIR, "contacts", "email.png"),
    "telegram": os.path.join(ICONS_DIR, "contacts", "telegram.png"),
    "discord": os.path.join(ICONS_DIR, "contacts", "discord.png"),
}

OTHER_ICONS = {
    "refresh": os.path.join(ICONS_DIR, "refresh.svg"),
    "clear-log": os.path.join(ICONS_DIR, "clear-log.svg"),
    "comfyui": os.path.join(ICONS_DIR, "comfyui-text.svg")
}

USER_CONFIG_PATH = os.path.join(BASE_DIR, "user_config.json")


DEFAULT_USER_CONFIG = {
    "ask_on_exit": True,
    "exit_mode": "always_stop",
    "browser_patch_registry": {},
}


def load_user_config():
    if not os.path.exists(USER_CONFIG_PATH):
        save_user_config(DEFAULT_USER_CONFIG)
        return DEFAULT_USER_CONFIG.copy()
    try:
        with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key, val in DEFAULT_USER_CONFIG.items():
                data.setdefault(key, val)
            return data
    except Exception:
        return DEFAULT_USER_CONFIG.copy()


def save_user_config(data: dict):
    try:
        with open(USER_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Failed to save config: {e}")


def get_comfyui_path() -> str:
    """Returns the current path to ComfyUI (from user_config.json or default)."""
    data = load_user_config()
    return data.get("comfyui_path", "")
