"""The "taking longer than usual" card and how the browser reacts to it.

The browser part runs on a stand-in ``self`` (as in test_browser_close) so the
whole ComfyBrowser window and a real ComfyUI start are not needed.
"""

import os
import time
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402
from PyQt6.QtWidgets import QWidget  # noqa: E402

import ui.browser as browser  # noqa: E402
from ui.dialogs.slow_start_notice import SlowStartNotice  # noqa: E402

# ── the card ─────────────────────────────────────────────────────────────


def test_elapsed_time_is_shown_as_minutes_and_seconds(qapp):
    notice = SlowStartNotice(time.monotonic() - 102)
    assert notice.elapsed.text() == "1:42"


def test_card_sits_right_under_the_splash_with_its_width(qapp):
    splash = QWidget()
    splash.setGeometry(300, 200, 700, 260)
    splash.show()
    notice = SlowStartNotice(time.monotonic())
    notice.place(splash)

    assert notice.width() == splash.frameGeometry().width()
    assert notice.x() == splash.frameGeometry().left()
    assert notice.y() > splash.frameGeometry().bottom()
    splash.close()


def test_without_splash_the_card_is_centered(qapp):
    notice = SlowStartNotice(time.monotonic())
    notice.place(None)
    area = notice.screen().availableGeometry()
    assert abs(notice.frameGeometry().center().x() - area.center().x()) <= 1


def test_card_is_owned_by_the_splash_so_it_rises_with_it(qapp):
    splash = QWidget()
    notice = SlowStartNotice(time.monotonic(), splash)
    # An owned (Dialog) window stays above its owner and shares its taskbar
    # button; owned by the hidden main window it got lost behind other apps.
    assert notice.parent() is splash
    assert notice.windowType() == Qt.WindowType.Dialog


def test_without_splash_the_card_is_a_window_of_its_own(qapp):
    notice = SlowStartNotice(time.monotonic())
    assert notice.windowType() == Qt.WindowType.Window


def test_popup_flashes_the_taskbar_button(qapp, monkeypatch):
    import ui.dialogs.slow_start_notice as mod

    alerted = []
    monkeypatch.setattr(mod.QApplication, "alert", lambda w, *a: alerted.append(w))
    splash = QWidget()
    splash.setGeometry(300, 200, 700, 260)
    splash.show()
    notice = SlowStartNotice(time.monotonic(), splash)
    notice.popup(splash)
    assert alerted == [splash]
    assert notice.isVisible()
    notice.close()
    splash.close()


@pytest.mark.parametrize("key", [Qt.Key.Key_Return, Qt.Key.Key_Escape])
def test_enter_and_esc_mean_wait(qapp, key):
    notice = SlowStartNotice(time.monotonic())
    got = []
    notice.waitRequested.connect(lambda: got.append("wait"))
    notice.stopRequested.connect(lambda: got.append("stop"))
    QTest.keyClick(notice, key)
    assert got == ["wait"]


def test_stop_button_asks_to_stop(qapp):
    notice = SlowStartNotice(time.monotonic())
    got = []
    notice.stopRequested.connect(lambda: got.append("stop"))
    notice.btn_stop.click()
    assert got == ["stop"]


# ── the browser flow ─────────────────────────────────────────────────────


@pytest.fixture
def fake(monkeypatch):
    calls = []
    monkeypatch.setattr(browser, "log_event", lambda *a, **k: None)
    monkeypatch.setattr(
        browser, "stop_comfyui_hard", lambda path: calls.append(("stop", path))
    )

    f = types.SimpleNamespace(calls=calls, comfyui_path="C:/build")
    f.ui_state = "STARTING_COMFY"
    f.worker = types.SimpleNamespace(stop=lambda: calls.append(("worker_stop",)))
    f._enter_error_state = lambda code: (
        calls.append(("error", code)),
        setattr(f, "ui_state", "ERROR_STARTUP"),
    )
    f._start_comfyui = lambda: calls.append(("start",))
    for name in (
        "_on_slow_stop",
        "_on_comfy_ready",
        "_on_comfy_timeout",
        "_on_comfy_exited",
        "_on_comfy_error",
        "restart_comfy",
    ):
        setattr(f, name, types.MethodType(getattr(browser.ComfyBrowser, name), f))
    return f


def test_stop_kills_comfyui_and_shows_the_stopped_screen(qapp, fake):
    fake._on_slow_stop()
    assert fake.calls == [
        ("worker_stop",),
        ("stop", "C:/build"),
        ("error", "COMFY_START_STOPPED"),
    ]


def test_late_worker_signals_after_stop_are_ignored(qapp, fake):
    fake._on_slow_stop()
    fake.calls.clear()

    fake._on_comfy_ready()
    fake._on_comfy_timeout()
    fake._on_comfy_exited()
    fake._on_comfy_error("boom")
    assert fake.calls == []
    assert fake.ui_state == "ERROR_STARTUP"


def test_restart_from_an_error_screen_runs_the_whole_start_again(qapp, fake):
    fake.ui_state = "ERROR_STARTUP"
    fake.restart_comfy()
    assert fake.calls == [("start",)]
