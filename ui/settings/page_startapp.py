from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QHBoxLayout
from config import load_user_config, save_user_config
from ui.theme.manager import THEME
from ui.dialogs.messagebox import MessageBox as MB
from utils.process_launch import external_console_supported


class StartAppSettingsPage(QWidget):
    dirtyChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._saved = load_user_config()
        self._dirty = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # ─── CMD Section ──────────────────────────────
        title_cmd = QLabel("Startup")
        title_cmd.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(title_cmd)

        # The external CMD window is Windows-only. On other platforms ComfyUI
        # always uses the internal console, so this option makes no sense there:
        # keep the widget (reset()/apply() stay uniform) but hide it.
        self.cb_show_cmd = QCheckBox("Show CMD window on launch")
        self._descs = []
        if external_console_supported():
            desc_cmd = QLabel(
                "Show the Windows Command Prompt (CMD) window when launching ComfyUI.\n"
                "If disabled, ComfyUI starts without a CMD window."
            )
            desc_cmd.setWordWrap(True)
            self._descs.append(desc_cmd)
            layout.addWidget(desc_cmd)

            row_cmd = QHBoxLayout()
            row_cmd.setContentsMargins(14, 0, 0, 0)
            row_cmd.addWidget(self.cb_show_cmd)
            layout.addLayout(row_cmd)
        else:
            self.cb_show_cmd.hide()

        # ─── Splash Section ───────────────────────────
        desc_splash = QLabel(
            "Show the splash screen while ComfyUI is loading.\n"
            "If disabled, loading progress can be tracked via the Task Manager or CMD window."
        )
        desc_splash.setWordWrap(True)
        self._descs.append(desc_splash)
        layout.addWidget(desc_splash)

        self.cb_show_splash = QCheckBox("Show splash screen on launch")
        row_splash = QHBoxLayout()
        row_splash.setContentsMargins(14, 0, 0, 0)
        row_splash.addWidget(self.cb_show_splash)
        layout.addLayout(row_splash)

        layout.addStretch()

        self.reset()
        self._apply_theme()

        self.cb_show_cmd.stateChanged.connect(self._on_change)  # type: ignore
        self.cb_show_splash.stateChanged.connect(self._on_change)  # type: ignore
        THEME.themeChanged.connect(self._apply_theme)

    # ───────────────────── HELPERS ────────────────────────

    def _apply_theme(self, *args):
        c = THEME.colors
        for desc in self._descs:
            desc.setStyleSheet(f"color: {c['text_secondary']}; font-size: 13px;")
        for cb in (self.cb_show_cmd, self.cb_show_splash):
            cb.setStyleSheet(
                f"""
                QCheckBox {{
                    font-size: 14px;
                    color: {c['text_primary']};
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 18px; height: 18px;
                    border-radius: 4px;
                    border: 1px solid {c['border_color']};
                    background-color: transparent;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {c['accent']};
                    border: 1px solid {c['accent']};
                }}
            """
            )

    # ───────────────────── PUBLIC API ─────────────────────────

    def is_dirty(self):
        return self._dirty

    def apply(self):
        data = {
            "show_cmd": self.cb_show_cmd.isChecked(),
            "show_splash": self.cb_show_splash.isChecked(),
        }
        cfg = load_user_config()
        cfg.update(data)
        if not save_user_config(cfg):
            MB.save_failed(self.window())
            return False

        self._saved.update(data)
        self._set_dirty(False)

        MB.info(self.window(), "Saved", "To apply this setting, restart the launcher.")
        return True

    def reset(self):
        self.cb_show_cmd.blockSignals(True)
        self.cb_show_splash.blockSignals(True)

        self.cb_show_cmd.setChecked(self._saved.get("show_cmd", True))
        self.cb_show_splash.setChecked(self._saved.get("show_splash", True))

        self.cb_show_cmd.blockSignals(False)
        self.cb_show_splash.blockSignals(False)

        self._set_dirty(False)

    # ───────────────────── INTERNAL LOGIC ─────────────────────────

    def _on_change(self):
        cur = {
            "show_cmd": self.cb_show_cmd.isChecked(),
            "show_splash": self.cb_show_splash.isChecked(),
        }
        saved = {
            "show_cmd": self._saved.get("show_cmd", True),
            "show_splash": self._saved.get("show_splash", True),
        }
        self._set_dirty(cur != saved)

    def _set_dirty(self, val):
        if self._dirty != val:
            self._dirty = val
            self.dirtyChanged.emit(val)  # type: ignore
