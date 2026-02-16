import os


def is_valid_comfyui_build(path: str) -> bool:
    if not path or not os.path.isdir(path):
        return False
    return os.path.exists(os.path.join(path, "main.py"))
