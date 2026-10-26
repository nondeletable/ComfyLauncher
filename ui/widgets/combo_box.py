"""A drop-down list that looks like the rest of the app, not like Windows.

Plain QComboBox leaks the native style in three places: the hover highlight
(the system color plus a square focus frame), the arrow button (a raised
native button inside the rounded field) and the popup (a square window whose
corners stick out of the rounded border). Each needs its own fix:

- the popup gets a QListView, because the default item delegate ignores
  ``::item`` style rules — with the view, the highlight follows ``accent``.
  Only ``:selected`` is styled: the popup moves the selection under the mouse
  itself, and a separate ``:hover`` rule would light up two rows at once;
- the native arrow is hidden and a chevron is painted in the theme color, so no
  icon file has to be recolored per theme;
- the popup window is frameless and transparent, and the list paints its own
  rounded background, so nothing square shows behind the corners.
"""

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QComboBox, QListView

from ui.theme.manager import THEME, safe_repaint

_CHEVRON_ZONE = 26  # px on the right reserved for the chevron


class ThemedComboBox(QComboBox):
    def __init__(self, parent=None, font_size: int = 14):
        super().__init__(parent)
        self._font_size = font_size
        self._popup_open = False

        self.setView(QListView())
        popup = self.view().window()
        popup.setWindowFlags(
            popup.windowFlags()
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        if popup.layout() is not None:
            popup.layout().setContentsMargins(0, 0, 0, 0)

        self._apply_theme()
        THEME.themeChanged.connect(self._apply_theme)

    @safe_repaint
    def _apply_theme(self, *args):
        c = THEME.colors
        self.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1px solid {c['border_color']};
                border-radius: 6px;
                padding: 0 {_CHEVRON_ZONE}px 0 8px;
                font-size: {self._font_size}px;
            }}
            QComboBox:hover, QComboBox:on {{
                border-color: {c['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
                background: transparent;
                width: {_CHEVRON_ZONE}px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0;
                height: 0;
            }}
            QComboBoxPrivateContainer {{
                background: transparent;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['bg_input']};
                border: 1px solid {c['border_color']};
                border-radius: 6px;
                padding: 4px;
                outline: none;
                font-size: {self._font_size}px;
            }}
            QComboBox QAbstractItemView::item {{
                color: {c['text_primary']};
                min-height: 24px;
                padding: 0 8px;
                border: none;
                border-radius: 4px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
            }}
        """
        )
        self.update()

    # ── chevron ──────────────────────────────────────────────────────────

    def showPopup(self):
        self._popup_open = True
        self.update()
        super().showPopup()

    def hidePopup(self):
        super().hidePopup()
        self._popup_open = False
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        c = THEME.colors
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(c["accent"] if self._popup_open else c["text_secondary"]))
        pen.setWidthF(1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        cx = self.width() - _CHEVRON_ZONE / 2
        cy = self.height() / 2
        dy = -2.0 if self._popup_open else 2.0  # points up while open
        painter.drawPolyline(
            QPointF(cx - 4, cy - dy),
            QPointF(cx, cy + dy),
            QPointF(cx + 4, cy - dy),
        )
        painter.end()
