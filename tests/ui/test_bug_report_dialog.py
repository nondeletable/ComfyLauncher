import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from urllib.parse import parse_qs, urlparse  # noqa: E402

import pytest  # noqa: E402

from ui.dialogs import bug_report_dialog as dlg_mod  # noqa: E402
from utils import bug_report as br  # noqa: E402


def make_report(console="Total VRAM 1 MB\n"):
    return br.BugReport(
        source="error_screen",
        summary=[("Launcher version", "9.9.9"), ("Error", "boom")],
        sections={
            br.SECTION_LOG: "log line\n",
            br.SECTION_CONSOLE: console,
            br.SECTION_CONFIG: '{"theme": "dark"}',
        },
    )


@pytest.fixture
def calls(monkeypatch, tmp_path):
    """Swallow every side effect of a route and record it."""
    seen = {"open": [], "reveal": [], "info": [], "error": []}
    monkeypatch.setattr(dlg_mod.webbrowser, "open", seen["open"].append)
    monkeypatch.setattr(dlg_mod, "reveal_in_file_manager", seen["reveal"].append)
    monkeypatch.setattr(
        dlg_mod.MessageBox, "info", staticmethod(lambda *a: seen["info"].append(a))
    )
    monkeypatch.setattr(
        dlg_mod.MessageBox, "error", staticmethod(lambda *a: seen["error"].append(a))
    )
    save = br.save_report
    monkeypatch.setattr(
        dlg_mod.br, "save_report", lambda text: save(text, str(tmp_path))
    )
    return seen


def test_preview_shows_the_report_and_follows_the_boxes(qapp):
    dlg = dlg_mod.BugReportDialog("error_screen", "boom", report=make_report())
    text = dlg.report_text()
    assert "Launcher version" in text and "== LAUNCHER LOG" in text
    dlg._checks[br.SECTION_LOG].setChecked(False)
    assert "== LAUNCHER LOG" not in dlg.report_text()
    dlg.comment.setPlainText("my words")
    assert "my words" in dlg.report_text()


def test_automatic_route_is_shown_but_disabled(qapp):
    dlg = dlg_mod.BugReportDialog(report=make_report())
    assert not dlg.route_buttons["automatic"].isEnabled()
    assert dlg.route_buttons["github"].isEnabled()
    assert dlg.route_buttons["discord"].isEnabled()


def test_empty_console_box_says_so(qapp):
    dlg = dlg_mod.BugReportDialog(report=make_report(console=""))
    assert "(empty)" in dlg._checks[br.SECTION_CONSOLE].text()


def test_exception_window_has_its_own_title(qapp):
    dlg = dlg_mod.BugReportDialog("exception", report=make_report())
    assert dlg.windowTitle() == "Comfy Launcher hit an unexpected error"


def test_save_only_writes_the_edited_text(qapp, calls):
    dlg = dlg_mod.BugReportDialog(report=make_report())
    dlg.preview.setPlainText("hand edited\n")
    dlg._send("save")
    with open(dlg.saved_path, encoding="utf-8") as f:
        assert f.read() == "hand edited\n"
    assert calls["reveal"] == [dlg.saved_path]
    assert calls["open"] == []


def test_github_route_opens_a_prefilled_issue(qapp, calls):
    dlg = dlg_mod.BugReportDialog("error_screen", "boom", report=make_report())
    dlg._send("github")
    (url,) = calls["open"]
    q = parse_qs(urlparse(url).query)
    assert q["title"] == ["[Report] boom"]
    assert "Launcher version" in q["body"][0]
    assert "log line" not in q["body"][0]
    assert os.path.basename(dlg.saved_path) in q["body"][0]
    assert calls["reveal"] == [dlg.saved_path]


def test_issue_title_follows_the_shown_text_not_the_raw_error(qapp, calls):
    raw = r"OSError: C:\Users\Jane\ComfyUI missing"
    dlg = dlg_mod.BugReportDialog("exception", raw, report=make_report())
    dlg.preview.setPlainText(dlg.report_text().replace("boom", "edited by user"))
    dlg._send("github")
    (url,) = calls["open"]
    assert parse_qs(urlparse(url).query)["title"] == ["[Report] edited by user"]


def test_discord_route_opens_the_invite(qapp, calls):
    dlg = dlg_mod.BugReportDialog(report=make_report())
    dlg._send("discord")
    assert calls["open"] == [br.DISCORD_INVITE]
    assert calls["info"]


def test_failed_save_reports_and_stays_open(qapp, calls, monkeypatch):
    def fail(text):
        raise OSError("disk full")

    monkeypatch.setattr(dlg_mod.br, "save_report", fail)
    dlg = dlg_mod.BugReportDialog(report=make_report())
    dlg._send("discord")
    assert calls["error"] and calls["open"] == []
    assert dlg.saved_path is None
