""""Open Release Page" must actually stand out once an update is found.

The emphasis used to be appended after the last closing brace of the button's
stylesheet, outside any rule, and Qt silently dropped it.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtGui import QPalette  # noqa: E402
from PyQt6.QtWidgets import QWidget  # noqa: E402

import ui.settings.page_about as page_about  # noqa: E402
from ui.theme.manager import THEME  # noqa: E402


@pytest.fixture
def page(qapp, monkeypatch):
    # the logo's looping video decoder can kill a headless run (exit 127)
    monkeypatch.setattr(page_about, "AnimatedLogo", QWidget)
    p = page_about.AboutSettingsPage()
    yield p
    p.deleteLater()


def test_release_page_button_is_bold_in_the_primary_text_color(page):
    btn = page.update_btn
    page._on_manual_update_found("9.9.9", "https://example.invalid/release")
    btn.ensurePolished()
    assert btn.text() == "Open Release Page"
    assert btn.font().bold() is True
    text_color = btn.palette().color(QPalette.ColorRole.ButtonText).name()
    assert text_color == THEME.colors["text_primary"].lower()


def test_emphasis_follows_a_theme_change_and_is_never_stacked(page, monkeypatch):
    btn = page.update_btn
    page._on_manual_update_found("9.9.9", "https://example.invalid/release")
    page._on_manual_update_found("9.9.9", "https://example.invalid/release")
    assert btn.styleSheet().count("font-weight: bold") == 1

    colors = dict(THEME.colors, text_primary="#123456", border_color="#654321")
    monkeypatch.setattr(THEME, "_colors", colors)
    page._apply_theme()
    assert "color: #123456;" in btn.styleSheet()
    assert "#654321" in page.report_btn.styleSheet()
    assert "font-weight: bold" not in page.report_btn.styleSheet()
