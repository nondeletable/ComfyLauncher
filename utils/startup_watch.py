"""Decides whether a starting ComfyUI is ready, still working, dead or stuck.

ComfyUI opens its port only at the very end of startup (after torch, custom
nodes and prestartup scripts), so "port closed" alone says nothing about
whether it is alive. A slow machine or a heavy custom-node set can easily need
minutes. Instead of a fixed deadline we watch the process itself: as long as it
burns CPU or does I/O it is working, and we only give up when it dies or goes
silent for ``stall_timeout`` seconds.

On Windows with the external console the launched process is a ``cmd.exe /k``
wrapper that outlives ComfyUI (it keeps the window open to show the traceback),
so there liveness is judged by the wrapper's children, not by the wrapper.
"""

from __future__ import annotations

from enum import Enum, auto

import psutil


class StartupState(Enum):
    READY = auto()
    WAITING = auto()
    EXITED = auto()
    STALLED = auto()


def decide(
    port_open: bool,
    alive: bool | None,
    idle_seconds: float,
    stall_timeout: float,
) -> StartupState:
    """Pure decision for one poll tick.

    ``alive`` is None when we don't own the process (ComfyUI was started by
    someone else) and can't tell; then only the idle clock counts.
    ``stall_timeout`` of 0 means wait forever.
    """
    if port_open:
        return StartupState.READY
    if alive is False:
        return StartupState.EXITED
    if stall_timeout > 0 and idle_seconds >= stall_timeout:
        return StartupState.STALLED
    return StartupState.WAITING


# Hosts of the console window itself: a child of the wrapper for as long as the
# window is open, so they must not count as "ComfyUI is still running".
_CONSOLE_HOSTS = {"conhost.exe", "openconsole.exe"}


def _workers(root: psutil.Process, wrapped: bool) -> list[psutil.Process]:
    """Processes that are ComfyUI itself (plus anything it spawned)."""
    children = root.children(recursive=True)
    if not wrapped:
        return [root] + children
    workers = []
    for child in children:
        try:
            if child.name().lower() not in _CONSOLE_HOSTS:
                workers.append(child)
        except psutil.Error:
            pass
    return workers


def is_alive(pid: int, wrapped: bool) -> bool:
    """True while ComfyUI (not just its console wrapper) is running."""
    try:
        root = psutil.Process(pid)
        if not root.is_running() or root.status() == psutil.STATUS_ZOMBIE:
            return False
        return bool(_workers(root, wrapped))
    except psutil.Error:
        return False


class ProcessActivity:
    """Samples a process tree and reports whether it did any work since last time."""

    def __init__(self, pid: int, wrapped: bool):
        self.pid = pid
        self.wrapped = wrapped
        self._last: float | None = None
        # The wrapper starts python a moment after itself; until we have seen
        # it once, an empty wrapper means "not yet", not "already dead".
        self._seen_worker = not wrapped

    def sample(self) -> tuple[bool, bool]:
        """Return ``(alive, active)``."""
        try:
            root = psutil.Process(self.pid)
            if not root.is_running() or root.status() == psutil.STATUS_ZOMBIE:
                return False, False
            workers = _workers(root, self.wrapped)
        except psutil.Error:
            return False, False

        if workers:
            self._seen_worker = True
        elif self._seen_worker:
            return False, False
        else:
            return True, True  # wrapper is still spawning python

        total = sum(self._work_of(p) for p in workers)
        active = self._last is None or total > self._last
        self._last = total
        return True, active

    @staticmethod
    def _work_of(proc: psutil.Process) -> float:
        """CPU seconds plus I/O bytes (scaled) — anything that only grows while working."""
        work = 0.0
        try:
            cpu = proc.cpu_times()
            work += cpu.user + cpu.system
        except psutil.Error:
            pass
        try:
            io = proc.io_counters()
            work += (io.read_bytes + io.write_bytes) / 1e6
        except (psutil.Error, AttributeError, NotImplementedError):
            pass
        return work
