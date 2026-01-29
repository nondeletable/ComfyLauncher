from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt, QSize, QRectF
from PyQt6.QtGui import QIcon, QPainterPath, QRegion

from config import load_user_config, save_user_config, ICON_PATH, ICON_PATHS
from ui.header import colorize_svg
from ui.theme.manager import THEME
from ui.settings.page_build import BuildSettingsPage


class SetupWindow(QDialog):
    """The initial path setup window for ComfyUI"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ComfyLauncher Setup")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setModal(True)
        self.setFixedSize(500, 220)
        self.setObjectName("SetupWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("setup_main_frame")

        outer.addWidget(self.main_frame)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(24, 20, 24, 18)  # твои текущие отступы перенеси сюда
        layout.setSpacing(14)

        r = 9  # radius
        b = 3  # border

        self.main_frame.setStyleSheet(
            f"""
        QFrame#setup_main_frame {{
            background-color: {THEME.colors['bg_header']};
            border: {b}px solid {THEME.colors['border_color']};
            border-radius: {r}px;
        }}
        """
        )

        info = QLabel(
            "Specify the folder where ComfyUI is located (folder with main.py).<br>"
            "For example: <code>D:/Portable/ComfyUI</code>"
        )
        info.setStyleSheet(
            f"""
            QLabel {{
                font-size: 14px;
                color: {THEME.colors['text_secondary']};
            }}
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

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
        browse_btn.setFixedSize(38, 36)
        browse_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {THEME.colors['bg_input']};
                border: 1px solid {THEME.colors['border_color']};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {THEME.colors['bg_hover']};
            }}
        """
        )
        browse_btn.clicked.connect(self._browse)  # type: ignore
        row = QHBoxLayout()
        row.setSpacing(8)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Path to ComfyUI… (Folder with main.py)")
        self.path_edit.setFixedHeight(36)
        self.path_edit.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {THEME.colors['bg_input']};
                color: {THEME.colors['text_primary']};
                border: 1px solid {THEME.colors['border_color']};
                border-radius: 6px;
                padding-left: 10px;
            }}
        """
        )
        self.path_edit.textChanged.connect(self._on_path_changed)

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
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: {THEME.colors['text_secondary']};
                    border: 1px solid {THEME.colors['border_color']};
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {THEME.colors['accent']};
                    color: {THEME.colors['text_inverse']};
                    border-color: {THEME.colors['accent']};
                }}
            """
            )
        self.ok_btn.setEnabled(False)
        btn_row.setSpacing(8)

        self.ok_btn.clicked.connect(self._accept)  # type: ignore
        self.cancel_btn.clicked.connect(self.reject)  # type: ignore
        btn_row.addWidget(self.ok_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)
        # self._round_corners(10)
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

    def _round_corners(self, radius: int):
        from PyQt6.QtGui import QPainterPath, QRegion
        from PyQt6.QtCore import QRectF

        path = QPainterPath()
        rect = QRectF(self.rect())
        path.addRoundedRect(rect, radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_rounded_mask()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_rounded_mask()

    def _apply_rounded_mask(self):
        r = 10
        rect = QRectF(self.rect()).adjusted(1.0, 1.0, -1.0, -1.0)
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))
