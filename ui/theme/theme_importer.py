import json
import re
from typing import Optional

from PyQt6.QtGui import QColor

from ui.theme.tokens import DARK_THEME

# ───────────────────────────────────────────────
# Helpers: HEX/RGBA processing
# ───────────────────────────────────────────────

_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")
_CHANNEL = r"\s*(\d{1,3}(?:\.\d+)?)\s*"
_RGB_RE = re.compile(
    rf"rgba?\({_CHANNEL},{_CHANNEL},{_CHANNEL}(?:,\s*(?:\d*\.)?\d+\s*)?\)"
)


def is_qt_color(value) -> bool:
    """Whether Qt can paint this value. The one test for every color that goes
    through QColor - None or a non-string there kills the launcher."""
    return isinstance(value, str) and QColor.isValidColorName(value)


def _rgba_to_hex(rgba: str) -> str:
    """
    Converts rgba(40,42,54,0.95) to #282a36
    Uses only RGB part.
    """
    match = re.findall(r"\d+(?:\.\d+)?", rgba)
    r, g, b = map(float, match[:3])
    return "#{:02X}{:02X}{:02X}".format(int(r), int(g), int(b))


def _normalize_color(value) -> Optional[str]:
    """
    "#rgb", "#rrggbb", "#rrggbbaa" (CSS order) and "rgb(...)" / "rgba(...)" -
    the forms ComfyUI palettes use, its own default palette is written in "#rgb" -
    become "#rrggbb" (alpha dropped). Any other color Qt knows ("white",
    "transparent") is kept as written. Anything else is None.
    """
    if not isinstance(value, str):
        return None
    value = value.strip()
    if _HEX_RE.fullmatch(value):
        digits = value[1:]
        if len(digits) == 3:
            digits = "".join(ch * 2 for ch in digits)
        return "#" + digits[:6]
    match = _RGB_RE.fullmatch(value)
    if match:
        if any(float(c) > 255 for c in match.groups()):
            return None
        return _rgba_to_hex(value)
    if is_qt_color(value):
        return value
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
            with open(path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ThemeImportError(
                f"The file is not valid JSON (line {e.lineno}, column {e.colno})."
            ) from e
        except (OSError, ValueError, RecursionError, MemoryError) as e:
            # ValueError covers a bad encoding and an int over Python's digit
            # limit; RecursionError a JSON nested ~1000 levels deep.
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
        # Only the required colors are refused when unreadable; any other one
        # is dropped to None, as before - the stylesheet just skips it.
        invalid = [
            f"{k} = {comfy_base[k]!r}"
            for k in REQUIRED_COMFY_KEYS
            if _normalize_color(comfy_base[k]) is None
        ]
        if invalid:
            raise ThemeImportError(
                "These required colors are not valid: " + ", ".join(invalid) + "."
            )

    def _map_to_tokens(self, comfy_base):
        result = {}

        for my_key, comfy_keys in THEME_MAP.items():
            value = None
            for ck in comfy_keys:
                if comfy_base.get(ck) is not None:
                    value = comfy_base[ck]
                    break

            value = _normalize_color(value)
            result[my_key] = value

        return result

    def _apply_fallbacks(self, t):
        # accent_hover (accent comes from the required drag-text)
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

        return t
