"""ThemedComboBox: the app's drop-down, styled through the theme, not the OS."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtWidgets import QListView  # noqa: E402

from ui.theme.manager import THEME  # noqa: E402
from ui.widgets.combo_box import ThemedComboBox  # noqa: E402


def test_popup_uses_a_list_view_so_item_rules_apply(qapp):
    combo = ThemedComboBox()
    # The default delegate ignores ::item rules; hover would fall back to the
    # native highlight color.
    assert isinstance(combo.view(), QListView)
    assert "::item:selected" in combo.styleSheet()


def test_popup_window_is_frameless_and_transparent(qapp):
    combo = ThemedComboBox()
    popup = combo.view().window()
    assert popup.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert popup.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_highlight_follows_the_theme_accent(qapp):
    combo = ThemedComboBox()
    assert THEME.colors["accent"] in combo.styleSheet()


def test_font_size_is_configurable(qapp):
    assert "font-size: 12px" in ThemedComboBox(font_size=12).styleSheet()


def test_chevron_paints_without_errors_open_and_closed(qapp):
    combo = ThemedComboBox()
    combo.addItems(["a", "b"])
    combo.resize(160, 28)
    combo.grab()
    combo._popup_open = True
    combo.grab()
