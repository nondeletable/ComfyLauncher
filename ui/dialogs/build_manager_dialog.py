from __future__ import annotations

import os
from typing import Optional

from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QPainterPath, QRegion, QIcon, QFontMetrics
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QWidget,
    QToolButton,
)
from ui.theme.manager import THEME
from config import load_user_config, ICON_PATH, ICON_PATHS
from ui.dialogs.setup_window import SetupWindow
from ui.header import colorize_svg

try:
    from config import DOODLE_ICON_PATHS, DEFAULT_DOODLE_ID
except Exception:
    DOODLE_ICON_PATHS = {}
    DEFAULT_DOODLE_ID = "default"


class BuildManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ComfyLauncher")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setModal(True)
        self.setFixedSize(700, 420)
        self.setObjectName("BuildManagerDialog")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.selected_build_id: Optional[str] = None

        data = load_user_config()
        self.builds = data.get("builds", []) or []
        self.last_used_id = data.get("last_used_build_id", "")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("build_manager_main_frame")
        root.addWidget(self.main_frame)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(14)

        r = 9
        b = 3
        self.main_frame.setStyleSheet(f"""
            QFrame#build_manager_main_frame {{
                background-color: {THEME.colors['bg_header']};
                border: {b}px solid {THEME.colors['border_color']};
                border-radius: {r}px;
            }}
            """)

        title = QLabel("Select a build to launch")
        title.setStyleSheet(
            f"font-size: 16px; "
            f"font-weight: 600; "
            f"color: {THEME.colors['text_primary']};"
        )
        layout.addWidget(title)

        # --- Scroll area with build rows ---
        scroll = QScrollArea(self.main_frame)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {THEME.colors['bg_header']};
            }}
            QScrollArea::viewport {{
                background-color: {THEME.colors['bg_header']};
                border: none;
            }}
            """)

        container = QWidget()
        container.setStyleSheet(f"background-color: {THEME.colors['bg_header']};")
        container.setAutoFillBackground(True)

        self.list_layout = QVBoxLayout(container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        if not self.builds:
            empty = QLabel("No builds found. Please run initial setup.")
            empty.setStyleSheet(f"color: {THEME.colors['text_secondary']};")
            self.list_layout.addWidget(empty)
        else:
            for b in self.builds:
                self.list_layout.addWidget(self._build_row(b))

        scroll.setWidget(container)

        # ── dynamic max height: shrink to content, but keep scroll when too long
        container.adjustSize()  # помогает пересчитать sizeHint сразу
        content_h = container.sizeHint().height()

        MAX_LIST_H = 260
        scroll.setMaximumHeight(min(content_h, MAX_LIST_H))

        # 0 вместо 1 — скролл больше не "съедает" всё место
        layout.addWidget(scroll, 0)

        # ── Add Build row (under the list) ─────────────────────────
        add_row = QHBoxLayout()
        add_row.setContentsMargins(0, 0, 0, 0)
        add_row.setSpacing(10)

        btn_add = QToolButton()
        btn_add.setIcon(
            QIcon(
                colorize_svg(
                    ICON_PATHS["plus"],
                    THEME.colors["icon_color_window"],
                )
            )
        )
        btn_add.setIconSize(QSize(30, 30))
        btn_add.setFixedSize(44, 44)
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
        btn_add.clicked.connect(self._add_build)  # type: ignore

        lbl_add = QLabel("Add Build")
        lbl_add.setStyleSheet(f"color: {THEME.colors['text_secondary']};")

        add_row.addWidget(btn_add, 0, Qt.AlignmentFlag.AlignLeft)
        add_row.addWidget(lbl_add, 0, Qt.AlignmentFlag.AlignVCenter)
        add_row.addStretch(1)

        layout.addLayout(add_row)
        layout.addStretch(1)

        # --- Bottom buttons ---
        bottom = QHBoxLayout()
        bottom.addStretch(1)

        self.btn_close = QPushButton("Close")
        self.btn_close.setFixedSize(110, 34)
        self.btn_close.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {THEME.colors['text_secondary']};
                        border: 1px solid {THEME.colors['border_color']};
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background-color: {THEME.colors['bg_hover']};
                    }}
                    """)
        self.btn_close.clicked.connect(self.reject)  # type: ignore
        bottom.addWidget(self.btn_close)

        layout.addLayout(bottom)

    def _build_row(self, build: dict) -> QWidget:
        build_id = str(build.get("id", ""))
        name = str(build.get("name", "Unnamed"))
        path = str(build.get("path", ""))
        icon_id = str(build.get("icon_id", DEFAULT_DOODLE_ID))

        row = QFrame()
        row.setObjectName("BuildRow")
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        is_last = build_id == self.last_used_id

        bg = THEME.colors["bg_header"]
        border = THEME.colors["border_color"]

        row.setStyleSheet(f"""
            QFrame#BuildRow {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            """)

        h = QHBoxLayout(row)
        h.setContentsMargins(10, 8, 10, 8)
        h.setSpacing(10)

        # Icon
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(20, 20)

        icon_path = DOODLE_ICON_PATHS.get(icon_id) or DOODLE_ICON_PATHS.get(
            DEFAULT_DOODLE_ID
        )
        if icon_path and os.path.exists(icon_path):
            themed_svg_path_or_data = colorize_svg(
                icon_path, THEME.colors["icon_color_window"]
            )
            pm = QIcon(themed_svg_path_or_data).pixmap(20, 20)
            icon_lbl.setPixmap(pm)

        h.addWidget(icon_lbl)

        # Text block (name + elided path)
        text_box = QVBoxLayout()
        text_box.setSpacing(2)

        name_lbl = QLabel(name + ("  (last used)" if is_last else ""))
        name_lbl.setStyleSheet(
            f"font-size: 14px; "
            f"font-weight: 600; "
            f"color: {THEME.colors['text_primary']};"
        )

        path_lbl = QLabel()
        path_lbl.setStyleSheet(f"color: {THEME.colors['text_secondary']};")
        path_lbl.setToolTip(path)

        fm = QFontMetrics(path_lbl.font())
        elided = fm.elidedText(path, Qt.TextElideMode.ElideMiddle, 360)
        path_lbl.setText(elided)

        text_box.addWidget(name_lbl)
        text_box.addWidget(path_lbl)

        h.addLayout(text_box, 1)

        # Edit button
        btn_edit = QToolButton()
        btn_edit.setFixedSize(36, 36)
        btn_edit.setIcon(
            QIcon(
                colorize_svg(ICON_PATHS["settings"], THEME.colors["icon_color_window"])
            )
        )
        btn_edit.setIconSize(QSize(18, 18))
        btn_edit.setToolTip("Edit build")
        btn_edit.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: 1px solid {THEME.colors['border_color']};
                border-radius: 6px;
            }}
            QToolButton:hover {{
                background-color: {THEME.colors['bg_hover']};
            }}
        """)
        btn_edit.clicked.connect(  # type: ignore
            lambda checked=False, b=build: self._edit_build(b)
        )
        h.addWidget(btn_edit)

        # Launch button
        btn = QPushButton("Launch")
        btn.setFixedSize(110, 34)
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
        btn.clicked.connect(lambda: self._launch(build_id))  # type: ignore
        h.addWidget(btn)

        return row

    def _launch(self, build_id: str):
        self.selected_build_id = build_id
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_rounded_mask()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_rounded_mask()

    def _apply_rounded_mask(self):
        radius = 9
        path = QPainterPath()
        rect = QRectF(self.rect())
        path.addRoundedRect(rect, radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def _edit_build(self, build: dict):
        dlg = SetupWindow(self, build=build)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._reload_builds()

    def _add_build(self):
        dlg = SetupWindow(self)
        res = dlg.exec()
        if res == QDialog.DialogCode.Accepted:
            self._reload_builds()

    def _reload_builds(self):
        data = load_user_config()
        self.builds = data.get("builds", []) or []
        self.last_used_id = data.get("last_used_build_id", "")

        # очистить list_layout (кроме stretch)
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        if not self.builds:
            empty = QLabel("No builds found. Please run initial setup.")
            empty.setStyleSheet(f"color: {THEME.colors['text_secondary']};")
            self.list_layout.addWidget(empty)
        else:
            for b in self.builds:
                self.list_layout.addWidget(self._build_row(b))

        self.list_layout.addStretch(1)
