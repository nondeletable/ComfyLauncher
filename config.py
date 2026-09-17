import json
import os
import shutil

from utils.logger import log_event
from utils.platform_paths import app_dir

# ── Base paths ──────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
DATA_DIR = os.path.join(ASSETS_DIR, "data")
SPLASH_DIR = os.path.join(ASSETS_DIR, "splash")
INTERFACE_DIR = os.path.join(ASSETS_DIR, "interface")
DOODLES_DIR = os.path.join(ICONS_DIR, "doodles")

COMFYUI_PORT = 8188

# ── Waiting parameters ────────────────────────
CHECK_INTERVAL = 1
MAX_WAIT_TIME = 90

# ── User data directories ─────────────────────────────
# Single per-user directory (see utils/platform_paths). On Windows this is the
# same %APPDATA%/ComfyLauncher as before — existing installs keep their data.
APP_DATA_DIR = app_dir()
THEMES_DIR = os.path.join(APP_DATA_DIR, "themes")

# ── Shared resources ─────────────────────────────
ICON_PATH = os.path.join(ICONS_DIR, "icon.png")
FLAGS_JSON_PATH = os.path.join(DATA_DIR, "flags.json")
SPLASH_PATH = os.path.join(SPLASH_DIR, "1618x616_qt.mp4")
ABOUT_LOGO_BG = os.path.join(INTERFACE_DIR, "back.png")
ABOUT_LOGO_ANIM = os.path.join(INTERFACE_DIR, "menu_anim.mp4")

# ── Set of icons for toolbar ──────────────────
ICON_PATHS = {
    "restart": os.path.join(ICONS_DIR, "restart.svg"),
    "stop": os.path.join(ICONS_DIR, "stop.svg"),
    "open_folder": os.path.join(ICONS_DIR, "open_folder.svg"),
    "open_browser": os.path.join(ICONS_DIR, "open_in_browser.svg"),
    "settings": os.path.join(ICONS_DIR, "settings.svg"),
    "open_output": os.path.join(ICONS_DIR, "output.svg"),
    "refresh": os.path.join(ICONS_DIR, "reload.svg"),
    "terminal": os.path.join(ICONS_DIR, "terminal.svg"),
    "plus": os.path.join(ICONS_DIR, "plus.svg"),
    "delete": os.path.join(ICONS_DIR, "delete.svg"),
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

DOODLE_ICON_PATHS = {
    "rhombus": os.path.join(DOODLES_DIR, "rhombus.svg"),
    "triangle": os.path.join(DOODLES_DIR, "triangle.svg"),
    "puzzle": os.path.join(DOODLES_DIR, "puzzle.svg"),
    "banana": os.path.join(DOODLES_DIR, "banana.svg"),
    "palette": os.path.join(DOODLES_DIR, "palette.svg"),
    "rocket": os.path.join(DOODLES_DIR, "rocket.svg"),
    "clover": os.path.join(DOODLES_DIR, "clover.svg"),
    "unicorn": os.path.join(DOODLES_DIR, "unicorn.svg"),
    "default": os.path.join(DOODLES_DIR, "default.svg"),
}
DEFAULT_DOODLE_ID = "default"

OTHER_ICONS = {
    "refresh": os.path.join(ICONS_DIR, "refresh.svg"),
    "clear-log": os.path.join(ICONS_DIR, "clear-log.svg"),
    "comfyui": os.path.join(ICONS_DIR, "comfyui-text.svg"),
}

# ── User config ───────────────────────────────
# Stored in %APPDATA% so it stays writable even for all-users installs
# (Program Files, where the in-app folder is read-only). LEGACY_* is the old
# in-app location, kept only for one-time migration of existing users.
USER_CONFIG_PATH = os.path.join(APP_DATA_DIR, "user_config.json")
LEGACY_USER_CONFIG_PATH = os.path.join(BASE_DIR, "user_config.json")

# ── Startup-mode → flags migration table ──────
# Legacy `startup_mode` was replaced by a plain `extra_flags` list (the single
# source of truth). This table only drives the one-time fold in the config
# migration below; it is not used at launch time anymore.
LAUNCH_PRESETS = {
    "cpu": ["--cpu", "--windows-standalone-build"],
    "gpu": ["--windows-standalone-build"],
    "fast_fp16": ["--windows-standalone-build", "--fast", "fp16_accumulation"],
}

DEFAULT_USER_CONFIG = {
    "ask_on_exit": True,
    "exit_mode": "always_stop",
    "browser_patch_registry": {},
    "builds": [],
    "last_used_build_id": "",
    "ui": {
        "show_manager_on_start": True,
    },
    "update_etag": None,
    "last_update_check": None,
    "update_interval_hours": 48,
    "updates_enabled": True,
}


def _migrate_legacy_config():
    """One-time move of a pre-%APPDATA% config from the in-app folder.

    Only runs when no config exists at the new location yet, so it never
    clobbers an existing one. Never raises.
    """
    if os.path.exists(USER_CONFIG_PATH):
        return
    if not os.path.exists(LEGACY_USER_CONFIG_PATH):
        return
    try:
        os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
        shutil.copy2(LEGACY_USER_CONFIG_PATH, USER_CONFIG_PATH)
        log_event(f"🗂 Migrated user config to {USER_CONFIG_PATH}")
    except Exception as e:
        log_event(f"⚠️ Failed to migrate user config: {e}")


def _migrate_build_flags(build: dict) -> None:
    """Fold a legacy `startup_mode` into `extra_flags` (single source of truth).

    In-place. `extra_flags` becomes the explicit flag list and the obsolete
    `startup_mode` field is dropped. Idempotent: builds without `startup_mode`
    (already migrated or written by the current UI) are left untouched.
    """
    if not isinstance(build, dict):
        return

    build.setdefault("extra_flags", [])

    if "startup_mode" not in build:
        return

    mode = str(build.get("startup_mode", "gpu"))
    old_extra = build.get("extra_flags") or []

    if mode == "custom":
        new_flags = list(old_extra)
    else:
        preset = LAUNCH_PRESETS.get(mode, LAUNCH_PRESETS["gpu"])
        new_flags = list(preset) + [f for f in old_extra if f not in preset]

    build["extra_flags"] = new_flags
    build.pop("startup_mode", None)


def load_user_config():
    _migrate_legacy_config()

    if not os.path.exists(USER_CONFIG_PATH):
        save_user_config(DEFAULT_USER_CONFIG)
        return DEFAULT_USER_CONFIG.copy()

    try:
        with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1) Дефолты верхнего уровня
        for key, val in DEFAULT_USER_CONFIG.items():
            data.setdefault(key, val)

        # 2) Migration: fold legacy startup_mode into extra_flags
        for b in data.get("builds") or []:
            _migrate_build_flags(b)

        return data

    except Exception:
        return DEFAULT_USER_CONFIG.copy()


def save_user_config(data: dict) -> bool:
    """Write the user config. Returns True on success, False on failure.

    Never raises and never shows UI — it is also called from background threads
    (e.g. the update checker). Callers on a UI path should check the return
    value and warn the user if it is False.
    """
    try:
        os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
        with open(USER_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"⚠️ Failed to save config: {e}")
        log_event(f"⚠️ Failed to save config: {e}")
        return False


def get_comfyui_path() -> str:
    """Returns the current path to ComfyUI (from user_config.json or default)."""
    data = load_user_config()
    return data.get("comfyui_path", "")
