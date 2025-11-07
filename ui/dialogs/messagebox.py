from PyQt6.QtCore import Qt
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
)

from ui.header import colorize_svg
from ui.theme.manager import THEME
from config import MESSAGEBOX_ICONS


class _Badge(QLabel):
    """SVG icon instead of a color badge."""

    def __init__(self, icon_path: str, color: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(45, 45)
        icon = colorize_svg(icon_path, color, QSize(22, 22))
        self.setPixmap(icon.pixmap(QSize(22, 22)))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class MessageBox(QDialog):
    """
    Custom popup in theme style.
    Usage:
        MessageBox.info(self, "Title", "Text")
        MessageBox.warning(self, "Title", "Text")
        MessageBox.error(self, "Title", "Text")
        ok = MessageBox.ask_yes_no(self, "Confirm", "Do you want to continue?")
    Returns:
        .exec() -> int (Accepted / Rejected)
        ask_yes_no -> bool
    """

    def __init__(self, title: str, text: str, kind: str = "info", parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(420)

        # Removing the system header
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
        )

        c = THEME.colors  # We take current tokens

        # — dialog and button styles
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {c['popup_bg']};
                color: {c['popup_text']};
                border: 1px solid {c['popup_border']};
                border-radius: 10px;
                padding: 12px;
            }}
            QLabel#title {{
                color: {c['text_primary']};
                font-size: 15px;
                font-weight: 600;
                margin-bottom: 4px;
            }}
            QLabel#body {{
                color: {c['popup_text']};
                font-size: 13px;
                line-height: 1.3em;
            }}
            QPushButton {{
                background-color: transparent;
                color: {c['text_primary']};
                border: 1px solid {c['border_color']};
                border-radius: 6px;
                padding: 6px 14px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
                border-color: {c['accent']};
            }}
        """
        )

        # — main layout
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        # — title line: badge + title
        header = QHBoxLayout()
        header.setSpacing(10)
        header.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        icon_paths = MESSAGEBOX_ICONS

        icon_path = icon_paths.get(kind, icon_paths["info"])

        badge_color = {
            "info": c["accent"],
            "warning": "#F59E0B",
            "error": c["error"],
            "ask_yes_no": c["accent"],
        }.get(kind, c["accent"])

        self._badge = _Badge(icon_path, badge_color)
        self._badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        header.addWidget(self._badge, 0, Qt.AlignmentFlag.AlignVCenter)

        title_label = QLabel(title)
        title_label.setObjectName("title")
        title_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        header.addWidget(title_label, 1, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(header)

        # — message body
        body = QLabel(text)
        body.setObjectName("body")
        body.setWordWrap(True)
        root.addWidget(body)

        # — buttons
        self._buttons = QHBoxLayout()
        self._buttons.addStretch()
        root.addLayout(self._buttons)
        THEME.themeChanged.connect(self._apply_theme)
        self._apply_theme()

    # — auxiliary addition of buttons
    def _add_button(self, text: str, role: str):
        btn = QPushButton(text)
        if role == "accept":
            btn.clicked.connect(self.accept)  # type: ignore
        elif role == "reject":
            btn.clicked.connect(self.reject)  # type: ignore
        self._buttons.addWidget(btn)
        return btn

    # — static convenience methods
    @staticmethod
    def info(parent, title: str, text: str):
        dlg = MessageBox(title, text, "info", parent)
        dlg._add_button("OK", "accept")
        return dlg.exec()

    @staticmethod
    def warning(parent, title: str, text: str):
        dlg = MessageBox(title, text, "warning", parent)
        dlg._add_button("OK", "accept")
        return dlg.exec()

    @staticmethod
    def error(parent, title: str, text: str):
        dlg = MessageBox(title, text, "error", parent)
        dlg._add_button("OK", "accept")
        return dlg.exec()

    @staticmethod
    def ask_yes_no(parent, title: str, text: str) -> bool:
        dlg = MessageBox(title, text, "ask_yes_no", parent)
        dlg._add_button("Yes", "accept")
        dlg._add_button("No", "reject")
        # center over parent (carefully)
        if parent:
            geo = parent.frameGeometry()
            dlg.move(geo.center() - dlg.rect().center())
        return dlg.exec() == QDialog.DialogCode.Accepted

    def _apply_theme(self, *args):
        c = THEME.colors

        # background, text, and frame — by popup_* tokens
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {c['popup_bg']};
                color: {c['popup_text']};
                border: 1px solid {c['popup_border']};
                border-radius: 10px;
                padding: 12px;
            }}
            QLabel#title {{
                color: {c['text_primary']};
                font-size: 15px;
                font-weight: 600;
                margin-bottom: 4px;
            }}
            QLabel#body {{
                color: {c['popup_text']};
                font-size: 13px;
                line-height: 1.3em;
            }}
            QPushButton {{
                background-color: transparent;
                color: {c['text_primary']};
                border: 1px solid {c['border_color']};
                border-radius: 6px;
                padding: 6px 14px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
                border-color: {c['accent']};
            }}
        """
        )

        # 🔹 Recolor the icon to match the active theme
        icon_paths = MESSAGEBOX_ICONS
        kind = getattr(self, "_kind", "info")
        icon_path = icon_paths.get(kind, icon_paths["info"])

        badge_color = {
            "info": c["accent"],
            "warning": "#F59E0B",
            "error": c["error"],
            "ask_yes_no": c["accent"],
        }.get(kind, c["accent"])

        # If the icon already exists, update its pixmap
        badge = self.findChild(QLabel)
        if badge:
            icon = colorize_svg(icon_path, badge_color, QSize(22, 22))
            badge.setPixmap(icon.pixmap(QSize(22, 22)))
