from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from config import load_user_config, save_user_config, ICON_PATHS
from ui.header import colorize_svg
from ui.theme.manager import THEME
from ui.settings.page_build import BuildSettingsPage


class SetupWindow(QDialog):
    """The initial path setup window for ComfyUI"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ComfyLauncher Setup")
        self.setModal(True)
        self.setFixedSize(500, 220)
        self.setStyleSheet(
            f"background-color: {THEME.colors['bg_header']}; color: {THEME.colors['text_primary']};"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        label = QLabel("Select your ComfyUI build folder:")
        label.setStyleSheet("font-size: 14px; font-weight: 500;")
        layout.addWidget(label)

        # path field
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Choose ComfyUI folder...")
        self.path_edit.setFixedHeight(36)
        self.path_edit.textChanged.connect(self._on_path_changed)  # type: ignore
        layout.addWidget(self.path_edit)

        # browse button
        browse_btn = QPushButton()
        browse_btn.setIcon(
            QIcon(
                colorize_svg(
                    ICON_PATHS["open_folder"],
                    THEME.colors["icon_color_window"],
                    QSize(20, 20),
                )
            )
        )
        browse_btn.setFixedSize(40, 36)
        browse_btn.clicked.connect(self._browse)  # type: ignore
        row = QHBoxLayout()
        row.addWidget(self.path_edit)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        # action buttons
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        for btn in (self.ok_btn, self.cancel_btn):
            btn.setFixedSize(100, 34)
        self.ok_btn.setEnabled(False)

        self.ok_btn.clicked.connect(self._accept)  # type: ignore
        self.cancel_btn.clicked.connect(self.reject)  # type: ignore
        btn_row.addWidget(self.ok_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        self.build_checker = BuildSettingsPage()  # for reuse validate_build_path()

    def _browse(self):
        directory = QFileDialog.getExistingDirectory(self, "Select ComfyUI folder")
        if directory:
            self.path_edit.setText(directory)

    def _on_path_changed(self, text):
        valid = self.build_checker.validate_build_path(text.strip())
        self.ok_btn.setEnabled(valid)

    def _accept(self):
        path = self.path_edit.text().strip()
        if not self.build_checker.validate_build_path(path):
            QMessageBox.warning(
                self, "Invalid path", "This folder does not contain main.py"
            )
            return

        data = load_user_config()
        data["comfyui_path"] = path
        save_user_config(data)
        self.accept()
