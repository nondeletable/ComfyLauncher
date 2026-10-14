"""detect_build_type: a build with its own Python is 'portable', else 'standalone'.

Windows looks for the python_embeded sibling; elsewhere there is no embedded
Python, so a venv in or next to the build counts instead.
"""

import os
import sys

from utils import build_validation as bv


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()
    return path


def _build(tmp_path):
    comfy = tmp_path / "ComfyUI"
    comfy.mkdir()
    return comfy


def test_windows_embedded_is_portable(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    comfy = _build(tmp_path)
    (tmp_path / "python_embeded").mkdir()

    assert bv.detect_build_type(str(comfy)) == "portable"


def test_windows_without_embedded_is_standalone(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    comfy = _build(tmp_path)

    assert bv.detect_build_type(str(comfy)) == "standalone"


def test_linux_sibling_venv_is_portable(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    comfy = _build(tmp_path)
    _touch(str(tmp_path / "venv" / "bin" / "python"))

    assert bv.detect_build_type(str(comfy)) == "portable"


def test_linux_venv_inside_build_is_portable(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    comfy = _build(tmp_path)
    _touch(str(comfy / ".venv" / "bin" / "python"))

    assert bv.detect_build_type(str(comfy)) == "portable"


def test_linux_without_venv_is_standalone(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    comfy = _build(tmp_path)

    assert bv.detect_build_type(str(comfy)) == "standalone"
