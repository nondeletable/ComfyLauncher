from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QFrame,
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
        self._saved = load_user_config()
        self._dirty = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        title = QLabel("Exit Options")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(title)

        desc = QLabel(
            "Do you want to always confirm when exiting ComfyLauncher?\n"
            "You can choose a default action."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            color: {THEME.colors['text_secondary']};
            font-size: 13px;
            margin-bottom: 10px;
            """)
        layout.addWidget(desc)

        # --- 3 exclusive options (radio group) ---
        self.rb_ask = QRadioButton("Ask on exit")
        self.rb_always = QRadioButton("Always stop server on exit")
        self.rb_never = QRadioButton("Never stop server on exit")

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for rb in (self.rb_ask, self.rb_always, self.rb_never):
            self.group.addButton(rb)

        # Style (same "filled" indicator as before)
        radio_style = f"""
            QRadioButton {{
                font-size: 14px;
                color: {THEME.colors['text_primary']};
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 18px; height: 18px;
                border-radius: 4px;
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
        """

        for rb in (self.rb_ask, self.rb_always, self.rb_never):
            rb.setStyleSheet(radio_style)

        # Indent like you had (14px from left)
        rb_col = QVBoxLayout()
        rb_col.setContentsMargins(14, 0, 0, 0)
        rb_col.setSpacing(10)
        rb_col.addWidget(self.rb_ask)
        rb_col.addWidget(self.rb_always)
        rb_col.addWidget(self.rb_never)
        layout.addLayout(rb_col)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {THEME.colors['border_color']};")
        layout.addWidget(div)

        layout.addStretch()

        # --- Load saved values into UI ---
        self.reset()

        # --- Signals: mark dirty only ---
        self.rb_ask.toggled.connect(self._on_any_change)  # type: ignore
        self.rb_always.toggled.connect(self._on_any_change)  # type: ignore
        self.rb_never.toggled.connect(self._on_any_change)  # type: ignore

    # ---- Public API for SettingsWindow ----
    def is_dirty(self) -> bool:
        return self._dirty

    def apply(self) -> bool:
        data = self._current_data()
        cfg = load_user_config()
        cfg.update(data)
        save_user_config(cfg)

        self._saved = data
        self._set_dirty(False)

        MB.info(
            self.window(),
            "Settings saved",
            "Exit behavior settings have been saved successfully.",
        )
        return True

    def reset(self):
        ask = self._saved.get("ask_on_exit", True)
        mode = self._saved.get("exit_mode", "always_stop")

        for rb in (self.rb_ask, self.rb_always, self.rb_never):
            rb.blockSignals(True)

        if ask:
            self.rb_ask.setChecked(True)
        else:
            if mode == "never_stop":
                self.rb_never.setChecked(True)
            else:
                self.rb_always.setChecked(True)

        for rb in (self.rb_ask, self.rb_always, self.rb_never):
            rb.blockSignals(False)

        self._set_dirty(False)

    # ---- Internal logic ----
    def _on_any_change(self):
        self._compare_with_saved()

    def _compare_with_saved(self):
        if self.rb_ask.isChecked():
            cur = {
                "ask_on_exit": True,
                "exit_mode": self._saved.get("exit_mode", "always_stop"),
            }
        elif self.rb_always.isChecked():
            cur = {"ask_on_exit": False, "exit_mode": "always_stop"}
        else:
            cur = {"ask_on_exit": False, "exit_mode": "never_stop"}

        saved = {
            "ask_on_exit": self._saved.get("ask_on_exit", True),
            "exit_mode": self._saved.get("exit_mode", "always_stop"),
        }

        self._set_dirty(cur != saved)

    def _set_dirty(self, val: bool):
        if self._dirty != val:
            self._dirty = val
            self.dirtyChanged.emit(val)  # type: ignore[attr-defined]

    def _current_data(self) -> dict:
        if self.rb_ask.isChecked():
            # exit_mode сохраняем прошлый (чтобы не терять выбор пользователя)
            return {
                "ask_on_exit": True,
                "exit_mode": self._saved.get("exit_mode", "always_stop"),
            }
        if self.rb_always.isChecked():
            return {"ask_on_exit": False, "exit_mode": "always_stop"}
        return {"ask_on_exit": False, "exit_mode": "never_stop"}
