"""Bug report window: preview what is sent, then pick where it goes.

The report is collected and scrubbed when the window opens (utils/bug_report).
The user sees the exact text in an editable box, can drop the log, console or
config sections and add a comment. Nothing leaves the machine on its own: every
route is a button press, and the GitHub and Discord routes only save the file
and open a page - the user attaches the file there.
"""

from __future__ import annotations

import os
import webbrowser

from PyQt6.QtCore import Qt
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
from utils.logger import log_event
from utils.platform_paths import reveal_in_file_manager

SECTION_LABELS = {
    br.SECTION_LOG: "Launcher log",
    br.SECTION_CONSOLE: "ComfyUI console",
    br.SECTION_CONFIG: "Settings",
}

ROUTES = (
    (
        "github",
        "GitHub Issue",
        "Public. Needs a GitHub account. You attach the file yourself.",
    ),
    (
        "automatic",
        "Automatic",
        "Private. One click, no account. Not available yet - the report server "
        "is still being built.",
    ),
    (
        "discord",
        "Discord",
        "Talk to us directly. Needs a Discord account. You attach the file yourself.",
    ),
)


class BugReportDialog(QDialog):
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
        self.error_text = error_text
        self.report = report or br.collect_report(source, error_text, traceback_text)
        self.saved_path: str | None = None
        self._checks: dict[str, QCheckBox] = {}
        self._drag_pos = None

        title = (
            "Comfy Launcher hit an unexpected error"
            if source == "exception"
            else "Report a problem"
        )
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

        intro = QLabel(
            "Nothing is sent until you choose where it goes. Below is the exact "
            "text of the report - personal folder, user and computer names are "
            "already hidden. You can edit or delete anything in it."
        )
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.comment = QPlainTextEdit()
        self.comment.setPlaceholderText(
            "What were you doing, and what did you expect to happen? (optional)"
        )
        self.comment.setFixedHeight(60)
        self.comment.textChanged.connect(self._rebuild_preview)  # type: ignore
        layout.addWidget(self.comment)

        checks = QHBoxLayout()
        checks.setSpacing(16)
        include_label = QLabel("Include:")
        include_label.setObjectName("muted")
        checks.addWidget(include_label)
        for name in br.OPTIONAL_SECTIONS:
            box = QCheckBox(SECTION_LABELS[name])
            box.setChecked(True)
            if name == br.SECTION_CONSOLE and not self.report.sections.get(name):
                box.setText(f"{SECTION_LABELS[name]} (empty)")
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

        note = QLabel(
            "Changing the comment or the boxes above rebuilds the text and drops "
            "your edits in it."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addSpacing(4)
        send_label = QLabel("Send it")
        send_label.setObjectName("section")
        layout.addWidget(send_label)

        self.route_buttons: dict[str, QPushButton] = {}
        for key, name, caption in ROUTES:
            row = QHBoxLayout()
            row.setSpacing(12)
            btn = QPushButton(name)
            btn.setFixedSize(140, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cap = QLabel(caption)
            cap.setObjectName("muted")
            cap.setWordWrap(True)
            if key == "automatic":
                btn.setEnabled(False)
                btn.setToolTip("Coming later, together with the report server.")
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
        self.save_btn = QPushButton("Save report only")
        self.save_btn.setFixedHeight(32)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(lambda: self._send("save"))  # type: ignore
        footer.addWidget(self.save_btn)
        footer.addStretch(1)
        close_btn = QPushButton("Close")
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
        return self.preview.toPlainText()

    def _send(self, route: str) -> None:
        text = self.report_text()
        try:
            path = br.save_report(text)
        except OSError as e:
            log_event(f"❌ Bug report could not be saved: {e}")
            MessageBox.error(self, "Could not save the report", str(e))
            return
        self.saved_path = path
        log_event(f"📝 Bug report saved ({route})")

        if route == "github":
            name = os.path.basename(path)
            url = br.github_issue_url(
                br.issue_title(self.error_text), br.issue_body(text, name)
            )
            webbrowser.open(url)
            reveal_in_file_manager(path)
            MessageBox.info(
                self,
                "Almost done",
                f"The report is saved to:\n{path}\n\n"
                "Drag the file into the issue, then press Submit.",
            )
        elif route == "discord":
            webbrowser.open(br.DISCORD_INVITE)
            reveal_in_file_manager(path)
            MessageBox.info(
                self,
                "Almost done",
                f"The report is saved to:\n{path}\n\n"
                "Post the file in the #bug-report channel of our Discord server.",
            )
        else:
            reveal_in_file_manager(path)
        self.accept()

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
    """Collect a report and show the window. Logs instead of raising."""
    try:
        BugReportDialog(source, error_text, traceback_text, parent).exec()
    except Exception as e:
        log_event(f"❌ Bug report window failed: {type(e).__name__}: {e}")
