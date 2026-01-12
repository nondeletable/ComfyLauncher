from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QHBoxLayout
from config import load_user_config, save_user_config
from ui.theme.manager import THEME
from ui.dialogs.messagebox import MessageBox as MB


class StartAppSettingsPage(QWidget):
    dirtyChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._saved = load_user_config()
        self._dirty = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        title = QLabel("Start App")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        layout.addWidget(title)

        desc = QLabel(
            "Show the Windows Command Prompt (CMD) window when launching ComfyUI.\n"
            "If disabled, ComfyUI starts without a CMD window."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {THEME.colors['text_secondary']}; font-size: 13px;")
        layout.addWidget(desc)

        # ─── Checkbox ──────────────────────────────
        self.cb_show_cmd = QCheckBox("Show CMD window on launch")
        self.cb_show_cmd.setStyleSheet(
            f"""
            QCheckBox {{
                font-size: 14px;
                color: {THEME.colors['text_primary']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border-radius: 4px;
                border: 1px solid {THEME.colors['border_color']};
                background-color: transparent;
            }}
            QCheckBox::indicator:checked {{
                background-color: {THEME.colors['accent']};
                border: 1px solid {THEME.colors['accent']};
            }}
        """
        )

        row = QHBoxLayout()
        row.setContentsMargins(14, 0, 0, 0)
        row.addWidget(self.cb_show_cmd)
        layout.addLayout(row)

        layout.addStretch()

        self.reset()

        self.cb_show_cmd.stateChanged.connect(self._on_change)  # type: ignore

    # ───────────────────── PUBLIC API ─────────────────────────

    def is_dirty(self):
        return self._dirty

    def apply(self):
        data = {"show_cmd": self.cb_show_cmd.isChecked()}
        cfg = load_user_config()
        cfg.update(data)
        save_user_config(cfg)

        self._saved.update(data)
        self._set_dirty(False)

        MB.info(self, "Saved", "To apply this setting, restart the launcher.")
        return True

    def reset(self):
        val = self._saved.get("show_cmd", True)

        self.cb_show_cmd.blockSignals(True)
        self.cb_show_cmd.setChecked(val)
        self.cb_show_cmd.blockSignals(False)

        self._set_dirty(False)

    # ───────────────────── INTERNAL LOGIC ─────────────────────────

    def _on_change(self):
        cur = {"show_cmd": self.cb_show_cmd.isChecked()}
        saved = {"show_cmd": self._saved.get("show_cmd", True)}
        self._set_dirty(cur != saved)

    def _set_dirty(self, val):
        if self._dirty != val:
            self._dirty = val
            self.dirtyChanged.emit(val)
