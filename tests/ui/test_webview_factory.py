"""Tests for the web-view facade: platform dispatch, the placeholder's
contract, and the regression that ``ui.browser`` stays importable off Windows.

The engine modules are never imported for real here: the Windows branch is
checked with a stand-in module, because importing the real one loads a .NET
runtime (see ``ui/webview/factory.py``).
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import importlib  # noqa: E402
import sys  # noqa: E402
import types  # noqa: E402

import pytest  # noqa: E402
from PyQt6.QtWidgets import QVBoxLayout, QWidget  # noqa: E402

from ui.theme.manager import THEME  # noqa: E402

from ui.webview import create_webview  # noqa: E402
from ui.webview.base import WebViewBase  # noqa: E402
from ui.webview.placeholder import PlaceholderWebView  # noqa: E402


@pytest.fixture
def app(qapp):
    """The session-wide QApplication (see tests/conftest.py)."""
    return qapp


URL = "http://127.0.0.1:8188"


def test_placeholder_on_non_windows(app, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    view = create_webview(URL)
    assert isinstance(view, PlaceholderWebView)
    assert isinstance(view, WebViewBase)
    assert isinstance(view, QWidget)


def test_windows_branch_uses_webview2_without_importing_it(app, monkeypatch):
    """The win32 branch must construct WebView2Widget(url, parent=parent).

    A stand-in module stands for the real engine, so this passes on Linux and
    proves the factory does not import it on other platforms.
    """
    calls = []

    class FakeWebView2Widget(WebViewBase):
        def __init__(self, url, dll_dir=None, parent=None):
            super().__init__(parent)
            calls.append((url, dll_dir, parent))

    fake = types.ModuleType("ui.webview2_widget")
    fake.WebView2Widget = FakeWebView2Widget
    monkeypatch.setitem(sys.modules, "ui.webview2_widget", fake)
    monkeypatch.setattr(sys, "platform", "win32")

    view = create_webview(URL)
    assert isinstance(view, FakeWebView2Widget)
    assert calls == [(URL, None, None)]


def test_placeholder_satisfies_the_contract(app):
    view = PlaceholderWebView(URL)
    # Every contract method is a no-op, but none may raise NotImplementedError.
    view.reload()
    view.go_back()
    view.go_forward()
    view.shutdown()
    view.navigate("http://127.0.0.1:9999")
    assert view._url == "http://127.0.0.1:9999"


def test_placeholder_never_reports_a_load(app):
    """A False here would log a misleading "server still starting"."""
    seen = []
    view = PlaceholderWebView(URL)
    view.loaded.connect(seen.append)
    view.show()
    view.reload()
    assert seen == []


def test_base_contract_is_abstract(app):
    view = WebViewBase()
    with pytest.raises(NotImplementedError):
        view.navigate(URL)
    for method in ("reload", "go_back", "go_forward", "shutdown"):
        with pytest.raises(NotImplementedError):
            getattr(view, method)()


@pytest.mark.skipif(sys.platform == "win32", reason="engine present on Windows")
def test_browser_module_imports_without_an_engine(app):
    """Regression: ui.browser used to import WebView2 (and a .NET runtime)
    at module level, so it could not be imported off Windows at all."""
    assert importlib.import_module("ui.browser") is not None


@pytest.fixture
def no_ambient_qss(app):
    """Strip the theme's application stylesheet, leaving the placeholder
    nothing to inherit a background from."""
    THEME.apply()
    previous = app.styleSheet()
    app.setStyleSheet("")
    yield
    app.setStyleSheet(previous)


def test_placeholder_paints_its_background_inside_a_window(app, no_ambient_qss):
    """Regression: the panel rendered with the ambient light palette, which made
    the text_primary title white-on-white. A QWidget subclass only paints a
    stylesheet background with WA_StyledBackground set, and a standalone
    widget.grab() hides the bug — it has to be rendered through its parent.
    """
    view = PlaceholderWebView(URL)
    host = QWidget()
    host.resize(400, 300)
    layout = QVBoxLayout(host)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(view, 1)
    host.show()
    app.processEvents()

    pixel = host.grab().toImage().pixelColor(4, 150).name().lower()
    assert pixel == THEME.colors["bg_header"].lower()
    host.close()


def test_placeholder_follows_a_theme_change(app):
    """Colors are read once at build time, so the panel has to listen for
    themeChanged — otherwise it keeps stale colors after a switch."""
    view = PlaceholderWebView(URL)
    before = view._title.styleSheet()

    original = THEME._colors
    try:
        THEME._colors = dict(original, text_primary="#ABCDEF")
        THEME.themeChanged.emit(THEME._colors)
        assert "#ABCDEF" in view._title.styleSheet()
        assert view._title.styleSheet() != before
    finally:
        THEME._colors = original
        THEME.themeChanged.emit(original)
