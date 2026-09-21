"""Engine-agnostic contract for the embedded web view.

``ui.browser`` talks to the web view only through this interface, so the
concrete engine (WebView2 on Windows, still undecided elsewhere) can be
swapped without touching the window code.

Concrete engines must never be imported at module level by platform-neutral
code — that is what ``ui.webview.factory`` is for.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget


class WebViewBase(QWidget):
    """Abstract embedded browser panel.

    The signals mirror what the Windows implementation already emitted, so
    extracting this base class does not change Windows behavior.
    """

    # True when the page finished loading, False when it failed
    loaded = pyqtSignal(bool)
    # (basename, full_path) — emitted when a download finishes
    download_saved = pyqtSignal(str, str)

    def navigate(self, url: str) -> None:
        raise NotImplementedError

    def reload(self) -> None:
        raise NotImplementedError

    def go_back(self) -> None:
        raise NotImplementedError

    def go_forward(self) -> None:
        raise NotImplementedError

    def shutdown(self) -> None:
        raise NotImplementedError
