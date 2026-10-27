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
from utils.i18n import I18N, safe_retranslate, t
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
        self.title = title_cmd = QLabel()
        title_cmd.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(title_cmd)

        # The external CMD window is Windows-only. On other platforms ComfyUI
        # always uses the internal console, so this option makes no sense there:
        # keep the widget (reset()/apply() stay uniform) but hide it.
        self.cb_show_cmd = QCheckBox()
        self._descs = []
        self.desc_cmd = None
        if external_console_supported():
            self.desc_cmd = desc_cmd = QLabel()
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
        self.desc_splash = desc_splash = QLabel()
        desc_splash.setWordWrap(True)
        self._descs.append(desc_splash)
        layout.addWidget(desc_splash)

        self.cb_show_splash = QCheckBox()
        row_splash = QHBoxLayout()
        row_splash.setContentsMargins(14, 0, 0, 0)
        row_splash.addWidget(self.cb_show_splash)
        layout.addLayout(row_splash)

        # ─── Startup timeout Section ──────────────────
        self.desc_stall = desc_stall = QLabel()
        desc_stall.setWordWrap(True)
        self._descs.append(desc_stall)
        layout.addWidget(desc_stall)

        self.lbl_stall = QLabel()
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
        self._retranslate()
        I18N.languageChanged.connect(self._retranslate)

    # ───────────────────── HELPERS ────────────────────────

    @safe_retranslate
    def _retranslate(self, *args):
        self.title.setText(t("settings.menu.startup"))
        if self.desc_cmd is not None:
            self.desc_cmd.setText(t("startup.cmd.description"))
        self.cb_show_cmd.setText(t("settings.startup.show_cmd"))
        self.desc_splash.setText(t("startup.splash.description"))
        self.cb_show_splash.setText(t("startup.splash.label"))
        self.desc_stall.setText(t("startup.stall.description"))
        self.lbl_stall.setText(t("startup.stall.label"))
        # Relabel in place: refilling would drop a hand-edited value
        # and touch the selection.
        for i in range(self.cmb_stall.count()):
            self.cmb_stall.setItemText(i, _stall_label(self.cmb_stall.itemData(i)))

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
            MB.info(self.window(), t("startup.saved.title"), t("startup.saved.restart"))
        else:
            MB.info(
                self.window(), t("startup.saved.title"), t("startup.saved.next_start")
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
        if selected not in choices:
            choices.insert(-1, selected)  # keep "Never" last
        self.cmb_stall.clear()
        for sec in choices:
            self.cmb_stall.addItem(_stall_label(sec), sec)
        self.cmb_stall.setCurrentIndex(choices.index(selected))

    def _on_change(self):
        self._set_dirty(self._current_data() != self._saved_data())

    def _set_dirty(self, val):
        if self._dirty != val:
            self._dirty = val
            self.dirtyChanged.emit(val)  # type: ignore


def _stall_label(seconds: int) -> str:
    """Abbreviated units: one form for any number, in every language."""
    if seconds == 0:
        return t("startup.stall.never")
    if seconds % 60 == 0:
        label = t("startup.stall.minutes", n=seconds // 60)
    else:
        label = t("startup.stall.seconds", n=seconds)
    if seconds not in STARTUP_STALL_CHOICES:  # hand-edited in the config
        label = t("startup.stall.custom", value=label)
    return label
