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
from PyQt6.QtWidgets import QApplication, QWidget  # noqa: E402

from ui.webview import create_webview  # noqa: E402
from ui.webview.base import WebViewBase  # noqa: E402
from ui.webview.placeholder import PlaceholderWebView  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


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
