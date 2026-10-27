"""The interface-language drop-down shared by Settings and the first-run window.

"System (…)" comes first, then every language under its own name, which stays
the same whatever language the interface is in: a user lost in a foreign
interface looks for the name of their own language, not its translation.
"""

from PyQt6.QtWidgets import QComboBox, QSizePolicy

from ui.widgets.combo_box import ThemedComboBox
from utils.i18n import (
    AUTO,
    I18N,
    LANGUAGES,
    detect_system_language,
    safe_retranslate,
    t,
)


class LanguageComboBox(ThemedComboBox):
    """Items carry the preference as data: ``"auto"`` or a language code."""

    def __init__(self, parent=None, font_size: int = 14):
        super().__init__(parent, font_size=font_size)
        self.addItem("", AUTO)
        for code, name in LANGUAGES.items():
            self.addItem(name, code)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._retranslate()
        I18N.languageChanged.connect(self._retranslate)

    def preference(self) -> str:
        return self.currentData()

    def set_preference(self, preference: str) -> None:
        """Select without emitting; an unknown code falls back to System."""
        self.blockSignals(True)
        self.setCurrentIndex(max(self.findData(preference), 0))
        self.blockSignals(False)

    @safe_retranslate
    def _retranslate(self, *args):
        system = LANGUAGES[detect_system_language()]
        self.setItemText(0, t("settings.language.system", language=system))
