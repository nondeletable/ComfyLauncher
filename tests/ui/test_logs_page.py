"""The Launcher Logs page shows the whole log without freezing the window."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QPlainTextEdit  # noqa: E402

import ui.settings.page_logs as page_logs  # noqa: E402
from ui.settings.page_logs import LogsSettingsPage  # noqa: E402


def test_logs_page_shows_a_large_log_in_a_plain_text_view(qapp, tmp_path, monkeypatch):
    """QTextEdit laid a 600 KB log out in growing chunks on the UI thread and
    froze the whole window for about three seconds; QPlainTextEdit lays out only
    what is on screen."""
    log = tmp_path / "launcher.log"
    lines = [f"[2026-10-04 07:00:00] line {i}" for i in range(20000)]
    log.write_text("\n".join(lines), encoding="utf-8")
    monkeypatch.setattr(page_logs, "LOG_FILE", str(log))

    page = LogsSettingsPage()
    try:
        assert isinstance(page.text_edit, QPlainTextEdit)
        assert page.text_edit.toPlainText().endswith("line 19999")
        assert page.text_edit.textCursor().atEnd()
    finally:
        page.close()
