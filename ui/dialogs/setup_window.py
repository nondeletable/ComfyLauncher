from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QFrame,
    QButtonGroup,
    QToolButton,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QColor

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
from utils.build_validation import is_valid_comfyui_build, detect_build_type
from ui.dialogs.messagebox import MessageBox as MB
from ui.dialogs.flags_picker_dialog import FlagsPickerDialog

import os
import uuid
from enum import Enum


class SetupMode(Enum):
    MANAGER = "manager"
    SETTINGS = "settings"


class SetupWindow(QDialog):
    """The initial path setup window for ComfyUI"""

    WINDOW_WIDTH = 530
    WINDOW_HEIGHT = 400
    BORDER_RADIUS = 9
    DEFAULT_FLAGS = "--windows-standalone-build"

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
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setObjectName("SetupWindow")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(15, 15, 15, 15)
        outer.setSpacing(0)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("setup_main_frame")

        outer.addWidget(self.main_frame)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.main_frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(14)

        r = self.BORDER_RADIUS

        self.main_frame.setStyleSheet(
            f"""
        QFrame#setup_main_frame {{
            background-color: {THEME.colors['bg_header']};
            border-radius: {r}px;
        }}
        """
        )

        info = QLabel(
            "Specify the folder where ComfyUI is located (folder with main.py).<br>"
            "For example: <code>D:/Portable/ComfyUI</code>. "
            "Be sure to give the build a name and select an icon."
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
                )
            )
        )
        browse_btn.setIconSize(QSize(20, 20))
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
        self.path_edit.setStyleSheet(self._line_edit_style())
        self.path_edit.textChanged.connect(self._on_path_changed)  # type: ignore

        row.addWidget(self.path_edit)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Build name")
        self.name_edit.setFixedHeight(36)
        self.name_edit.setStyleSheet(self._line_edit_style())

        self.name_edit.textChanged.connect(self._update_ok_state)  # type: ignore
        name_row.addWidget(self.name_edit)
        layout.addLayout(name_row)

        # ── DOODLES ─────────────────────────
        self.doodle_group = QButtonGroup(self)
        self.doodle_group.setExclusive(True)

        doodle_row = QHBoxLayout()
        doodle_row.setSpacing(16)

        self.selected_doodle_id = DEFAULT_DOODLE_ID

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
            btn.setStyleSheet(
                f"""
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
                """
            )

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

        # ── Startup flags ────────────────────────────────────────────────────
        flags_label = QLabel("Startup flags")
        flags_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: 12px;
                color: {THEME.colors['text_secondary']};
            }}
        """
        )
        layout.addWidget(flags_label)

        flags_row = QHBoxLayout()
        flags_row.setSpacing(8)

        self.flags_edit = QLineEdit()
        self.flags_edit.setPlaceholderText(
            "--windows-standalone-build --lowvram --listen"
        )
        self.flags_edit.setFixedHeight(36)
        self.flags_edit.setStyleSheet(self._line_edit_style())

        add_btn = QPushButton()
        add_btn.setIcon(
            QIcon(
                colorize_svg(
                    ICON_PATHS["plus"],
                    THEME.colors["icon_color_window"],
                )
            )
        )
        add_btn.setIconSize(QSize(20, 20))
        add_btn.setFixedSize(38, 36)
        add_btn.setToolTip("Add flags")
        add_btn.setStyleSheet(
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
        add_btn.clicked.connect(self._open_flags_picker)  # type: ignore

        flags_row.addWidget(self.flags_edit)
        flags_row.addWidget(add_btn)
        layout.addLayout(flags_row)

        if not build:
            self.flags_edit.setText(self.DEFAULT_FLAGS)

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

            extra_flags = build.get("extra_flags", [])
            self.flags_edit.setText(" ".join(extra_flags))
            self._update_ok_state()
        layout.addStretch(1)

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

    def _browse(self):
        directory = QFileDialog.getExistingDirectory(self, "Select ComfyUI folder")
        if not directory:
            return

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
            MB.warning(self, "Invalid path", "This folder does not contain main.py")
            return

        if detect_build_type(path) == "standalone":
            proceed = MB.ask_yes_no(
                self,
                "Non-portable build",
                "No embedded Python was found next to this folder, so it looks like "
                "a non-portable or third-party ComfyUI install "
                "(e.g. system Python or Stability Matrix).\n\n"
                "ComfyLauncher will launch it using the system Python. "
                "Add this build anyway?",
            )
            if not proceed:
                return

        if not name:
            MB.warning(self, "Missing name", "Please enter a build name.")
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
                    b["extra_flags"] = self._get_extra_flags()
                    b.pop("startup_mode", None)
                    updated = True
                    break

            if not updated:
                builds.append(
                    {
                        "id": self.edit_build_id,
                        "name": name,
                        "path": path,
                        "icon_id": self.selected_doodle_id,
                        "extra_flags": self._get_extra_flags(),
                    }
                )

            apply_manager_defaults(self.edit_build_id)

            data["builds"] = builds
            if not save_user_config(data):
                self._warn_save_failed()
                return
            self.accept()
            return

        build_id = str(uuid.uuid4())
        builds.append(
            {
                "id": build_id,
                "name": name,
                "path": path,
                "icon_id": self.selected_doodle_id,
                "extra_flags": self._get_extra_flags(),
            }
        )

        data["builds"] = builds
        apply_manager_defaults(build_id)

        if not save_user_config(data):
            self._warn_save_failed()
            return
        self.accept()

    def _warn_save_failed(self):
        MB.warning(
            self,
            "Could not save",
            "Failed to save the settings. Make sure the app can write to your "
            "AppData folder, then try again.",
        )

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

    def _open_flags_picker(self):
        picker = FlagsPickerDialog(self, flags_text=self.flags_edit.text())
        picker.flagsChanged.connect(self.flags_edit.setText)
        picker.exec()

    def _get_extra_flags(self) -> list[str]:
        raw = self.flags_edit.text().strip()
        return raw.split() if raw else []

    def _line_edit_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: {THEME.colors['bg_input']};
                color: {THEME.colors['text_primary']};
                border: 1px solid {THEME.colors['border_color']};
                border-radius: 6px;
                padding-left: 10px;
            }}
        """
