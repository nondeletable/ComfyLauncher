"""Settings and the console open over the main window, on its screen.

Regression: both centred themselves on the primary monitor (and from its size
alone, ignoring where that screen sits on the desktop), so with the launcher on
a second monitor they popped up on the other one.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtCore import QPoint, QRect, QSize  # noqa: E402
from PyQt6.QtWidgets import QWidget  # noqa: E402

from ui.browser import ComfyBrowser  # noqa: E402
from ui.dialogs.console_window import ConsoleWindow  # noqa: E402
from ui.settings.settings_window import SettingsWindow  # noqa: E402
from ui.window_placement import (  # noqa: E402
    center_over,
    centered_top_left,
    is_off_screen,
)

# A second monitor to the right of a 1920x1080 primary, taskbar at the bottom.
SECOND = QRect(1920, 0, 2560, 1400)


def test_centred_over_the_anchor_on_its_own_screen():
    anchor = QRect(2200, 200, 1600, 900)
    assert centered_top_left(QSize(400, 300), anchor, SECOND) == QPoint(2800, 500)


def test_anchor_on_a_screen_left_of_and_above_the_primary():
    screen = QRect(-1920, -300, 1920, 1040)
    anchor = QRect(-1800, -200, 1000, 600)
    assert centered_top_left(QSize(400, 200), anchor, screen) == QPoint(-1500, 0)


def test_anchor_partly_past_the_right_edge_keeps_the_window_inside():
    anchor = QRect(4000, 100, 1000, 600)
    pos = centered_top_left(QSize(800, 400), anchor, SECOND)
    assert pos == QPoint(SECOND.x() + SECOND.width() - 800, 200)


def test_anchor_partly_above_and_left_of_the_screen():
    anchor = QRect(1500, -400, 800, 600)
    assert centered_top_left(QSize(600, 400), anchor, SECOND) == QPoint(1920, 0)


def test_window_larger_than_the_screen_is_pinned_to_its_top_left():
    small = QRect(1920, 40, 1280, 680)
    pos = centered_top_left(QSize(1230, 730), QRect(1920, 40, 1280, 680), small)
    assert pos == QPoint(1945, 40)
    pos = centered_top_left(QSize(1400, 730), QRect(2000, 100, 600, 400), small)
    assert pos == QPoint(1920, 40)


def test_maximized_anchor_centres_on_the_screen():
    pos = centered_top_left(QSize(1230, 730), SECOND, SECOND)
    assert pos == QPoint(1920 + (2560 - 1230) // 2, (1400 - 730) // 2)


# ─── Real widgets on the offscreen platform ────────────────────────────


@pytest.fixture
def available(qapp):
    return qapp.primaryScreen().availableGeometry()


@pytest.fixture
def anchor(qapp):
    """Stand-in for ComfyBrowser: the attributes open_settings/console touch."""
    win = QWidget()
    win.settings_window = None
    win.console_window = None
    win._on_settings_destroyed = lambda *a: setattr(win, "settings_window", None)
    yield win
    for child in (win.settings_window, win.console_window):
        if child is not None:
            child.hide()
            child.deleteLater()
    win.deleteLater()


def test_center_over_a_small_window(anchor, available):
    anchor.setGeometry(available.x() + 100, available.y() + 50, 400, 300)
    win = QWidget()
    win.setFixedSize(200, 100)
    center_over(win, anchor)
    assert win.pos() == QPoint(available.x() + 200, available.y() + 150)
    win.deleteLater()


def test_anchor_off_its_screen_centres_on_the_screen(anchor, available):
    # Windows parks a minimized window at -32000,-32000.
    anchor.setGeometry(-32000, -32000, 160, 28)
    win = QWidget()
    win.setFixedSize(200, 100)
    center_over(win, anchor)
    assert win.frameGeometry().center() == available.center()
    win.deleteLater()


def test_settings_open_over_the_main_window_inside_the_screen(anchor, available):
    anchor.setGeometry(available.x() + 300, available.y() + 200, 400, 300)
    ComfyBrowser.open_settings(anchor)
    settings = anchor.settings_window
    assert isinstance(settings, SettingsWindow)
    assert settings.isVisible()
    expected = centered_top_left(settings.size(), anchor.frameGeometry(), available)
    assert settings.pos() == expected
    assert settings.x() >= available.x() and settings.y() >= available.y()


def test_console_centres_on_first_show_then_stays_where_it_was_left(anchor, available):
    anchor.setGeometry(available.x() + 300, available.y() + 200, 400, 300)
    ComfyBrowser.open_console_logs(anchor)
    console = anchor.console_window
    assert isinstance(console, ConsoleWindow)
    assert console.pos() == centered_top_left(
        console.size(), anchor.frameGeometry(), available
    )

    left_at = QPoint(available.x() + 10, available.y() + 20)
    console.move(left_at)
    console.hide()
    anchor.move(available.x() + 50, available.y() + 60)
    ComfyBrowser.open_console_logs(anchor)
    assert console.pos() == left_at


def test_console_left_off_screen_comes_back_over_the_main_window(anchor, available):
    ComfyBrowser.open_console_logs(anchor)
    console = anchor.console_window
    console.move(-50000, -50000)
    assert is_off_screen(console)
    console.hide()
    ComfyBrowser.open_console_logs(anchor)
    assert not is_off_screen(console)
    assert console.pos() == centered_top_left(
        console.size(), anchor.frameGeometry(), available
    )
