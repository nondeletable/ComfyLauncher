import os
import json
from ui.theme.tokens import THEMES
from utils.logger import log_event


class ThemeRegistry:
    """
    Stores custom themes, prevents duplicates,
    saves JSON copies, assigns unique names.
    """

    STORAGE_DIR = os.path.join("data", "themes")

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

                # avoid rewriting built-ins
                if name not in THEMES:
                    THEMES[name] = theme_dict

            except Exception as e:
                log_event(f"Failed to load theme {filename}: {e}")


REGISTRY = ThemeRegistry()
