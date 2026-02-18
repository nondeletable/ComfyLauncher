import json
import os
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from ui.theme.tokens import THEMES
from ui.theme.theme_registry import REGISTRY
from config import USER_CONFIG_PATH as CONFIG_PATH
from utils.logger import log_event

_ = REGISTRY


class ThemeManager(QObject):
    """Theme Manager. Manages the active color scheme of the application."""

    themeChanged = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._themes = THEMES
        self._active_name = self._load_last_theme()
        self._colors = self._themes.get(self._active_name, self._themes["dark"])

    # ─── Properties ──────────────────────────────────────
    @property
    def name(self) -> str:
        """Name of the active theme."""
        return self._active_name

    @property
    def colors(self) -> dict:
        """Active theme colors."""
        return self._colors

    # ─── The main application of the theme ────────────────
    def apply(self):
        """Applies a theme to QApplication via QSS."""
        app = QApplication.instance()
        if not app:
            return

        t = self._colors
        qss = f"""
        QWidget {{
            background-color: {t['bg_header']};
            color: {t['text_primary']};
            border: none;
        }}
        QFrame {{
            background-color: {t['bg_header']};
        }}

        QListWidget {{
            background-color: {t['bg_menu']};
            color: {t['text_secondary']};
            border: none;
        }}
        QListWidget::item:selected {{
            background-color: {t['accent']};
            color: {t['text_inverse']};
        }}
        QListWidget::item:hover {{
            background-color: {t['bg_hover']};
        }}

        QStackedWidget {{
            background-color: {t['bg_header']};
        }}
        QPushButton {{
            background: transparent;
            border: 1px solid {t['border_color']};
            color: {t['icon_color_window']};
            border-radius: 6px;
            padding: 5px 10px;
        }}
        QPushButton:hover {{
            background-color: {t['accent']};
            color: {t['text_inverse']};
            border-color: {t['accent']};
        }}
        QLineEdit, QPlainTextEdit {{
            background-color: {t['bg_input']};
            color: {t['text_primary']};
            border: 1px solid {t['border_color']};
            border-radius: 4px;
            padding: 4px 6px;
        }}
        QLabel {{
            color: {t['text_primary']};
            background: transparent;
        }}
        QDialog {{
            background-color: {t['popup_bg']};
            color: {t['popup_text']};
            border: 1px solid {t['popup_border']};
            border-radius: 10px;
            padding: 10px;
        }}
        QDialog QPushButton {{
            background-color: transparent;
            color: {t['text_primary']};
            border: 1px solid {t['border_color']};
            border-radius: 6px;
            padding: 4px 10px;
        }}
        QDialog QPushButton:hover {{
            background-color: {t['accent']};
            color: {t['text_inverse']};
            border-color: {t['accent']};
        }}
        """
        app.setStyleSheet(qss)
        self.themeChanged.emit(t)

    # ─── Switching themes ──────────────────────────────
    def switch(self, name: str):
        """Changes the active theme and applies it."""
        if name not in self._themes:
            log_event(f"⚠️ Theme '{name}' not found. Using current: {self._active_name}")
            return

        if name == self._active_name:
            return

        self._active_name = name
        self._colors = self._themes[name]
        self._save_last_theme()
        self.apply()
        log_event(f"🎨 Theme switched to: {name}")

        # 🔹 Force refresh of all widgets
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                try:
                    widget.setStyleSheet(widget.styleSheet())
                except Exception:
                    pass

    # ─── Saving and loading ─────────────────────────
    def _save_last_theme(self):
        """Saves the selected theme to user_config.json."""
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        data["theme"] = self._active_name
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_last_theme(self) -> str:
        """Loads the theme from user_config.json."""
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            theme = data.get("theme", "dark")
            return theme if theme in self._themes else "dark"
        except Exception:
            return "dark"


# Singleton
THEME = ThemeManager()
