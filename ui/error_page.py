from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)
from PyQt6.QtCore import Qt


class ErrorScreen(QWidget):
    def __init__(self, error_widget: QWidget, parent=None):
        super().__init__(parent)

        self.setObjectName("ErrorScreen")
        self.setAutoFillBackground(True)
        self.setStyleSheet("""
            QWidget#ErrorScreen {
                background-color: #353535;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(error_widget, 1)


class ErrorWidget(QWidget):
    """
    Sterile inline error screen.
    No themes, no icons, no config, no side effects on import.
    Safe to create even in partially damaged Python runtime.
    """

    def __init__(
        self,
        title: str,
        message: str,
        hint: str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self._build_ui(title, message, hint)

    def _build_ui(self, title: str, message: str, hint: str | None):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ─── Card ────────────────────────────────────────────────
        card = QWidget(self)
        card.setObjectName("ErrorCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 32, 36, 32)
        card_layout.setSpacing(14)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ─── Title ───────────────────────────────────────────────
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: #ff5555;
            """)

        # ─── Message ─────────────────────────────────────────────
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            font-size: 15px;
            color: #d0d0d0;
            """)

        # ─── Hint (optional) ─────────────────────────────────────
        if hint:
            hint_label = QLabel(hint)
            hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint_label.setWordWrap(True)
            hint_label.setStyleSheet("""
                font-size: 14px;
                color: #9a9a9a;
                """)
        else:
            hint_label = None

        # Assemble card
        card_layout.addWidget(title_label)
        card_layout.addSpacing(4)
        card_layout.addWidget(message_label)

        if hint_label:
            card_layout.addSpacing(6)
            card_layout.addWidget(hint_label)

        # Card style (inline, no theme)
        card.setStyleSheet("""
        QWidget#ErrorCard {
            background-color: #353535;
            border-radius: 12px;

        }
        """)

        root.addWidget(card)
