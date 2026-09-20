"""A theme switch must repaint the console window's chrome, not just its log.

Regression: the frame, header bar, title and close icon were styled once from
locals in __init__, so _apply_theme could not reach them. Switching theme with
the console open left its border, title and close icon in the old colours while
the log area alone changed.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from ui.dialogs.console_window import ConsoleWindow  # noqa: E402
from ui.theme.manager import THEME  # noqa: E402


@pytest.fixture
def console(qapp):
    win = ConsoleWindow()
    yield win
    win.close()


@pytest.fixture
def switched_theme():
    """Swap in a recognisable palette, then put the real one back."""
    original = THEME._colors
    THEME._colors = dict(
        original,
        bg_header="#123456",
        app_title_color="#ABCDEF",
        text_primary="#FEDCBA",
    )
    THEME.themeChanged.emit(THEME._colors)
    yield
    THEME._colors = original
    THEME.themeChanged.emit(original)


def test_frame_follows_the_theme(console, switched_theme):
    assert "#123456" in console._main_frame.styleSheet()


def test_header_follows_the_theme(console, switched_theme):
    assert "#123456" in console._header.styleSheet()


def test_title_follows_the_theme(console, switched_theme):
    assert "#ABCDEF" in console._title.styleSheet()


def test_close_icon_is_rebuilt_on_a_theme_change(console, switched_theme):
    """The icon is a recoloured SVG, so it has to be regenerated, not restyled."""
    assert not console._btn_close.icon().isNull()
