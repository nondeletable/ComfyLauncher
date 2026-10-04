import os
import json
from ui.theme.theme_importer import is_qt_color
from ui.theme.tokens import DARK_THEME, THEMES
from utils.logger import log_event
from config import THEMES_DIR

# Colors painted through QColor (icons, message box badges). None there is a
# TypeError inside a Qt slot, and PyQt6 kills the whole launcher on that.
_PAINTED_KEYS = ("icon_color_window", "accent", "error", "warning")


def theme_problems(theme) -> list[str]:
    """
    Why a theme can't be used safely; empty when it can.

    Every token but "warning" is read as colors[key] somewhere, so it must be
    present. None is tolerated where the value only lands in a stylesheet (Qt
    drops that declaration, and themes imported from comfyui-themes.com have
    a few), but the painted colors must be real - "warning" too when present,
    since colors.get("warning", default) hands back its None.
    """
    if not isinstance(theme, dict):
        return ["the theme is not a JSON object"]
    problems = [
        f'"{key}" is missing'
        for key in DARK_THEME
        if key != "warning" and key not in theme
    ]
    for key in _PAINTED_KEYS:
        value = theme.get(key)
        if key in theme and not is_qt_color(value):
            problems.append(f'"{key}" is not a color: {value!r}')
    return problems


class ThemeRegistry:
    """
    Stores custom themes, prevents duplicates,
    saves JSON copies, assigns unique names.
    """

    STORAGE_DIR = THEMES_DIR

    def __init__(self):
        os.makedirs(self.STORAGE_DIR, exist_ok=True)

        self._load_existing()

    # ────────────────────────────────────────────
    def add_custom(self, name: str, theme_dict: dict) -> str:
        """
        Registers a new custom theme.
        Ensures uniqueness: if name exists, adds suffix (-1, -2).
        Saves JSON file to data/themes/.
        Returns final theme name.
        """

        original = name
        counter = 1

        while name in THEMES:
            name = f"{original}-{counter}"
            counter += 1

        # Save .json
        filepath = os.path.join(self.STORAGE_DIR, f"{name}.json")
        with open(filepath, "w", encoding="utf8") as f:
            json.dump(theme_dict, f, indent=2, ensure_ascii=False)

        THEMES[name] = theme_dict
        return name

    # ────────────────────────────────────────────
    def theme_exists(self, theme_dict: dict) -> str | None:
        """
        Checks if an identical theme already exists.
        Returns its name or None.
        """
        for name, t in THEMES.items():
            if t == theme_dict:
                return name
        return None

    def _load_existing(self):
        """Loads all previously saved custom themes from data/themes/"""
        for filename in os.listdir(self.STORAGE_DIR):
            if not filename.endswith(".json"):
                continue

            path = os.path.join(self.STORAGE_DIR, filename)
            try:
                with open(path, "r", encoding="utf8") as f:
                    theme_dict = json.load(f)

                name = os.path.splitext(filename)[0]

                # A theme that would crash the app is left out, so it can be
                # neither picked nor restored as the last theme at startup.
                problems = theme_problems(theme_dict)
                if problems:
                    log_event(
                        f"Skipping broken theme {filename}: {'; '.join(problems)}"
                    )
                    continue

                # avoid rewriting built-ins
                if name not in THEMES:
                    THEMES[name] = theme_dict

            except Exception as e:
                log_event(f"Failed to load theme {filename}: {e}")


REGISTRY = ThemeRegistry()
