"""
Dev-only: screenshot translated windows in every language for a visual check.

NOT shipped to users. Opens each registered screen once per language, saves
PNGs to ``build/i18n_screens/<screen>/<lang>.png`` and exits. The launcher runs
against a throwaway config with one demo build, so your real
``user_config.json`` is neither shown nor touched.

Usage
-----
    python tools/i18n_screens.py [lang ...]     # default: every language

Windows flash on screen while they are captured: real fonts and DPI matter here,
which the offscreen platform would hide.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "build", "i18n_screens")

# Before any project import: config.py resolves its paths at import time.
_CONFIG_HOME = tempfile.mkdtemp(prefix="comfylauncher-i18n-")
os.environ["COMFYLAUNCHER_CONFIG_HOME"] = _CONFIG_HOME
sys.path.insert(0, ROOT)
# The app prints emoji status lines; a cp1252 console would crash on them.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from config import USER_CONFIG_PATH  # noqa: E402
from utils.i18n import I18N, LANGUAGES  # noqa: E402

DEMO_CONFIG = {
    "ask_on_exit": True,
    "builds": [
        {
            "id": "demo",
            "name": "ComfyUI Portable",
            "path": "D:/Portable/ComfyUI",
            "icon_id": "default",
            "extra_flags": ["--windows-standalone-build"],
        }
    ],
}


def _settings_window(save):
    """Every page of the Settings window, one PNG per page."""
    from ui.settings.settings_window import _MENU_KEYS, SettingsWindow

    w = SettingsWindow(None)
    w.show()
    for row, key in enumerate(_MENU_KEYS):
        w.menu.setCurrentRow(row)
        QApplication.processEvents()
        save(f"settings_{key.rsplit('.', 1)[-1]}", w)
    w._dirty_pages = lambda: []
    w.close()


# Every i18n block registers the screens it translated.
SCREENS = [_settings_window]


def main(languages: list[str]) -> None:
    os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
    with open(USER_CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(DEMO_CONFIG, fh)

    app = QApplication(sys.argv)
    from ui.theme.manager import THEME

    THEME.apply()
    for code in languages:
        I18N.set_language(code)

        def save(name, widget, code=code):
            folder = os.path.join(OUT_DIR, name)
            os.makedirs(folder, exist_ok=True)
            widget.grab().save(os.path.join(folder, f"{code}.png"))

        for screen in SCREENS:
            screen(save)
    app.quit()
    print(f"Screenshots: {OUT_DIR}")


if __name__ == "__main__":
    wanted = sys.argv[1:] or list(LANGUAGES)
    unknown = [c for c in wanted if c not in LANGUAGES]
    if unknown:
        sys.exit(f"Unknown language(s): {', '.join(unknown)}")
    main(wanted)
