from dataclasses import dataclass
from enum import Enum, auto


class ErrorLevel(Enum):
    STARTUP = auto()
    DEGRADED = auto()


@dataclass(frozen=True)
class ErrorInfo:
    level: ErrorLevel
    title: str
    message: str
    hint: str | None = None


ERRORS = {
    "COMFY_PATH_INVALID": ErrorInfo(
        level=ErrorLevel.STARTUP,
        title="Incorrect path to ComfyUI",
        message="The specified directory does not contain ComfyUI or is corrupted.",
        hint="In the application header, find Settings -> Paths, select the correct path to the folder with ComfyUI and try again.",
    ),
    "PROCESS_START_FAILED": ErrorInfo(
        level=ErrorLevel.STARTUP,
        title="Failed to start ComfyUI",
        message="The ComfyUI process did not start.",
        hint="In the app header, go to Settings -> Application Logs and check for any issues. Also, check for proper installation.",
    ),
    "COMFY_START_TIMEOUT": ErrorInfo(
        level=ErrorLevel.STARTUP,
        title="ComfyUI is not responding",
        message="The server did not become available within a reasonable time.",
        hint="Check that the path to the ComfyUI folder is correct. Try restarting the app or check the Settings -> Application Logs section in the app header.",
    ),
    "PORT_ALREADY_IN_USE": ErrorInfo(
        level=ErrorLevel.STARTUP,
        title="The port is occupied",
        message="The ComfyUI port (8088) is already in use by another process.",
        hint="Close the conflicting application or change the port.",
    ),
}
