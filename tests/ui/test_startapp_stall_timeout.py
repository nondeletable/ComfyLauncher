"""Settings -> Startup: the startup timeout picker."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

import ui.settings.page_startapp as startapp  # noqa: E402


@pytest.fixture
def page_with(qapp, monkeypatch):
    """Build the page over a given saved config; record saves and info boxes."""
    saved, infos = [], []

    def make(cfg):
        monkeypatch.setattr(startapp, "load_user_config", lambda: dict(cfg))
        monkeypatch.setattr(
            startapp, "save_user_config", lambda c: saved.append(c) or True
        )
        monkeypatch.setattr(
            startapp.MB, "info", staticmethod(lambda p, t, text: infos.append(text))
        )
        return startapp.StartAppSettingsPage()

    make.saved, make.infos = saved, infos
    return make


def items(page):
    return [page.cmb_stall.itemData(i) for i in range(page.cmb_stall.count())]


def test_presets_with_default_selected(page_with):
    page = page_with({})
    assert items(page) == [120, 300, 600, 0]
    assert page.cmb_stall.currentData() == 120
    assert page.cmb_stall.itemText(3).startswith("Never")
    assert not page.is_dirty()


def test_hand_edited_value_is_kept_as_custom(page_with):
    page = page_with({"startup_stall_timeout": 900})
    assert items(page) == [120, 300, 600, 900, 0]  # "Never" stays last
    assert page.cmb_stall.currentText() == "15 minutes (custom)"
    assert not page.is_dirty()


def test_change_marks_dirty_and_back_clears_it(page_with):
    page = page_with({})
    page.cmb_stall.setCurrentIndex(3)
    assert page.is_dirty()
    page.cmb_stall.setCurrentIndex(0)
    assert not page.is_dirty()


def test_apply_saves_seconds_without_asking_for_restart(page_with):
    page = page_with({})
    page.cmb_stall.setCurrentIndex(3)  # Never

    assert page.apply() is True
    assert page_with.saved[-1]["startup_stall_timeout"] == 0
    assert "restart" not in page_with.infos[-1]
    assert not page.is_dirty()


def test_console_change_still_asks_for_restart(page_with):
    page = page_with({})
    page.cb_show_splash.setChecked(False)

    page.apply()
    assert "restart" in page_with.infos[-1]


def test_reset_restores_saved_choice(page_with):
    page = page_with({"startup_stall_timeout": 600})
    page.cmb_stall.setCurrentIndex(0)
    page.reset()
    assert page.cmb_stall.currentData() == 600
    assert not page.is_dirty()
