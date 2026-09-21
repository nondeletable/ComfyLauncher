"""Opens one bench URL in one engine and keeps it up until killed.

Started as a subprocess by run.py so the harness can measure the whole
process tree, engine helper processes included.

    python _host.py <engine> <url>
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ENGINE, URL = sys.argv[1], sys.argv[2]

# QtWebEngine has to be imported before the QApplication exists, otherwise it
# raises "QtWebEngineWidgets must be imported ... before a QCoreApplication
# instance is created". That is why this import sits up here, ahead of the Qt
# widgets import, instead of inside main() where the engine is chosen.
if ENGINE == "qtwebengine":
    from PyQt6.QtWebEngineWidgets import QWebEngineView

from PyQt6.QtCore import QUrl  # noqa: E402
from PyQt6.QtWidgets import QApplication, QMainWindow  # noqa: E402

WINDOW = (1400, 900)


def main() -> None:
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.resize(*WINDOW)

    if ENGINE == "qtwebengine":
        view = QWebEngineView()
        win.setCentralWidget(view)
        win.show()
        view.load(QUrl(URL))

    elif ENGINE == "webview2":
        # The launcher's own widget, so the number describes what ships today.
        from ui.webview2_widget import WebView2Widget

        view = WebView2Widget(URL)
        win.setCentralWidget(view)
        win.show()

    else:
        raise SystemExit(f"_host.py does not drive '{ENGINE}'")

    app.exec()


main()
