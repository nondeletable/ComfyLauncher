"""The frameless main window must minimize from a taskbar click on Windows.

A frameless window loses WS_MINIMIZEBOX there, so a taskbar click restored the
window but never minimized it again.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys  # noqa: E402

import pytest  # noqa: E402
from PyQt6.QtCore import Qt  # noqa: E402

from ui.browser import ComfyBrowser  # noqa: E402


@pytest.fixture
def browser(qapp, monkeypatch):
    # Constructing the window would otherwise spawn ComfyUI and a splash.
    monkeypatch.setattr(ComfyBrowser, "_start_comfyui", lambda self: None)
    win = ComfyBrowser()
    yield win
    win.close()
    win.deleteLater()


@pytest.mark.skipif(sys.platform != "win32", reason="WS_MINIMIZEBOX is Windows-only")
def test_window_keeps_its_minimize_box_on_windows(browser):
    assert browser.windowFlags() & Qt.WindowType.WindowMinimizeButtonHint
    assert browser.windowFlags() & Qt.WindowType.FramelessWindowHint
