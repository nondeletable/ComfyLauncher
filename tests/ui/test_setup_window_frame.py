"""The setup window must move by its empty spots and minimize from the taskbar.

It was a frameless dialog with no move logic, so it stayed where it opened, and
on Windows it lost WS_MINIMIZEBOX, so a taskbar click could not minimize it.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys  # noqa: E402

import pytest  # noqa: E402
from PyQt6.QtCore import QPoint, QPointF, Qt  # noqa: E402
from PyQt6.QtGui import QMouseEvent  # noqa: E402
from PyQt6.QtWidgets import QApplication, QLabel, QWidget  # noqa: E402

import ui.dialogs.setup_window as sw  # noqa: E402


@pytest.fixture
def dialog(qapp):
    dlg = sw.SetupWindow()
    dlg.move(100, 100)
    dlg.show()
    qapp.processEvents()
    yield dlg
    dlg.close()
    dlg.deleteLater()


@pytest.fixture
def manual_move(monkeypatch):
    # Windows moves the window itself; elsewhere the compositor would.
    monkeypatch.setattr(sys, "platform", "win32")


def send(kind, target, local, buttons):
    button = Qt.MouseButton.NoButton
    if kind != QMouseEvent.Type.MouseMove:
        button = Qt.MouseButton.LeftButton
    event = QMouseEvent(
        kind,
        QPointF(local),
        QPointF(target.mapToGlobal(local)),
        button,
        buttons,
        Qt.KeyboardModifier.NoModifier,
    )
    # sendEvent, not a direct handler call: an ignored press has to travel up
    # to the dialog the way a real click does.
    QApplication.sendEvent(target, event)


def drag(target, local, delta=QPoint(40, 30)):
    left = Qt.MouseButton.LeftButton
    send(QMouseEvent.Type.MouseButtonPress, target, local, left)
    send(QMouseEvent.Type.MouseMove, target, local + delta, left)
    send(QMouseEvent.Type.MouseButtonRelease, target, local + delta, left)


def test_drag_by_an_empty_spot_moves_the_window(dialog, manual_move):
    start = dialog.pos()
    drag(dialog.main_frame, QPoint(dialog.main_frame.width() - 20, 250))
    assert dialog.pos() - start == QPoint(40, 30)


def test_drag_on_the_info_label_moves_the_window(dialog, manual_move):
    # The rich-text hint at the top is the most natural spot to grab.
    info = next(
        label
        for label in dialog.findChildren(QLabel)
        if label.text().startswith("Specify the folder")
    )
    start = dialog.pos()
    drag(info, QPoint(10, 10))
    assert dialog.pos() - start == QPoint(40, 30)


@pytest.mark.parametrize(
    "control",
    [
        lambda d: d.path_edit,
        lambda d: d.name_edit,
        lambda d: d.flags_edit,
        lambda d: d.cancel_btn,
        lambda d: d.doodle_group.buttons()[0],
    ],
    ids=["path", "name", "flags", "cancel", "doodle"],
)
def test_drag_on_a_control_leaves_the_window_in_place(dialog, control):
    target: QWidget = control(dialog)
    start = dialog.pos()
    drag(target, QPoint(10, 10))
    assert dialog.pos() == start


@pytest.mark.skipif(sys.platform != "win32", reason="WS_MINIMIZEBOX is Windows-only")
def test_first_run_window_keeps_its_minimize_box_on_windows(qapp):
    assert sw.SetupWindow().windowFlags() & Qt.WindowType.WindowMinimizeButtonHint


def test_owned_window_gets_no_minimize_box(qapp):
    # Over the selector it has no taskbar button; a minimize box would only let
    # Win+Down shrink it alone while the selector under it stays disabled.
    owner = QWidget()
    dlg = sw.SetupWindow(owner)
    assert not dlg.windowFlags() & Qt.WindowType.WindowMinimizeButtonHint
    owner.deleteLater()
