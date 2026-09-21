"""closeEvent must tear the embedded web view down on every accepted exit.

QtWebEngine aborts at process exit if its page/profile are not shut down
synchronously, so browser.shutdown() has to run on the default "ask on exit"
Yes/No paths too — not only on the auto-exit path. Regression guard for that.

closeEvent is exercised on a stand-in ``self`` so the whole ComfyBrowser window
(webview, timers, ComfyUI launch) need not be constructed; no QApplication is
required.
"""

import types

import pytest

import ui.browser as browser


class _StubWebView:
    def __init__(self):
        self.shutdown_calls = 0

    def shutdown(self):
        self.shutdown_calls += 1


class _Event:
    def __init__(self):
        self.accepted = False
        self.ignored = False

    def accept(self):
        self.accepted = True

    def ignore(self):
        self.ignored = True


def _make_self():
    fake = types.SimpleNamespace()
    fake.comfyui_path = "C:/x"
    fake.browser = _StubWebView()
    fake._restore_comfy_on_exit = lambda: None
    fake._close_settings_if_open = lambda: None
    # bind the real helper so we test the actual teardown wiring
    fake._shutdown_webview = types.MethodType(
        browser.ComfyBrowser._shutdown_webview, fake
    )
    return fake


@pytest.fixture(autouse=True)
def _patch_module(monkeypatch):
    monkeypatch.setattr(browser, "stop_comfyui_hard", lambda *a, **k: None)
    monkeypatch.setattr(browser, "save_user_config", lambda *a, **k: True)
    monkeypatch.setattr(browser, "log_event", lambda *a, **k: None)


@pytest.mark.parametrize("choice", ["yes", "no"])
def test_ask_on_exit_paths_shutdown_webview(monkeypatch, choice):
    monkeypatch.setattr(
        browser,
        "load_user_config",
        lambda: {"ask_on_exit": True, "exit_mode": "always_stop"},
    )
    monkeypatch.setattr(browser.MB, "ask_exit", lambda *a, **k: choice)

    fake = _make_self()
    event = _Event()
    browser.ComfyBrowser.closeEvent(fake, event)

    assert event.accepted is True
    assert fake.browser.shutdown_calls == 1, f"shutdown() not called on '{choice}' exit"


def test_cancel_does_not_shutdown(monkeypatch):
    monkeypatch.setattr(
        browser,
        "load_user_config",
        lambda: {"ask_on_exit": True, "exit_mode": "always_stop"},
    )
    monkeypatch.setattr(browser.MB, "ask_exit", lambda *a, **k: "cancel")

    fake = _make_self()
    event = _Event()
    browser.ComfyBrowser.closeEvent(fake, event)

    assert event.ignored is True
    assert fake.browser.shutdown_calls == 0


def test_auto_mode_shuts_down_webview(monkeypatch):
    monkeypatch.setattr(
        browser,
        "load_user_config",
        lambda: {"ask_on_exit": False, "exit_mode": "always_stop"},
    )

    fake = _make_self()
    event = _Event()
    browser.ComfyBrowser.closeEvent(fake, event)

    assert event.accepted is True
    assert fake.browser.shutdown_calls == 1
