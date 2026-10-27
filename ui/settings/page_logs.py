import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QHBoxLayout,
    QFrame,
)
from PyQt6.QtGui import QTextCursor, QIcon
from PyQt6.QtCore import Qt, QSize
from config import OTHER_ICONS
from utils.logger import LOG_FILE, log_event
from ui.header import colorize_svg
from ui.theme.manager import THEME, safe_repaint
from ui.dialogs.messagebox import MessageBox as MB
from utils.i18n import I18N, safe_retranslate, t


class LogsSettingsPage(QWidget):
    """Elegant launcher logs page."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # ─── Basic layout ───────────────────────────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # ─── Title ────────────────────────────────────
        self.title = QLabel()
        self.title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self.title)

        # ─── Log text field ─────────────────────────
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(self._build_textedit_style())
        log_container = QHBoxLayout()
        log_container.setContentsMargins(14, 0, 0, 0)  # ← твой идеальный отступ
        log_container.addWidget(self.text_edit)

        layout.addLayout(log_container, stretch=1)

        # ─── Divider ──────────────────────────────────
        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.Shape.HLine)
        self.divider.setStyleSheet(f"color: {THEME.colors['border_color']};")
        layout.addWidget(self.divider)

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

        layout.addLayout(btn_layout)

        # ─── Signals ──────────────────────────────────────
        self.btn_refresh.clicked.connect(self.load_logs)  # type: ignore
        self.btn_clear.clicked.connect(self.clear_logs)  # type: ignore

        # ─── Initial loading ───────────────────────────
        # Key of the note shown instead of the log, or None while the log is.
        self._note = None
        self.load_logs()
        self._retranslate()
        I18N.languageChanged.connect(self._retranslate)

        # ─── Reaction to a change of topic ───────────────
        THEME.themeChanged.connect(self._apply_theme)

    @safe_retranslate
    def _retranslate(self, *args):
        self.title.setText(t("settings.menu.logs"))
        self.btn_refresh.setToolTip(t("logs.refresh"))
        self.btn_clear.setToolTip(t("logs.clear"))
        if self._note:
            self._show_note(self._note)

    def _show_note(self, key):
        """Show a note in place of the log (no file, empty, just cleared)."""
        self._note = key
        self.text_edit.setPlainText(t(key))

    # ─────────────────────────────────────────────────────
    def _build_textedit_style(self) -> str:
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

    @safe_repaint
    def _apply_theme(self, *args):
        """Applies the active theme."""
        c = THEME.colors
        self.setStyleSheet(
            f"background-color: {c['bg_header']}; color: {c['text_primary']};"
        )
        self.text_edit.setStyleSheet(self._build_textedit_style())
        self.divider.setStyleSheet(f"color: {c['border_color']};")
        for btn, icon in (
            (self.btn_refresh, "refresh"),
            (self.btn_clear, "clear-log"),
        ):
            btn.setIcon(
                QIcon(
                    colorize_svg(
                        OTHER_ICONS[icon], c["icon_color_window"], QSize(18, 18)
                    )
                )
            )
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
            self._show_note("logs.none")
            return

        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            if content:
                self._note = None
                self.text_edit.setPlainText(content)
            else:
                self._show_note("logs.empty")
            self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
            log_event("📖 Logs page refreshed.")
        except Exception as e:
            MB.error(self.window(), t("common.error"), t("logs.read_failed", error=e))

    def clear_logs(self):
        """Clears the log with confirmation."""
        if not MB.ask_yes_no(self.window(), t("logs.clear"), t("logs.clear.ask")):
            return
        try:
            open(LOG_FILE, "w", encoding="utf-8").close()
            log_event("🧹 Log file cleared by user.")
            self._show_note("logs.cleared")
        except Exception as e:
            MB.error(self.window(), t("common.error"), t("logs.clear_failed", error=e))
