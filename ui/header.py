from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPainter, QPixmap, QColor

from config import ICON_PATH, ICON_PATHS, HEAD_ICON_PATHS, load_user_config
from ui.theme.manager import THEME


def colorize_svg(svg_path, color=THEME.colors["icon_color_window"], size=QSize(20, 20)):
    """Creates a QIcon from an SVG and recolors it to the specified color."""
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)

    icon = QIcon(svg_path)
    painter = QPainter(pixmap)
    icon.paint(painter, pixmap.rect())
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()

    return QIcon(pixmap)


class HeaderBar(QWidget):
    """Custom window header that combines toolbar and control buttons."""

    # signals from the toolbar
    console_clicked = pyqtSignal()
    restart_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    folder_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    output_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.drag_pos = QPoint(0, 0)
        self.setObjectName("HeaderBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(46)

        cfg = load_user_config()
        show_cmd = cfg.get("show_cmd", True)
        self.use_internal_console = not show_cmd

        self.setStyleSheet(
            f"""
            #HeaderBar {{
                background-color: {THEME.colors['bg_header']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            QPushButton {{
                background-color: {THEME.colors['bg_header']};
                border: none;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {THEME.colors['bg_hover']}; }}
            QPushButton:pressed {{ background-color: {THEME.colors['bg_hover']}; }}
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(10)

        # ── Left side ───────────────────────────────
        self.app_icon = QLabel()
        self.app_icon.setPixmap(QIcon(ICON_PATH).pixmap(24, 24))
        layout.addWidget(self.app_icon)

        self.title = QLabel("ComfyLauncher")
        self.title.setStyleSheet(
            f"color: {THEME.colors['app_title_color']}; font-weight: bold; font-size: 15px;"
        )
        layout.addWidget(self.title)

        layout.addSpacerItem(
            QSpacerItem(15, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        )

        # ── Central part (toolbar) ────────────────
        self.btn_settings = QPushButton(colorize_svg(ICON_PATHS["settings"]), "")
        self.btn_folder = QPushButton(colorize_svg(ICON_PATHS["open_folder"]), "")
        self.btn_output = QPushButton(colorize_svg(ICON_PATHS["open_output"]), "")
        self.btn_reload = QPushButton(colorize_svg(ICON_PATHS["refresh"]), "")

        for btn in [
            self.btn_settings,
            self.btn_folder,
            self.btn_output,
            self.btn_reload,
        ]:
            btn.setIconSize(QSize(20, 20))
            layout.addWidget(btn)

        layout.addStretch()

        # ── Right side ───────────────────────────────

        # indicator online
        self.status_label = QLabel("Online")
        self.status_label.setStyleSheet(
            f"""
            color: {THEME.colors['success']};
            background-color: rgba(60,60,60,0.7);
            border-radius: 6px;
            padding: 3px 8px;
            font-weight: bold;
        """
        )
        layout.addWidget(self.status_label)

        layout.addSpacerItem(
            QSpacerItem(25, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        )

        # Stop and Restart buttons are located right behind the indicator
        self.btn_console = QPushButton(colorize_svg(ICON_PATHS["terminal"]), "")
        self.btn_restart = QPushButton(colorize_svg(ICON_PATHS["restart"]), "")
        self.btn_stop = QPushButton(colorize_svg(ICON_PATHS["stop"]), "")

        self.btn_console.setVisible(self.use_internal_console)

        for btn in [self.btn_console, self.btn_restart, self.btn_stop]:
            btn.setIconSize(QSize(20, 20))
            layout.addWidget(btn)

        self.btn_min = QPushButton(
            colorize_svg(
                HEAD_ICON_PATHS["minimize"],
                THEME.colors["icon_color_window"],
                QSize(20, 20),
            ),
            "",
        )
        self.btn_max = QPushButton(
            colorize_svg(
                HEAD_ICON_PATHS["maximize"],
                THEME.colors["icon_color_window"],
                QSize(20, 20),
            ),
            "",
        )
        self.btn_close = QPushButton(
            colorize_svg(
                HEAD_ICON_PATHS["close"],
                THEME.colors["icon_color_window"],
                QSize(20, 20),
            ),
            "",
        )

        for btn in [self.btn_min, self.btn_max, self.btn_close]:
            btn.setFixedSize(25, 25)
            btn.setIconSize(QSize(20, 20))
            btn.setStyleSheet(
                """
                QPushButton {
                    border: none;
                    background: transparent;
                }
                QPushButton:hover {{ background: {THEME.colors['bg_hover']}; }}
            """
            )
            layout.addWidget(btn)

        self.btn_restart.setToolTip("Restart ComfyUI")
        self.btn_stop.setToolTip("Stop ComfyUI")
        self.btn_settings.setToolTip("Settings")
        self.btn_folder.setToolTip("Open ComfyUI folder")
        self.btn_output.setToolTip("Open output")
        self.btn_reload.setToolTip("Refresh UI")
        self.btn_console.setToolTip("Command Prompt")

        # ── Signals ───────────────────────────────────
        self.btn_restart.clicked.connect(self.restart_clicked.emit)  # type: ignore
        self.btn_stop.clicked.connect(self.stop_clicked.emit)  # type: ignore
        self.btn_folder.clicked.connect(self.folder_clicked.emit)  # type: ignore
        self.btn_settings.clicked.connect(self.settings_clicked.emit)  # type: ignore
        self.btn_output.clicked.connect(self.output_clicked.emit)  # type: ignore
        self.btn_reload.clicked.connect(self._on_reload_clicked)  # type: ignore
        if hasattr(self, "btn_console"):
            self.btn_console.clicked.connect(self.console_clicked.emit)

        self.btn_min.clicked.connect(self.parent.showMinimized)  # type: ignore
        self.btn_max.clicked.connect(lambda: self.parent.showNormal() if self.parent.isMaximized() else self.parent.showMaximized())  # type: ignore
        self.btn_close.clicked.connect(self.parent.close)  # type: ignore

        self._apply_theme()
        THEME.themeChanged.connect(self._apply_theme)

    def _on_reload_clicked(self):
        if hasattr(self.parent, "browser") and self.parent.browser:
            self.parent.browser.reload()

    # ── Dragging a window ───────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.parent.move(
                self.parent.pos() + event.globalPosition().toPoint() - self.drag_pos
            )
            self.drag_pos = event.globalPosition().toPoint()

    def _apply_theme(self, *args):
        """Reapplies colors when changing themes."""
        c = THEME.colors
        self.setStyleSheet(
            f"""
            #HeaderBar {{
                background-color: {c['bg_header']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            QPushButton {{
                background-color: {c['bg_header']};
                border: none;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {c['bg_hover']}; }}
            QPushButton:pressed {{ background-color: {c['bg_hover']}; }}
        """
        )

        self.title.setStyleSheet(
            f"color: {c['app_title_color']}; font-weight: bold; font-size: 15px;"
        )
        self.status_label.setStyleSheet(
            f"""
            color: {c['success']};
            background-color: rgba(60,60,60,0.7);
            border-radius: 6px;
            padding: 3px 8px;
            font-weight: bold;
        """
        )

        # Re-creating icons for a new theme
        self.btn_min.setIcon(
            colorize_svg(
                HEAD_ICON_PATHS["minimize"], c["icon_color_window"], QSize(20, 20)
            )
        )
        self.btn_max.setIcon(
            colorize_svg(
                HEAD_ICON_PATHS["maximize"], c["icon_color_window"], QSize(20, 20)
            )
        )
        self.btn_close.setIcon(
            colorize_svg(
                HEAD_ICON_PATHS["close"], c["icon_color_window"], QSize(20, 20)
            )
        )
        self.btn_restart.setIcon(
            colorize_svg(ICON_PATHS["restart"], c["icon_color_window"], QSize(20, 20))
        )
        self.btn_stop.setIcon(
            colorize_svg(ICON_PATHS["stop"], c["icon_color_window"], QSize(20, 20))
        )
        self.btn_settings.setIcon(
            colorize_svg(ICON_PATHS["settings"], c["icon_color_window"], QSize(20, 20))
        )
        self.btn_folder.setIcon(
            colorize_svg(
                ICON_PATHS["open_folder"], c["icon_color_window"], QSize(20, 20)
            )
        )
        self.btn_output.setIcon(
            colorize_svg(
                ICON_PATHS["open_output"], c["icon_color_window"], QSize(20, 20)
            )
        )
        self.btn_reload.setIcon(
            colorize_svg(ICON_PATHS["refresh"], c["icon_color_window"], QSize(20, 20))
        )
        self.btn_console.setIcon(
            colorize_svg(ICON_PATHS["terminal"], c["icon_color_window"], QSize(20, 20))
        )
