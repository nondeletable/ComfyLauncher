"""Closing Settings asks about the unsaved changes of every page, not one.

Regression: the window tracked only the page on screen. Edit Startup, switch to
Exit Options, Close - no question, the edit was gone. Applying a color theme
closes the window on its own, and it dropped the other pages' edits the same way.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6 import sip  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402

import ui.settings.page_behavior as behavior  # noqa: E402
import ui.settings.page_startapp as startapp  # noqa: E402
from ui.dialogs.messagebox import MessageBox  # noqa: E402
from ui.settings.settings_window import SettingsWindow  # noqa: E402
from ui.theme.manager import THEME, THEMES  # noqa: E402

STARTUP, EXIT_OPTIONS, COLOR_THEMES = 1, 2, 3


@pytest.fixture
def prompts(monkeypatch):
    """Answer the close prompt with ``prompts.answer`` and record every ask."""

    class Prompts:
        answer = "cancel"
        asked = []

    def choose(parent, title, text, kind, buttons):
        Prompts.asked.append(text)
        return Prompts.answer

    Prompts.asked = []
    monkeypatch.setattr(MessageBox, "choose", staticmethod(choose))
    monkeypatch.setattr(MessageBox, "info", staticmethod(lambda *a: None))
    return Prompts


@pytest.fixture
def saved(monkeypatch):
    """Keep the pages' Apply away from the config file, record what it saves."""
    writes = []

    def save(cfg):
        writes.append(dict(cfg))
        return True

    for module in (behavior, startapp):
        monkeypatch.setattr(module, "save_user_config", save)
    return writes


@pytest.fixture
def window(qapp, prompts, saved):
    theme = THEME.name
    w = SettingsWindow(None)
    yield w
    if not sip.isdeleted(w):
        w._dirty_pages = lambda: []
        w.close()
    THEME.switch(theme)


def _dirty_startup(window):
    window.menu.setCurrentRow(STARTUP)
    page = window.pages.currentWidget()
    page.cb_show_splash.toggle()
    assert page.is_dirty()
    return page


def _dirty_exit_options(window):
    window.menu.setCurrentRow(EXIT_OPTIONS)
    page = window.pages.currentWidget()
    other = page.rb_always if not page.rb_always.isChecked() else page.rb_never
    other.setChecked(True)
    assert page.is_dirty()
    return page


def test_an_edit_survives_a_switch_and_closing_asks_about_it(window, prompts):
    startup = _dirty_startup(window)
    splash = startup.cb_show_splash.isChecked()
    window.menu.setCurrentRow(EXIT_OPTIONS)
    assert not window.btn_apply.isEnabled()

    assert window.close() is False
    assert len(prompts.asked) == 1
    assert "Startup" in prompts.asked[0]
    assert "Exit Options" not in prompts.asked[0]

    window.menu.setCurrentRow(STARTUP)
    assert window.pages.currentWidget() is startup
    assert startup.cb_show_splash.isChecked() == splash
    assert startup.is_dirty()
    assert window.btn_apply.isEnabled()


def test_one_prompt_names_every_dirty_page(window, prompts):
    _dirty_startup(window)
    _dirty_exit_options(window)

    window.close()
    assert len(prompts.asked) == 1
    assert "Startup, Exit Options" in prompts.asked[0]


def test_discard_closes_without_saving(window, prompts, saved):
    _dirty_startup(window)
    prompts.answer = "discard"
    assert window.close() is True
    assert saved == []


def test_apply_saves_every_dirty_page_and_closes(window, prompts, saved):
    startup = _dirty_startup(window)
    exit_options = _dirty_exit_options(window)
    window.menu.setCurrentRow(0)
    prompts.answer = "apply"

    assert window.close() is True
    assert len(saved) == 2
    assert saved[0]["show_splash"] == startup.cb_show_splash.isChecked()
    assert saved[1]["exit_mode"] == exit_options._current_data()["exit_mode"]


def test_a_failed_apply_keeps_settings_open(window, prompts, monkeypatch):
    monkeypatch.setattr(startapp, "save_user_config", lambda cfg: False)
    monkeypatch.setattr(MessageBox, "save_failed", staticmethod(lambda p: None))
    startup = _dirty_startup(window)
    exit_options = _dirty_exit_options(window)
    prompts.answer = "apply"

    assert window.close() is False
    assert startup.is_dirty()
    assert not exit_options.is_dirty()


def test_footer_apply_applies_only_the_page_on_screen(window, saved):
    startup = _dirty_startup(window)
    exit_options = _dirty_exit_options(window)

    window.btn_apply.click()
    assert len(saved) == 1
    assert not exit_options.is_dirty()
    assert startup.is_dirty()
    assert not window.btn_apply.isEnabled()


def test_clean_and_never_visited_pages_close_without_asking(window, prompts):
    window.menu.setCurrentRow(STARTUP)
    assert window.close() is True
    assert prompts.asked == []


def test_theme_apply_asks_before_closing_over_another_dirty_page(window, prompts):
    _dirty_startup(window)
    window.menu.setCurrentRow(COLOR_THEMES)
    themes = window.pages.currentWidget()
    target = next(name for name in THEMES if name != THEME.name)
    themes._on_theme_selected(target)

    window.btn_apply.click()
    assert THEME.name == target
    QTest.qWait(250)

    assert len(prompts.asked) == 1
    assert "Startup" in prompts.asked[0]
    assert "Color Themes" not in prompts.asked[0]
    assert not sip.isdeleted(window)
    assert window.pages.widget(STARTUP).is_dirty()


def test_applying_a_theme_from_the_close_prompt_does_not_crash(window, prompts):
    window.menu.setCurrentRow(COLOR_THEMES)
    themes = window.pages.currentWidget()
    target = next(name for name in THEMES if name != THEME.name)
    themes._on_theme_selected(target)
    prompts.answer = "apply"

    assert window.close() is True
    assert THEME.name == target
    # The theme page's own delayed close is still pending at a window that is
    # being deleted; an exception in that slot would abort the whole process.
    QTest.qWait(250)
    assert sip.isdeleted(window)
