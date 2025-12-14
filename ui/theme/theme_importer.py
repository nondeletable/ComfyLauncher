import json
import re
from typing import Optional

from ui.theme.tokens import DARK_THEME


# ───────────────────────────────────────────────
# Helpers: HEX/RGBA processing
# ───────────────────────────────────────────────


def _rgba_to_hex(rgba: str) -> str:
    """
    Converts rgba(40,42,54,0.95) to #282a36
    Uses only RGB part.
    """
    match = re.findall(r"([\d.]+)", rgba)
    if len(match) < 3:
        return "#000000"
    r, g, b = map(float, match[:3])
    return "#{:02X}{:02X}{:02X}".format(int(r), int(g), int(b))


def _normalize_color(value: str) -> Optional[str]:
    """
    Accepts "#hex" or "rgba(...)".
    Returns normalized "#hex" or None if value is invalid.
    """
    if not value:
        return None
    value = value.strip()
    if value.startswith("#"):
        return value
    if value.startswith("rgba"):
        return _rgba_to_hex(value)
    return None


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _lighten(color: str, percent: int = 15) -> str:
    """Lightens HEX color by percent."""
    if not color or not color.startswith("#"):
        return color
    rgb = _hex_to_rgb(color)
    new = tuple(min(255, int(c + (255 - c) * (percent / 100))) for c in rgb)
    return _rgb_to_hex(new)


def _inverse_bw(color: str) -> str:
    """Black/white inverse by luminance."""
    if not color or not color.startswith("#"):
        return "#000000"
    r, g, b = _hex_to_rgb(color)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#000000" if luminance > 0.5 else "#FFFFFF"


# ───────────────────────────────────────────────
# Mapping from ComfyUI comfy_base → Launcher Tokens
# ───────────────────────────────────────────────

THEME_MAP = {
    "bg_header": ["bg-color"],
    "bg_menu": ["comfy-menu-secondary-bg", "comfy-menu-bg"],
    "bg_hover": ["comfy-menu-hover-bg"],
    "bg_input": ["comfy-input-bg"],
    "text_primary": ["fg-color"],
    "text_secondary": ["descrip-text"],
    "app_title_color": ["fg-color"],
    "icon_color_window": ["drag-text"],
    "border_color": ["border-color"],
    "accent": ["drag-text"],
    "error": ["error-text"],
    "popup_bg": ["content-bg"],
    "popup_text": ["content-fg"],
    "popup_border": ["border-color"],
}


# ───────────────────────────────────────────────
# Theme Importer
# ───────────────────────────────────────────────


class ThemeImporter:
    """
    Converts a ComfyUI theme JSON into a Launcher theme dict.
    """

    def load(self, path: str) -> dict:
        data = self._load_json(path)
        comfy = self._extract_comfy_base(data)
        mapped = self._map_to_tokens(comfy)
        final = self._apply_fallbacks(mapped)
        return final

    # ───────────────────────────────────────────────

    def _load_json(self, path):
        with open(path, "r", encoding="utf8") as f:
            return json.load(f)

    def _extract_comfy_base(self, data):
        return data.get("colors", {}).get("comfy_base", {})

    def _map_to_tokens(self, comfy_base):
        result = {}

        for my_key, comfy_keys in THEME_MAP.items():
            value = None
            for ck in comfy_keys:
                if ck in comfy_base:
                    value = comfy_base[ck]
                    break

            value = _normalize_color(value)
            result[my_key] = value

        return result

    def _apply_fallbacks(self, t):
        # accent_hover
        if not t.get("accent"):
            t["accent"] = DARK_THEME["accent"]

        t["accent_hover"] = _lighten(t["accent"], 15)

        # text_inverse
        t["text_inverse"] = _inverse_bw(t["text_primary"])

        # success — currently default (no direct ComfyUI analog)
        t["success"] = DARK_THEME["success"]

        # Ensure popup_border exists
        if not t.get("popup_border"):
            t["popup_border"] = t.get("border_color", "#444444")

        # Final normalization
        for k, v in t.items():
            if isinstance(v, str) and v.startswith("rgba"):
                t[k] = _normalize_color(v)

        return t
