"""Cross-platform ComfyUI process launch.

Isolates the platform-specific console handling so the rest of the launcher can
stay platform-agnostic.

Windows keeps its historical behavior exactly:
- external console requested (``show_cmd``) → a ``cmd.exe /k`` window
  (``CREATE_NEW_CONSOLE``); the launcher does not read its output.
- otherwise → a hidden process (``CREATE_NO_WINDOW``) whose stdout we pipe into
  the internal console.

Linux/macOS have no ``cmd.exe`` and no single terminal emulator guaranteed to be
present (gnome-terminal / konsole / xterm / ... — any may be missing, especially
on minimal or live systems). Attaching to one reliably is not worth the
fragility, so there we always run headless, with output appended to
``COMFY_LOG_FILE`` and tailed into the internal console. A file rather than a
pipe on purpose: the launcher holds a pipe's read end, so a ComfyUI the user
chose to leave running (``No`` in the exit dialog) would die with
``BrokenPipeError`` the next time it wrote to stdout. ``start_new_session`` does
not help there — it detaches signals, not the pipe. Spawning an external
terminal there can be added later if needed.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import NamedTuple

from utils.logger import LOG_DIR

# ComfyUI's own output, next to launcher.log. Appended to, never truncated: a
# ComfyUI left running by "No" may still be writing to it.
COMFY_LOG_FILE = os.path.join(LOG_DIR, "comfyui.log")

# Pipe settings for the Windows hidden-console launch: an unbuffered UTF-8 line
# stream with stderr folded into stdout, decoded resiliently so a non-Latin
# byte from a custom node can't crash the reader thread.
_PIPE_KWARGS = dict(
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace",
    bufsize=1,
)


class LaunchInfo(NamedTuple):
    """How the launched ComfyUI reports its output."""

    proc: subprocess.Popen
    # True when proc.stdout is a pipe the caller must drain into the console
    # buffer: the Windows hidden-console mode, and nothing else.
    piped: bool
    # Byte offset in COMFY_LOG_FILE where this launch's output starts, for the
    # caller to tail from. None when output doesn't go to that file.
    log_offset: int | None


def external_console_supported() -> bool:
    """True on platforms that offer a separate OS console window (Windows only)."""
    return sys.platform == "win32"


def _open_comfy_log():
    """Open COMFY_LOG_FILE for appending.

    Returns the handle together with the byte offset the new output starts at.
    The caller keeps it only until the child has inherited the descriptor.
    """
    try:
        start = os.path.getsize(COMFY_LOG_FILE)
    except OSError:
        start = 0
    return open(COMFY_LOG_FILE, "ab"), start


def spawn_comfy(
    args: list[str], cwd: str, env: dict, external_console: bool
) -> LaunchInfo:
    """Launch ComfyUI and report where its output went (``LaunchInfo``).

    ``external_console`` is honored only where it is supported; elsewhere it is
    ignored and the process always runs headless.
    """
    if sys.platform == "win32":
        if external_console:
            proc = subprocess.Popen(
                ["cmd.exe", "/k"] + args,
                cwd=cwd,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            return LaunchInfo(proc, False, None)
        proc = subprocess.Popen(
            args,
            cwd=cwd,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW,
            **_PIPE_KWARGS,
        )
        return LaunchInfo(proc, True, None)

    # posix: always headless, writing to COMFY_LOG_FILE. start_new_session puts
    # ComfyUI in its own process group, so a signal to the launcher's own
    # terminal (e.g. Ctrl+C) doesn't reach it and process-tree teardown stays
    # clean.
    log, start = _open_comfy_log()
    try:
        proc = subprocess.Popen(
            args,
            cwd=cwd,
            env=env,
            start_new_session=True,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    finally:
        # The child holds its own descriptor; keeping this one would only tie
        # the file's lifetime to the launcher.
        log.close()
    return LaunchInfo(proc, False, start)
