from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QFrame,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCursor, QColor

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
        self.setFixedSize(930, 630)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowSystemMenuHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

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
            }}
        """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(15, 15, 15, 15)
        outer.addWidget(main_frame)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 180))
        main_frame.setGraphicsEffect(shadow)

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
        self.text_edit.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        # Full text currently shown; used to append only the new tail on
        # refresh so the user's selection and scroll position survive.
        self._last_text = ""

        log_container = QHBoxLayout()

        log_container.setContentsMargins(14, 8, 14, 6)
        log_container.addWidget(self.text_edit)

        # ─── View-only hint ────────────────────────────
        # The internal console is output-only: the process runs with
        # CREATE_NO_WINDOW and its stdin is a pipe, not a real console, so
        # keystrokes (Esc, arrows, …) cannot be delivered to it. Point users
        # to the external CMD window when they need interactive input.
        self.hint_label = QLabel(
            "View-only. To type into the console, enable "
            "“Show CMD window on launch” in Settings."
        )
        self.hint_label.setWordWrap(True)
        hint_container = QHBoxLayout()
        hint_container.setContentsMargins(16, 0, 16, 12)
        hint_container.addWidget(self.hint_label)

        layout.addWidget(header)
        layout.addLayout(log_container)
        layout.addLayout(hint_container)

        # ─── Timer for updates ─────────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(500)  # ms
        self._timer.timeout.connect(self._refresh_logs)  # type: ignore
        self._timer.start()

        self._apply_theme()
        THEME.themeChanged.connect(self._apply_theme)

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
            QScrollBar:vertical {{
                background: {c['bg_input']};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: #555555;
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #787878;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """

    def _hint_style(self) -> str:
        c = THEME.colors
        return f"color: {c['text_secondary']}; font-size: 11px;"

    def _apply_theme(self, *args):
        c = THEME.colors
        self.setStyleSheet(
            f"background-color: {c['bg_header']}; color: {c['text_primary']};"
        )
        self.text_edit.setStyleSheet(self._build_text_style())
        self.hint_label.setStyleSheet(self._hint_style())

    # ─────────────────────────────────────────────────
    def _refresh_logs(self):
        text = ConsoleBuffer.get_all()
        if text == self._last_text:
            return

        sb = self.text_edit.verticalScrollBar()
        # Follow the tail only when the user is already at the bottom, so
        # scrolling up to select text is not yanked back down.
        at_bottom = sb.value() >= sb.maximum() - 4

        if text.startswith(self._last_text):
            # Common case: buffer only grew — append the new tail with a
            # detached cursor so the user's selection is left untouched.
            delta = text[len(self._last_text) :]
            cursor = QTextCursor(self.text_edit.document())
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(delta)
        else:
            # Buffer was cleared or truncated: fall back to a full rebuild
            # (selection can't be preserved here).
            self.text_edit.setPlainText(text)

        self._last_text = text

        if at_bottom:
            sb.setValue(sb.maximum())

    # ── geometry/drag/rounding ───────────────────────
    def _center(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def resizeEvent(self, event):
        super().resizeEvent(event)

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
