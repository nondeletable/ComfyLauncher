"""Tests for cross-platform ComfyUI process launch (Linux port, Stage 3).

Verifies the platform-specific console handling: Windows external console
(``cmd.exe /k`` + ``CREATE_NEW_CONSOLE``, not piped), Windows internal console
(``CREATE_NO_WINDOW``, piped), and posix (headless, ``start_new_session``,
piped, external request ignored). ``sys.platform`` and ``subprocess.Popen`` are
monkeypatched so every branch runs on any host without spawning a process; the
Windows-only creation flags are injected too, so the win32 branch is testable on
Linux CI as well.
"""

import subprocess
import sys

from utils import process_launch as pl

ARGS = ["python", "-s", "-u", "main.py"]


class _FakePopen:
    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.pid = 1234


def _install_fake_popen(monkeypatch):
    def fake(args, **kwargs):
        return _FakePopen(args, **kwargs)

    monkeypatch.setattr(pl.subprocess, "Popen", fake)
    # These flags exist only on Windows; provide them so the win32 branch can be
    # exercised on any host.
    monkeypatch.setattr(pl.subprocess, "CREATE_NEW_CONSOLE", 0x10, raising=False)
    monkeypatch.setattr(pl.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)


# ── external_console_supported ────────────────────────────────────────


def test_external_console_supported_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert pl.external_console_supported() is True


def test_external_console_supported_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert pl.external_console_supported() is False


# ── Windows: external console ─────────────────────────────────────────


def test_windows_external_console(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    _install_fake_popen(monkeypatch)

    proc, piped = pl.spawn_comfy(ARGS, "cwd", {"A": "1"}, external_console=True)

    assert piped is False
    assert proc.args[:2] == ["cmd.exe", "/k"]
    assert proc.args[2:] == ARGS
    assert proc.kwargs["creationflags"] == pl.subprocess.CREATE_NEW_CONSOLE
    assert "stdout" not in proc.kwargs  # output goes to the cmd.exe window


# ── Windows: internal (hidden) console ────────────────────────────────


def test_windows_internal_console(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    _install_fake_popen(monkeypatch)

    proc, piped = pl.spawn_comfy(ARGS, "cwd", {}, external_console=False)

    assert piped is True
    assert proc.args == ARGS
    assert proc.kwargs["creationflags"] == pl.subprocess.CREATE_NO_WINDOW
    assert proc.kwargs["stdout"] == subprocess.PIPE
    assert proc.kwargs["stderr"] == subprocess.STDOUT
    assert proc.kwargs["encoding"] == "utf-8"
    assert "start_new_session" not in proc.kwargs


# ── posix: always headless + piped ────────────────────────────────────


def test_posix_ignores_external_console(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    _install_fake_popen(monkeypatch)

    # external_console=True must still yield a headless, piped launch on posix.
    proc, piped = pl.spawn_comfy(ARGS, "cwd", {}, external_console=True)

    assert piped is True
    assert proc.args == ARGS
    assert "creationflags" not in proc.kwargs
    assert proc.kwargs["start_new_session"] is True
    assert proc.kwargs["stdout"] == subprocess.PIPE
    assert proc.kwargs["stderr"] == subprocess.STDOUT


def test_posix_internal_console(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    _install_fake_popen(monkeypatch)

    proc, piped = pl.spawn_comfy(ARGS, "cwd", {}, external_console=False)

    assert piped is True
    assert proc.kwargs["start_new_session"] is True
    assert "creationflags" not in proc.kwargs
