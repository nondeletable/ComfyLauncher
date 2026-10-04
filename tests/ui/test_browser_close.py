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
    fake._close_settings_if_open = lambda: True
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


@pytest.mark.parametrize(
    "ask, choice", [(True, "yes"), (True, "no"), (False, None)], ids=str
)
def test_settings_applied_on_exit_are_not_overwritten(monkeypatch, ask, choice):
    """Settings closes before the config snapshot that exit writes back whole.

    Regression: the snapshot was read first, Settings was closed after it - and
    whatever "Apply" in Settings' unsaved prompt saved was overwritten.
    """
    store = {"ask_on_exit": ask, "exit_mode": "never_stop", "show_splash": True}
    saved = []
    monkeypatch.setattr(browser, "load_user_config", lambda: dict(store))
    monkeypatch.setattr(browser, "save_user_config", lambda cfg: saved.append(cfg))
    monkeypatch.setattr(browser.MB, "ask_exit", lambda *a, **k: choice)

    def settings_applies_and_closes():
        store["show_splash"] = False
        return True

    fake = _make_self()
    fake._close_settings_if_open = settings_applies_and_closes
    event = _Event()
    browser.ComfyBrowser.closeEvent(fake, event)

    assert event.accepted is True
    assert saved and saved[-1]["show_splash"] is False


def test_cancel_in_settings_keeps_the_launcher_open(monkeypatch):
    monkeypatch.setattr(
        browser,
        "load_user_config",
        lambda: {"ask_on_exit": True, "exit_mode": "always_stop"},
    )
    asked = []
    monkeypatch.setattr(browser.MB, "ask_exit", lambda *a, **k: asked.append(1))
    stopped = []
    monkeypatch.setattr(browser, "stop_comfyui_hard", lambda *a: stopped.append(1))

    fake = _make_self()
    fake._close_settings_if_open = lambda: False
    event = _Event()
    browser.ComfyBrowser.closeEvent(fake, event)

    assert event.ignored is True and event.accepted is False
    assert fake._exit_in_progress is False
    assert asked == [] and stopped == []
    assert fake.browser.shutdown_calls == 0


class _StubSettings:
    def __init__(self, result):
        self.result = result

    def close(self):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.mark.parametrize(
    "result, closed",
    [(True, True), (False, False), (RuntimeError("deleted"), True)],
    ids=["closed", "kept-open", "already-deleted"],
)
def test_close_settings_reports_whether_it_closed(result, closed):
    fake = types.SimpleNamespace(settings_window=_StubSettings(result))
    assert browser.ComfyBrowser._close_settings_if_open(fake) is closed
    assert (fake.settings_window is None) is closed


def test_close_settings_with_none_open():
    fake = types.SimpleNamespace(settings_window=None)
    assert browser.ComfyBrowser._close_settings_if_open(fake) is True
