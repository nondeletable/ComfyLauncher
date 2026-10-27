"""The header shows the server state, not a ready-made string.

The window only says which state ComfyUI is in; the header picks the text and
the color, so a theme change keeps the current state instead of painting it as
"online", and the pill style survives every update.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtWidgets import QMainWindow  # noqa: E402

from ui.header import STATUSES, HeaderBar  # noqa: E402
from ui.theme.manager import THEME  # noqa: E402
from utils.i18n import I18N, t  # noqa: E402


@pytest.fixture
def header(qapp):
    win = QMainWindow()
    yield HeaderBar(win)
    win.deleteLater()


@pytest.mark.parametrize("status", sorted(STATUSES))
def test_status_sets_text_and_color(header, status):
    icon, key, color = STATUSES[status]
    header.set_status(status)
    assert header.status_label.text() == f"{icon} {t(key)}"
    qss = header.status_label.styleSheet()
    assert f"color: {THEME.colors[color]};" in qss
    assert "border-radius" in qss  # the pill, not bare text


def test_theme_change_keeps_the_state(header, monkeypatch):
    header.set_status("offline")
    monkeypatch.setattr(THEME, "_colors", dict(THEME.colors, error="#123456"))
    header._apply_theme()
    assert t("header.status.offline") in header.status_label.text()
    assert "color: #123456;" in header.status_label.styleSheet()


def test_language_change_keeps_the_state(header):
    header.set_status("restarting")
    try:
        I18N.set_language("de")
        assert header.status_label.text() == "🟠 Neustart…"
    finally:
        I18N.set_language("en")
