from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
)
from config import load_user_config, save_user_config
from ui.theme.manager import THEME
from ui.dialogs.messagebox import MessageBox as MB


class BehaviorSettingsPage(QWidget):
    dirtyChanged = pyqtSignal(
        bool
    )  # Let's tell the Settings window when unsaved files appear/disappear

    def __init__(self, parent=None):
        super().__init__(parent)
        self._saved = load_user_config()  # последнее сохранённое состояние (из файла)
        self._dirty = False  # есть ли несохранённые изменения

        # ---- UI ----
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        title = QLabel("Exit behavior")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        layout.addWidget(title)

        desc = QLabel(
            "Do you want to always confirm when exiting ComfyLauncher?\n"
            "You can choose a default action."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"""
            color: {THEME.colors['text_secondary']};
            font-size: 13px;
            margin-bottom: 10px;
        """
        )
        layout.addWidget(desc)

        self.ask_checkbox = QCheckBox("Ask on exit")
        self.ask_checkbox.setStyleSheet(
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
            QCheckBox::indicator:hover {{
                border: 1px solid {THEME.colors['accent_hover']};
            }}
        """
        )
        cb_row = QHBoxLayout()
        cb_row.setContentsMargins(14, 0, 0, 0)  # ← ваш идеальный отступ
        cb_row.addWidget(self.ask_checkbox)

        layout.addLayout(cb_row)

        self.radio_always = QRadioButton("Always stop server on exit")
        self.radio_never = QRadioButton("Never stop server on exit")
        self.group = QButtonGroup(self)
        self.group.addButton(self.radio_always)
        self.group.addButton(self.radio_never)

        for rb in (self.radio_always, self.radio_never):
            rb.setEnabled(False)
            rb.setStyleSheet(
                f"""
                QRadioButton {{
                    font-size: 14px;
                    color: {THEME.colors['text_secondary']};
                    spacing: 8px;
                }}
                QRadioButton::indicator {{
                    width: 18px; height: 18px;
                    border-radius: 9px;
                    border: 1px solid {THEME.colors['border_color']};
                    background: transparent;
                }}
                QRadioButton::indicator:checked {{
                    background-color: {THEME.colors['accent']};
                    border: 1px solid {THEME.colors['accent']};
                }}
                QRadioButton::indicator:hover {{
                    border: 1px solid {THEME.colors['accent_hover']};
                }}
                QRadioButton::indicator:disabled {{
                    background-color: {THEME.colors['bg_menu']};
                    border: 1px solid #555;
                }}
            """
            )
            rb_row = QVBoxLayout()
            rb_row.setContentsMargins(14, 0, 0, 0)
            rb_row.addWidget(self.radio_always)
            rb_row.addWidget(self.radio_never)

            layout.addLayout(rb_row)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color:{THEME.colors['border_color']};")
        layout.addWidget(div)

        layout.addStretch()

        # ---- Loading saved values into the UI ----
        self.reset()

        # ---- Signals: Mark as dirty, but do NOT save ----
        self.ask_checkbox.stateChanged.connect(self._on_any_change)  # type: ignore
        self.radio_always.toggled.connect(self._on_any_change)  # type: ignore
        self.radio_never.toggled.connect(self._on_any_change)  # type: ignore

    # ---- Public API for SettingsWindow ----
    def is_dirty(self) -> bool:
        return self._dirty

    def apply(self) -> bool:
        """Validates, saves to user_config.json and displays a notification"""
        ask = self.ask_checkbox.isChecked()
        always = self.radio_always.isChecked()
        never = self.radio_never.isChecked()

        # Check: Cannot save empty state
        if not ask and not (always or never):
            MB.warning(
                self,
                "Invalid selection",
                "Please select at least one behavior before applying.",
            )
            return False

        # Saving data
        data = {
            "ask_on_exit": ask,
            "exit_mode": "always_stop" if always else "never_stop",
        }
        save_user_config(data)
        self._saved = data
        self._set_dirty(False)

        # 💬 User confirmation
        MB.info(
            self,
            "Settings saved",
            "Exit behavior settings have been saved successfully.",
        )
        return True

    def reset(self):
        """Reset the UI to its last saved state (without writing a file)"""
        ask = self._saved.get("ask_on_exit", True)
        mode = self._saved.get("exit_mode", "always_stop")

        # 1) Ask
        self.ask_checkbox.blockSignals(True)
        self.ask_checkbox.setChecked(ask)
        self.ask_checkbox.blockSignals(False)

        # 2) Radio buttons
        self._sync_radios_enabled(not ask)
        self._set_radios(None)  # сначала очистим

        if not ask:
            self._set_radios("always" if mode == "always_stop" else "never")

        self._set_dirty(False)

    # ---- Internal logic ----
    def _on_any_change(self):
        # Enable/disable radio buttons and auto-selection according to the technical specifications
        if self.sender() is self.ask_checkbox:
            if self.ask_checkbox.isChecked():
                # Ask ON -> disable and clear
                self._sync_radios_enabled(False)
                self._set_radios(None)
            else:
                # Ask OFF -> enable; if nothing is selected, select Always
                self._sync_radios_enabled(True)
                if not (self.radio_always.isChecked() or self.radio_never.isChecked()):
                    self.radio_always.setChecked(True)

        # Let's mark the form as dirty by comparing it with the saved one.
        self._compare_with_saved()

    def _compare_with_saved(self):
        cur = {
            "ask_on_exit": self.ask_checkbox.isChecked(),
            "exit_mode": (
                "always_stop"
                if self.radio_always.isChecked()
                else ("never_stop" if self.radio_never.isChecked() else None)
            ),
        }
        saved = {
            "ask_on_exit": self._saved.get("ask_on_exit", True),
            "exit_mode": self._saved.get("exit_mode", "always_stop"),
        }
        # If Ask is enabled, the radio button selection is irrelevant - we only compare ask_on_exit
        dirty = (cur["ask_on_exit"] != saved["ask_on_exit"]) or (
            not cur["ask_on_exit"] and cur["exit_mode"] != saved["exit_mode"]
        )
        self._set_dirty(dirty)

    def _set_dirty(self, val: bool):
        if self._dirty != val:
            self._dirty = val
            self.dirtyChanged.emit(val)  # type: ignore[attr-defined]

    def _sync_radios_enabled(self, enabled: bool):
        self.radio_always.setEnabled(enabled)
        self.radio_never.setEnabled(enabled)
        color = "#FFFFFF" if enabled else "#A0A0A0"
        for rb in (self.radio_always, self.radio_never):
            rb.setStyleSheet(
                rb.styleSheet().replace("#A0A0A0", color).replace("#FFFFFF", color)
            )

    def _set_radios(self, which: str | None):
        # which: "always" | "never" | None
        self.radio_always.blockSignals(True)
        self.radio_never.blockSignals(True)
        self.radio_always.setChecked(which == "always")
        self.radio_never.setChecked(which == "never")
        self.radio_always.blockSignals(False)
        self.radio_never.blockSignals(False)
