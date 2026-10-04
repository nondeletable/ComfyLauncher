"""The settings window builds each page on its first visit.

Built all at once, Color Themes, Launcher Logs and About added a few hundred
ms to every opening of the window, though most openings never look at them.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from ui.settings.page_build import BuildSettingsPage  # noqa: E402
from ui.settings.page_logs import LogsSettingsPage  # noqa: E402
from ui.settings.page_startapp import StartAppSettingsPage  # noqa: E402
from ui.settings.settings_window import SettingsWindow  # noqa: E402


@pytest.fixture
def window(qapp):
    w = SettingsWindow(None)
    yield w
    w._dirty_any = False
    w.close()


def test_only_the_first_page_is_built_on_open(window):
    assert window.pages.count() == 6
    assert isinstance(window.pages.widget(0), BuildSettingsPage)
    assert window._built_pages == {0}
    assert window.pages.currentIndex() == 0


def test_a_page_is_built_on_its_first_visit_and_kept(window):
    window.menu.setCurrentRow(4)
    logs = window.pages.currentWidget()
    assert isinstance(logs, LogsSettingsPage)
    assert window.pages.indexOf(logs) == 4
    assert window.pages.count() == 6

    window.menu.setCurrentRow(0)
    window.menu.setCurrentRow(4)
    assert window.pages.currentWidget() is logs


def test_apply_follows_a_page_built_late(window):
    window.menu.setCurrentRow(1)
    page = window.pages.currentWidget()
    assert isinstance(page, StartAppSettingsPage)
    assert not window.btn_apply.isEnabled()

    page.cb_show_splash.toggle()
    assert window.btn_apply.isEnabled()

    page.cb_show_splash.toggle()
    assert not window.btn_apply.isEnabled()
