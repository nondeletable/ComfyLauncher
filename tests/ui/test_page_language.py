"""Settings -> Language: Apply saves the choice and the launcher switches at once."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6 import sip  # noqa: E402

import ui.settings.page_language as page_language  # noqa: E402
import ui.widgets.language_combo as language_combo  # noqa: E402
import utils.i18n as i18n  # noqa: E402
from ui.settings.settings_window import SettingsWindow  # noqa: E402
from utils.i18n import AUTO, I18N  # noqa: E402

LANGUAGE = 4


@pytest.fixture
def saved(monkeypatch):
    writes = []

    def save(cfg):
        writes.append(dict(cfg))
        return True

    monkeypatch.setattr(page_language, "save_user_config", save)
    return writes


@pytest.fixture
def window(qapp, saved, monkeypatch):
    # The tests must not depend on the language of the machine running them.
    for module in (i18n, language_combo):
        monkeypatch.setattr(module, "detect_system_language", lambda: "en")
    monkeypatch.setattr(page_language, "get_language_preference", lambda: AUTO)
    I18N.set_language(AUTO)
    w = SettingsWindow(None)
    w.menu.setCurrentRow(LANGUAGE)
    yield w
    if not sip.isdeleted(w):
        w._dirty_pages = lambda: []
        w.close()
    I18N.set_language(AUTO)


def _pick(window, code):
    page = window.pages.currentWidget()
    page.cmb_language.setCurrentIndex(page.cmb_language.findData(code))
    return page


def test_the_page_starts_on_system(window):
    page = window.pages.currentWidget()
    assert isinstance(page, page_language.LanguageSettingsPage)
    assert page.cmb_language.currentData() == AUTO
    assert page.cmb_language.itemText(0) == "System (English)"
    assert not window.btn_apply.isEnabled()


def test_picking_alone_changes_nothing(window, saved):
    _pick(window, "de")
    assert window.btn_apply.isEnabled()
    assert I18N.language == "en"
    assert window.menu.item(LANGUAGE).text() == "Language"
    assert saved == []

    _pick(window, AUTO)  # back to the saved value
    assert not window.btn_apply.isEnabled()


def test_apply_saves_and_switches_live(window, saved):
    page = _pick(window, "de")
    window.btn_apply.click()

    assert saved[-1]["language"] == "de"
    assert I18N.language == "de"
    assert not window.btn_apply.isEnabled()
    # The open window is retranslated without being rebuilt.
    assert window.menu.item(LANGUAGE).text() == "Sprache"
    assert window.btn_apply.text() == "Übernehmen"
    assert page.title.text() == "Sprache"
    assert page.cmb_language.itemText(0) == "Systemsprache (English)"
    # Language names never change with the interface language.
    assert page.cmb_language.itemText(page.cmb_language.findData("zh")) == (
        "中文 (简体)"
    )


def test_back_to_system_follows_the_os(window, saved):
    _pick(window, "ru")
    window.btn_apply.click()
    assert I18N.language == "ru"

    _pick(window, AUTO)
    window.btn_apply.click()
    assert saved[-1]["language"] == AUTO
    assert (I18N.preference, I18N.language) == (AUTO, "en")
    assert window.menu.item(LANGUAGE).text() == "Language"
