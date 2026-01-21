from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QFrame,
)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainterPath, QRegion, QTextCursor

from ui.theme.manager import THEME
from ui.header import colorize_svg
from config import HEAD_ICON_PATHS
from utils.console_buffer import ConsoleBuffer


class ConsoleWindow(QWidget):
    """Separate window to view ComfyUI console logs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = None
        self.setWindowTitle("ComfyUI Console")
        self.setFixedSize(900, 600)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowSystemMenuHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        c = THEME.colors

        # ─── Main frame ────────────────────────────────
        main_frame = QFrame(self)
        main_frame.setObjectName("console_main_frame")
        main_frame.setStyleSheet(
            f"""
            QFrame#console_main_frame {{
                background-color: {c['bg_header']};
                color: {c['text_primary']};
                border-radius: 10px;
                border: 1px solid {c['border_color']};
            }}
        """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(main_frame)

        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ─── Header bar ────────────────────────────────
        header = QFrame()
        header.setStyleSheet(
            f"""
            QFrame {{
                background-color: {c['bg_header']};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }}
        """
        )
        hbox = QHBoxLayout(header)
        hbox.setContentsMargins(12, 6, 12, 6)
        hbox.setSpacing(8)

        title = QLabel("ComfyUI Console")
        title.setStyleSheet(
            f"color: {c['app_title_color']}; font-weight: 500; font-size: 15px;"
        )

        hbox.addWidget(title)
        hbox.addStretch()

        btn_close = QPushButton()

        btn_close.setFixedSize(24, 24)
        btn_close.setIcon(
            colorize_svg(HEAD_ICON_PATHS["close"], c["icon_color_window"])
        )
        btn_close.setStyleSheet(
            """
            QPushButton { border: none; background: transparent; }
        """
        )

        hbox.addWidget(btn_close)

        btn_close.clicked.connect(self.hide)  # type: ignore

        # ─── Log area ──────────────────────────────────
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(self._build_text_style())
        self.text_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)

        log_container = QHBoxLayout()

        log_container.setContentsMargins(14, 8, 14, 14)
        log_container.addWidget(self.text_edit)

        layout.addWidget(header)
        layout.addLayout(log_container)

        # ─── Timer for updates ─────────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(500)  # ms
        self._timer.timeout.connect(self._refresh_logs)  # type: ignore
        self._timer.start()

        self._apply_theme()
        THEME.themeChanged.connect(self._apply_theme)

        self._round_corners(10)
        self._center()
        self._refresh_logs()

    # ─────────────────────────────────────────────────
    def _build_text_style(self) -> str:
        c = THEME.colors
        return f"""
            QPlainTextEdit {{
                background-color: {c['bg_input']};
                color: {c['text_secondary']};
                border: 1px solid {c['border_color']};
                border-radius: 8px;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 10px;
            }}
            QPlainTextEdit:focus {{
                border-color: {c['accent']};
            }}
        """

    def _apply_theme(self, *args):
        c = THEME.colors
        self.setStyleSheet(
            f"background-color: {c['bg_header']}; color: {c['text_primary']};"
        )
        self.text_edit.setStyleSheet(self._build_text_style())

    # ─────────────────────────────────────────────────
    def _refresh_logs(self):
        text = ConsoleBuffer.get_all()
        # To avoid flashing, we update only if there is a real change.
        if text != self.text_edit.toPlainText():
            self.text_edit.setPlainText(text)
            self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

    # ── geometry/drag/rounding ───────────────────────
    def _center(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _round_corners(self, radius: int):
        path = QPainterPath()
        rect = QRectF(self.rect())
        path.addRoundedRect(rect, radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.isVisible():
            self._round_corners(10)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
