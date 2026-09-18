"""Fallback panel for platforms with no embedded engine wired up yet.

The Linux/macOS port has the process side in place (paths, interpreter,
spawn) while the engine is still being chosen, so ``create_webview`` hands
back this panel there. It lets the launcher window, header, theming and the
whole startup sequence be exercised without any engine at all; ComfyUI
itself is already running and reachable, just not embedded.

It deliberately never emits ``loaded``: nothing was loaded, and a ``False``
would make ``ComfyBrowser.on_load_finished`` log a misleading "server
probably still starting".
"""

from __future__ import annotations

import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from ui.theme.manager import THEME
from ui.webview.base import WebViewBase
from utils.logger import log_event


class PlaceholderWebView(WebViewBase):
    """Static panel standing in for a real engine on unsupported platforms."""

    def __init__(self, url: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._url = url
        self._build_ui()
        log_event(
            f"ℹ️ No embedded engine on this platform — placeholder shown for {url}"
        )

    def _build_ui(self) -> None:
        c = THEME.colors

        self.setObjectName("PlaceholderWebView")
        self.setAutoFillBackground(True)
        self.setStyleSheet(
            f"""
            QWidget#PlaceholderWebView {{
                background-color: {c["bg_header"]};
            }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.setSpacing(14)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("No embedded engine on this platform")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"font-size: 18px; font-weight: 600; color: {c['text_primary']};"
        )

        message = QLabel(
            "ComfyUI is running and reachable, but no web engine is wired up "
            "for this platform yet. Open the interface in your browser."
        )
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)
        message.setStyleSheet(f"font-size: 15px; color: {c['text_secondary']};")

        address = QLabel(self._url)
        address.setAlignment(Qt.AlignmentFlag.AlignCenter)
        address.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        address.setStyleSheet(
            f"font-size: 14px; color: {c['accent']}; background: transparent;"
        )

        open_button = QPushButton("Open in browser")
        open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        open_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {c["accent"]};
                color: {c["text_inverse"]};
                border: none;
                border-radius: 10px;
                padding: 8px 18px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {c["accent_hover"]};
            }}
            """
        )
        open_button.clicked.connect(self._open_in_system_browser)

        root.addWidget(title)
        root.addWidget(message)
        root.addWidget(address)
        root.addWidget(open_button, 0, Qt.AlignmentFlag.AlignCenter)

    def _open_in_system_browser(self) -> None:
        log_event(f"🌐 Opening {self._url} in the system browser.")
        webbrowser.open(self._url)

    # ─── WebViewBase contract ────────────────────────────
    def navigate(self, url: str) -> None:
        """Remember the new address; there is no engine to send it to."""
        self._url = url

    def reload(self) -> None:
        """No-op: nothing is loaded."""

    def go_back(self) -> None:
        """No-op: there is no history."""

    def go_forward(self) -> None:
        """No-op: there is no history."""

    def shutdown(self) -> None:
        """No-op: no engine, no native window, nothing to tear down."""
