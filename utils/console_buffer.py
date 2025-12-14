from typing import List


class ConsoleBuffer:
    """In-memory buffer for ComfyUI console output."""

    _lines: List[str] = []

    @classmethod
    def add(cls, text: str) -> None:
        if not text:
            return
        cls._lines.append(text)

        # Let's limit the volume so it doesn't grow endlessly
        if len(cls._lines) > 10000:
            cls._lines = cls._lines[-8000:]

    @classmethod
    def clear(cls) -> None:
        cls._lines = []

    @classmethod
    def get_all(cls) -> str:
        return "".join(cls._lines) if cls._lines else ""
