"""Rounded corners have to survive the platform's masking rules.

Regression: the window's corners were rounded with setMask on the window
itself. Wayland has no shape extension — QWaylandWindow::setMask narrows the
*input* region only — so the pixels stayed square there while Windows and X11
clipped natively. On Wayland the mask now goes on the central container, which
Qt clips itself.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtGui import QGuiApplication  # noqa: E402

from ui.browser import ComfyBrowser  # noqa: E402


@pytest.fixture
def browser(qapp, monkeypatch):
    # Constructing the window would otherwise spawn ComfyUI and a splash.
    monkeypatch.setattr(ComfyBrowser, "_start_comfyui", lambda self: None)
    win = ComfyBrowser()
    yield win
    win.close()
    win.deleteLater()


def test_native_platforms_keep_masking_the_window(browser):
    """Windows and X11 clip a window mask, so nothing there changes."""
    if not browser._clips_window_mask:
        pytest.skip("this session runs on Wayland")
    browser._round_corners(10)
    mask = browser.mask()
    assert not mask.isEmpty()
    assert not mask.contains(browser.rect().topLeft())
    assert mask.contains(browser.rect().center())


def test_wayland_rounds_the_container_and_goes_translucent(qapp, monkeypatch):
    monkeypatch.setattr(
        QGuiApplication, "platformName", staticmethod(lambda: "wayland")
    )
    monkeypatch.setattr(ComfyBrowser, "_start_comfyui", lambda self: None)
    win = ComfyBrowser()
    try:
        from PyQt6.QtCore import Qt

        assert win.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        win._round_corners(10)
        central = win.centralWidget()
        mask = central.mask()
        assert not mask.isEmpty(), "the container carries the rounding on Wayland"
        assert not mask.contains(central.rect().topLeft())
        assert mask.contains(central.rect().center())
        # The window mask would be a no-op there, so it must not be relied on.
        assert win.mask().isEmpty()
    finally:
        win.close()
        win.deleteLater()


def test_the_region_actually_cuts_the_corner(browser):
    """A radius that never reaches the corner would silently do nothing."""
    from PyQt6.QtCore import QPoint, QRect

    region = ComfyBrowser._rounded_region(QRect(0, 0, 200, 200), 20)
    assert not region.contains(QPoint(0, 0))
    assert region.contains(QPoint(100, 100))
    assert region.contains(QPoint(199, 100))
