"""QtWebEngine implementation of the web-view contract (Linux/macOS).

Chosen over WebKitGTK by the fps spike in ``tools/webview_bench``: on Qt
6.11 (Chromium 140) this engine lands within a few percent of a system
Chromium on a litegraph-shaped canvas, at roughly half its memory.

Windows keeps WebView2 — this module is never imported there.

Two engine-specific constraints shape the code below:

* ``QtWebEngineWidgets`` refuses to import once a ``QCoreApplication``
  exists, unless ``AA_ShareOpenGLContexts`` was set beforehand. ``main.py``
  sets that attribute on non-Windows, which is what keeps the import in
  ``ui.webview.factory`` lazy.
* A ``QWebEngineProfile`` must outlive the page that uses it, so the
  profile is held on the widget rather than passed in and forgotten.
"""

from __future__ import annotations

import os

from PyQt6 import sip
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import (
    QWebEngineDownloadRequest,
    QWebEnginePage,
    QWebEngineProfile,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from ui.webview.base import WebViewBase
from utils.logger import log_event
from utils.platform_paths import APP_NAME, app_dir


class QtWebEngineView(WebViewBase):
    """Embedded Chromium panel, an ordinary Qt widget.

    Unlike WebView2 there is no native-handle reparenting here, so this
    works on Wayland and X11 alike.
    """

    def __init__(self, url: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._url = url

        # A named profile is persistent, and it has to be: ComfyUI keeps its
        # settings in localStorage, which the default off-the-record profile
        # would drop on every launch. It is deliberately left unparented —
        # Qt destroys children in construction order, so a child profile would
        # be released before the page using it, and this widget's own
        # reference is what keeps it alive instead.
        self._profile = QWebEngineProfile(APP_NAME)
        # Kept inside the app's own directory: the port decided on a single
        # per-user dir rather than an XDG split, and Qt would otherwise put
        # this under ~/.local/share. Mirrors WebView2's own data subfolder.
        storage = os.path.join(app_dir(), "webengine")
        self._profile.setPersistentStoragePath(os.path.join(storage, "storage"))
        self._profile.setCachePath(os.path.join(storage, "cache"))
        self._profile.downloadRequested.connect(self._on_download_requested)

        self._page = QWebEnginePage(self._profile, self)
        self._view = QWebEngineView(self)
        self._view.setPage(self._page)
        self._view.loadFinished.connect(self._on_load_finished)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._view, 1)

        self._view.setUrl(QUrl(url))

    # ─── internals ───────────────────────────────────────
    def _on_load_finished(self, ok: bool) -> None:
        self.loaded.emit(ok)  # type: ignore[attr-defined]

    def _on_download_requested(self, item: QWebEngineDownloadRequest) -> None:
        """Save downloads silently, then announce the finished file.

        Mirrors the WebView2 behavior: Chromium's own download UI is not
        shown, the file lands in the default download directory, and
        ``download_saved`` carries ``(basename, full path)``.
        """

        def _on_finished() -> None:
            if (
                item.state()
                != QWebEngineDownloadRequest.DownloadState.DownloadCompleted
            ):
                return
            path = os.path.join(item.downloadDirectory(), item.downloadFileName())
            self.download_saved.emit(os.path.basename(path), path)  # type: ignore[attr-defined]

        item.isFinishedChanged.connect(_on_finished)
        item.accept()

    # ─── WebViewBase contract ────────────────────────────
    def navigate(self, url: str) -> None:
        self._url = url
        self._view.setUrl(QUrl(url))

    def reload(self) -> None:
        self._view.reload()

    def go_back(self) -> None:
        history = self._view.history()
        if history.canGoBack():
            history.back()

    def go_forward(self) -> None:
        history = self._view.history()
        if history.canGoForward():
            history.forward()

    def shutdown(self) -> None:
        """Stop the engine before the window goes away.

        Chromium tears its render process down asynchronously; letting the
        widget be destroyed mid-load is the usual source of exit crashes.
        """
        if self._profile is None:  # already shut down
            return
        try:
            self._view.stop()
            # Torn down synchronously and in this order on purpose. Qt requires
            # the profile to outlive its page; deleteLater() would leave both
            # alive until an event loop that no longer runs at exit, and the
            # profile then dies first — "Release of profile requested but
            # WebEnginePage still not deleted", followed by an abort.
            sip.delete(self._view)
            sip.delete(self._page)
            self._profile = None
        except Exception as e:
            log_event(f"⚠️ QtWebEngine shutdown: {e}")
