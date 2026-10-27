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
        },
        {
            "id": "demo2",
            "name": "SDXL test",
            "path": "E:/AI/ComfyUI_sdxl",
            "icon_id": "default",
            "extra_flags": [],
        },
    ],
    "last_used_build_id": "demo",
}


def _shoot(save, name, widget):
    widget.show()
    QApplication.processEvents()
    save(name, widget)
    widget.close()


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


def _first_run(save):
    """The setup window as on first run (with the language list), list open too."""
    from ui.dialogs.setup_window import SetupWindow

    w = SetupWindow()
    w.show()
    QApplication.processEvents()
    save("setup_first_run", w)
    w.language_combo.showPopup()
    QApplication.processEvents()
    save("setup_language_list", w.language_combo.view().window())
    w.language_combo.hidePopup()
    w.close()


def _build_manager(save):
    from ui.dialogs.build_manager_dialog import BuildManagerDialog

    _shoot(save, "build_manager", BuildManagerDialog())


def _flags_picker(save):
    from ui.dialogs.flags_picker_dialog import FlagsPickerDialog

    _shoot(save, "flags_picker", FlagsPickerDialog(flags_text="--lowvram --listen"))


def _message_boxes(save):
    """The longest first-run boxes, buttons as their real callers add them."""
    from ui.dialogs.messagebox import MessageBox
    from utils.i18n import t

    boxes = {
        "box_nonportable": (
            "setup.nonportable.title",
            t(
                "setup.nonportable.text",
                reason=t("setup.nonportable.reason_windows"),
            ),
            "ask_yes_no",
            ["common.yes", "common.no"],
        ),
        "box_restore": (
            "restore.ask.title",
            t("restore.ask.text", path="D:/Documents/ComfyLauncher/backup"),
            "ask_yes_no",
            ["common.yes", "common.no"],
        ),
        "box_webview2": (
            "webview2.title",
            t("webview2.ask"),
            "warning",
            ["webview2.button.install", "webview2.button.page", "webview2.button.quit"],
        ),
    }
    for name, (title, text, kind, buttons) in boxes.items():
        box = MessageBox(t(title), text, kind)
        for key in buttons:
            box._add_button(t(key), "accept")
        _shoot(save, name, box)


def _main_window(save):
    """The main window's own parts: it needs a live ComfyUI to show whole."""
    import time

    from PyQt6.QtWidgets import QMainWindow, QWidget

    from ui.browser import StartingWidget
    from ui.dialogs.console_window import ConsoleWindow
    from ui.dialogs.messagebox import MessageBox
    from ui.dialogs.slow_start_notice import SlowStartNotice
    from ui.header import STATUSES, HeaderBar
    from ui.webview.placeholder import PlaceholderWebView
    from utils.i18n import t

    win = QMainWindow()
    win.resize(1100, 46)
    header = HeaderBar(win)
    win.setMenuWidget(header)
    win.show()
    for status in STATUSES:
        header.set_status(status)
        QApplication.processEvents()
        save(f"header_{status}", header)
    win.close()

    starting = StartingWidget()
    starting.resize(600, 200)
    _shoot(save, "starting", starting)
    _shoot(save, "slow_start", SlowStartNotice(time.monotonic() - 95))
    _shoot(save, "console", ConsoleWindow())
    placeholder = PlaceholderWebView("http://127.0.0.1:8188")
    placeholder.resize(700, 400)
    _shoot(save, "placeholder", placeholder)

    if sys.platform == "win32":
        from ui.webview2_widget import _DownloadToast

        anchor = QWidget()
        anchor.resize(700, 300)
        anchor.show()
        toast = _DownloadToast()
        toast.show_saved(
            "ComfyUI_00042_.png", "D:/Downloads/ComfyUI_00042_.png", anchor
        )
        QApplication.processEvents()
        save("toast_saved", toast)
        toast.close()
        anchor.close()

    boxes = {
        "box_stop": (
            "main.stop.title",
            t("main.stop.text"),
            "ask_yes_no",
            ["common.yes", "common.no"],
        ),
        "box_exit": (
            "main.exit.title",
            t("main.exit.text"),
            "ask_yes_no",
            ["common.yes", "common.no", "common.cancel"],
        ),
        "box_update": (
            "update.title",
            t("update.text", latest="1.11.0", current="1.10.1"),
            "info",
            ["update.button.update", "update.button.postpone"],
        ),
    }
    for name, (title, text, kind, buttons) in boxes.items():
        box = MessageBox(t(title), text, kind)
        for key in buttons:
            box._add_button(t(key), "accept")
        _shoot(save, name, box)


# Every i18n block registers the screens it translated.
SCREENS = [
    _settings_window,
    _first_run,
    _build_manager,
    _flags_picker,
    _message_boxes,
    _main_window,
]


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
