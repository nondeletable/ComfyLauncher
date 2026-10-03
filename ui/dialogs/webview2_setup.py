"""Startup check for the WebView2 Runtime, with an offer to install it.

Runs before any window that needs the web view. Without the runtime the
launcher used to fail with a raw error and gave no hint what was missing.
"""

from __future__ import annotations

import html
import subprocess
import threading

import requests
from PyQt6.QtCore import QEventLoop, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QPushButton

from ui.dialogs.messagebox import MessageBox as MB
from utils import webview2_runtime as runtime
from utils.logger import log_event

TITLE = "Missing component"
ASK_TEXT = (
    "Comfy Launcher couldn't find Microsoft Edge WebView2 Runtime on this "
    "computer. The launcher needs it to show the ComfyUI interface.<br><br>"
    "Download and install it now? Windows may ask for permission."
)
INSTALLING_TEXT = "Installing WebView2 Runtime...<br>Please don't close this window."
DONE_TEXT = "Done. Comfy Launcher will now start."
FOUND_TITLE = "WebView2 Runtime installed"
FOUND_TEXT = (
    "Microsoft Edge WebView2 Runtime is now installed. "
    "Continue launching Comfy Launcher?"
)
FAILED_TEXT = (
    "Installation failed: {reason}<br><br>"
    'You can install it manually: <a href="{url}">{url}</a>'
)

POLL_MS = 5000


def _install() -> str | None:
    """Download and run the bootstrapper. Returns an error reason, or None."""
    try:
        code = runtime.run_bootstrapper(runtime.download_bootstrapper())
    except (requests.ConnectionError, requests.Timeout):
        return "couldn't download the installer. Check your internet connection."
    except subprocess.TimeoutExpired:
        minutes = runtime.INSTALL_TIMEOUT_S // 60
        return f"the installer didn't finish in {minutes} minutes."
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        return f"the download server returned an error (HTTP {status})."
    except Exception as e:
        return str(e) or e.__class__.__name__
    if runtime.installed_version() is None:
        return (
            f"the installer finished (code {code}), "
            "but WebView2 Runtime still wasn't found."
        )
    return None


def _install_with_progress() -> str | None:
    """Run ``_install`` off the UI thread behind a box that cannot be closed."""
    box = MB(TITLE, INSTALLING_TEXT, "info")
    box.reject = lambda: None  # Esc / close must not abandon a running install
    box.show()

    result: dict = {}
    worker = threading.Thread(
        target=lambda: result.update(error=_install()), daemon=True
    )
    worker.start()

    loop = QEventLoop()
    poll = QTimer()
    poll.timeout.connect(lambda: None if worker.is_alive() else loop.quit())  # type: ignore
    poll.start(200)
    loop.exec()
    poll.stop()
    box.hide()
    box.deleteLater()
    return result.get("error")


def _ask(text: str, kind: str, buttons) -> str | None:
    """Show the missing-runtime box and return the pressed button's key.

    "page" opens the download page but keeps the box up, so a manual install
    does not end with the launcher gone. While the box is open the runtime is
    re-checked every few seconds; if it shows up, returns "found".
    """
    box = MB(TITLE, text, kind)
    box.body.setOpenExternalLinks(True)
    answer: dict = {"key": None}

    def pick(key):
        if key == "page":
            QDesktopServices.openUrl(QUrl(runtime.DOWNLOAD_PAGE_URL))
            return
        answer["key"] = key
        box.accept()

    for label, key in buttons:
        btn = QPushButton(label)
        btn.clicked.connect(lambda _=False, k=key: pick(k))  # type: ignore
        box._buttons.addWidget(btn)

    def poll():
        if runtime.installed_version():
            answer["key"] = "found"
            box.accept()

    timer = QTimer(box)
    timer.timeout.connect(poll)  # type: ignore
    timer.start(POLL_MS)
    box.exec()
    timer.stop()
    return answer["key"]


def ensure_webview2_runtime() -> bool:
    """True if the runtime is present (or was just installed); False to quit."""
    version = runtime.installed_version()
    if version:
        log_event(f"🧩 WebView2 Runtime {version} found.")
        return True

    log_event("⚠️ WebView2 Runtime not found.")
    answer = _ask(
        ASK_TEXT,
        "warning",
        [("Install", "install"), ("Open download page", "page"), ("Quit", "quit")],
    )
    if answer == "install":
        error = _install_with_progress()
        if error is None:
            log_event("✅ WebView2 Runtime installed.")
            MB.info(None, TITLE, DONE_TEXT)
            return True
        log_event(f"❌ WebView2 Runtime install failed: {error}")
        answer = _ask(
            FAILED_TEXT.format(
                reason=html.escape(error), url=runtime.DOWNLOAD_PAGE_URL
            ),
            "error",
            [("Open download page", "page"), ("Quit", "quit")],
        )

    if answer == "found":
        log_event("✅ WebView2 Runtime installed manually.")
        choice = MB.choose(
            None,
            FOUND_TITLE,
            FOUND_TEXT,
            "info",
            [("Continue", "continue"), ("Quit", "quit")],
        )
        return choice == "continue"
    return False
