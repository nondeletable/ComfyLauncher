"""The console polls ConsoleBuffer only while it is on screen.

Closing the console only hides it, and the 500 ms timer used to keep joining and
comparing the whole buffer (up to 10 000 lines) for the rest of the session,
re-rendering everything whenever the buffer trimmed. Output written while the
window is hidden stays in ConsoleBuffer and has to appear on the next show,
exactly once.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from ui.dialogs.console_window import ConsoleWindow  # noqa: E402
from utils.console_buffer import ConsoleBuffer  # noqa: E402


@pytest.fixture
def console(qapp):
    ConsoleBuffer.clear()
    win = ConsoleWindow()
    yield win
    win.close()
    ConsoleBuffer.clear()


def test_timer_runs_only_while_shown(console):
    assert not console._timer.isActive()
    console.show()
    assert console._timer.isActive()
    console.hide()
    assert not console._timer.isActive()


def test_show_catches_up_with_output_written_while_hidden(console):
    console.show()
    ConsoleBuffer.add("first\n")
    console._refresh_logs()
    console.hide()

    ConsoleBuffer.add("second\n")
    ConsoleBuffer.add("third\n")
    assert console.text_edit.toPlainText() == "first\n"

    console.show()
    assert console.text_edit.toPlainText() == "first\nsecond\nthird\n"


def test_reopening_does_not_duplicate_text(console):
    ConsoleBuffer.add("line\n")
    console.show()
    console.hide()
    console.show()
    console._refresh_logs()
    assert console.text_edit.toPlainText() == "line\n"
