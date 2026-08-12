import os
from utils.platform import IS_WINDOWS, has_venv


def is_valid_comfyui_build(path: str) -> bool:
    if not path or not os.path.isdir(path):
        return False
    return os.path.exists(os.path.join(path, "main.py"))


def detect_build_type(path: str) -> str:
    """
    Returns:
        'portable'   — python_embeded/python_embedded found (Windows) or venv found (macOS)
        'standalone' — no embedded/venv python found
    """
    base_dir = os.path.dirname(path)

    if IS_WINDOWS:
        has_python = os.path.isdir(
            os.path.join(base_dir, "python_embeded")
        ) or os.path.isdir(os.path.join(base_dir, "python_embedded"))
    else:
        has_python = has_venv(path)

    return "portable" if has_python else "standalone"
