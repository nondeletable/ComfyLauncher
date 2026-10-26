"""Startup wait: no fixed deadline, only a dead or silent ComfyUI ends it.

A user on a slow machine hit the old fixed 90 s timeout on most launches while
ComfyUI was still busily loading custom nodes.
"""

import subprocess
import sys

import pytest

from utils import startup_watch as sw
from utils.startup_watch import ProcessActivity, StartupState, decide


@pytest.mark.parametrize(
    "port_open, alive, idle, timeout, expected",
    [
        (True, False, 999, 120, StartupState.READY),  # port wins over everything
        (False, False, 0, 120, StartupState.EXITED),  # dead → at once, no waiting
        (False, True, 119, 120, StartupState.WAITING),
        (False, True, 120, 120, StartupState.STALLED),
        (False, True, 10_000, 0, StartupState.WAITING),  # 0 = no limit
        (False, None, 50, 120, StartupState.WAITING),  # not ours: idle clock only
        (False, None, 120, 120, StartupState.STALLED),
    ],
)
def test_decide(port_open, alive, idle, timeout, expected):
    assert decide(port_open, alive, idle, timeout) is expected


class FakeProc:
    def __init__(self, work=0.0, children=(), name="python.exe"):
        self.work = work
        self._children = list(children)
        self._name = name
        self.running = True

    def name(self):
        return self._name

    def is_running(self):
        return self.running

    def status(self):
        return "running"

    def children(self, recursive=False):
        return self._children

    def cpu_times(self):
        return type("T", (), {"user": self.work, "system": 0.0})()

    def io_counters(self):
        raise sw.psutil.AccessDenied()


def patch_process(monkeypatch, root):
    monkeypatch.setattr(sw.psutil, "Process", lambda _pid: root)


def test_activity_goes_quiet_when_cpu_stops_growing(monkeypatch):
    root = FakeProc(work=1.0)
    patch_process(monkeypatch, root)
    act = ProcessActivity(1, wrapped=False)

    assert act.sample() == (True, True)  # first look counts as activity
    assert act.sample() == (True, False)  # nothing changed
    root.work = 1.5
    assert act.sample() == (True, True)


def test_wrapper_without_python_yet_is_not_dead(monkeypatch):
    root = FakeProc()  # cmd.exe, python not spawned yet
    patch_process(monkeypatch, root)
    act = ProcessActivity(1, wrapped=True)

    assert act.sample() == (True, True)


def test_wrapper_left_alone_after_python_died_counts_as_exited(monkeypatch):
    python = FakeProc(work=2.0)
    root = FakeProc(children=[python])
    patch_process(monkeypatch, root)
    act = ProcessActivity(1, wrapped=True)
    assert act.sample()[0] is True

    # ComfyUI crashed; cmd /k keeps the window open, and with it conhost.exe
    root._children = [FakeProc(work=9.0, name="conhost.exe")]
    assert act.sample() == (False, False)
    assert sw.is_alive(1, wrapped=True) is False


def test_wrapper_itself_is_not_counted_as_work(monkeypatch):
    python = FakeProc(work=1.0)
    root = FakeProc(work=500.0, children=[python])
    patch_process(monkeypatch, root)
    act = ProcessActivity(1, wrapped=True)
    act.sample()

    root.work = 900.0  # only the wrapper moved
    assert act.sample() == (True, False)


def test_real_process_lifecycle():
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        act = ProcessActivity(proc.pid, wrapped=False)
        assert act.sample()[0] is True
        assert sw.is_alive(proc.pid, wrapped=False) is True
    finally:
        proc.kill()
        proc.wait()
    assert act.sample() == (False, False)
    assert sw.is_alive(proc.pid, wrapped=False) is False
