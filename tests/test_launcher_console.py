"""Regression tests for the internal-console stdout reader (issue #38-B).

Background: in internal-console mode the child was spawned with text=True but no
explicit encoding, so the parent decoded stdout with the locale codec (cp1251 /
charmap on RU Windows). A non-Latin byte from a custom node crashed the reader
thread, which then stopped draining the pipe -> the child blocked on write ->
ComfyUI hung on startup ("ComfyUI is not responding").
"""

import io
import threading
import time

import launcher as launcher_mod
from launcher import _read_process_output
from utils.console_buffer import ConsoleBuffer


class _FakeProc:
    """Minimal stand-in for subprocess.Popen exposing only .stdout."""

    def __init__(self, stdout):
        self.stdout = stdout


class _FakeLiveProc:
    """Stand-in for a running ComfyUI: stays alive until told otherwise."""

    def __init__(self):
        self.returncode = None

    def poll(self):
        return self.returncode


def setup_function(_):
    ConsoleBuffer.clear()


def test_reader_survives_undecodable_bytes():
    # Exactly the failing scenario: a stray 0x98 (invalid UTF-8) between valid
    # text, wrapped the same way Popen(encoding="utf-8", errors="replace") does.
    raw = "Custom Node ".encode("utf-8") + b"\x98" + " loaded\n中文\n".encode("utf-8")
    stream = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8", errors="replace")

    _read_process_output(_FakeProc(stream))  # must not raise

    out = ConsoleBuffer.get_all()
    assert "Custom Node" in out
    assert "loaded" in out
    assert "中文" in out
    assert "�" in out  # the bad byte became the replacement char
    assert "[Console reader error]" not in out


def test_reader_keeps_draining_after_buffer_error(monkeypatch):
    # If ConsoleBuffer.add throws on one line, the loop must keep draining the
    # rest — otherwise the pipe fills and the child blocks.
    recorded = []

    def flaky_add(cls, text):
        if text == "b\n":
            raise RuntimeError("boom")
        recorded.append(text)

    monkeypatch.setattr(ConsoleBuffer, "add", classmethod(flaky_add))

    _read_process_output(_FakeProc(iter(["a\n", "b\n", "c\n"])))

    assert recorded == ["a\n", "c\n"]


def test_reader_handles_missing_stdout():
    _read_process_output(_FakeProc(None))  # must not raise
    assert ConsoleBuffer.get_all() == ""


# ── the posix log tailer (the pipe would die with the launcher) ───────


def _wait_until(predicate, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return False


def test_tail_skips_earlier_sessions_and_follows_new_output(monkeypatch, tmp_path):
    path = tmp_path / "comfyui.log"
    path.write_bytes(b"previous session\n")
    monkeypatch.setattr(launcher_mod, "COMFY_LOG_FILE", str(path))

    proc = _FakeLiveProc()
    offset = len(b"previous session\n")
    tailer = threading.Thread(
        target=launcher_mod._tail_comfy_log, args=(proc, offset), daemon=True
    )
    tailer.start()

    # The child keeps appending, including a byte no UTF-8 decoder accepts.
    with open(path, "ab") as fh:
        fh.write("🔵 Total VRAM 15204 MB\n".encode("utf-8") + b"bad \x98 byte\n")

    assert _wait_until(lambda: "Total VRAM" in ConsoleBuffer.get_all())

    proc.returncode = 0
    tailer.join(timeout=5)
    assert not tailer.is_alive()  # exits once ComfyUI is gone

    out = ConsoleBuffer.get_all()
    assert "Total VRAM 15204 MB" in out
    assert "bad \ufffd byte" in out  # replacement char, reader survived
    assert "previous session" not in out  # earlier output is not replayed
