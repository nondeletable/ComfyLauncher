"""Interface translations: language choice, lookup fallbacks, dictionary parity."""

import json
import os
import re
import string

import pytest

import utils.i18n as i18n
from config import I18N_DIR
from utils.i18n import AUTO, LANGUAGES, I18n, match_language


@pytest.mark.parametrize(
    "ui_languages, expected",
    [
        (["de-DE", "en-US"], "de"),
        (["fr-FR", "es-MX"], "es"),  # first *supported* one wins
        (["zh-Hans-CN"], "zh"),
        (["zh-Hant-TW"], "zh"),  # all Chinese variants share one translation
        (["ru_RU"], "ru"),  # underscore form
        (["EN-gb"], "en"),
        (["fr-FR", "ja-JP"], "en"),  # nothing supported
        ([], "en"),
    ],
)
def test_match_language(ui_languages, expected):
    assert match_language(ui_languages) == expected


def _write(directory, code, table):
    with open(os.path.join(directory, f"{code}.json"), "w", encoding="utf-8") as fh:
        json.dump(table, fh, ensure_ascii=False)


@pytest.fixture
def tables(tmp_path):
    _write(tmp_path, "en", {"hello": "Hello", "greet": "Hi, {name}", "only.en": "E"})
    _write(tmp_path, "de", {"hello": "Hallo", "greet": "Hallo, {nam}"})
    return str(tmp_path)


def test_lookup_and_fallbacks(tables):
    tr = I18n(tables)
    tr.set_language("de")
    assert tr.t("hello") == "Hallo"
    assert tr.t("only.en") == "E"  # missing in German -> English
    assert tr.t("no.such.key") == "no.such.key"  # missing everywhere -> key


def test_broken_placeholder_falls_back_to_english(tables):
    tr = I18n(tables)
    tr.set_language("de")
    assert tr.t("greet", name="Sasha") == "Hi, Sasha"


def test_missing_language_file_falls_back_to_english(tables):
    tr = I18n(tables)
    tr.set_language("es")  # supported, but no es.json in this directory
    assert tr.language == "es"
    assert tr.t("hello") == "Hello"


def test_signal_only_on_real_change(tables):
    tr = I18n(tables)
    seen = []
    tr.languageChanged.connect(seen.append)
    tr.set_language("en")  # already English
    tr.set_language("de")
    tr.set_language("de")
    assert seen == ["de"]


def test_auto_follows_the_system(tables, monkeypatch):
    monkeypatch.setattr(i18n, "detect_system_language", lambda: "de")
    tr = I18n(tables)
    tr.set_language(AUTO)
    assert (tr.preference, tr.language) == (AUTO, "de")


def test_unknown_preference_means_auto(tables, monkeypatch):
    monkeypatch.setattr(i18n, "detect_system_language", lambda: "en")
    tr = I18n(tables)
    tr.set_language("klingon")
    assert (tr.preference, tr.language) == (AUTO, "en")


# ── The shipped dictionaries ────────────────────────────────────────────────


def _shipped(code):
    with open(os.path.join(I18N_DIR, f"{code}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _slots(text):
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_every_language_has_a_file():
    assert sorted(f[:-5] for f in os.listdir(I18N_DIR)) == sorted(LANGUAGES)


@pytest.mark.parametrize("code", sorted(set(LANGUAGES) - {"en"}))
def test_same_keys_as_english(code):
    en, other = _shipped("en"), _shipped(code)
    assert set(other) - set(en) == set(), "keys English does not have"
    assert set(en) - set(other) == set(), "keys still untranslated"


@pytest.mark.parametrize("code", sorted(LANGUAGES))
def test_same_placeholders_as_english(code):
    en, other = _shipped("en"), _shipped(code)
    for key, text in other.items():
        assert _slots(text) == _slots(en.get(key, "")), key


@pytest.mark.parametrize("code", sorted(LANGUAGES))
def test_keys_are_dotted_lowercase(code):
    for key in _shipped(code):
        assert re.fullmatch(r"[a-z0-9_]+(\.[a-z0-9_]+)+", key), key
