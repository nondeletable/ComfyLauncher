import re
from typing import List


# ComfyUI colours its log levels, so the raw pipe carries escape sequences
# (``\x1b[32m[INFO]\x1b[0m``). A terminal renders them as colour; QPlainTextEdit
# renders them as litter around otherwise readable text, so they are dropped on
# the way in. Covers CSI (colour, cursor moves), OSC (window title, hyperlinks)
# and the two-character escapes.
_ANSI_RE = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\)|[@-Z\\-_])"
)


def strip_ansi(text: str) -> str:
    """Remove terminal escape sequences, leaving the text itself untouched."""
    return _ANSI_RE.sub("", text)


class ConsoleBuffer:
    """In-memory buffer for ComfyUI console output."""

    _lines: List[str] = []

    @classmethod
    def add(cls, text: str) -> None:
        if not text:
            return
        cls._lines.append(strip_ansi(text))

        # Let's limit the volume so it doesn't grow endlessly
        if len(cls._lines) > 10000:
            cls._lines = cls._lines[-8000:]

    @classmethod
    def clear(cls) -> None:
        cls._lines = []

    @classmethod
    def get_all(cls) -> str:
        return "".join(cls._lines) if cls._lines else ""
