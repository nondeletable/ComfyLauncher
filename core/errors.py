from dataclasses import dataclass
from enum import Enum, auto

from config import COMFYUI_PORT
from utils.i18n import I18N, t


class ErrorLevel(Enum):
    STARTUP = auto()
    DEGRADED = auto()


@dataclass(frozen=True)
class ErrorInfo:
    """What kind of failure a code is; its texts live in the dictionaries.

    Keys: ``error.<code in lowercase>.title`` / ``.message`` / ``.hint``.
    """

    level: ErrorLevel


ERRORS = {
    "COMFY_PATH_INVALID": ErrorInfo(ErrorLevel.STARTUP),
    "PROCESS_START_FAILED": ErrorInfo(ErrorLevel.STARTUP),
    "COMFY_START_TIMEOUT": ErrorInfo(ErrorLevel.STARTUP),
    "COMFY_PROCESS_EXITED": ErrorInfo(ErrorLevel.STARTUP),
    "COMFY_START_STOPPED": ErrorInfo(ErrorLevel.STARTUP),
    "PORT_ALREADY_IN_USE": ErrorInfo(ErrorLevel.STARTUP),
}


def _params(translate) -> dict:
    """Values the texts may name: the port and Settings pages by their menu
    labels, so a hint always matches the menu in any language."""

    def page(menu_key):
        return f"{translate('settings.window_title')} → {translate(menu_key)}"

    return {
        "port": COMFYUI_PORT,
        "builds": page("settings.menu.builds"),
        "startup": page("settings.menu.startup"),
        "logs": page("settings.menu.logs"),
    }


def error_texts(code: str, translate=t) -> tuple[str, str, str | None]:
    """(title, message, hint) of an error; ``I18N.english`` for logs/reports."""
    if code not in ERRORS:
        raise KeyError(code)
    key = f"error.{code.lower()}"
    params = _params(translate)
    hint = translate(f"{key}.hint", **params) if I18N.has(f"{key}.hint") else None
    return (
        translate(f"{key}.title", **params),
        translate(f"{key}.message", **params),
        hint,
    )
