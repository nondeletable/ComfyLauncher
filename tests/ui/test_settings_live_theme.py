"""Settings repaints in place when the theme changes.

Regression: the menu, page area, footer and most pages built their styles once,
from the theme active at construction, and kept them after THEME.switch. Only
the window frame, Color Themes and Logs followed the switch.
"""

import os
import re

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6 import sip  # noqa: E402
from PyQt6.QtWidgets import QFrame  # noqa: E402

from ui.settings.settings_window import SettingsWindow  # noqa: E402
from ui.theme.manager import THEME, THEMES  # noqa: E402

# dracula shares no color with dark, so any dark color left over is stale.
OLD, NEW = "dark", "dracula"
# Colors written into the styles literally, the same in every theme.
FIXED = {"#fff", "#555555"}
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def _colors(*widgets) -> set[str]:
    return {m.lower() for w in widgets for m in HEX.findall(w.styleSheet())}


def _theme(name) -> set[str]:
    return {v.lower() for v in THEMES[name].values() if isinstance(v, str)}


@pytest.fixture
def window(qapp):
    before = THEME.name
    THEME.switch(OLD)
    w = SettingsWindow(None)
    yield w
    if not sip.isdeleted(w):
        w._dirty_pages = lambda: []
        w.close()
    THEME.switch(before)


def test_the_window_parts_take_the_new_theme(window):
    parts = (
        window,
        window.findChild(QFrame, "settings_main_frame"),
        window.menu,
        window.pages,
        window.footer,
        window.btn_apply,
        window.btn_close,
    )
    assert _colors(*parts) & _theme(OLD)

    THEME.switch(NEW)

    colors = _colors(*parts)
    assert colors <= _theme(NEW) | FIXED
    assert THEMES[NEW]["bg_menu"].lower() in _colors(window.menu, window.footer)
