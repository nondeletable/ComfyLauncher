"""Tests for cross-platform interpreter resolution (Linux port, Stage 2).

Covers the autodetect order per platform (Windows: embedded → system; other:
venv → system) and the per-kind launch environment. Platform is monkeypatched
so both branches run on any host; fake interpreter files stand in for a real
embedded/venv layout.
"""

import os
import sys

from utils import python_resolver as pr


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("")
    return path


# ── Windows autodetect: embedded → system ─────────────────────────────


def test_windows_finds_embedded(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    comfy = tmp_path / "ComfyUI"
    comfy.mkdir()
    exe = _touch(str(tmp_path / "python_embeded" / "python.exe"))

    interp = pr.resolve_interpreter(str(comfy))

    assert interp.kind == "embedded"
    assert interp.exe == exe
    assert interp.home == str(tmp_path / "python_embeded")


def test_windows_embedded_second_spelling(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    comfy = tmp_path / "ComfyUI"
    comfy.mkdir()
    exe = _touch(str(tmp_path / "python_embedded" / "python.exe"))

    interp = pr.resolve_interpreter(str(comfy))

    assert interp.kind == "embedded"
    assert interp.exe == exe


def test_windows_no_embedded_falls_to_system(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    comfy = tmp_path / "ComfyUI"
    comfy.mkdir()

    interp = pr.resolve_interpreter(str(comfy))

    assert interp.kind == "system"
    assert interp.exe == "python"
    assert interp.home is None


def test_windows_ignores_venv(tmp_path, monkeypatch):
    # A venv next to a Windows build must NOT be picked silently (product rule).
    monkeypatch.setattr(sys, "platform", "win32")
    comfy = tmp_path / "ComfyUI"
    comfy.mkdir()
    _touch(str(comfy / ".venv" / "Scripts" / "python.exe"))

    interp = pr.resolve_interpreter(str(comfy))

    assert interp.kind == "system"


# ── Linux autodetect: venv → system ──────────────────────────────────


def test_linux_finds_venv_inside_build(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    comfy = tmp_path / "ComfyUI"
    comfy.mkdir()
    exe = _touch(str(comfy / ".venv" / "bin" / "python"))

    interp = pr.resolve_interpreter(str(comfy))

    assert interp.kind == "venv"
    assert interp.exe == exe
    assert interp.home is None


def test_linux_finds_sibling_venv(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    comfy = tmp_path / "ComfyUI"
    comfy.mkdir()
    exe = _touch(str(tmp_path / "venv" / "bin" / "python"))

    interp = pr.resolve_interpreter(str(comfy))

    assert interp.kind == "venv"
    assert interp.exe == exe


def test_linux_no_venv_falls_to_system(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(pr.shutil, "which", lambda name: "/usr/bin/python3")
    comfy = tmp_path / "ComfyUI"
    comfy.mkdir()

    interp = pr.resolve_interpreter(str(comfy))

    assert interp.kind == "system"
    assert interp.exe == "/usr/bin/python3"


# ── build_env: only embedded gets PYTHONHOME/PYTHONPATH/PATH ──────────


def test_build_env_embedded_sets_home_and_path():
    interp = pr.Interpreter(
        exe="C:/b/python_embeded/python.exe",
        kind="embedded",
        home="C:/b/python_embeded",
    )
    env = pr.build_env(interp, "C:/b/ComfyUI", base_env={"PATH": "X"})

    assert env["PYTHONHOME"] == "C:/b/python_embeded"
    assert env["PYTHONPATH"] == "C:/b/ComfyUI"
    assert env["PATH"] == "C:/b/python_embeded" + os.pathsep + "X"
    assert env["PYTHONUNBUFFERED"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"


def test_build_env_venv_leaves_home_unset():
    interp = pr.Interpreter(exe="/b/.venv/bin/python", kind="venv")
    env = pr.build_env(interp, "/b/ComfyUI", base_env={"PATH": "X"})

    assert "PYTHONHOME" not in env
    assert "PYTHONPATH" not in env
    assert env["PATH"] == "X"  # untouched
    assert env["PYTHONUNBUFFERED"] == "1"


def test_build_env_system_leaves_home_unset():
    interp = pr.Interpreter(exe="python3", kind="system")
    env = pr.build_env(interp, "/b/ComfyUI", base_env={})

    assert "PYTHONHOME" not in env
    assert env["PYTHONIOENCODING"] == "utf-8"
