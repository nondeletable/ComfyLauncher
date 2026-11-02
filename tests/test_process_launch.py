"""Tests for cross-platform ComfyUI process launch (Linux port, Stage 3).

Verifies the platform-specific console handling: Windows external console
(``cmd.exe /k`` + ``CREATE_NEW_CONSOLE``, not piped), Windows internal console
(``CREATE_NO_WINDOW``, piped), and posix (headless, ``start_new_session``,
output appended to ``COMFY_LOG_FILE``, external request ignored). ``sys.platform``
and ``subprocess.Popen`` are monkeypatched so every branch runs on any host
without spawning a process; the Windows-only creation flags are injected too,
so the win32 branch is testable on Linux CI as well.

The posix branch is also where the log file matters for lifetimes: the launcher
used to hold a pipe's read end, which killed a ComfyUI left running by the exit
dialog's "No" the next time it wrote to stdout. The log file is redirected to
``tmp_path`` so the suite stays out of the developer's real app directory.
"""

import subprocess
import sys

import pytest

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


@pytest.fixture
def isolated_log(monkeypatch, tmp_path):
    """Point COMFY_LOG_FILE at tmp_path; returns the path as a string."""
    path = tmp_path / "comfyui.log"
    monkeypatch.setattr(pl, "COMFY_LOG_FILE", str(path))
    return str(path)


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

    launch = pl.spawn_comfy(ARGS, "cwd", {"A": "1"}, external_console=True)

    assert launch.piped is False
    assert launch.log_offset is None
    assert launch.proc.args[:2] == ["cmd.exe", "/k"]
    assert launch.proc.args[2:] == ARGS
    assert launch.proc.kwargs["creationflags"] == pl.subprocess.CREATE_NEW_CONSOLE
    assert "stdout" not in launch.proc.kwargs  # output goes to the cmd.exe window


# ── Windows: internal (hidden) console ────────────────────────────────


def test_windows_internal_console(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    _install_fake_popen(monkeypatch)

    launch = pl.spawn_comfy(ARGS, "cwd", {}, external_console=False)

    assert launch.piped is True
    assert launch.log_offset is None  # Windows still pipes into the console
    assert launch.proc.args == ARGS
    assert launch.proc.kwargs["creationflags"] == pl.subprocess.CREATE_NO_WINDOW
    assert launch.proc.kwargs["stdout"] == subprocess.PIPE
    assert launch.proc.kwargs["stderr"] == subprocess.STDOUT
    assert launch.proc.kwargs["encoding"] == "utf-8"
    assert "start_new_session" not in launch.proc.kwargs


# ── posix: headless, output in the shared log ────────────────────────


def test_posix_ignores_external_console(monkeypatch, isolated_log):
    monkeypatch.setattr(sys, "platform", "linux")
    _install_fake_popen(monkeypatch)

    # external_console=True must still yield a headless launch on posix.
    launch = pl.spawn_comfy(ARGS, "cwd", {}, external_console=True)

    assert launch.proc.args == ARGS
    assert "creationflags" not in launch.proc.kwargs
    assert launch.proc.kwargs["start_new_session"] is True
    assert launch.proc.kwargs["stderr"] == subprocess.STDOUT


def test_posix_writes_output_to_log_instead_of_a_pipe(monkeypatch, isolated_log):
    monkeypatch.setattr(sys, "platform", "darwin")
    _install_fake_popen(monkeypatch)

    launch = pl.spawn_comfy(ARGS, "cwd", {}, external_console=False)

    # No pipe: nothing for the caller to drain, and the child survives the
    # launcher closing its own ends of anything.
    assert launch.piped is False
    assert launch.log_offset == 0

    log = launch.proc.kwargs["stdout"]
    assert log.name == isolated_log
    assert launch.proc.kwargs["stderr"] == subprocess.STDOUT
    # The parent's copy is closed straight away; the child keeps its own.
    assert log.closed is True


def test_posix_log_offset_starts_where_this_launch_writes(monkeypatch, isolated_log):
    monkeypatch.setattr(sys, "platform", "linux")
    _install_fake_popen(monkeypatch)

    with open(isolated_log, "ab") as fh:
        fh.write(b"previous session\n")

    launch = pl.spawn_comfy(ARGS, "cwd", {}, external_console=False)

    # Appending, not truncating: an earlier ComfyUI may still hold the file.
    assert launch.log_offset == len(b"previous session\n")
    with open(isolated_log, "rb") as fh:
        assert fh.read() == b"previous session\n"
