"""Last-resort handlers for exceptions nobody caught.

Without them a packaged build (no console) just vanishes: PyQt aborts the
process on an exception escaping a slot, and the traceback goes nowhere. These
hooks log the traceback and offer the bug report window instead.

Two steps, because the window needs a QApplication:

- ``install_exception_hooks()`` - as early as possible. Until the next step an
  exception is only logged and written to ``crash-*.txt`` next to the log.
- ``enable_report_window()`` - right after the QApplication exists, in the GUI
  thread. From then on an exception opens the report window.

The window always opens in the GUI thread: other threads hand it over through
a queued signal. Only one window is shown at a time, and an exception raised
while it is open (or by the window itself) is logged, never re-reported, so a
broken window cannot loop.
"""

from __future__ import annotations

import os
import sys
import threading
import traceback
from datetime import datetime

from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication

from utils import logger
from utils.logger import log_event

_dispatcher: "_Dispatcher | None" = None
_window_open = False


class _Dispatcher(QObject):
    """Lives in the GUI thread; a queued signal carries reports into it."""

    report = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.report.connect(self._on_report, Qt.ConnectionType.QueuedConnection)

    def _on_report(self, error: str, text: str) -> None:
        _show_window(error, text)


def install_exception_hooks() -> None:
    sys.excepthook = _sys_hook
    threading.excepthook = _thread_hook


def enable_report_window() -> None:
    global _dispatcher
    _dispatcher = _Dispatcher()


def _sys_hook(exc_type, exc, tb) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc, tb)
        return
    _handle(exc_type, exc, tb)


def _thread_hook(args) -> None:
    if args.exc_type is SystemExit:
        return
    _handle(args.exc_type, args.exc_value, args.exc_traceback, args.thread)


def _handle(exc_type, exc, tb, thread: threading.Thread | None = None) -> None:
    try:
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        where = f" in thread {thread.name}" if thread is not None else ""
        log_event(f"❌ Unhandled exception{where}:\n{text.rstrip()}")
        error = f"{exc_type.__name__}: {exc}"

        if _dispatcher is None or QApplication.instance() is None:
            _write_crash_file(error, text)
            return
        if _window_open:
            return

        on_gui = threading.current_thread() is threading.main_thread()
        if on_gui and QThread.currentThread().loopLevel() == 0:
            # No event loop is running (the app is starting up or already
            # unwinding), so a queued signal would never arrive.
            _show_window(error, text)
        else:
            _dispatcher.report.emit(error, text)
    except Exception:
        try:
            sys.__excepthook__(exc_type, exc, tb)
        except Exception:
            pass


def _show_window(error: str, text: str) -> None:
    global _window_open
    if _window_open:
        return
    _window_open = True
    try:
        from ui.dialogs.bug_report_dialog import BugReportDialog

        BugReportDialog("exception", error, text, QApplication.activeWindow()).exec()
    except Exception as e:
        log_event(f"❌ Report window for an unhandled exception failed: {e}")
        _write_crash_file(error, text)
    finally:
        _window_open = False


def _write_crash_file(error: str, text: str) -> None:
    try:
        from utils import bug_report as br

        body = br.render_report(br.collect_report("exception", error, text))
    except Exception:
        body = text
    path = os.path.join(
        logger.LOG_DIR, f"crash-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    )
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        log_event(f"📝 Crash report written to {path}")
    except OSError as e:
        log_event(f"⚠️ Crash report could not be written: {e}")
