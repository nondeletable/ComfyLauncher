"""Smoke test for the real QtWebEngine engine (Linux/macOS).

The factory tests deliberately use stand-in modules, so nothing there would
notice if the actual implementation stopped matching ``WebViewBase``. This
file constructs the real thing. It skips itself on Windows, which stays on
PyQt6 6.6.1 with no WebEngine installed.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtTest import QSignalSpy  # noqa: E402

from ui.webview.base import WebViewBase  # noqa: E402

pytest.importorskip(
    "PyQt6.QtWebEngineWidgets", reason="PyQt6-WebEngine is not installed"
)

from ui.webview.qtwebengine_view import QtWebEngineView  # noqa: E402


URL = "about:blank"


@pytest.fixture
def view(qapp):
    v = QtWebEngineView(URL)
    yield v
    v.shutdown()


def test_it_implements_the_contract(view):
    """Every contract method must run on the real engine without raising."""
    assert isinstance(view, WebViewBase)
    view.navigate(URL)
    view.reload()
    view.go_back()
    view.go_forward()


def test_shutdown_is_idempotent(view):
    """ComfyBrowser closes can overlap; a second teardown must not raise."""
    view.shutdown()
    view.shutdown()


def test_it_uses_a_persistent_profile(view):
    """An off-the-record profile would drop ComfyUI's localStorage settings
    on every launch, so the named profile is a functional requirement."""
    assert not view._profile.isOffTheRecord()
    assert view._page.profile() is view._profile


def test_it_reports_a_finished_load(view):
    """``loaded`` drives ComfyBrowser.on_load_finished — it has to fire.

    The load is asynchronous, so this needs a real event loop: spinning
    processEvents() returns before Chromium has finished.
    """
    seen = []
    view.loaded.connect(seen.append)
    spy = QSignalSpy(view.loaded)
    view.navigate(URL)
    assert spy.wait(10_000), "loadFinished never arrived"
    assert seen == [True]
