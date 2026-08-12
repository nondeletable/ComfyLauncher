from __future__ import annotations

from PyQt6.QtCore import pyqtSignal, QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from utils.platform import detect_system_language


class WebEngineWidget(QWidget):
    """Cross-platform browser widget (macOS/Linux), interface aligned with WebView2Widget."""

    loaded = pyqtSignal(bool)

    def __init__(self, url: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._url = url

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._view = QWebEngineView(self)
        layout.addWidget(self._view, 1)

        # ── Set browser Accept-Language header ──
        lang = detect_system_language()
        if lang and lang != "en":
            profile = QWebEngineProfile.defaultProfile()  # type: ignore[arg-type]
            profile.setHttpAcceptLanguage(
                f"{lang},{lang.split('-')[0]};q=0.9,en;q=0.8"
            )

        self._view.loadFinished.connect(self._on_load_finished)
        self._view.setUrl(QUrl(url))

    def _on_load_finished(self, ok: bool):
        # ── Language injection deferred: ComfyUI uses i18nextLng, needs further investigation ──
        self.loaded.emit(ok)

    def navigate(self, url: str) -> None:
        self._url = url
        self._view.setUrl(QUrl(url))

    def reload(self) -> None:
        self._view.reload()

    def go_back(self) -> None:
        self._view.back()

    def go_forward(self) -> None:
        self._view.forward()

    def shutdown(self) -> None:
        """Release resources."""
        try:
            self._view.setUrl(QUrl("about:blank"))
            self._view.setPage(None)  # type: ignore[arg-type]
        except Exception:
            pass
