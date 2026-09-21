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
fragility, so there we always run headless and pipe output into the internal
console. Spawning an external terminal there can be added later if needed.
"""

from __future__ import annotations

import subprocess
import sys

# Pipe settings shared by every headless launch: an unbuffered UTF-8 line
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


def external_console_supported() -> bool:
    """True on platforms that offer a separate OS console window (Windows only)."""
    return sys.platform == "win32"


def spawn_comfy(
    args: list[str], cwd: str, env: dict, external_console: bool
) -> tuple[subprocess.Popen, bool]:
    """Launch ComfyUI. Returns ``(proc, piped)``.

    ``piped`` is True when ``proc.stdout`` is a pipe the caller must drain into
    the console buffer (i.e. start the reader thread). It is False only for the
    Windows external-console case, where output goes to the ``cmd.exe`` window.

    ``external_console`` is honored only where it is supported; elsewhere it is
    ignored and the process always runs headless + piped.
    """
    if sys.platform == "win32":
        if external_console:
            proc = subprocess.Popen(
                ["cmd.exe", "/k"] + args,
                cwd=cwd,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            return proc, False
        proc = subprocess.Popen(
            args,
            cwd=cwd,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW,
            **_PIPE_KWARGS,
        )
        return proc, True

    # posix: always headless + piped. start_new_session puts ComfyUI in its own
    # process group, so a signal to the launcher's own terminal (e.g. Ctrl+C)
    # doesn't reach it and process-tree teardown stays clean.
    proc = subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        start_new_session=True,
        **_PIPE_KWARGS,
    )
    return proc, True
