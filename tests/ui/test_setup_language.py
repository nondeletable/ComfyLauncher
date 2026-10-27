"""The first-run window picks the interface language and switches at once.

No Apply and no restart there: the user has just opened the app. The choice is
saved right away, so a cancelled setup still opens in that language next time.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtWidgets import QWidget  # noqa: E402

import ui.dialogs.setup_window as sw  # noqa: E402
import ui.widgets.language_combo as language_combo  # noqa: E402
import utils.i18n as i18n  # noqa: E402
from utils.i18n import AUTO, I18N  # noqa: E402


@pytest.fixture
def saved(monkeypatch):
    writes = []

    def save(cfg):
        writes.append(dict(cfg))
        return True

    monkeypatch.setattr(sw, "save_user_config", save)
    monkeypatch.setattr(sw, "load_user_config", lambda: {"builds": []})
    monkeypatch.setattr(sw, "get_language_preference", lambda: AUTO)
    for module in (i18n, language_combo):
        monkeypatch.setattr(module, "detect_system_language", lambda: "en")
    I18N.set_language(AUTO)
    yield writes
    I18N.set_language(AUTO)


@pytest.fixture
def first_run(qapp, saved):
    dlg = sw.SetupWindow()
    yield dlg
    dlg.deleteLater()


def _pick(dlg, code):
    combo = dlg.language_combo
    combo.setCurrentIndex(combo.findData(code))


def test_first_run_offers_the_language(first_run):
    combo = first_run.language_combo
    assert combo is not None
    assert combo.preference() == AUTO
    assert combo.itemText(0) == "System (English)"


def test_picking_switches_at_once_and_is_saved(first_run, saved):
    _pick(first_run, "de")
    assert I18N.language == "de"
    assert saved[-1] == {"builds": [], "language": "de"}
    assert first_run.cancel_btn.text() == "Abbrechen"
    assert first_run.windowTitle() == "ComfyLauncher-Einrichtung"
    assert first_run.language_combo.itemText(0) == "Systemsprache (English)"


def test_back_to_system(first_run, saved):
    _pick(first_run, "zh")
    _pick(first_run, AUTO)
    assert (I18N.preference, I18N.language) == (AUTO, "en")
    assert saved[-1]["language"] == AUTO
    assert first_run.cancel_btn.text() == "Cancel"


@pytest.mark.parametrize("mode", list(sw.SetupMode))
def test_owned_windows_have_no_language_choice(qapp, saved, mode):
    owner = QWidget()
    dlg = sw.SetupWindow(owner, mode=mode)
    assert dlg.language_combo is None
    dlg.deleteLater()
    owner.deleteLater()
