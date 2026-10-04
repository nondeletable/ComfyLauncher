"""Edge resizing for the frameless main window.

A frameless window has no OS border to grab, so nothing resized it at all.
The window keeps a thin strip of its own around the content while it is not
maximized; hovering that strip shows the resize cursor, and pressing it hands
the resize to the window system through ``startSystemResize()``.

The strip has to be real Qt area: the embedded web view is a native child
window and swallows every mouse event over it, so a border drawn on top of it
would never be reached.
"""

from PyQt6.QtCore import QEvent, QObject, QPoint, QRect, Qt

RESIZE_MARGIN = 5

_CURSORS = {
    Qt.Edge.LeftEdge: Qt.CursorShape.SizeHorCursor,
    Qt.Edge.RightEdge: Qt.CursorShape.SizeHorCursor,
    Qt.Edge.TopEdge: Qt.CursorShape.SizeVerCursor,
    Qt.Edge.BottomEdge: Qt.CursorShape.SizeVerCursor,
    Qt.Edge.LeftEdge | Qt.Edge.TopEdge: Qt.CursorShape.SizeFDiagCursor,
    Qt.Edge.RightEdge | Qt.Edge.BottomEdge: Qt.CursorShape.SizeFDiagCursor,
    Qt.Edge.RightEdge | Qt.Edge.TopEdge: Qt.CursorShape.SizeBDiagCursor,
    Qt.Edge.LeftEdge | Qt.Edge.BottomEdge: Qt.CursorShape.SizeBDiagCursor,
}


def edges_at(pos: QPoint, rect: QRect, margin: int = RESIZE_MARGIN) -> Qt.Edge:
    """Window edges within ``margin`` of ``pos``; empty when it is inside."""
    edges = Qt.Edge(0)
    if pos.x() < rect.left() + margin:
        edges |= Qt.Edge.LeftEdge
    elif pos.x() > rect.right() - margin:
        edges |= Qt.Edge.RightEdge
    if pos.y() < rect.top() + margin:
        edges |= Qt.Edge.TopEdge
    elif pos.y() > rect.bottom() - margin:
        edges |= Qt.Edge.BottomEdge
    return edges


class EdgeResizer(QObject):
    """Event filter that resizes ``window`` from the edges of watched widgets.

    ``allowed`` limits which edges resize, and ``area`` gives the rectangle the
    edges are measured from, in window coordinates (the whole window if unset)
    — for a window whose visible frame sits inside a transparent shadow margin.
    """

    ALL_EDGES = (
        Qt.Edge.LeftEdge | Qt.Edge.RightEdge | Qt.Edge.TopEdge | Qt.Edge.BottomEdge
    )

    def __init__(self, window, allowed=ALL_EDGES, area=None):
        super().__init__(window)
        self.window = window
        self.allowed = allowed
        self.area = area
        self._resizing = False

    def watch(self, widget):
        widget.setMouseTracking(True)
        widget.installEventFilter(self)

    def _edges(self, event) -> Qt.Edge:
        if self.window.isMaximized() or self.window.isFullScreen():
            return Qt.Edge(0)
        pos = self.window.mapFromGlobal(event.globalPosition().toPoint())
        rect = self.area() if self.area else self.window.rect()
        return edges_at(pos, rect) & self.allowed

    def eventFilter(self, obj, event):
        kind = event.type()
        if kind == QEvent.Type.MouseMove and event.buttons() == Qt.MouseButton.NoButton:
            edges = self._edges(event)
            if edges:
                self.window.setCursor(_CURSORS[edges])
            else:
                self.window.unsetCursor()
        elif (
            kind == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
        ):
            # Reset on every press: on Windows the system resize loop eats the
            # release, so it cannot be relied on to end the resize.
            self._resizing = False
            edges = self._edges(event)
            handle = self.window.windowHandle()
            if edges and handle is not None:
                self._resizing = bool(handle.startSystemResize(edges))
                return self._resizing
        elif kind == QEvent.Type.MouseMove and self._resizing:
            # The press never reached the widget, so the header would drag the
            # window from a stale point if these moves got through on X11.
            return True
        elif kind == QEvent.Type.MouseButtonRelease and self._resizing:
            self._resizing = False
            return True
        elif kind == QEvent.Type.Leave:
            self.window.unsetCursor()
        return False
