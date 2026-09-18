"""The main window needs a sane size for when it is not maximized.

It is always shown maximized, and nothing set a normal size, so un-maximizing
it — by dragging it off the top edge, which only became possible once the
Wayland drag fix landed, or with the restore button — dropped it to Qt's
640x480 default. Its size hint is the header strip alone (765x46).
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtCore import QSize  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from ui.browser import ComfyBrowser  # noqa: E402


@pytest.fixture
def browser(qapp, monkeypatch):
    # Constructing the window would otherwise spawn ComfyUI and a splash.
    monkeypatch.setattr(ComfyBrowser, "_start_comfyui", lambda self: None)
    win = ComfyBrowser()
    yield win
    win.close()
    win.deleteLater()


@pytest.fixture
def available():
    return QApplication.primaryScreen().availableGeometry()


def test_normal_size_is_most_of_the_screen(browser, available):
    assert browser.width() == int(available.width() * 0.8)
    assert browser.height() == int(available.height() * 0.8)


def test_minimum_size_is_set_and_fits_the_screen(browser, available):
    assert browser.minimumWidth() > 0
    assert browser.minimumHeight() > 0
    # Capped against the normal size, so it cannot exceed a small screen.
    assert browser.minimumWidth() <= browser.width()
    assert browser.minimumHeight() <= browser.height()
    assert browser.minimumWidth() <= available.width()
    assert browser.minimumHeight() <= available.height()


def test_restoring_from_maximized_keeps_the_normal_size(browser, qapp):
    normal = browser.size()
    browser.showMaximized()
    qapp.processEvents()
    browser.showNormal()
    qapp.processEvents()

    assert browser.size() == normal


def test_restore_size_is_not_the_qt_default(browser):
    """Regression: the window fell back to Qt's 640x480 default, whose height
    is not far off the header strip (765x46) that is its only size hint."""
    assert browser.size() != QSize(640, 480)
    assert browser.height() > browser.header.height() * 4
    assert browser.height() >= browser.minimumHeight()
