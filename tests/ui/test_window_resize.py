"""The frameless main window must resize from its edges and minimize from the taskbar.

A frameless window has no OS border to grab, so it could not be resized at
all. On Windows it also lost WS_MINIMIZEBOX, so a taskbar click restored the
window but never minimized it again.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys  # noqa: E402

import pytest  # noqa: E402
from PyQt6.QtCore import QPoint, QRect, Qt  # noqa: E402

from ui.browser import ComfyBrowser  # noqa: E402
from ui.window_resize import RESIZE_MARGIN, edges_at  # noqa: E402

RECT = QRect(0, 0, 800, 600)


@pytest.fixture
def browser(qapp, monkeypatch):
    # Constructing the window would otherwise spawn ComfyUI and a splash.
    monkeypatch.setattr(ComfyBrowser, "_start_comfyui", lambda self: None)
    win = ComfyBrowser()
    yield win
    win.close()
    win.deleteLater()


@pytest.mark.parametrize(
    "pos, expected",
    [
        (QPoint(400, 300), Qt.Edge(0)),
        (QPoint(0, 300), Qt.Edge.LeftEdge),
        (QPoint(799, 300), Qt.Edge.RightEdge),
        (QPoint(400, 0), Qt.Edge.TopEdge),
        (QPoint(400, 599), Qt.Edge.BottomEdge),
        (QPoint(0, 0), Qt.Edge.LeftEdge | Qt.Edge.TopEdge),
        (QPoint(799, 599), Qt.Edge.RightEdge | Qt.Edge.BottomEdge),
        (QPoint(RESIZE_MARGIN, 300), Qt.Edge(0)),
    ],
)
def test_edges_at(pos, expected):
    assert edges_at(pos, RECT) == expected


def test_content_leaves_a_resize_strip_when_normal(browser, qapp):
    browser.showNormal()
    qapp.processEvents()
    m = browser.centralWidget().layout().contentsMargins()
    assert (m.left(), m.top(), m.right(), m.bottom()) == (
        RESIZE_MARGIN,
        0,
        RESIZE_MARGIN,
        RESIZE_MARGIN,
    )


def test_no_resize_strip_when_maximized(browser, qapp):
    browser.showMaximized()
    qapp.processEvents()
    m = browser.centralWidget().layout().contentsMargins()
    assert (m.left(), m.top(), m.right(), m.bottom()) == (0, 0, 0, 0)


@pytest.mark.skipif(sys.platform != "win32", reason="WS_MINIMIZEBOX is Windows-only")
def test_window_keeps_its_minimize_box_on_windows(browser):
    assert browser.windowFlags() & Qt.WindowType.WindowMinimizeButtonHint
    assert browser.windowFlags() & Qt.WindowType.FramelessWindowHint
