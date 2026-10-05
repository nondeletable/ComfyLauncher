"""Open a window centred over another one, on the screen that one is on.

All geometry here is Qt's logical (device-independent) coordinates: frame
geometry and ``QScreen.availableGeometry()`` share that space on every monitor,
whatever its DPI, so no scaling is done by hand.
"""

from PyQt6.QtCore import QPoint, QRect, QSize
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QWidget


def centered_top_left(size: QSize, anchor: QRect, available: QRect) -> QPoint:
    """Top-left that centres ``size`` over ``anchor``, kept inside ``available``.

    A window larger than ``available`` is pinned to its top-left corner, so its
    header stays on screen.
    """
    x = anchor.x() + (anchor.width() - size.width()) // 2
    y = anchor.y() + (anchor.height() - size.height()) // 2
    x = max(available.x(), min(x, available.x() + available.width() - size.width()))
    y = max(available.y(), min(y, available.y() + available.height() - size.height()))
    return QPoint(x, y)


def center_over(window: QWidget, anchor: QWidget) -> None:
    """Move ``window`` to the centre of ``anchor``, inside ``anchor``'s screen.

    A minimized ``anchor`` keeps its screen; if its geometry is then nowhere on
    that screen, ``window`` is centred on the screen itself.
    """
    available = anchor.screen().availableGeometry()
    rect = anchor.frameGeometry()
    if not rect.intersects(available):
        rect = available
    window.move(centered_top_left(window.frameGeometry().size(), rect, available))


# Down from the top edge into the header, past the transparent shadow margin.
HEADER_PROBE = 30


def is_off_screen(window: QWidget) -> bool:
    """True when the middle or the header of ``window`` is on no screen.

    The header is the only place to drag the window by: with it off screen, or
    in a gap between monitors, the window cannot be moved back by hand.
    """
    rect = window.frameGeometry()
    header = QPoint(rect.center().x(), rect.top() + HEADER_PROBE)
    return any(QGuiApplication.screenAt(p) is None for p in (rect.center(), header))
