import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QFrame,
)
from PyQt6.QtGui import QTextCursor, QIcon
from PyQt6.QtCore import Qt, QSize
from config import OTHER_ICONS
from utils.logger import LOG_FILE, log_event
from ui.header import colorize_svg
from ui.theme.manager import THEME
from ui.dialogs.messagebox import MessageBox as MB


class LogsSettingsPage(QWidget):
    """Elegant launcher logs page."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # ─── Basic layout ───────────────────────────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # ─── Title ────────────────────────────────────
        title = QLabel("Launcher Logs")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        layout.addWidget(title)

        # ─── Log text field ─────────────────────────
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(self._build_textedit_style())
        log_container = QHBoxLayout()
        log_container.setContentsMargins(14, 0, 0, 0)  # ← твой идеальный отступ
        log_container.addWidget(self.text_edit)

        layout.addLayout(log_container, stretch=1)

        # ─── Divider ──────────────────────────────────
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {THEME.colors['border_color']};")
        layout.addWidget(divider)

        # ─── Bottom buttons with icons ─────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        btn_layout.setSpacing(10)

        # Refresh button
        self.btn_refresh = QPushButton()
        self.btn_refresh.setIcon(
            QIcon(
                colorize_svg(
                    OTHER_ICONS["refresh"],
                    THEME.colors["icon_color_window"],
                    QSize(18, 18),
                )
            )
        )
        self.btn_refresh.setIconSize(QSize(18, 18))
        self.btn_refresh.setFixedSize(36, 36)

        # Clear log button
        self.btn_clear = QPushButton()
        self.btn_clear.setIcon(
            QIcon(
                colorize_svg(
                    OTHER_ICONS["clear-log"],
                    THEME.colors["icon_color_window"],
                    QSize(18, 18),
                )
            )
        )
        self.btn_clear.setIconSize(QSize(18, 18))
        self.btn_clear.setFixedSize(36, 36)

        # Apply common style
        for btn in (self.btn_refresh, self.btn_clear):
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {THEME.colors['border_color']};
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {THEME.colors['accent']};
                    border-color: {THEME.colors['accent']};
                }}
                QPushButton:pressed {{
                    background-color: {THEME.colors['accent_hover']};
                }}
                """
            )
            btn_layout.addWidget(btn)

        self.btn_refresh.setToolTip("Refresh log")
        self.btn_clear.setToolTip("Clear log")

        layout.addLayout(btn_layout)

        # ─── Signals ──────────────────────────────────────
        self.btn_refresh.clicked.connect(self.load_logs)  # type: ignore
        self.btn_clear.clicked.connect(self.clear_logs)  # type: ignore

        # ─── Initial loading ───────────────────────────
        self.load_logs()

        # ─── Reaction to a change of topic ───────────────
        THEME.themeChanged.connect(self._apply_theme)

    # ─────────────────────────────────────────────────────
    def _build_textedit_style(self) -> str:
        c = THEME.colors
        return f"""
            QTextEdit {{
                background-color: {c['bg_input']};
                color: {c['text_secondary']};
                border: 1px solid {c['border_color']};
                border-radius: 8px;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 10px;
            }}
            QTextEdit:focus {{
                border-color: {c['accent']};
            }}
        """

    def _apply_theme(self, *args):
        """Applies the active theme."""
        c = THEME.colors
        self.setStyleSheet(
            f"background-color: {c['bg_header']}; color: {c['text_primary']};"
        )
        self.text_edit.setStyleSheet(self._build_textedit_style())
        for btn in (self.btn_refresh, self.btn_clear):
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: {c['text_secondary']};
                    border: 1px solid {c['border_color']};
                    border-radius: 6px;
                    transition: all 0.2s ease-in-out;
                }}
                QPushButton:hover {{
                    background-color: {c['accent']};
                    color: {c['text_inverse']};
                    border-color: {c['accent']};
                }}
            """
            )

    # ─────────────────────────────────────────────────────
    def load_logs(self):
        """Loads the log into a text field."""
        if not os.path.exists(LOG_FILE):
            self.text_edit.setPlainText("No logs yet.")
            return

        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_edit.setPlainText(content or "Log file is empty.")
            self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
            log_event("📖 Logs page refreshed.")
        except Exception as e:
            MB.error(self.window(), "Error", f"Failed to read log file:\n{e}")

    def clear_logs(self):
        """Clears the log with confirmation."""
        if not MB.ask_yes_no(
            self.window(), "Clear logs", "Are you sure you want to clear the log file?"
        ):
            return
        try:
            open(LOG_FILE, "w", encoding="utf-8").close()
            log_event("🧹 Log file cleared by user.")
            self.text_edit.setPlainText("Log cleared.")
        except Exception as e:
            MB.error(self.window(), "Error", f"Failed to clear logs:\n{e}")
