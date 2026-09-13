"""Grouped ComfyUI startup-flags picker (Stage 5).

Opens from the Setup Window's "Add" button. Shows the curated catalog
(assets/data/flags.json) as grouped, clickable chips and syncs the result back
to the caller's flags text field live: clicking a chip inserts the flag,
clicking again removes it. Value/choice flags carry an inline editor pre-filled
with a sensible default so no dangling ``--port`` can be produced. The flags
string stays the single source of truth: it is parsed on open and rebuilt on
every change, preserving unknown/manual tokens (e.g. ``--windows-standalone-build``)
in place.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QFrame,
    QScrollArea,
    QWidget,
    QLayout,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QColor, QIcon

from config import ICON_PATH
from ui.theme.manager import THEME
from utils.flags_catalog import load_flags_catalog, iter_flags


# Quick presets: additively merged into the current selection (dedupe +
# exclusive-group aware). Each is a list of flags to switch on.
QUICK_PRESETS = [
    ("CPU", ["--cpu"]),
    ("Low VRAM", ["--lowvram"]),
    ("Fast", ["--fast"]),
]


class FlowLayout(QLayout):
    """A left-to-right wrapping layout (chips flow onto new rows as needed).

    Hidden widgets are skipped so inline editors reserve no space until shown.
    """

    def __init__(self, parent=None, hspacing=8, vspacing=8):
        super().__init__(parent)
        self._items: list = []
        self._hspace = hspacing
        self._vspace = vspacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        right = rect.right() - m.right()
        line_h = 0
        for item in self._items:
            w = item.widget()
            if w is not None and not w.isVisible():
                continue
            hint = item.sizeHint()
            iw, ih = hint.width(), hint.height()
            if x + iw > right and line_h > 0:
                x = rect.x() + m.left()
                y += line_h + self._vspace
                line_h = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += iw + self._hspace
            line_h = max(line_h, ih)
        return y + line_h - rect.y() + m.bottom()


class FlagsPickerDialog(QDialog):
    """Modal flags picker. Emits ``flagsChanged`` with the rebuilt flag string."""

    flagsChanged = pyqtSignal(str)

    WINDOW_WIDTH = 640
    WINDOW_HEIGHT = 600
    BORDER_RADIUS = 9

    def __init__(self, parent=None, flags_text: str = ""):
        super().__init__(parent)

        self.catalog = load_flags_catalog()
        self.by_flag = {f["flag"]: f for f in iter_flags(self.catalog)}

        # ordered list of {"kind": "flag"|"raw", ...}; single source of truth
        self.entries: list[dict] = self._parse(flags_text)

        # widget registries, filled while building the UI
        self._chips: dict[str, QPushButton] = {}
        self._editors: dict[str, QWidget] = {}
        self._flows: list[FlowLayout] = []
        self._loading = False

        self.setWindowTitle("Startup flags")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setModal(True)
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._build_ui()
        self._refresh()

    # ── parsing / building the flag string ──────────────────────────────

    def _parse(self, text: str) -> list[dict]:
        tokens = text.split()
        entries: list[dict] = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            spec = self.by_flag.get(tok)
            if spec and spec.get("type") in ("value", "choice"):
                value = ""
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    value = tokens[i + 1]
                    i += 1
                entries.append({"kind": "flag", "flag": tok, "value": value})
            elif spec and spec.get("type") == "bool":
                entries.append({"kind": "flag", "flag": tok, "value": None})
            else:
                entries.append({"kind": "raw", "token": tok})
            i += 1
        return entries

    def _build_string(self) -> str:
        parts: list[str] = []
        for e in self.entries:
            if e["kind"] == "raw":
                parts.append(e["token"])
                continue
            flag = e["flag"]
            value = e.get("value")
            parts.append(flag)
            if value not in (None, ""):
                parts.append(str(value))
        return " ".join(parts)

    # ── model helpers ────────────────────────────────────────────────────

    def _is_active(self, flag: str) -> bool:
        return any(e["kind"] == "flag" and e["flag"] == flag for e in self.entries)

    def _value_of(self, flag: str) -> str:
        for e in self.entries:
            if e["kind"] == "flag" and e["flag"] == flag:
                return "" if e.get("value") in (None,) else str(e["value"])
        return ""

    def _remove(self, flag: str) -> None:
        self.entries = [
            e for e in self.entries if not (e["kind"] == "flag" and e["flag"] == flag)
        ]

    def _default_value(self, spec: dict) -> str:
        default = spec.get("default")
        if default is None and spec.get("type") == "choice":
            choices = spec.get("choices") or []
            return str(choices[0]) if choices else ""
        return "" if default is None else str(default)

    def _add(self, flag: str) -> None:
        spec = self.by_flag.get(flag)
        if spec is None:
            return
        # exclusive group: drop siblings first
        group = spec.get("exclusive_group")
        if group:
            for other, ospec in self.by_flag.items():
                if other != flag and ospec.get("exclusive_group") == group:
                    self._remove(other)
        if self._is_active(flag):
            return
        if spec.get("type") in ("value", "choice"):
            self.entries.append(
                {"kind": "flag", "flag": flag, "value": self._default_value(spec)}
            )
        else:
            self.entries.append({"kind": "flag", "flag": flag, "value": None})

    # ── event handlers ───────────────────────────────────────────────────

    def _toggle(self, flag: str) -> None:
        if self._is_active(flag):
            self._remove(flag)
        else:
            self._add(flag)
        self._refresh()
        self._emit()

    def _on_value_edited(self, flag: str, value) -> None:
        if self._loading:
            return
        for e in self.entries:
            if e["kind"] == "flag" and e["flag"] == flag:
                e["value"] = str(value).strip()
                break
        self._emit()

    def _apply_preset(self, flags: list[str]) -> None:
        for flag in flags:
            self._add(flag)
        self._refresh()
        self._emit()

    def _emit(self) -> None:
        self.flagsChanged.emit(self._build_string())

    # ── UI refresh ───────────────────────────────────────────────────────

    def _refresh(self) -> None:
        self._loading = True
        for flag, chip in self._chips.items():
            active = self._is_active(flag)
            chip.setChecked(active)
            editor = self._editors.get(flag)
            if editor is not None:
                editor.setVisible(active)
                if active:
                    self._set_editor_value(flag, editor, self._value_of(flag))
        self._loading = False
        for fl in self._flows:
            fl.invalidate()

    def _set_editor_value(self, flag: str, editor: QWidget, value: str) -> None:
        if isinstance(editor, QComboBox):
            idx = editor.findText(value)
            editor.setCurrentIndex(idx if idx >= 0 else 0)
        elif isinstance(editor, QLineEdit):
            editor.setText(value)

    # ── UI construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(15, 15, 15, 15)
        outer.setSpacing(0)

        frame = QFrame(self)
        frame.setObjectName("flags_main_frame")
        frame.setStyleSheet(
            f"""
            QFrame#flags_main_frame {{
                background-color: {THEME.colors['bg_header']};
                border-radius: {self.BORDER_RADIUS}px;
            }}
            """
        )
        outer.addWidget(frame)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 180))
        frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(14)

        title = QLabel("Startup flags")
        title.setStyleSheet(
            f"QLabel {{ font-size: 16px; font-weight: 600; "
            f"color: {THEME.colors['text_primary']}; }}"
        )
        layout.addWidget(title)

        # quick presets
        presets_row = QHBoxLayout()
        presets_row.setSpacing(8)
        presets_label = QLabel("Presets:")
        presets_label.setStyleSheet(
            f"QLabel {{ font-size: 12px; color: {THEME.colors['text_secondary']}; }}"
        )
        presets_row.addWidget(presets_label)
        for name, flags in QUICK_PRESETS:
            btn = QPushButton(name)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._preset_style())
            btn.clicked.connect(lambda _=False, f=flags: self._apply_preset(f))  # type: ignore
            presets_row.addWidget(btn)
        presets_row.addStretch(1)
        layout.addLayout(presets_row)

        # scrollable groups
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 6, 0)
        content_layout.setSpacing(16)

        if not self.catalog.get("groups"):
            empty = QLabel("No flags catalog found. You can still type flags manually.")
            empty.setStyleSheet(
                f"QLabel {{ color: {THEME.colors['text_secondary']}; }}"
            )
            empty.setWordWrap(True)
            content_layout.addWidget(empty)

        for group in self.catalog.get("groups", []):
            content_layout.addWidget(self._build_group(group))

        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # footer
        footer = QHBoxLayout()
        footer.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(110, 34)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(self._preset_style())
        close_btn.clicked.connect(self.accept)  # type: ignore
        footer.addWidget(close_btn)
        layout.addLayout(footer)

    def _build_group(self, group: dict) -> QWidget:
        box = QWidget()
        box.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(box)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(8)

        header = QLabel(group.get("title", group.get("id", "")))
        header.setStyleSheet(
            f"QLabel {{ font-size: 12px; font-weight: 600; "
            f"color: {THEME.colors['text_secondary']}; }}"
        )
        vbox.addWidget(header)

        flow = FlowLayout(hspacing=8, vspacing=8)
        self._flows.append(flow)
        for flag in group.get("flags", []):
            self._build_flag_widgets(flag, flow)
        flow_host = QWidget()
        flow_host.setStyleSheet("background: transparent;")
        flow_host.setLayout(flow)
        vbox.addWidget(flow_host)
        return box

    def _build_flag_widgets(self, spec: dict, flow: FlowLayout) -> None:
        flag = spec["flag"]
        chip = QPushButton(flag)
        chip.setCheckable(True)
        chip.setCursor(Qt.CursorShape.PointingHandCursor)
        chip.setToolTip(spec.get("description", ""))
        chip.setFixedHeight(26)
        chip.setStyleSheet(self._chip_style())
        chip.clicked.connect(lambda _=False, f=flag: self._toggle(f))  # type: ignore
        self._chips[flag] = chip
        flow.addWidget(chip)

        ftype = spec.get("type")
        if ftype == "choice":
            combo = QComboBox()
            combo.addItems([str(c) for c in (spec.get("choices") or [])])
            combo.setFixedHeight(26)
            combo.setStyleSheet(self._editor_style())
            combo.setVisible(False)
            combo.currentTextChanged.connect(  # type: ignore
                lambda text, f=flag: self._on_value_edited(f, text)
            )
            self._editors[flag] = combo
            flow.addWidget(combo)
        elif ftype == "value":
            edit = QLineEdit()
            edit.setPlaceholderText(self._default_value(spec))
            edit.setFixedSize(90, 26)
            edit.setStyleSheet(self._editor_style())
            edit.setVisible(False)
            edit.textChanged.connect(  # type: ignore
                lambda text, f=flag: self._on_value_edited(f, text)
            )
            self._editors[flag] = edit
            flow.addWidget(edit)

    # ── styles ───────────────────────────────────────────────────────────

    def _chip_style(self) -> str:
        c = THEME.colors
        return f"""
            QPushButton {{
                background-color: {c['bg_input']};
                color: {c['text_secondary']};
                border: 1px solid {c['border_color']};
                border-radius: 13px;
                padding: 3px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
            }}
            QPushButton:checked {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
                border-color: {c['accent']};
            }}
        """

    def _editor_style(self) -> str:
        c = THEME.colors
        return f"""
            QLineEdit, QComboBox {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1px solid {c['border_color']};
                border-radius: 6px;
                padding-left: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1px solid {c['border_color']};
                selection-background-color: {c['accent']};
                selection-color: {c['text_inverse']};
                outline: none;
            }}
        """

    def _preset_style(self) -> str:
        c = THEME.colors
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {c['text_secondary']};
                border: 1px solid {c['border_color']};
                border-radius: 6px;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
                border-color: {c['accent']};
            }}
        """
