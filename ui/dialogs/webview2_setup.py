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
from utils.i18n import I18N, t
from utils.logger import log_event

POLL_MS = 5000

# Why an install failed: an i18n key and its placeholders. The box shows it in
# the interface language, the log in English.
Reason = tuple[str, dict]


def _install() -> Reason | None:
    """Download and run the bootstrapper. Returns the error reason, or None."""
    try:
        code = runtime.run_bootstrapper(runtime.download_bootstrapper())
    except (requests.ConnectionError, requests.Timeout):
        return "webview2.reason.offline", {}
    except subprocess.TimeoutExpired:
        return "webview2.reason.timeout", {"minutes": runtime.INSTALL_TIMEOUT_S // 60}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        return "webview2.reason.http", {"status": status}
    except Exception as e:
        return "webview2.reason.other", {"error": str(e) or e.__class__.__name__}
    if runtime.installed_version() is None:
        return "webview2.reason.still_missing", {"code": code}
    return None


def _reason_text(reason: Reason) -> str:
    key, params = reason
    return t(key, **params)


def _install_with_progress() -> Reason | None:
    """Run ``_install`` off the UI thread behind a box that cannot be closed."""
    box = MB(t("webview2.title"), t("webview2.installing"), "info")
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
    box = MB(t("webview2.title"), text, kind)
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
    page = (t("webview2.button.page"), "page")
    quit_ = (t("webview2.button.quit"), "quit")
    answer = _ask(
        t("webview2.ask"),
        "warning",
        [(t("webview2.button.install"), "install"), page, quit_],
    )
    if answer == "install":
        error = _install_with_progress()
        if error is None:
            log_event("✅ WebView2 Runtime installed.")
            MB.info(None, t("webview2.title"), t("webview2.done"))
            return True
        key, params = error
        log_event(f"❌ WebView2 Runtime install failed: {I18N.english(key, **params)}")
        answer = _ask(
            t(
                "webview2.failed",
                reason=html.escape(_reason_text(error)),
                url=runtime.DOWNLOAD_PAGE_URL,
            ),
            "error",
            [page, quit_],
        )

    if answer == "found":
        log_event("✅ WebView2 Runtime installed manually.")
        choice = MB.choose(
            None,
            t("webview2.found.title"),
            t("webview2.found.text"),
            "info",
            [(t("webview2.button.continue"), "continue"), quit_],
        )
        return choice == "continue"
    return False
