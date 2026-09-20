"""Platform dispatch for the embedded web view.

Windows uses WebView2, everything else QtWebEngine. Both imports stay
inside their branch, for two unrelated reasons:

* The WebView2 module loads a .NET runtime as an import side effect
  (``pythonnet.load("netfx")``), which on Linux raises ``RuntimeError`` —
  not ``ImportError``. A module-level import here would make
  ``ui.browser`` unimportable on every other platform.
* QtWebEngine is only shipped on non-Windows (see ``requirements.txt``),
  so importing it unconditionally would break the Windows install, which
  stays on PyQt6 6.6.1 without WebEngine.

``main.py`` sets ``AA_ShareOpenGLContexts`` before the ``QApplication`` on
non-Windows; without it the QtWebEngine import below would raise, since
the engine refuses to load once an application object exists.
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QWidget

from ui.webview.base import WebViewBase
from utils.logger import log_event


def create_webview(url: str, parent: QWidget | None = None) -> WebViewBase:
    """Return the embedded web view panel for the current platform."""
    if sys.platform == "win32":
        from ui.webview2_widget import WebView2Widget

        return WebView2Widget(url, parent=parent)

    try:
        from ui.webview.qtwebengine_view import QtWebEngineView

        return QtWebEngineView(url, parent=parent)
    except Exception as e:
        # A missing PyQt6-WebEngine, a mismatched Qt6 pair or a missing
        # system library must not take the whole launcher down: the
        # placeholder still gives a working window and a link to ComfyUI.
        log_event(f"⚠️ QtWebEngine unavailable ({e}) — falling back to placeholder.")

    from ui.webview.placeholder import PlaceholderWebView

    return PlaceholderWebView(url, parent=parent)
