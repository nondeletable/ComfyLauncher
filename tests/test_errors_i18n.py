"""Error screens take their texts from the dictionaries."""

import pytest

from config import COMFYUI_PORT
from core.errors import ERRORS, error_texts
from utils.i18n import I18N, LANGUAGES, t


@pytest.fixture
def language():
    yield I18N.set_language
    I18N.set_language("en")


@pytest.mark.parametrize("code", sorted(ERRORS))
def test_every_error_has_its_texts(code):
    title, message, hint = error_texts(code, I18N.english)
    for text in (title, message, hint):
        assert text and not text.startswith("error."), code


def test_hint_names_the_settings_page_as_the_menu_does(language):
    for code in LANGUAGES:
        language(code)
        hint = error_texts("COMFY_START_STOPPED")[2]
        assert t("settings.menu.startup") in hint, code


def test_port_comes_from_config():
    assert str(COMFYUI_PORT) in error_texts("PORT_ALREADY_IN_USE")[1]


def test_report_text_stays_english(language):
    language("de")
    assert error_texts("COMFY_START_STOPPED", I18N.english)[0] == "Startup stopped"


def test_unknown_code_is_an_error():
    with pytest.raises(KeyError):
        error_texts("NO_SUCH_ERROR")
