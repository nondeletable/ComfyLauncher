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
    QButtonGroup,
    QToolButton,
    QRadioButton,
)
from PyQt6.QtCore import Qt, QSize, QRectF
from PyQt6.QtGui import QIcon, QPainterPath, QRegion

from config import (
    load_user_config,
    save_user_config,
    ICON_PATH,
    ICON_PATHS,
    DOODLE_ICON_PATHS,
    DEFAULT_DOODLE_ID,
)
from ui.header import colorize_svg
from ui.theme.manager import THEME
from utils.build_validation import is_valid_comfyui_build

import os
import uuid
from enum import Enum


class SetupMode(Enum):
    MANAGER = "manager"  # выбор/запуск билда => пишет last_used + comfyui_path
    SETTINGS = "settings"  # просто CRUD билдов => не трогает last_used/comfyui_path


class SetupWindow(QDialog):
    """The initial path setup window for ComfyUI"""

    def __init__(
        self,
        parent=None,
        build: dict | None = None,
        mode: SetupMode = SetupMode.MANAGER,
    ):
        super().__init__(parent)
        self.mode = mode
        self.edit_build_id = str(build.get("id", "")) if build else ""

        self.setWindowTitle("ComfyLauncher Setup")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setModal(True)
        self.setFixedSize(500, 350)
        self.setObjectName("SetupWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("setup_main_frame")

        outer.addWidget(self.main_frame)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(14)

        r = 9  # radius
        b = 3  # border

        self.main_frame.setStyleSheet(f"""
        QFrame#setup_main_frame {{
            background-color: {THEME.colors['bg_header']};
            border: {b}px solid {THEME.colors['border_color']};
            border-radius: {r}px;
        }}
        """)

        info = QLabel(
            "Specify the folder where ComfyUI is located (folder with main.py).<br>"
            "For example: <code>D:/Portable/ComfyUI</code>. "
            "Be sure to give the build a name and select an icon."
        )
        info.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {THEME.colors['text_secondary']};
            }}
        """)
        info.setWordWrap(True)
        layout.addWidget(info)

        # browse button
        browse_btn = QPushButton()
        browse_btn.setIcon(
            QIcon(
                colorize_svg(
                    ICON_PATHS["open_folder"],
                    THEME.colors["icon_color_window"],
                )
            )
        )
        browse_btn.setIconSize(QSize(20, 20))
        browse_btn.setFixedSize(38, 36)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME.colors['bg_input']};
                border: 1px solid {THEME.colors['border_color']};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {THEME.colors['bg_hover']};
            }}
        """)
        browse_btn.clicked.connect(self._browse)  # type: ignore
        row = QHBoxLayout()
        row.setSpacing(8)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Path to ComfyUI… (Folder with main.py)")
        self.path_edit.setFixedHeight(36)
        self.path_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME.colors['bg_input']};
                color: {THEME.colors['text_primary']};
                border: 1px solid {THEME.colors['border_color']};
                border-radius: 6px;
                padding-left: 10px;
            }}
        """)
        self.path_edit.textChanged.connect(self._on_path_changed)  # type: ignore

        row.addWidget(self.path_edit)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Build name")
        self.name_edit.setFixedHeight(36)
        self.name_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME.colors['bg_input']};
                color: {THEME.colors['text_primary']};
                border: 1px solid {THEME.colors['border_color']};
                border-radius: 6px;
                padding-left: 10px;
            }}
        """)

        self.name_edit.textChanged.connect(self._update_ok_state)  # type: ignore
        name_row.addWidget(self.name_edit)
        layout.addLayout(name_row)

        # ── DOODLES ─────────────────────────
        self.doodle_group = QButtonGroup(self)
        self.doodle_group.setExclusive(True)

        doodle_row = QHBoxLayout()
        doodle_row.setSpacing(16)

        self.selected_doodle_id = DEFAULT_DOODLE_ID
        self.selected_startup_mode = "cpu"

        for doodle_id, doodle_path in DOODLE_ICON_PATHS.items():
            if not os.path.exists(doodle_path):
                continue

            btn = QToolButton()
            btn.setCheckable(True)
            btn.setIcon(
                QIcon(
                    colorize_svg(
                        (doodle_path),
                        THEME.colors["icon_color_window"],
                    )
                )
            )
            btn.setIconSize(QSize(30, 30))
            btn.setFixedSize(36, 36)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background-color: {THEME.colors['bg_input']};
                    border: 1px solid {THEME.colors['border_color']};
                    border-radius: 8px;
                }}
                QToolButton:hover {{
                    background-color: {THEME.colors['bg_hover']};
                }}
                QToolButton:checked {{
                    border: 2px solid {THEME.colors['accent']};
                }}
                """)

            # store id on widget
            btn.setProperty("doodle_id", doodle_id)
            btn.clicked.connect(self._on_doodle_selected)  # type: ignore

            self.doodle_group.addButton(btn)
            doodle_row.addWidget(btn)

        for b in self.doodle_group.buttons():
            if b.property("doodle_id") == DEFAULT_DOODLE_ID:
                b.setChecked(True)
                break

        layout.addLayout(doodle_row)

        # ── Startup mode radios ──────────────────────────────────────────────
        self.startup_group = QButtonGroup(self)
        self.startup_group.setExclusive(True)

        modes_row = QHBoxLayout()
        modes_row.setSpacing(14)

        rb_cpu = QRadioButton("CPU")
        rb_gpu = QRadioButton("NVIDIA GPU")
        rb_fp16 = QRadioButton("NVIDIA GPU (fast fp16)")

        for rb, mode in [(rb_cpu, "cpu"), (rb_gpu, "gpu"), (rb_fp16, "fast_fp16")]:
            rb.setProperty("startup_mode", mode)
            rb.toggled.connect(self._on_startup_mode_changed)  # type: ignore
            self.startup_group.addButton(rb)
            modes_row.addWidget(rb)

            rb.setStyleSheet(f"""
                            QRadioButton {{
                                font-size: 12px;
                                color: {THEME.colors['text_primary']};
                                spacing: 8px;
                            }}
                            QRadioButton::indicator {{
                                width: 16px; height: 16px;
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
                        """)

        # default
        rb_cpu.setChecked(True)

        layout.addLayout(modes_row)

        if build:
            self.path_edit.blockSignals(True)
            self.name_edit.blockSignals(True)

            self.name_edit.setText(str(build.get("name", "")))
            self.path_edit.setText(str(build.get("path", "")))

            self.path_edit.blockSignals(False)
            self.name_edit.blockSignals(False)

            icon_id = str(build.get("icon_id", DEFAULT_DOODLE_ID))
            self.selected_doodle_id = icon_id

            for b in self.doodle_group.buttons():
                b.blockSignals(True)

            for b in self.doodle_group.buttons():
                if b.property("doodle_id") == icon_id:
                    b.setChecked(True)
                    break

            for b in self.doodle_group.buttons():
                b.blockSignals(False)

            mode = str(build.get("startup_mode", "cpu"))
            self.selected_startup_mode = mode

            for rb in self.startup_group.buttons():
                rb.blockSignals(True)

            for rb in self.startup_group.buttons():
                if rb.property("startup_mode") == mode:
                    rb.setChecked(True)
                    break

            for rb in self.startup_group.buttons():
                rb.blockSignals(False)

            self._update_ok_state()
        layout.addStretch(1)

        # action buttons
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        for btn in (self.ok_btn, self.cancel_btn):
            btn.setFixedSize(100, 34)
            btn.setStyleSheet(f"""
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
            """)
        self.ok_btn.setEnabled(False)
        btn_row.setSpacing(8)

        self.ok_btn.clicked.connect(self._accept)  # type: ignore
        self.cancel_btn.clicked.connect(self.reject)  # type: ignore
        btn_row.addWidget(self.ok_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)
        # self._round_corners(10)

    def _browse(self):
        directory = QFileDialog.getExistingDirectory(self, "Select ComfyUI folder")
        if directory:
            self.path_edit.setText(directory)
        if not self.name_edit.text().strip():
            self.name_edit.setText(
                os.path.basename(directory.rstrip("/\\")) or "My Build"
            )

    def _on_path_changed(self):
        self._update_ok_state()

    def _accept(self):
        path = self.path_edit.text().strip()
        name = self.name_edit.text().strip()

        if not is_valid_comfyui_build(path):
            QMessageBox.warning(
                self, "Invalid path", "This folder does not contain main.py"
            )
            return

        if not name:
            QMessageBox.warning(self, "Missing name", "Please enter a build name.")
            return

        data = load_user_config()
        builds = data.get("builds", []) or []

        def apply_manager_defaults(selected_id: str):
            if self.mode == SetupMode.MANAGER:
                data["comfyui_path"] = path
                data["last_used_build_id"] = selected_id

        # ── EDIT MODE: update by id ──
        if self.edit_build_id:
            updated = False
            for b in builds:
                if str(b.get("id", "")) == self.edit_build_id:
                    b["name"] = name
                    b["path"] = path
                    b["icon_id"] = self.selected_doodle_id
                    b["startup_mode"] = self.selected_startup_mode
                    updated = True
                    break

            if not updated:
                builds.append(
                    {
                        "id": self.edit_build_id,
                        "name": name,
                        "path": path,
                        "icon_id": self.selected_doodle_id,
                        "startup_mode": self.selected_startup_mode,
                    }
                )

            apply_manager_defaults(self.edit_build_id)

            data["builds"] = builds
            save_user_config(data)
            self.accept()
            return

        # ── ADD MODE: keep legacy dedupe-by-path ──
        for b in builds:
            if os.path.normpath(b.get("path", "")) == os.path.normpath(path):
                b["name"] = name
                b["icon_id"] = self.selected_doodle_id
                b["startup_mode"] = self.selected_startup_mode

                apply_manager_defaults(str(b.get("id", "")))

                data["builds"] = builds
                save_user_config(data)
                self.accept()
                return

        build_id = str(uuid.uuid4())
        builds.append(
            {
                "id": build_id,
                "name": name,
                "path": path,
                "icon_id": self.selected_doodle_id,
                "startup_mode": self.selected_startup_mode,
            }
        )

        data["builds"] = builds
        apply_manager_defaults(build_id)

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

    def _on_doodle_selected(self):
        btn = self.sender()
        if btn:
            self.selected_doodle_id = btn.property("doodle_id") or DEFAULT_DOODLE_ID
        self._update_ok_state()

    def _update_ok_state(self):
        path_ok = is_valid_comfyui_build(self.path_edit.text().strip())
        name_ok = bool(self.name_edit.text().strip())
        if hasattr(self, "ok_btn"):
            self.ok_btn.setEnabled(path_ok and name_ok)

    def _on_startup_mode_changed(self):
        rb = self.sender()
        if rb and rb.isChecked():
            self.selected_startup_mode = rb.property("startup_mode") or "cpu"
            self._update_ok_state()
