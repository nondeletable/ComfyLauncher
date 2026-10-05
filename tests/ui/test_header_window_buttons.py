"""The min / max / close buttons must get a real hover color.

Their stylesheet used to be a plain string, so the literal text
``{THEME.colors['bg_hover']}`` went into the QSS and the hover rule did nothing.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtWidgets import QMainWindow  # noqa: E402

from ui.header import HeaderBar  # noqa: E402
from ui.theme.manager import THEME  # noqa: E402


@pytest.fixture
def header(qapp):
    win = QMainWindow()
    yield HeaderBar(win)
    win.deleteLater()


def window_buttons(header):
    return [header.btn_min, header.btn_max, header.btn_close]


def test_hover_uses_the_theme_color(header):
    for btn in window_buttons(header):
        qss = btn.styleSheet()
        assert "{THEME" not in qss
        assert "{{" not in qss
        assert f"QPushButton:hover {{ background: {THEME.colors['bg_hover']}; }}" in qss


def test_hover_follows_a_theme_change(header, monkeypatch):
    monkeypatch.setattr(THEME, "_colors", dict(THEME.colors, bg_hover="#123456"))
    header._apply_theme()
    for btn in window_buttons(header):
        assert "background: #123456;" in btn.styleSheet()
