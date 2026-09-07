"""Regression tests for the internal-console stdout reader (issue #38-B).

Background: in internal-console mode the child was spawned with text=True but no
explicit encoding, so the parent decoded stdout with the locale codec (cp1251 /
charmap on RU Windows). A non-Latin byte from a custom node crashed the reader
thread, which then stopped draining the pipe -> the child blocked on write ->
ComfyUI hung on startup ("ComfyUI is not responding").
"""

import io

from launcher import _read_process_output
from utils.console_buffer import ConsoleBuffer


class _FakeProc:
    """Minimal stand-in for subprocess.Popen exposing only .stdout."""

    def __init__(self, stdout):
        self.stdout = stdout


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
