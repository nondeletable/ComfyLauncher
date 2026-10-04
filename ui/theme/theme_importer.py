import json
import re
from typing import Optional

from ui.theme.tokens import DARK_THEME

# ───────────────────────────────────────────────
# Helpers: HEX/RGBA processing
# ───────────────────────────────────────────────

_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")


def _rgba_to_hex(rgba: str) -> str:
    """
    Converts rgba(40,42,54,0.95) to #282a36
    Uses only RGB part.
    """
    match = re.findall(r"\d+(?:\.\d+)?", rgba)
    if len(match) < 3:
        return "#000000"
    r, g, b = map(float, match[:3])
    return "#{:02X}{:02X}{:02X}".format(int(r), int(g), int(b))


def _normalize_color(value) -> Optional[str]:
    """
    Accepts "#rgb", "#rrggbb", "#rrggbbaa" (CSS order) or "rgb(...)" / "rgba(...)",
    the forms ComfyUI palettes use - its own default palette is written in "#rgb".
    Returns normalized "#rrggbb" (alpha dropped) or None if value is invalid.
    """
    if not isinstance(value, str):
        return None
    value = value.strip()
    if _HEX_RE.fullmatch(value):
        digits = value[1:]
        if len(digits) == 3:
            digits = "".join(ch * 2 for ch in digits)
        return "#" + digits[:6]
    if value.startswith("rgb"):
        channels = re.findall(r"\d+(?:\.\d+)?", value)
        if len(channels) < 3 or any(float(c) > 255 for c in channels[:3]):
            return None
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

# Without these a file is not a usable theme: background, text, and the color
# every icon is painted with (the painting crashes on a missing one).
REQUIRED_COMFY_KEYS = ("bg-color", "fg-color", "drag-text")


class ThemeImportError(ValueError):
    """The file can't be used as a theme; the message says why, for the user."""


# ───────────────────────────────────────────────
# Theme Importer
# ───────────────────────────────────────────────


class ThemeImporter:
    """
    Converts a ComfyUI theme JSON into a Launcher theme dict.
    """

    def load(self, path: str) -> dict:
        """Raises ThemeImportError when the file is not a usable ComfyUI theme."""
        data = self._load_json(path)
        comfy = self._extract_comfy_base(data)
        self._validate(comfy)
        mapped = self._map_to_tokens(comfy)
        final = self._apply_fallbacks(mapped)
        return final

    # ───────────────────────────────────────────────

    def _load_json(self, path):
        try:
            with open(path, "r", encoding="utf8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ThemeImportError(
                f"The file is not valid JSON (line {e.lineno}, column {e.colno})."
            ) from e
        except (OSError, UnicodeDecodeError) as e:
            raise ThemeImportError(f"The file could not be read: {e}") from e

    def _extract_comfy_base(self, data):
        colors = data.get("colors") if isinstance(data, dict) else None
        comfy_base = colors.get("comfy_base") if isinstance(colors, dict) else None
        return comfy_base if isinstance(comfy_base, dict) else {}

    def _validate(self, comfy_base):
        if not comfy_base:
            raise ThemeImportError(
                'The file has no "colors.comfy_base" section - '
                "it does not look like a ComfyUI theme."
            )
        missing = [k for k in REQUIRED_COMFY_KEYS if comfy_base.get(k) is None]
        if missing:
            raise ThemeImportError(
                "Required colors are missing: " + ", ".join(missing) + "."
            )
        used = {ck for keys in THEME_MAP.values() for ck in keys}
        invalid = [
            f"{k} = {comfy_base[k]!r}"
            for k in sorted(used)
            if k in comfy_base and _normalize_color(comfy_base[k]) is None
        ]
        if invalid:
            raise ThemeImportError(
                "These colors are not valid (expected #hex or rgb()/rgba()): "
                + ", ".join(invalid)
                + "."
            )

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

        # error paints the error message box badge; None there kills the app
        if not t.get("error"):
            t["error"] = DARK_THEME["error"]

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
