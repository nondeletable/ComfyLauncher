import os
import sys

from utils.python_resolver import resolve_interpreter


def is_valid_comfyui_build(path: str) -> bool:
    if not path or not os.path.isdir(path):
        return False
    return os.path.exists(os.path.join(path, "main.py"))


def detect_build_type(path: str) -> str:
    """
    Returns:
        'portable'   — the build brings its own Python: python_embeded/python_embedded
                       next to the ComfyUI folder on Windows, a venv in or next to
                       it elsewhere (there is no embedded Python outside Windows)
        'standalone' — no own Python found, the system one will be used
    """
    if sys.platform != "win32":
        return (
            "standalone" if resolve_interpreter(path).kind == "system" else "portable"
        )

    base_dir = os.path.dirname(path)
    has_python = os.path.isdir(
        os.path.join(base_dir, "python_embeded")
    ) or os.path.isdir(os.path.join(base_dir, "python_embedded"))
    return "portable" if has_python else "standalone"
