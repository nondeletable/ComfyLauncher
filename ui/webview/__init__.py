"""Embedded web view: engine-agnostic contract plus platform dispatch."""

from ui.webview.base import WebViewBase
from ui.webview.factory import create_webview

__all__ = ["WebViewBase", "create_webview"]
