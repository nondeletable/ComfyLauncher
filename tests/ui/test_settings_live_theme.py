"""Settings repaints in place when the theme changes.

Regression: the menu, page area, footer and most pages built their styles once,
from the theme active at construction, and kept them after THEME.switch. Only
the window frame, Color Themes and Logs followed the switch.
"""

import gc
import os
import re
import weakref

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6 import sip  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402
from PyQt6.QtWidgets import QFrame, QWidget  # noqa: E402

import ui.settings.page_build as page_build  # noqa: E402
import ui.settings.page_logs as page_logs  # noqa: E402
from ui.settings.page_about import AboutSettingsPage  # noqa: E402
from ui.settings.page_behavior import BehaviorSettingsPage  # noqa: E402
from ui.settings.page_colortheme import ColorThemesPage  # noqa: E402
from ui.settings.page_startapp import StartAppSettingsPage  # noqa: E402
from ui.settings.settings_window import SettingsWindow  # noqa: E402
from ui.theme.manager import THEME, THEMES  # noqa: E402

PAGE_CLASSES = (
    page_build.BuildSettingsPage,
    StartAppSettingsPage,
    BehaviorSettingsPage,
    ColorThemesPage,
    page_logs.LogsSettingsPage,
    AboutSettingsPage,
)
# dracula shares no color with dark, so any dark color left over is stale.
OLD, NEW = "dark", "dracula"
# Colors written into the styles literally, the same in every theme.
FIXED = {"#fff", "#555555"}
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def _colors(*widgets) -> set[str]:
    return {m.lower() for w in widgets for m in HEX.findall(w.styleSheet())}


def _theme(name) -> set[str]:
    return {v.lower() for v in THEMES[name].values() if isinstance(v, str)}


@pytest.fixture
def window(qapp):
    before = THEME.name
    THEME.switch(OLD)
    w = SettingsWindow(None)
    yield w
    if not sip.isdeleted(w):
        w._dirty_pages = lambda: []
        w.close()
    THEME.switch(before)


def test_the_window_parts_take_the_new_theme(window):
    parts = (
        window,
        window.findChild(QFrame, "settings_main_frame"),
        window.menu,
        window.pages,
        window.footer,
        window.btn_apply,
        window.btn_close,
    )
    assert _colors(*parts) & _theme(OLD)

    THEME.switch(NEW)

    colors = _colors(*parts)
    assert colors <= _theme(NEW) | FIXED
    assert THEMES[NEW]["bg_menu"].lower() in _colors(window.menu, window.footer)


@pytest.fixture
def one_build(monkeypatch):
    """Give Builds a row to paint, without touching the config file."""
    cfg = {
        "builds": [{"id": "1", "name": "Comfy", "path": "C:/ComfyUI"}],
        "last_used_build_id": "1",
    }
    monkeypatch.setattr(page_build, "load_user_config", lambda: dict(cfg))


@pytest.fixture
def icon_colors(monkeypatch):
    """Record the color of every icon the pages paint."""
    painted = []
    real = page_build.colorize_svg

    def spy(path, color, *args, **kwargs):
        painted.append(color)
        return real(path, color, *args, **kwargs)

    for module in (page_build, page_logs):
        monkeypatch.setattr(module, "colorize_svg", spy)
    return painted


def _page_colors(page) -> set[str]:
    # Theme cards preview every theme on purpose. The About footer buttons are
    # restyled on a theme change by PR #73.
    skip = list(getattr(page, "cards", {}).values())
    if isinstance(page, AboutSettingsPage):
        skip += [page.update_btn, page.report_btn]
    widgets = [page] + [
        w
        for w in page.findChildren(QWidget)
        if not any(s is w or s.isAncestorOf(w) for s in skip)
    ]
    return _colors(*widgets)


def test_every_built_page_takes_the_new_theme(one_build, icon_colors, window):
    for row in range(window.pages.count()):
        window.menu.setCurrentRow(row)
    pages = [window.pages.widget(i) for i in range(window.pages.count())]
    assert window.findChildren(QFrame, "BuildRow")
    for page in pages:
        assert _page_colors(page) & _theme(OLD), type(page).__name__

    icon_colors.clear()
    THEME.switch(NEW)

    for page in pages:
        colors = _page_colors(page)
        assert colors <= _theme(NEW) | FIXED, (type(page).__name__, colors)
        assert colors & _theme(NEW), type(page).__name__
    assert window.findChildren(QFrame, "BuildRow")
    assert set(icon_colors) == {THEMES[NEW]["icon_color_window"]}


def _settle():
    """Let deleted widgets and their PyQt slot proxies actually go.

    A closed window is deleted on the event loop and wrappers caught in
    reference cycles by the gc. PyQt disables the proxy of a slot whose object
    is gone, and it drops the connection on the next emit and an event loop pass.
    """
    for _ in range(3):
        THEME.themeChanged.emit(THEME.colors)
        gc.collect()
        QTest.qWait(10)


def test_a_closed_settings_window_leaves_no_theme_slot_behind(qapp, monkeypatch):
    """Every part subscribes to themeChanged; once the window is gone, a theme
    switch must not reach any of them, and the connections must go too."""
    calls = []
    for cls in (SettingsWindow, *PAGE_CLASSES):

        def spy(self, *args, _real=cls._apply_theme):
            calls.append(sip.isdeleted(self))
            return _real(self)

        monkeypatch.setattr(cls, "_apply_theme", spy)

    before = THEME.name
    THEME.switch(OLD)
    _settle()
    baseline = THEME.receivers(THEME.themeChanged)
    try:
        w = SettingsWindow(None)
        for row in range(w.pages.count()):
            w.menu.setCurrentRow(row)
        parts = [weakref.ref(w)]
        parts += [weakref.ref(w.pages.widget(i)) for i in range(w.pages.count())]
        assert THEME.receivers(THEME.themeChanged) == baseline + len(parts)

        calls.clear()
        THEME.switch(NEW)
        assert calls == [False] * len(parts)

        w.close()
        del w
        _settle()
        assert [ref() for ref in parts] == [None] * len(parts)

        calls.clear()
        THEME.switch(OLD)
        _settle()
        assert calls == []
        assert THEME.receivers(THEME.themeChanged) == baseline
    finally:
        THEME.switch(before)
