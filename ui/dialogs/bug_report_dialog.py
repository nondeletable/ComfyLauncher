"""Bug report window: preview what is sent, then pick where it goes.

The report is collected and scrubbed when the window opens (utils/bug_report).
The user sees the exact text in an editable box, can drop the log, console or
config sections and add a comment. Nothing leaves the machine on its own: every
route is a button press, and the GitHub and Discord routes only save the file
and open a page - the user attaches the file there.

The window speaks the interface language, the report itself stays English (we
read and search it). The window is modal, so the language cannot change while
it is open: texts are set once, there is no _retranslate.
"""

from __future__ import annotations

import os
import webbrowser

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config import ICON_PATH
from ui.dialogs.messagebox import MessageBox
from ui.theme.manager import THEME
from utils import bug_report as br
from utils.i18n import t
from utils.logger import log_event
from utils.platform_paths import reveal_in_file_manager

# Section -> i18n key of its checkbox label.
SECTION_LABELS = {
    br.SECTION_LOG: "report.section.log",
    br.SECTION_CONSOLE: "report.section.console",
    br.SECTION_CONFIG: "report.section.config",
}

# Route ids; the button label and caption are report.route.<id>[.caption].
ROUTES = ("github", "automatic", "discord")


class BugReportDialog(QDialog):
    # The report window on screen, if any - there is never a second one.
    active: "BugReportDialog | None" = None

    WINDOW_WIDTH = 760
    WINDOW_HEIGHT = 720
    BORDER_RADIUS = 9

    def __init__(
        self,
        source: str = "manual",
        error_text: str = "",
        traceback_text: str = "",
        parent=None,
        report: br.BugReport | None = None,
    ):
        super().__init__(parent)
        self.source = source
        self.report = report or br.collect_report(source, error_text, traceback_text)
        self.saved_path: str | None = None
        self._checks: dict[str, QCheckBox] = {}
        self._drag_pos = None

        title = t("report.title.exception" if source == "exception" else "about.report")
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setModal(True)
        self.resize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._build_ui(title)
        self._rebuild_preview()

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self, title_text: str) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(15, 15, 15, 15)

        frame = QFrame(self)
        frame.setObjectName("bug_report_frame")
        frame.setStyleSheet(self._style())
        outer.addWidget(frame)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 180))
        frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(10)

        title = QLabel(title_text)
        title.setObjectName("title")
        layout.addWidget(title)

        intro = QLabel(t("report.intro"))
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.comment = QPlainTextEdit()
        self.comment.setPlaceholderText(t("report.comment"))
        self.comment.setFixedHeight(60)
        # Re-rendering ~130 KB of text on every keystroke makes typing lag.
        self._rebuild_timer = QTimer(self)
        self._rebuild_timer.setSingleShot(True)
        self._rebuild_timer.setInterval(300)
        self._rebuild_timer.timeout.connect(self._rebuild_preview)  # type: ignore
        self.comment.textChanged.connect(self._rebuild_timer.start)  # type: ignore
        layout.addWidget(self.comment)

        checks = QHBoxLayout()
        checks.setSpacing(16)
        include_label = QLabel(t("report.include"))
        include_label.setObjectName("muted")
        checks.addWidget(include_label)
        for name in br.OPTIONAL_SECTIONS:
            box = QCheckBox(t(SECTION_LABELS[name]))
            box.setChecked(True)
            if name == br.SECTION_CONSOLE and not self.report.sections.get(name):
                box.setText(t("report.section.empty", section=t(SECTION_LABELS[name])))
            box.toggled.connect(self._rebuild_preview)  # type: ignore
            self._checks[name] = box
            checks.addWidget(box)
        checks.addStretch(1)
        layout.addLayout(checks)

        self.preview = QPlainTextEdit()
        self.preview.setObjectName("preview")
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSize(9)
        self.preview.setFont(mono)
        self.preview.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.preview, 1)

        note = QLabel(t("report.note"))
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addSpacing(4)
        send_label = QLabel(t("report.send"))
        send_label.setObjectName("section")
        layout.addWidget(send_label)

        self.route_buttons: dict[str, QPushButton] = {}
        for key in ROUTES:
            row = QHBoxLayout()
            row.setSpacing(12)
            btn = QPushButton(t(f"report.route.{key}"))
            btn.setFixedSize(140, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cap = QLabel(t(f"report.route.{key}.caption"))
            cap.setObjectName("muted")
            cap.setWordWrap(True)
            if key == "automatic":
                btn.setEnabled(False)
                btn.setToolTip(t("report.route.automatic.tip"))
            else:
                btn.clicked.connect(  # type: ignore
                    lambda _=False, k=key: self._send(k)
                )
            self.route_buttons[key] = btn
            row.addWidget(btn)
            row.addWidget(cap, 1)
            layout.addLayout(row)

        layout.addSpacing(6)
        footer = QHBoxLayout()
        self.save_btn = QPushButton(t("report.save_only"))
        self.save_btn.setFixedHeight(32)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(lambda: self._send("save"))  # type: ignore
        footer.addWidget(self.save_btn)
        footer.addStretch(1)
        close_btn = QPushButton(t("common.close"))
        close_btn.setFixedSize(110, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)  # type: ignore
        footer.addWidget(close_btn)
        layout.addLayout(footer)

    def _style(self) -> str:
        c = THEME.colors
        return f"""
            QFrame#bug_report_frame {{
                background-color: {c['bg_header']};
                border-radius: {self.BORDER_RADIUS}px;
            }}
            QLabel {{ background: transparent; color: {c['text_primary']}; }}
            QLabel#title {{ font-size: 16px; font-weight: 600; }}
            QLabel#section {{ font-size: 13px; font-weight: 600; }}
            QLabel#muted {{ font-size: 12px; color: {c['text_secondary']}; }}
            QCheckBox {{ background: transparent; color: {c['text_primary']}; }}
            QPlainTextEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1px solid {c['border_color']};
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton {{
                background-color: transparent;
                color: {c['text_primary']};
                border: 1px solid {c['border_color']};
                border-radius: 6px;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
                border-color: {c['accent']};
            }}
            QPushButton:disabled {{
                color: {c['text_secondary']};
                border-style: dashed;
            }}
        """

    # ── Behaviour ─────────────────────────────────────────────────────────

    def included_sections(self) -> set[str]:
        return {name for name, box in self._checks.items() if box.isChecked()}

    def _rebuild_preview(self, *args) -> None:
        if not hasattr(self, "preview"):
            return
        self.preview.setPlainText(
            br.render_report(
                self.report,
                include=self.included_sections(),
                comment=self.comment.toPlainText(),
            )
        )

    def report_text(self) -> str:
        """What the user sees is what is sent, edits included."""
        if self._rebuild_timer.isActive():
            self._rebuild_timer.stop()
            self._rebuild_preview()
        return self.preview.toPlainText()

    def _send(self, route: str) -> None:
        text = self.report_text()
        try:
            path = br.save_report(text)
        except OSError as e:
            log_event(f"❌ Bug report could not be saved: {e}")
            MessageBox.error(self, t("report.save_failed"), str(e))
            return
        self.saved_path = path
        log_event(f"📝 Bug report saved ({route})")

        if route == "github":
            name = os.path.basename(path)
            url = br.github_issue_url(br.issue_title(text), br.issue_body(text, name))
            webbrowser.open(url)
            reveal_in_file_manager(path)
            MessageBox.info(
                self, t("report.done.title"), t("report.done.github", path=path)
            )
        elif route == "discord":
            webbrowser.open(br.DISCORD_INVITE)
            reveal_in_file_manager(path)
            MessageBox.info(
                self, t("report.done.title"), t("report.done.discord", path=path)
            )
        else:
            reveal_in_file_manager(path)
        self.accept()

    def exec(self) -> int:
        BugReportDialog.active = self
        try:
            return super().exec()
        finally:
            BugReportDialog.active = None

    # ── Frameless window drag ────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


def open_bug_report(
    parent: QWidget | None = None,
    source: str = "manual",
    error_text: str = "",
    traceback_text: str = "",
) -> None:
    """Collect a report and show the window. Logs instead of raising.

    If a report window is already open it is brought forward instead.
    """
    active = BugReportDialog.active
    if active is not None:
        active.raise_()
        active.activateWindow()
        return
    try:
        BugReportDialog(source, error_text, traceback_text, parent).exec()
    except Exception as e:
        log_event(f"❌ Bug report window failed: {type(e).__name__}: {e}")
