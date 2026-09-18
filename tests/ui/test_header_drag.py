"""Window dragging must go through the compositor off Windows.

Wayland ignores a client's own move(), so the frameless window did not follow
the mouse at all; startSystemMove() asks the compositor to run the drag.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys  # noqa: E402

import pytest  # noqa: E402
from PyQt6.QtCore import QPoint, QPointF, Qt  # noqa: E402
from PyQt6.QtGui import QMouseEvent  # noqa: E402
from PyQt6.QtWidgets import QMainWindow  # noqa: E402

from ui.header import HeaderBar  # noqa: E402


class FakeHandle:
    def __init__(self, supported=True):
        self.supported = supported
        self.calls = 0

    def startSystemMove(self):
        self.calls += 1
        return self.supported


def fake_out(window, monkeypatch, handle):
    """Give a real window a stubbed handle and record its move() calls.

    HeaderBar needs a live QWidget parent — it connects the window buttons to
    parent.showMinimized and friends while constructing — so the parent is a
    real QMainWindow with only these two methods replaced.
    """
    moves = []
    monkeypatch.setattr(window, "windowHandle", lambda: handle)
    monkeypatch.setattr(window, "move", lambda point: moves.append(point))
    monkeypatch.setattr(window, "pos", lambda: QPoint(100, 100))
    return moves


def press(header, x=10, y=10):
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(x, y),
        QPointF(x, y),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    header.mousePressEvent(event)


def drag(header, x=30, y=20):
    event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(x, y),
        QPointF(x, y),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    header.mouseMoveEvent(event)


@pytest.fixture
def window(qapp):
    win = QMainWindow()
    yield win
    win.close()
    win.deleteLater()


@pytest.fixture
def header(window):
    return HeaderBar(window)


def test_non_windows_hands_the_drag_to_the_compositor(header, window, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    handle = FakeHandle(supported=True)
    moves = fake_out(window, monkeypatch, handle)

    press(header)
    drag(header)

    assert handle.calls == 1
    # The compositor owns the drag, so we must not also move() the window.
    assert moves == []


def test_windows_keeps_the_manual_move(header, window, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    handle = FakeHandle(supported=True)
    moves = fake_out(window, monkeypatch, handle)

    press(header)
    drag(header)

    assert handle.calls == 0, "startSystemMove would also enable native snapping"
    assert len(moves) == 1


def test_falls_back_to_manual_move_when_unsupported(header, window, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    handle = FakeHandle(supported=False)
    moves = fake_out(window, monkeypatch, handle)

    press(header)
    drag(header)

    assert handle.calls == 1
    assert len(moves) == 1


def test_release_clears_the_system_move_flag(header, window, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    fake_out(window, monkeypatch, FakeHandle(supported=True))

    press(header)
    assert header._system_move_active is True
    header.mouseReleaseEvent(None)
    assert header._system_move_active is False
