"""The startup check offers to install a missing WebView2 Runtime."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
import requests  # noqa: E402

import ui.dialogs.webview2_setup as setup  # noqa: E402


@pytest.fixture
def ui(monkeypatch, qapp):
    """Script the answers of the boxes and record what was shown."""
    calls = {"asked": [], "chosen": [], "info": [], "answers": [], "choices": []}

    def ask(text, kind, buttons):
        calls["asked"].append(kind)
        return calls["answers"].pop(0)

    def choose(parent, title, text, kind, buttons):
        calls["chosen"].append(title)
        return calls["choices"].pop(0)

    monkeypatch.setattr(setup, "_ask", ask)
    monkeypatch.setattr(setup.MB, "choose", staticmethod(choose))
    monkeypatch.setattr(
        setup.MB, "info", staticmethod(lambda *a: calls["info"].append(a))
    )
    monkeypatch.setattr(setup.runtime, "installed_version", lambda: None)
    return calls


def test_installed_runtime_asks_nothing(monkeypatch, ui):
    monkeypatch.setattr(setup.runtime, "installed_version", lambda: "1.2.3.4")
    assert setup.ensure_webview2_runtime() is True
    assert ui["asked"] == []


@pytest.mark.parametrize("answer", ["quit", None])
def test_quit_or_closing_the_box_stops_the_launcher(ui, answer):
    ui["answers"] = [answer]
    assert setup.ensure_webview2_runtime() is False


def test_successful_install_continues_the_launch(monkeypatch, ui):
    monkeypatch.setattr(setup, "_install_with_progress", lambda: None)
    ui["answers"] = ["install"]
    assert setup.ensure_webview2_runtime() is True
    assert len(ui["info"]) == 1


def test_failed_install_shows_the_reason_and_stops(monkeypatch, ui):
    monkeypatch.setattr(setup, "_install_with_progress", lambda: "no network")
    ui["answers"] = ["install", "quit"]
    assert setup.ensure_webview2_runtime() is False
    assert ui["asked"] == ["warning", "error"]


@pytest.mark.parametrize("choice, launches", [("continue", True), ("quit", False)])
def test_runtime_installed_by_hand_asks_to_continue(ui, choice, launches):
    ui["answers"] = ["found"]
    ui["choices"] = [choice]
    assert setup.ensure_webview2_runtime() is launches
    assert ui["chosen"] == [setup.FOUND_TITLE]


def test_manual_install_after_a_failed_one_is_noticed_too(monkeypatch, ui):
    monkeypatch.setattr(setup, "_install_with_progress", lambda: "no network")
    ui["answers"] = ["install", "found"]
    ui["choices"] = ["continue"]
    assert setup.ensure_webview2_runtime() is True


def _fail_download(exc):
    def download():
        raise exc

    return download


@pytest.mark.parametrize(
    "exc, reason",
    [
        (requests.ConnectionError("dns"), "Check your internet connection"),
        (requests.Timeout("slow"), "Check your internet connection"),
        (
            requests.HTTPError(response=type("R", (), {"status_code": 503})()),
            "HTTP 503",
        ),
        (PermissionError("access denied"), "access denied"),
        (setup.subprocess.TimeoutExpired("x", 900), "didn't finish in 15 minutes"),
    ],
)
def test_install_explains_a_failed_download(monkeypatch, exc, reason):
    monkeypatch.setattr(setup.runtime, "download_bootstrapper", _fail_download(exc))
    assert reason in setup._install()


def test_install_reports_a_runtime_still_missing_after_the_installer(monkeypatch):
    monkeypatch.setattr(setup.runtime, "download_bootstrapper", lambda: "x.exe")
    monkeypatch.setattr(setup.runtime, "run_bootstrapper", lambda path: 1603)
    monkeypatch.setattr(setup.runtime, "installed_version", lambda: None)
    assert "code 1603" in setup._install()


def test_ask_notices_a_runtime_installed_while_it_is_open(monkeypatch, qapp):
    monkeypatch.setattr(setup, "POLL_MS", 10)
    monkeypatch.setattr(setup.runtime, "installed_version", lambda: "1.2.3.4")
    assert setup._ask("text", "warning", [("Quit", "quit")]) == "found"


def test_download_page_keeps_the_box_open(monkeypatch, qapp):
    """The page button must not end the dialog; only Quit (or a found runtime) does."""
    opened = []
    monkeypatch.setattr(setup.QDesktopServices, "openUrl", opened.append)
    monkeypatch.setattr(setup.runtime, "installed_version", lambda: None)

    from PyQt6.QtCore import QTimer

    def press_page_then_quit():
        box = qapp.activeModalWidget()
        buttons = {b.text(): b for b in box.findChildren(setup.QPushButton)}
        buttons["Open download page"].click()
        assert box.isVisible()
        buttons["Quit"].click()

    QTimer.singleShot(50, press_page_then_quit)
    answer = setup._ask(
        "text", "warning", [("Open download page", "page"), ("Quit", "quit")]
    )
    assert answer == "quit"
    assert opened[0].toString() == setup.runtime.DOWNLOAD_PAGE_URL


def test_failure_reason_is_escaped_for_the_rich_text_box(monkeypatch, ui):
    texts = []
    monkeypatch.setattr(setup, "_install_with_progress", lambda: "<urllib3> & co")
    monkeypatch.setattr(
        setup,
        "_ask",
        lambda text, kind, buttons: texts.append(text)
        or ("install" if len(texts) == 1 else "quit"),
    )
    setup.ensure_webview2_runtime()
    assert "&lt;urllib3&gt; &amp; co" in texts[1]
