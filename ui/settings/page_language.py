from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
)
from config import load_user_config, save_user_config, get_language_preference
from ui.theme.manager import THEME, safe_repaint
from ui.dialogs.messagebox import MessageBox as MB
from ui.widgets.language_combo import LanguageComboBox
from utils.i18n import I18N, safe_retranslate, t


class LanguageSettingsPage(QWidget):
    """Interface language; Apply switches the whole launcher at once."""

    dirtyChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._saved = get_language_preference()
        self._dirty = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        self.title = QLabel()
        self.title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self.title)

        self.desc = QLabel()
        self.desc.setWordWrap(True)
        layout.addWidget(self.desc)

        self.lbl_language = QLabel()
        self.cmb_language = LanguageComboBox()
        self.cmb_language.setFixedHeight(28)
        row = QHBoxLayout()
        row.setContentsMargins(14, 0, 0, 0)
        row.setSpacing(10)
        row.addWidget(self.lbl_language)
        row.addWidget(self.cmb_language)
        row.addStretch()
        layout.addLayout(row)

        layout.addStretch()

        self._retranslate()
        self.reset()
        self._apply_theme()

        self.cmb_language.currentIndexChanged.connect(self._on_change)  # type: ignore
        THEME.themeChanged.connect(self._apply_theme)
        I18N.languageChanged.connect(self._retranslate)

    # ───────────────────── HELPERS ────────────────────────

    @safe_repaint
    def _apply_theme(self, *args):
        c = THEME.colors
        self.desc.setStyleSheet(f"color: {c['text_secondary']}; font-size: 13px;")
        self.lbl_language.setStyleSheet(f"font-size: 14px; color: {c['text_primary']};")

    @safe_retranslate
    def _retranslate(self, *args):
        self.title.setText(t("settings.menu.language"))
        self.desc.setText(t("settings.language.description"))
        self.lbl_language.setText(t("settings.language.label"))

    # ───────────────────── PUBLIC API ─────────────────────────

    def is_dirty(self):
        return self._dirty

    def apply(self):
        choice = self.cmb_language.preference()
        cfg = load_user_config()
        cfg["language"] = choice
        if not save_user_config(cfg):
            MB.save_failed(self.window())
            return False

        self._saved = choice
        self._set_dirty(False)
        I18N.set_language(choice)
        return True

    def reset(self):
        self.cmb_language.set_preference(self._saved)
        self._set_dirty(False)

    # ───────────────────── INTERNAL LOGIC ─────────────────────────

    def _on_change(self):
        self._set_dirty(self.cmb_language.preference() != self._saved)

    def _set_dirty(self, val):
        if self._dirty != val:
            self._dirty = val
            self.dirtyChanged.emit(val)  # type: ignore
