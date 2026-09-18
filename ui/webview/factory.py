"""Platform dispatch for the embedded web view.

The WebView2 module loads a .NET runtime as an import side effect
(``pythonnet.load("netfx")``), which on Linux raises ``RuntimeError`` — not
``ImportError``. So the import has to stay inside the win32 branch: a
module-level import here would make ``ui.browser`` unimportable on every
other platform.
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QWidget

from ui.webview.base import WebViewBase


def create_webview(url: str, parent: QWidget | None = None) -> WebViewBase:
    """Return the embedded web view panel for the current platform."""
    if sys.platform == "win32":
        from ui.webview2_widget import WebView2Widget

        return WebView2Widget(url, parent=parent)

    from ui.webview.placeholder import PlaceholderWebView

    return PlaceholderWebView(url, parent=parent)
