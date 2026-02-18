from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QDialog,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFontMetrics
from config import (
    load_user_config,
    save_user_config,
    ICON_PATHS,
    OTHER_ICONS,
)
from ui.header import colorize_svg
from ui.theme.manager import THEME
from ui.dialogs.messagebox import MessageBox as MB
from ui.dialogs.setup_window import SetupWindow, SetupMode

import webbrowser
import os

try:
    from config import DOODLE_ICON_PATHS, DEFAULT_DOODLE_ID
except Exception:
    DOODLE_ICON_PATHS = {}
    DEFAULT_DOODLE_ID = "default"


class BuildSettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(16)

        # ─── Headline ───────────────────────────────
        title = QLabel("Builds")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        content_layout.addWidget(title)

        desc = QLabel(
            "This section is entirely dedicated to ComfyUI builds.\n"
            "Here you can see all saved builds, edit the name or icon, and delete a build."
        )
        desc.setStyleSheet(f"color: {THEME.colors['text_secondary']}; font-size: 13px;")
        desc.setWordWrap(True)
        content_layout.addWidget(desc)

        # ─── Builds List ────────────────────────────
        self.builds_container = QWidget()
        self.builds_container.setStyleSheet(
            f"background-color: {THEME.colors['bg_header']};"
        )
        self.builds_container.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum,
        )

        self.builds_layout = QVBoxLayout(self.builds_container)
        self.builds_layout.setContentsMargins(14, 0, 0, 0)
        self.builds_layout.setSpacing(8)

        content_layout.addWidget(self.builds_container)
        content_layout.addStretch()

        # ---
        info_label = QLabel("Check for ComfyUI updates and download the new version:")
        info_label.setStyleSheet(
            f"color: {THEME.colors['text_secondary']}; font-size: 13px; margin-top: 14px;"
        )
        info_label.setWordWrap(True)
        content_layout.addWidget(info_label)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        btn_row.setContentsMargins(14, 0, 0, 0)
        btn_row.setSpacing(0)

        btn_download = QPushButton()
        btn_download.setIconSize(QSize(60, 28))
        btn_download.setFixedSize(100, 36)
        btn_download.setIcon(
            QIcon(
                colorize_svg(
                    OTHER_ICONS.get("comfyui"),
                    THEME.colors["icon_color_window"],
                    QSize(60, 28),
                )
            )
        )
        btn_download.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME.colors['bg_input']};
                border: 1px solid {THEME.colors['border_color']};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {THEME.colors['accent']};
                border-color: {THEME.colors['accent']};
            }}
        """)

        btn_download.clicked.connect(  # type: ignore
            lambda: webbrowser.open("https://www.comfy.org/download")
        )

        btn_row.addWidget(btn_download)
        content_layout.addLayout(btn_row)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        self._refresh_builds_list()

    def _sync_footer_buttons(self):
        p = self.parent()
        if p and hasattr(p, "btn_apply"):
            p.btn_apply.setEnabled(False)

    def apply_changes(self):
        return True

    def cancel_changes(self):
        self._sync_footer_buttons()
        return True

    def apply(self):
        return self.apply_changes()

    def reset(self):
        return self.cancel_changes()

    def _tool_icon_btn_style(self) -> str:
        return f"""
        QToolButton {{
            background-color: transparent;
            border: 1px solid {THEME.colors['border_color']};
            border-radius: 6px;
        }}
        QToolButton:hover {{
            background-color: {THEME.colors['bg_hover']};
        }}
        """

    def _clear_layout(self, layout: QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

    def _refresh_builds_list(self):
        if not hasattr(self, "builds_layout"):
            return

        cfg = load_user_config()
        builds = cfg.get("builds", []) or []
        last_id = cfg.get("last_used_build_id", "")

        self._clear_layout(self.builds_layout)

        if not builds:
            empty = QLabel("No builds saved yet.")
            empty.setStyleSheet(
                f"color: {THEME.colors['text_secondary']}; font-size: 13px;"
            )
            self.builds_layout.addWidget(empty)
        else:
            for b in builds:
                self.builds_layout.addWidget(self._build_row_widget(b, last_id))

        self.builds_layout.addWidget(self._add_build_row_widget())

        self.builds_container.adjustSize()
        self.builds_container.updateGeometry()

    def _on_add_build(self):
        dlg = SetupWindow(self, build=None, mode=SetupMode.SETTINGS)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_builds_list()

    def _build_row_widget(self, build: dict, last_used_id: str) -> QWidget:
        build_id = str(build.get("id", ""))
        name = str(build.get("name", "Unnamed"))
        path = str(build.get("path", ""))
        icon_id = str(build.get("icon_id", DEFAULT_DOODLE_ID))

        row = QFrame()
        row.setObjectName("BuildRow")
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row.setStyleSheet(f"""
            QFrame#BuildRow {{
                background-color: {THEME.colors['bg_header']};
                border: 1px solid {THEME.colors['border_color']};
                border-radius: 8px;
            }}
            """)

        h = QHBoxLayout(row)
        h.setContentsMargins(10, 8, 10, 8)
        h.setSpacing(10)

        # Icon (doodle)
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(40, 40)

        icon_path = DOODLE_ICON_PATHS.get(icon_id) or DOODLE_ICON_PATHS.get(
            DEFAULT_DOODLE_ID
        )
        if icon_path and os.path.exists(icon_path):
            themed = colorize_svg(icon_path, THEME.colors["icon_color_window"])
            pm = QIcon(themed).pixmap(36, 36)
            icon_lbl.setPixmap(pm)

        h.addWidget(icon_lbl)

        # Text
        text_box = QVBoxLayout()
        text_box.setSpacing(2)

        is_last = build_id == str(last_used_id)
        name_lbl = QLabel(name + ("  (last used)" if is_last else ""))
        name_lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {THEME.colors['text_primary']};
                margin: 0px;
            }}
            """)
        path_lbl = QLabel(path)
        path_lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {THEME.colors['text_secondary']};
                margin: 0px;
            }}
            """)
        path_lbl.setToolTip(path)

        fm = QFontMetrics(path_lbl.font())
        elided = fm.elidedText(path, Qt.TextElideMode.ElideMiddle, 360)
        path_lbl.setText(elided)

        text_box.addWidget(name_lbl)
        text_box.addWidget(path_lbl)
        h.addLayout(text_box, 1)

        # Edit / Delete buttons (themed icons)
        btn_edit = QToolButton()
        btn_edit.setFixedSize(36, 36)
        btn_edit.setIcon(
            QIcon(
                colorize_svg(ICON_PATHS["settings"], THEME.colors["icon_color_window"])
            )
        )
        btn_edit.setIconSize(QSize(18, 18))
        btn_edit.setToolTip("Edit build")
        btn_edit.setStyleSheet(self._tool_icon_btn_style())
        btn_edit.clicked.connect(lambda checked=False, b=build: self._on_edit_build(b))  # type: ignore

        btn_del = QToolButton()
        btn_del.setFixedSize(36, 36)
        btn_del.setIcon(
            QIcon(colorize_svg(ICON_PATHS["delete"], THEME.colors["icon_color_window"]))
        )
        btn_del.setIconSize(QSize(18, 18))
        btn_del.setToolTip("Delete build")
        btn_del.setStyleSheet(self._tool_icon_btn_style())
        btn_del.clicked.connect(lambda checked=False, b=build: self._on_delete_build(b))  # type: ignore

        h.addWidget(btn_edit)
        h.addWidget(btn_del)

        return row

    def _add_build_row_widget(self) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)

        btn_add = QToolButton()
        btn_add.setIcon(
            QIcon(
                colorize_svg(
                    ICON_PATHS["plus"],
                    THEME.colors["icon_color_window"],
                )
            )
        )
        btn_add.setIconSize(QSize(28, 28))
        btn_add.setFixedSize(40, 40)
        btn_add.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
            }}
            QToolButton:hover {{
                background-color: {THEME.colors['bg_hover']};
            }}
            """)
        btn_add.clicked.connect(self._on_add_build)  # type: ignore

        lbl = QLabel("Add Build")
        lbl.setStyleSheet(f"color: {THEME.colors['text_secondary']}; font-size: 13px;")

        h.addWidget(btn_add, 0, Qt.AlignmentFlag.AlignLeft)
        h.addWidget(lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        h.addStretch(1)

        return row

    def _on_edit_build(self, build: dict):
        dlg = SetupWindow(self, build=build, mode=SetupMode.SETTINGS)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_builds_list()

    def _sanitize_last_used(self, cfg: dict) -> None:
        """Ensure last_used_build_id points to an existing build or is empty."""
        builds = cfg.get("builds", []) or []
        ids = {str(b.get("id", "")) for b in builds}
        last_id = str(cfg.get("last_used_build_id", "") or "")
        if last_id and last_id not in ids:
            cfg["last_used_build_id"] = ""

    def _on_delete_build(self, build: dict):
        build_id = str(build.get("id", ""))
        name = str(build.get("name", "Unnamed"))

        if not build_id:
            MB.warning(self.window(), "Delete build", "Build ID is missing.")
            return

        if not MB.ask_yes_no(self.window(), "Delete build", f"Delete build “{name}”?"):
            return

        cfg = load_user_config()
        builds = cfg.get("builds", []) or []

        # remove by id
        cfg["builds"] = [b for b in builds if str(b.get("id", "")) != build_id]

        # if deleted last_used -> clear (do NOT auto-pick another)
        if str(cfg.get("last_used_build_id", "") or "") == build_id:
            cfg["last_used_build_id"] = ""

        # if last_used became invalid for any reason -> clear
        self._sanitize_last_used(cfg)

        save_user_config(cfg)

        # update UI
        self._refresh_builds_list()
