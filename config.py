import json
import os
import shutil
import sys
import time
import uuid

from utils.logger import log_event
from utils.platform_paths import APP_NAME, app_dir

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

# ── User config backup ────────────────────────
# %APPDATA% does not survive a Windows reinstall, so every save is mirrored to
# a backup outside it: the app folder when it is writable, else Documents.
BACKUP_DIR_NAME = "backup"
BACKUP_FILE_NAME = "user_config.json"

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


def _app_backup_dir():
    """Backup folder next to the exe of a frozen build; None from source.

    From source the "app folder" is the git checkout, and a backup there would
    show up as an untracked folder, so a dev run goes straight to Documents.
    """
    if not getattr(sys, "frozen", False):
        return None
    return os.path.join(os.path.dirname(sys.executable), BACKUP_DIR_NAME)


def _documents_backup_dir():
    """Documents/ComfyLauncher/backup, or None if the OS reports no Documents.

    QStandardPaths resolves the real Documents folder (SHGetKnownFolderPath on
    Windows, so a relocated or OneDrive-redirected one is honoured).
    """
    from PyQt6.QtCore import QStandardPaths

    docs = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DocumentsLocation
    )
    if not docs:
        return None
    return os.path.join(os.path.normpath(docs), APP_NAME, BACKUP_DIR_NAME)


def _backup_paths() -> list:
    """Backup file locations in order of preference."""
    dirs = (_app_backup_dir(), _documents_backup_dir())
    return [os.path.join(d, BACKUP_FILE_NAME) for d in dirs if d]


def _has_builds(raw: bytes) -> bool:
    """True if raw is a JSON config with at least one build.

    A config without builds is the first-run default (or a wiped file), and
    backing it up would overwrite a backup that still holds the user's builds.
    """
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return False
    return isinstance(data, dict) and bool(data.get("builds"))


def _read_bytes(path: str):
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return None


def _write_verified(path: str, raw: bytes) -> bool:
    """Atomically write raw to path and confirm by reading it back. Never raises.

    The temp file is checked before it replaces the target, so a bad write
    never takes the place of a good file; the target is checked again after.
    """
    tmp = path + ".tmp"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(tmp, "wb") as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        if _read_bytes(tmp) != raw:
            raise OSError("temp file content does not match")
        os.replace(tmp, path)
        if _read_bytes(path) != raw:
            raise OSError("written file content does not match")
        return True
    except OSError as e:
        log_event(f"⚠️ Could not write {path}: {e}")
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False


def backup_user_config():
    """Mirror user_config.json to the first backup location that verifies.

    Returns the backup path, or None if there was nothing to back up or no
    location could be written and verified. Never raises and never shows UI —
    it runs inside save_user_config, which background threads call too.
    """
    raw = _read_bytes(USER_CONFIG_PATH)
    if raw is None or not _has_builds(raw):
        return None
    for path in _backup_paths():
        if _write_verified(path, raw):
            log_event(f"💾 User config backed up to {path}")
            return path
    log_event("⚠️ User config backup failed: no location could be written")
    return None


def user_config_restore_candidate():
    """The backup to offer for restore on startup, or None.

    Offered only when %APPDATA% has no config, or one that is still exactly
    DEFAULT_USER_CONFIG — what the first load_user_config() writes, which may
    already have run by the time main.py gets here. A real config is never
    offered over, even with zero builds (the user may have removed them on
    purpose), and neither is one that exists but cannot be read or parsed.
    With several backups the newest wins. A legacy in-app config with builds
    (which _migrate_legacy_config would copy in) takes precedence unless the
    backup is newer: the legacy file is copied, not moved, so on an upgraded
    install it can be a stale leftover.
    """
    if os.path.exists(USER_CONFIG_PATH) and not _is_untouched_default():
        return None
    found = []
    for path in _backup_paths():
        raw = _read_bytes(path)
        if raw is not None and _has_builds(raw):
            found.append(path)
    newest = max(found, key=os.path.getmtime, default=None)
    legacy = _read_bytes(LEGACY_USER_CONFIG_PATH)
    if newest and legacy is not None and _has_builds(legacy):
        if os.path.getmtime(LEGACY_USER_CONFIG_PATH) >= os.path.getmtime(newest):
            return None
    return newest


def _is_untouched_default() -> bool:
    raw = _read_bytes(USER_CONFIG_PATH)
    if raw is None:
        return False
    try:
        return json.loads(raw.decode("utf-8")) == DEFAULT_USER_CONFIG
    except Exception:
        return False


def restore_user_config(backup_path: str) -> bool:
    """Copy a backup into %APPDATA%, verified. Returns True on success.

    A config already in place is first kept as user_config.json.before-restore;
    if that copy cannot be made, nothing is restored.
    """
    raw = _read_bytes(backup_path)
    ok = raw is not None and _has_builds(raw)
    if ok and os.path.exists(USER_CONFIG_PATH):
        current = _read_bytes(USER_CONFIG_PATH)
        ok = current is not None and _write_verified(
            USER_CONFIG_PATH + ".before-restore", current
        )
    if not ok or not _write_verified(USER_CONFIG_PATH, raw):
        log_event(f"⚠️ Failed to restore user config from {backup_path}")
        return False
    log_event(f"🗂 Restored user config from {backup_path}")
    return True


def set_aside_user_config_backup(backup_path: str) -> None:
    """Rename a declined backup so it is neither offered again nor overwritten.

    Without this the next save after a declined restore would replace the
    only copy of the user's old settings. The file is renamed, never deleted.
    """
    stamp = time.strftime("%Y%m%d-%H%M%S")
    aside = os.path.join(
        os.path.dirname(backup_path), f"user_config.declined-{stamp}.json"
    )
    try:
        os.replace(backup_path, aside)
        log_event(f"🗂 Declined config backup kept as {aside}")
    except OSError as e:
        log_event(f"⚠️ Could not set aside declined backup {backup_path}: {e}")


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


def _ensure_build_id(build: dict) -> bool:
    """Give a legacy build a stable `id` if it has none. Returns True if changed.

    Builds are matched by `id` everywhere (edit, delete, last_used_build_id), so
    a build without one cannot be edited in place — the edit is saved as a new
    build instead. The id must be persisted (see load_user_config): a fresh
    random id on every load would never match the one the editor captured.
    """
    if not isinstance(build, dict):
        return False
    if not str(build.get("id", "")).strip():
        build["id"] = str(uuid.uuid4())
        return True
    return False


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

        # 2) Migration: fold legacy startup_mode into extra_flags, and backfill
        #    a stable id for any build that predates id-based identification.
        needs_save = False
        for b in data.get("builds") or []:
            _migrate_build_flags(b)
            if _ensure_build_id(b):
                needs_save = True

        # Persist backfilled ids so they stay stable across loads.
        if needs_save:
            save_user_config(data)

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
    except Exception as e:
        print(f"⚠️ Failed to save config: {e}")
        log_event(f"⚠️ Failed to save config: {e}")
        return False
    backup_user_config()
    return True


def get_comfyui_path() -> str:
    """Returns the current path to ComfyUI (from user_config.json or default)."""
    data = load_user_config()
    return data.get("comfyui_path", "")
