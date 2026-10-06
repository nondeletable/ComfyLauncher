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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from ui.settings.page_build import BuildSettingsPage
from ui.settings.page_behavior import BehaviorSettingsPage
from ui.settings.page_colortheme import ColorThemesPage
from ui.settings.page_about import AboutSettingsPage
from ui.settings.page_logs import LogsSettingsPage
from ui.settings.page_startapp import StartAppSettingsPage
from ui.theme.manager import THEME, safe_repaint
from ui.dialogs.messagebox import MessageBox as MB
from config import ICON_PATH
from utils.logger import log_event


# ──────────────────────────────────────────────
class SettingsWindow(QWidget):
    """The launcher settings window is a single container without visual breaks."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # ─── Basic window parameters ─────────────────────────
        self.setWindowTitle("Settings")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setFixedSize(1230, 730)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.drag_position = None

        # ─── Main frame ───────────────────────────────────
        main_frame = QFrame(self)
        main_frame.setObjectName("settings_main_frame")
        main_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
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
                "Builds",
                "Startup",
                "Exit Options",
                "Color Themes",
                "Launcher Logs",
                "About",
            ]
        )
        self.menu.setFixedWidth(200)

        # ─── Right content panel ───────────────────────────
        self.pages = QStackedWidget()

        # ─── Bottom button bar ─────────────────────────────
        self.footer = QFrame()
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(20, 10, 20, 10)
        footer_layout.setSpacing(12)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.btn_apply = QPushButton("Apply")
        self.btn_close = QPushButton("Close")

        for btn in (self.btn_apply, self.btn_close):
            btn.setFixedSize(110, 34)
            footer_layout.addWidget(btn)

        # ─── Adding menus and pages to the body ─────────────────
        body_layout.addWidget(self.menu)
        body_layout.addWidget(self.pages)

        # ─── Add everything to the main layout ──────────────────
        main_layout.addLayout(body_layout, stretch=1)
        main_layout.addWidget(self.footer)

        # ─── Adding a main frame to the window ───────────────────
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(15, 15, 15, 15)
        outer_layout.addWidget(main_frame)
        self.setLayout(outer_layout)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 180))
        main_frame.setGraphicsEffect(shadow)

        # ─── Adding pages ───────────────────────────────
        # Each page is built on its first visit, an empty placeholder holds its
        # slot until then. Built all at once, Color Themes, Launcher Logs and
        # About alone added a few hundred ms to every opening of the window.
        self._page_classes = [
            BuildSettingsPage,
            StartAppSettingsPage,
            BehaviorSettingsPage,
            ColorThemesPage,
            LogsSettingsPage,
            AboutSettingsPage,
        ]
        self._built_pages = set()
        for _ in self._page_classes:
            self.pages.addWidget(QWidget())

        # ─── Logic and signals ─────────────────────────────────
        self.menu.currentRowChanged.connect(self._show_page)  # type: ignore
        self.menu.currentRowChanged.connect(self._sync_footer)  # type: ignore
        self.menu.setCurrentRow(0)

        self.btn_apply.clicked.connect(self._apply_current)  # type: ignore
        self.btn_close.clicked.connect(self.close)  # type: ignore

        # ─── Formatting ──────────────────
        THEME.themeChanged.connect(self._apply_theme)
        self._apply_theme()
        print("✅ Settings window initialized successfully")

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

    def _show_page(self, index: int):
        if index not in self._built_pages:
            page = self._page_classes[index](parent=self)
            self._built_pages.add(index)
            placeholder = self.pages.widget(index)
            self.pages.insertWidget(index, page)
            self.pages.removeWidget(placeholder)
            placeholder.deleteLater()
            # Every built page keeps reporting, not just the visible one: its
            # edits survive a switch to another page and must reach closeEvent.
            if hasattr(page, "dirtyChanged"):
                page.dirtyChanged.connect(self._sync_footer)  # type: ignore
        self.pages.setCurrentIndex(index)

    def _is_dirty(self, page: QWidget) -> bool:
        # An exception here would escape closeEvent, and PyQt6 aborts on that.
        try:
            return hasattr(page, "is_dirty") and bool(page.is_dirty())  # type: ignore
        except Exception as e:
            log_event(f"Settings: is_dirty failed on {type(page).__name__}: {e}")
            return False

    def _dirty_pages(self) -> list[int]:
        """Built pages holding unsaved changes; a page never visited has none."""
        return [
            i for i in sorted(self._built_pages) if self._is_dirty(self.pages.widget(i))
        ]

    def _sync_footer(self, *args):
        """Apply is for the page on screen, so it follows that page only."""
        self.btn_apply.setEnabled(self._is_dirty(self._current_page()))

    def _apply_page(self, page: QWidget) -> bool:
        if hasattr(page, "apply"):
            return bool(page.apply())  # type: ignore
        if hasattr(page, "apply_changes"):
            return bool(page.apply_changes())  # type: ignore
        return False

    def _apply_current(self):
        if self._apply_page(self._current_page()):
            self._sync_footer()

    def closeEvent(self, e):
        dirty = self._dirty_pages()
        if dirty:
            names = ", ".join(self.menu.item(i).text() for i in dirty)
            answer = MB.choose(
                self.window(),
                "Unsaved changes",
                f"Unsaved changes on: {names}.\n\nApply them before closing Settings?",
                "ask_yes_no",
                [("Apply", "apply"), ("Discard", "discard"), ("Cancel", "cancel")],
            )
            if answer == "apply":
                # Every page is applied even if one fails; a failed page has
                # shown its own warning and stays dirty, so Settings stays open.
                results = [self._apply_page(self.pages.widget(i)) for i in dirty]
                self._sync_footer()
                if not all(results):
                    e.ignore()
                    return
            elif answer != "discard":
                e.ignore()
                return
        e.accept()

    @safe_repaint
    def _apply_theme(self, *args):
        c = THEME.colors
        self.setStyleSheet("background: transparent;")
        self.findChild(QFrame, "settings_main_frame").setStyleSheet(
            f"""
            QFrame {{
                background-color: {c['bg_header']};
                color: {c['text_primary']};
                border-radius: 10px;
            }}
            QFrame#settings_main_frame {{
                border: none;
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
        self.menu.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {c['bg_menu']};
                color: {c['text_secondary']};
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
                background-color: {c['bg_hover']};
                color: {c['text_primary']};
            }}
            QListWidget::item:selected {{
                background-color: {c['accent']};
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
        self.pages.setStyleSheet(
            f"""
            QStackedWidget {{
                background-color: {c["bg_header"]};
                border-top-right-radius: 10px;
                border-top-left-radius: 0px;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: 0px;
            }}
            QLabel {{
                color: {c['text_primary']};
                font-size: 16px;
                margin: 10px;
            }}
        """
        )
        self.footer.setStyleSheet(
            f"""
            QFrame {{
                background-color: {c['bg_menu']};
                border-bottom-left-radius: 10px;
                border-top-left-radius: 0px;
                border-bottom-right-radius: 10px;
                border-top-right-radius: 0px;
            }}
        """
        )
        # Themes imported before the token existed keep the old fixed grey.
        disabled = c.get("text_disabled", "#555555")
        for btn in (self.btn_apply, self.btn_close):
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: {c['text_secondary']};
                    border: 1px solid {c['border_color']};
                    border-radius: 6px;
                    transition: all 0.2s ease-in-out;
                }}
                QPushButton:hover {{
                    background-color: {c['accent']};
                    color: #fff;
                    border-color: {c['accent']};
                }}
                QPushButton:disabled {{
                    color: {disabled};
                    border: 1px solid {disabled};
                }}
            """
            )
