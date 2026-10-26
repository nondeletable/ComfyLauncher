from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QHBoxLayout,
    QComboBox,
    QSizePolicy,
)
from config import (
    load_user_config,
    save_user_config,
    get_startup_stall_timeout,
    STARTUP_STALL_CHOICES,
)
from ui.theme.manager import THEME, safe_repaint
from ui.dialogs.messagebox import MessageBox as MB
from ui.widgets.combo_box import ThemedComboBox
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

        # ─── Startup timeout Section ──────────────────
        desc_stall = QLabel(
            "ComfyUI may take several minutes to start on a slow machine or with many custom nodes.\n"
            "The launcher waits while it is busy. If ComfyUI crashes, the error appears at once."
        )
        desc_stall.setWordWrap(True)
        self._descs.append(desc_stall)
        layout.addWidget(desc_stall)

        self.lbl_stall = QLabel("Show an error if ComfyUI shows no activity for:")
        self.cmb_stall = ThemedComboBox()
        self.cmb_stall.setFixedHeight(28)
        self.cmb_stall.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.cmb_stall.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        row_stall = QHBoxLayout()
        row_stall.setContentsMargins(14, 0, 0, 0)
        row_stall.setSpacing(10)
        row_stall.addWidget(self.lbl_stall)
        row_stall.addWidget(self.cmb_stall)
        row_stall.addStretch()
        layout.addLayout(row_stall)

        layout.addStretch()

        self.reset()
        self._apply_theme()

        self.cb_show_cmd.stateChanged.connect(self._on_change)  # type: ignore
        self.cb_show_splash.stateChanged.connect(self._on_change)  # type: ignore
        self.cmb_stall.currentIndexChanged.connect(self._on_change)  # type: ignore
        THEME.themeChanged.connect(self._apply_theme)

    # ───────────────────── HELPERS ────────────────────────

    @safe_repaint
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
        self.lbl_stall.setStyleSheet(f"font-size: 14px; color: {c['text_primary']};")

    # ───────────────────── PUBLIC API ─────────────────────────

    def is_dirty(self):
        return self._dirty

    def apply(self):
        data = self._current_data()
        saved = self._saved_data()
        cfg = load_user_config()
        cfg.update(data)
        if not save_user_config(cfg):
            MB.save_failed(self.window())
            return False

        self._saved.update(data)
        self._set_dirty(False)

        # The timeout is read on every ComfyUI start; only the console and
        # splash options need the launcher restarted.
        if any(data[k] != saved[k] for k in ("show_cmd", "show_splash")):
            MB.info(
                self.window(), "Saved", "To apply this setting, restart the launcher."
            )
        else:
            MB.info(
                self.window(),
                "Saved",
                "The new timeout applies the next time ComfyUI starts.",
            )
        return True

    def reset(self):
        widgets = (self.cb_show_cmd, self.cb_show_splash, self.cmb_stall)
        for w in widgets:
            w.blockSignals(True)

        self.cb_show_cmd.setChecked(self._saved.get("show_cmd", True))
        self.cb_show_splash.setChecked(self._saved.get("show_splash", True))
        self._fill_stall_choices(get_startup_stall_timeout(self._saved))

        for w in widgets:
            w.blockSignals(False)

        self._set_dirty(False)

    # ───────────────────── INTERNAL LOGIC ─────────────────────────

    def _current_data(self) -> dict:
        return {
            "show_cmd": self.cb_show_cmd.isChecked(),
            "show_splash": self.cb_show_splash.isChecked(),
            "startup_stall_timeout": self.cmb_stall.currentData(),
        }

    def _saved_data(self) -> dict:
        return {
            "show_cmd": self._saved.get("show_cmd", True),
            "show_splash": self._saved.get("show_splash", True),
            "startup_stall_timeout": get_startup_stall_timeout(self._saved),
        }

    def _fill_stall_choices(self, selected: int):
        """Offer the presets; a hand-edited value is kept as one more item."""
        choices = list(STARTUP_STALL_CHOICES)
        custom = selected not in choices
        if custom:
            choices.insert(-1, selected)  # keep "Never" last
        self.cmb_stall.clear()
        for sec in choices:
            label = _stall_label(sec)
            if custom and sec == selected:
                label += " (custom)"
            self.cmb_stall.addItem(label, sec)
        self.cmb_stall.setCurrentIndex(choices.index(selected))

    def _on_change(self):
        self._set_dirty(self._current_data() != self._saved_data())

    def _set_dirty(self, val):
        if self._dirty != val:
            self._dirty = val
            self.dirtyChanged.emit(val)  # type: ignore


def _stall_label(seconds: int) -> str:
    if seconds == 0:
        return "Never (wait while ComfyUI is running)"
    if seconds % 60 == 0:
        minutes = seconds // 60
        return f"{minutes} minute" if minutes == 1 else f"{minutes} minutes"
    return f"{seconds} seconds"
