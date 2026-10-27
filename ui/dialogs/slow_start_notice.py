"""Card shown when ComfyUI takes longer than usual to start.

It is not an error: the process is alive and working, it is just slow (many
custom nodes, a slow disk, a weak machine). The card says so, shows how long it
has been, and offers two answers - Wait (the safe, primary one) and Stop.

Non-modal on purpose: the elapsed time keeps ticking, and the browser closes
the card on its own as soon as ComfyUI comes up, crashes or goes silent.
It sits right under the splash when there is one; with the splash turned off
it is the only thing on screen, centered.
"""

import time

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.theme.manager import THEME, safe_repaint
from utils.i18n import I18N, safe_retranslate, t

_GAP = 8  # px between the splash and the card
_DEFAULT_WIDTH = 460


class SlowStartNotice(QWidget):
    waitRequested = pyqtSignal()
    stopRequested = pyqtSignal()

    def __init__(self, started_at: float, parent=None):
        super().__init__(parent)
        self._started_at = started_at

        # Owned by the splash (parent) it stays above it and comes back with it
        # from the taskbar, sharing its taskbar button. Without a splash it is
        # a window of its own, with its own button.
        kind = Qt.WindowType.Dialog if parent is not None else Qt.WindowType.Window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | kind)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("ComfyLauncher")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame(self)
        self.card.setObjectName("slow_start_card")
        outer.addWidget(self.card)

        root = QVBoxLayout(self.card)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(8)

        head = QHBoxLayout()
        self.title = QLabel()
        self.title.setObjectName("title")
        self.elapsed = QLabel()
        self.elapsed.setObjectName("elapsed")
        head.addWidget(self.title, 1)
        head.addWidget(self.elapsed)
        root.addLayout(head)

        self.body = QLabel()
        self.body.setObjectName("body")
        self.body.setWordWrap(True)
        root.addWidget(self.body)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addStretch()
        self.btn_stop = QPushButton()
        self.btn_stop.setObjectName("secondary")
        self.btn_wait = QPushButton()
        self.btn_wait.setObjectName("primary")
        buttons.addWidget(self.btn_stop)
        buttons.addWidget(self.btn_wait)
        root.addLayout(buttons)

        self.btn_wait.clicked.connect(self._on_wait)  # type: ignore
        self.btn_stop.clicked.connect(self._on_stop)  # type: ignore

        self._tick = QTimer(self)
        self._tick.setInterval(1000)
        self._tick.timeout.connect(self._update_elapsed)  # type: ignore
        self._tick.start()
        self._update_elapsed()

        self._apply_theme()
        THEME.themeChanged.connect(self._apply_theme)
        self._retranslate()
        I18N.languageChanged.connect(self._retranslate)

    @safe_retranslate
    def _retranslate(self, *args):
        self.title.setText(t("slow_start.title"))
        self.body.setText(t("slow_start.text"))
        self.btn_stop.setText(t("slow_start.stop"))
        self.btn_wait.setText(t("slow_start.wait"))

    # ── placement ────────────────────────────────────────────────────────

    def popup(self, anchor: QWidget | None):
        """Place, show and draw attention: the user may be in another window."""
        self.place(anchor)
        self.show()
        self.btn_wait.setFocus()
        # Windows won't let a background app jump in front; flashing its
        # taskbar button until the user looks is the accepted way to call.
        QApplication.alert(anchor if anchor is not None else self)

    def place(self, anchor: QWidget | None):
        """Glue the card under ``anchor`` (the splash), or center it on screen."""
        screen = (anchor.screen() if anchor else None) or self.screen()
        area = screen.availableGeometry()

        if anchor is not None and anchor.isVisible():
            box = anchor.frameGeometry()
            self.setFixedWidth(box.width())
            self.adjustSize()
            y = box.bottom() + 1 + _GAP
            if y + self.height() > area.bottom():  # no room below: go above
                y = box.top() - _GAP - self.height()
            self.move(box.left(), y)
        else:
            self.setFixedWidth(min(_DEFAULT_WIDTH, area.width()))
            self.adjustSize()
            geo = self.frameGeometry()
            geo.moveCenter(area.center())
            self.move(geo.topLeft())

    # ── behaviour ────────────────────────────────────────────────────────

    def _update_elapsed(self):
        seconds = int(time.monotonic() - self._started_at)
        self.elapsed.setText(f"{seconds // 60}:{seconds % 60:02d}")

    def _on_wait(self):
        self.waitRequested.emit()  # type: ignore
        self.close()

    def _on_stop(self):
        self.stopRequested.emit()  # type: ignore
        self.close()

    def keyPressEvent(self, event):
        # Enter answers with the safe default; Esc just dismisses, same as Wait.
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape):
            self._on_wait()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self._tick.stop()
        super().closeEvent(event)

    @safe_repaint
    def _apply_theme(self, *args):
        c = THEME.colors
        self.card.setStyleSheet(
            f"""
            QFrame#slow_start_card {{
                background-color: {c['popup_bg']};
                border: 1px solid {c['border_color']};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
            }}
            QLabel#title {{
                color: {c['text_primary']};
                font-size: 15px;
                font-weight: 600;
            }}
            QLabel#elapsed {{
                color: {c['text_secondary']};
                font-size: 13px;
            }}
            QLabel#body {{
                color: {c['popup_text']};
                font-size: 13px;
            }}
            QPushButton {{
                border-radius: 6px;
                padding: 0 16px;
                min-width: 96px;
                min-height: 32px;
                font-size: 13px;
            }}
            QPushButton#secondary {{
                background-color: transparent;
                color: {c['text_primary']};
                border: 1px solid {c['border_color']};
            }}
            QPushButton#secondary:hover {{
                border-color: {c['accent']};
            }}
            QPushButton#primary {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
                border: 1px solid {c['accent']};
            }}
            QPushButton#primary:hover {{
                background-color: {c['accent_hover']};
                border-color: {c['accent_hover']};
            }}
        """
        )
