"""A MessageBox opens over its parent's window, inside that window's screen.

Regression: a ``showEvent`` override moved the box to the centre of
``parent.frameGeometry()``. For a settings page - a child widget inside a
QStackedWidget - that rectangle is in the page's parent's coordinates, about
(0, 0) to the page size, and the box landed near the top-left of the primary
monitor. QDialog places a modal box by itself: over ``parent.window()``, on
that window's screen, inside its available geometry.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6 import sip  # noqa: E402
from PyQt6.QtCore import QMargins  # noqa: E402
from PyQt6.QtGui import QGuiApplication  # noqa: E402
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget  # noqa: E402

from ui.dialogs.messagebox import MessageBox  # noqa: E402

# Qt rounds the centre its own way; a pixel or two either side is the same spot.
TOLERANCE = 3


@pytest.fixture
def available(qapp):
    return qapp.primaryScreen().availableGeometry()


@pytest.fixture
def window(qapp):
    win = QWidget()
    yield win
    win.hide()
    sip.delete(win)


@pytest.fixture
def shown():
    """Show a box over ``parent``; every box is deleted at teardown.

    ``deleteLater`` would never run without an event loop, and a live box stays
    connected to ``THEME.themeChanged`` for the rest of the session.
    """
    boxes = []

    def show(parent, size=None):
        box = MessageBox("Title", "Text", "warning", parent)
        box._add_button("OK", "accept")
        if size is not None:
            box.setFixedSize(size)
        box.show()
        boxes.append(box)
        return box

    yield show
    for box in boxes:
        box.hide()
        sip.delete(box)


def _assert_centred_over(box, win):
    delta = box.frameGeometry().center() - win.frameGeometry().center()
    assert abs(delta.x()) <= TOLERANCE and abs(delta.y()) <= TOLERANCE


def test_page_parent_lands_over_the_page_window(window, available, shown):
    window.setGeometry(available.x() + 300, available.y() + 200, 400, 300)
    stack = QStackedWidget(window)
    page = QWidget()
    stack.addWidget(page)
    QVBoxLayout(window).addWidget(stack)
    window.show()

    box = shown(page)
    _assert_centred_over(box, window)
    assert available.contains(box.frameGeometry())


def test_window_parent_lands_over_the_window(window, available, shown):
    window.setGeometry(available.x() + 250, available.y() + 150, 500, 400)
    window.show()

    box = shown(window)
    _assert_centred_over(box, window)


def test_shown_again_follows_the_window(window, available, shown):
    window.setGeometry(available.x() + 50, available.y() + 50, 500, 400)
    window.show()
    box = shown(window)
    box.hide()

    window.move(available.x() + 250, available.y() + 150)
    box.show()
    _assert_centred_over(box, window)


def test_no_parent_lands_inside_a_screen(qapp, shown):
    box = shown(None)
    screen = QGuiApplication.screenAt(box.frameGeometry().center())
    assert screen is not None
    assert screen.availableGeometry().contains(box.frameGeometry())


def test_window_near_the_screen_edge_keeps_the_box_inside(window, available, shown):
    right = available.x() + available.width()
    window.setGeometry(right - 120, available.y() + 100, 200, 120)
    window.show()

    box = shown(window)
    assert available.contains(box.frameGeometry())
    assert abs(box.x() + box.width() - right) <= TOLERANCE


def test_box_larger_than_the_screen_is_pinned_to_its_top_left(window, available, shown):
    window.setGeometry(available.x() + 100, available.y() + 100, 300, 200)
    window.show()

    box = shown(window, size=available.size().grownBy(QMargins(0, 0, 200, 100)))
    assert box.pos() == available.topLeft()
