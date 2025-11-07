from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QApplication,
    QFrame,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from config import load_user_config, save_user_config, get_comfyui_path, ICON_PATHS
from ui.header import colorize_svg
from ui.theme.manager import THEME
from ui.dialogs.messagebox import MessageBox as MB

import os
import shutil


class BuildSettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # ─── Headline ───────────────────────────────
        title = QLabel("Build configuration")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        layout.addWidget(title)

        # ─── Current path ────────────────────────────
        current_path = get_comfyui_path()
        self.lbl_path = QLabel(f"Current build path:\n{current_path}")
        self.lbl_path.setStyleSheet(
            "color: {THEME.colors['text_secondary']}; font-size: 13px;"
        )
        layout.addWidget(self.lbl_path)

        # ─── Path selection field ─────────────────────────
        self.path_edit = QLineEdit()
        self.path_edit.textChanged.connect(self.on_path_changed)  # type: ignore
        self.path_edit.setPlaceholderText("Select new ComfyUI build folder...")
        self.path_edit.setFixedHeight(38)
        self.path_edit.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {THEME.colors['bg_input']};
                color: {THEME.colors['text_primary']};
                border: 1px solid {THEME.colors['border_color']};
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {THEME.colors['accent']};
            }}
        """
        )

        btn_browse = QPushButton()
        btn_browse.setIcon(
            QIcon(
                colorize_svg(
                    ICON_PATHS["open_folder"],
                    THEME.colors["icon_color_window"],
                    QSize(20, 20),
                )
            )
        )
        btn_browse.setIconSize(QSize(20, 20))
        btn_browse.setFixedSize(40, 38)
        btn_browse.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {THEME.colors['bg_input']};
                border: 1px solid {THEME.colors['border_color']};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {THEME.colors['accent']};
                border-color: {THEME.colors['accent']};
            }}
        """
        )
        btn_browse.clicked.connect(self.select_build_directory)  # type: ignore

        # ─── Horizontal container ─────────────────
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit)
        path_row.addWidget(btn_browse)
        layout.addLayout(path_row)

        # ─── Apply button ─────────────────────────────
        # ─── Text hint (environment type) ─────────
        self.lbl_env = QLabel("Environment type: —")
        self.lbl_env.setStyleSheet(
            "color: {THEME.colors['text_secondary']}; font-size: 13px;"
        )
        layout.addWidget(self.lbl_env)

        # ─── Divider ─────────────────────────────────
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #5E5E5E;")
        layout.addWidget(divider)

        # ─── Apply / Cancel Buttons───────────────────────
        btns_layout = QHBoxLayout()
        btns_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.btn_apply = QPushButton("Apply")
        self.btn_cancel = QPushButton("Cancel")

        for btn in (self.btn_apply, self.btn_cancel):
            btn.setFixedSize(100, 36)
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: {THEME.colors['text_secondary']};
                    border: 1px solid {THEME.colors['border_color']};
                    border-radius: 6px;
                    transition: all 0.2s ease-in-out;
                }}
                QPushButton:hover {{
                    background-color: {THEME.colors['accent']};
                    color: {THEME.colors['text_inverse']};
                    border-color: {THEME.colors['accent']};
                }}
                QPushButton:disabled {{
                    color: #555555;
                    border: 1px solid #555555;
                }}
            """
            )
            btns_layout.addWidget(btn)

        layout.addLayout(btns_layout)
        layout.addStretch()

        # ─── Button logic ───────────────────────────────
        self.btn_apply.clicked.connect(self.apply_changes)  # type: ignore
        self.btn_cancel.clicked.connect(self.cancel_changes)  # type: ignore
        self.btn_apply.setEnabled(False)

    # ─── Processors ────────────────────────────────
    def select_build_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select ComfyUI Build Folder"
        )
        if directory:
            self.path_edit.setText(directory)

    def on_path_changed(self, text: str):
        # check the path and update the UI
        if not text.strip():
            self.lbl_env.setText("Environment type: —")
            self.btn_apply.setEnabled(False)
            self._sync_footer_buttons()
            return

        if self.validate_build_path(text.strip()):
            # valid
            self._sync_footer_buttons()

    def _sync_footer_buttons(self):
        """We keep the synchronization of the lower buttons of
        the settings window with the current state of
        the page in one place."""
        p = self.parent()
        if not p:
            return
        # Apply at the bottom duplicates the Apply at the top.
        if hasattr(p, "btn_apply"):
            p.btn_apply.setEnabled(self.btn_apply.isEnabled())
        # Reset at the bottom is active when there is something to reset (the field is not empty)
        if hasattr(p, "btn_reset"):
            p.btn_reset.setEnabled(bool(self.path_edit.text().strip()))

    # ──────────────────────────────────────────────────────
    # Checking the build structure
    def validate_build_path(self, path: str) -> bool:
        """Checks the structure of the ComfyUI build and updates the signature."""
        if not path or not os.path.isdir(path):
            self.lbl_env.setText("Environment type: —")
            self.btn_apply.setEnabled(False)
            self._sync_footer_buttons()
            return False

        main_py = os.path.join(path, "main.py")
        if not os.path.exists(main_py):
            self.lbl_env.setText("Environment type: —")
            self.btn_apply.setEnabled(False)
            self._sync_footer_buttons()
            return False

        # ✅ main.py found - determine environment type
        embed_path = os.path.join(os.path.dirname(path), "python_embeded")
        if os.path.exists(embed_path):
            env_type = "Portable (embedded Python detected)"
        else:
            env_type = (
                "System (using system Python)"
                if shutil.which("python")
                else "Unknown (no Python found)"
            )

        self.lbl_env.setText(f"Environment type: {env_type}")
        self.btn_apply.setEnabled(True)
        self._sync_footer_buttons()
        return True

    def apply_changes(self):
        new_path = self.path_edit.text().strip()
        if not self.validate_build_path(new_path):
            MB.warning(
                self.window(), "Invalid build", "This folder doesn't contain main.py."
            )
            return False

        data = load_user_config()
        data["comfyui_path"] = new_path
        save_user_config(data)

        MB.info(
            self.window(),
            "Restart required",
            "The launcher will now close.\nPlease restart it to apply the new build.",
        )
        QApplication.quit()
        return True

    def cancel_changes(self):
        self.path_edit.clear()
        self.btn_apply.setEnabled(False)
        self._sync_footer_buttons()
        return True

    def apply(self):
        return self.apply_changes()

    def reset(self):
        return self.cancel_changes()
