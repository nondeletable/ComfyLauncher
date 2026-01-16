from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QStackedWidget,
    QPushButton,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainterPath, QRegion

from ui.settings.page_build import BuildSettingsPage
from ui.settings.page_behavior import BehaviorSettingsPage
from ui.settings.page_colortheme import ColorThemesPage
from ui.settings.page_about import AboutSettingsPage
from ui.settings.page_logs import LogsSettingsPage
from ui.settings.page_startapp import StartAppSettingsPage
from ui.theme.manager import THEME
from ui.dialogs.messagebox import MessageBox as MB


# ──────────────────────────────────────────────
class SettingsWindow(QWidget):
    """The launcher settings window is a single container without visual breaks."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # ─── Basic window parameters ─────────────────────────
        self.setWindowTitle("Settings")
        self.setFixedSize(1200, 700)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.colors = THEME.colors
        self.drag_position = None

        # ─── Main frame ───────────────────────────────────
        main_frame = QFrame(self)
        main_frame.setObjectName("settings_main_frame")
        main_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        main_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {self.colors['bg_header']};
                color: {self.colors['text_primary']};
                border-radius: 10px;
            }}
            QFrame#settings_main_frame {{
                border: 2px solid {self.colors['border_color']};
            }}
        """
        )

        # ─── ONE layout for the entire window ──────────────────
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── ONE layout for the body (menu + content) ──────────
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # ─── Left menu panel ────────────────────────────────
        self.menu = QListWidget()
        self.menu.addItems(
            [
                "Comfy Folder",
                "CMD Window",
                "Exit Options",
                "Color Themes",
                "Launcher Logs",
                "About",
            ]
        )
        self.menu.setFixedWidth(200)
        self.menu.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {self.colors['bg_menu']};
                color: {self.colors['text_secondary']};
                font-size: 15px;
                border-top-left-radius: 10px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 6px;
            }}
            QListWidget::item {{
                padding: 10px 18px;
                border-radius: 6px;
                transition: all 0.2s ease-in-out;
            }}
            QListWidget::item:hover {{
                background-color: {self.colors['bg_hover']};
                color: {self.colors['text_primary']};
            }}
            QListWidget::item:selected {{
                background-color: {self.colors['accent']};
                color: #fff;
                border: none;
                outline: none;
            }}
            QListWidget:focus {{
                outline: 0;
                border: none;
            }}
        """
        )

        # ─── Right content panel ───────────────────────────
        self.pages = QStackedWidget()
        self.pages.setStyleSheet(
            f"""
            QStackedWidget {{
                background-color: {self.colors["bg_header"]};
                border-top-right-radius: 10px;
                border-top-left-radius: 0px;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: 0px;
            }}
            QLabel {{
                color: {self.colors['text_primary']};
                font-size: 16px;
                margin: 10px;
            }}
        """
        )

        # ─── Bottom button bar ─────────────────────────────
        footer = QFrame()
        footer.setStyleSheet(
            f"""
            QFrame {{
                background-color: {self.colors['bg_menu']};
                border-bottom-left-radius: 10px;
                border-top-left-radius: 0px;
                border-bottom-right-radius: 10px;
                border-top-right-radius: 0px;
            }}
        """
        )
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 10, 20, 10)
        footer_layout.setSpacing(12)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.btn_apply = QPushButton("Apply")
        self.btn_close = QPushButton("Close")

        for btn in (self.btn_apply, self.btn_close):
            btn.setFixedSize(100, 36)
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.colors['text_secondary']};
                    border: 1px solid {self.colors['border_color']};
                    border-radius: 6px;
                    transition: all 0.2s ease-in-out;
                }}
                QPushButton:hover {{
                    background-color: {self.colors['accent']};
                    color: #fff;
                    border-color: {self.colors['accent']};
                }}
                QPushButton:disabled {{
                    color: #555555;
                    border: 1px solid #555555;
                }}
            """
            )
            footer_layout.addWidget(btn)

        # ─── Adding menus and pages to the body ─────────────────
        body_layout.addWidget(self.menu)
        body_layout.addWidget(self.pages)

        # ─── Add everything to the main layout ──────────────────
        main_layout.addLayout(body_layout, stretch=1)
        main_layout.addWidget(footer)

        # ─── Adding a main frame to the window ───────────────────
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(main_frame)
        self.setLayout(outer_layout)

        # ─── Adding pages ───────────────────────────────
        self.pages.addWidget(BuildSettingsPage(parent=self))
        self.pages.addWidget(StartAppSettingsPage(parent=self))
        self.pages.addWidget(BehaviorSettingsPage(parent=self))
        self.pages.addWidget(ColorThemesPage(parent=self))
        self.pages.addWidget(LogsSettingsPage(parent=self))
        self.pages.addWidget(AboutSettingsPage(parent=self))

        # ─── Logic and signals ─────────────────────────────────
        self.menu.currentRowChanged.connect(self.pages.setCurrentIndex)  # type: ignore
        self.menu.currentRowChanged.connect(self._on_page_changed)  # type: ignore
        self.menu.setCurrentRow(0)

        self._dirty_any = False
        self.btn_apply.setEnabled(False)

        self.btn_apply.clicked.connect(self._apply_current)  # type: ignore
        self.btn_close.clicked.connect(self.close)  # type: ignore

        # ─── Home page ───────────────────────────────
        self._on_page_changed(0)

        # ─── Centering and formatting──────────────────
        self.center()
        self._round_corners(10)
        THEME.themeChanged.connect(self._apply_theme)
        self._apply_theme()
        print("✅ Settings window initialized successfully")

    def center(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    # ─── Moving a window ────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def _current_page(self):
        return self.pages.currentWidget()

    def _on_page_changed(self, index: int):
        """We connect the active page's dirtyChanged
        and update the bottom buttons"""
        # Unsubscribe from the previous page
        try:
            if (
                hasattr(self, "_current_connected_page")
                and self._current_connected_page
            ):
                if hasattr(self._current_connected_page, "dirtyChanged"):
                    self._current_connected_page.dirtyChanged.disconnect(
                        self._on_dirty_changed
                    )
        except Exception:
            pass

        # New page
        page = self.pages.widget(index)
        self._current_connected_page = page

        # Connect the dirtyChanged signal, if it exists.
        if hasattr(page, "dirtyChanged"):
            page.dirtyChanged.connect(self._on_dirty_changed)  # type: ignore

        # Synchronize the bottom buttons with the current page
        self._sync_footer_by_page(page)

    def _sync_footer_by_page(self, page: QWidget | None = None):
        """Updates the state of the bottom buttons (Apply/Reset)"""
        if page is None:
            page = getattr(self, "_current_connected_page", None)
        dirty = False
        if hasattr(page, "is_dirty"):
            try:
                dirty = bool(page.is_dirty())  # type: ignore
            except Exception:
                dirty = False
        self.btn_apply.setEnabled(dirty)
        self._dirty_any = dirty

    def _on_dirty_changed(self, dirty: bool):
        """Reacting to the dirtyChanged signal from the current page"""
        self.btn_apply.setEnabled(dirty)
        self._dirty_any = dirty

    def _apply_current(self):
        page = getattr(self, "_current_connected_page", None)
        if not page:
            return
        ok = None
        if hasattr(page, "apply"):
            ok = page.apply()  # type: ignore
        elif hasattr(page, "apply_changes"):
            ok = page.apply_changes()  # type: ignore
        if ok:
            self._sync_footer_by_page(page)

    def closeEvent(self, e):
        if getattr(self, "_dirty_any", False):
            reply = MB.ask_yes_no(
                self.window(),
                "Unsaved changes",
                "Discard unsaved changes and close Settings?",
            )
            if not reply:
                e.ignore()
                return
        e.accept()

    def _round_corners(self, radius: int):
        """Software Window Rounding - Eliminates White Corners on Windows."""
        path = QPainterPath()
        rect = QRectF(self.rect())  # ← convert QRect → QRectF
        path.addRoundedRect(rect, radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def _apply_theme(self, *args):
        c = THEME.colors
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {c['bg_header']};
                color: {c['text_primary']};
            }}
            QPushButton {{
                background-color: transparent;
                color: {c['text_secondary']};
                border: 1px solid {c['border_color']};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
                border-color: {c['accent']};
            }}
        """
        )
