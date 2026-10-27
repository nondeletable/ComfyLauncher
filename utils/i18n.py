"""Interface translations: ``t(key)`` and the language switch.

Strings live in ``assets/i18n/<code>.json`` as flat dotted keys
(``"settings.menu.builds": "Builds"``). English is the reference: every other
file carries the same keys, and a key missing there falls back to English, then
to the key itself, so a gap shows up on screen instead of crashing.

The language changes live. Widgets set their texts in ``_retranslate()``, call
it once at the end of ``__init__`` and connect it to ``I18N.languageChanged``;
module-level constants hold keys, never translated text, because they are
evaluated only once.
"""

from __future__ import annotations

import functools
import json
import os
import traceback

from PyQt6.QtCore import QLocale, QObject, pyqtSignal

from config import I18N_DIR
from utils.logger import log_event

DEFAULT_LANGUAGE = "en"
AUTO = "auto"

# Shown as-is in every language: a user lost in a foreign interface looks for
# the name of their own language, not its translation.
LANGUAGES = {
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
    "zh": "中文 (简体)",
    "ru": "Русский",
}


def match_language(ui_languages: list[str]) -> str:
    """Pick the first supported language from the OS preference list.

    Takes BCP 47 tags as ``QLocale.uiLanguages()`` returns them (``de-DE``,
    ``zh-Hant-TW``) and matches by the primary subtag, so every Chinese variant
    lands on the one Simplified Chinese translation.
    """
    for tag in ui_languages:
        primary = tag.replace("_", "-").split("-")[0].lower()
        if primary in LANGUAGES:
            return primary
    return DEFAULT_LANGUAGE


def detect_system_language() -> str:
    return match_language(QLocale.system().uiLanguages())


def _load_strings(code: str, directory: str) -> dict[str, str]:
    """Read one language file; a missing or broken file is an empty table."""
    path = os.path.join(directory, f"{code}.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        log_event(f"⚠️ i18n: cannot read {path}: {e}")
        return {}
    if not isinstance(data, dict):
        log_event(f"⚠️ i18n: {path} is not a key/value table")
        return {}
    return {str(k): str(v) for k, v in data.items()}


def safe_retranslate(retranslate):
    """Decorate a languageChanged slot: a failing widget is logged, not fatal.

    Same reason as ``safe_repaint`` for themes: one switch runs every
    subscriber in a row, and an exception escaping a PyQt slot can take the
    process down.
    """

    @functools.wraps(retranslate)
    def wrapper(self, *_args):
        try:
            retranslate(self)
        except Exception:
            log_event(
                f"⚠️ {type(self).__name__} failed to retranslate:\n"
                f"{traceback.format_exc()}"
            )

    return wrapper


class I18n(QObject):
    """Holds the active language and looks strings up in it."""

    languageChanged = pyqtSignal(str)

    def __init__(self, directory: str = I18N_DIR):
        super().__init__()
        self._dir = directory
        self._preference = AUTO
        self._language = DEFAULT_LANGUAGE
        self._fallback = _load_strings(DEFAULT_LANGUAGE, directory)
        self._strings = self._fallback
        self._reported: set[tuple[str, str]] = set()

    @property
    def preference(self) -> str:
        """What the user picked: a language code or ``"auto"``."""
        return self._preference

    @property
    def language(self) -> str:
        """The language actually shown."""
        return self._language

    def set_language(self, preference: str) -> None:
        """Switch to a code or to ``"auto"``; emits only on a real change."""
        if preference != AUTO and preference not in LANGUAGES:
            log_event(f"⚠️ i18n: unknown language {preference!r}, using auto")
            preference = AUTO
        self._preference = preference
        code = detect_system_language() if preference == AUTO else preference
        if code == self._language:
            return
        self._language = code
        self._strings = (
            self._fallback
            if code == DEFAULT_LANGUAGE
            else _load_strings(code, self._dir)
        )
        log_event(f"🌐 Interface language: {code} (preference: {preference})")
        self.languageChanged.emit(code)

    def t(self, key: str, **kwargs) -> str:
        text = self._strings.get(key)
        if text is None:
            self._report(key)
            text = self._fallback.get(key, key)
        if not kwargs:
            return text
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            # A broken placeholder in a translation must not lose the message.
            self._report(key)
            return self._fallback.get(key, key).format(**kwargs)

    def _report(self, key: str) -> None:
        if (self._language, key) not in self._reported:
            self._reported.add((self._language, key))
            log_event(f"⚠️ i18n: no usable '{key}' in {self._language}")


I18N = I18n()


def t(key: str, **kwargs) -> str:
    """Translate ``key`` into the active language, formatting ``{name}`` slots."""
    return I18N.t(key, **kwargs)
