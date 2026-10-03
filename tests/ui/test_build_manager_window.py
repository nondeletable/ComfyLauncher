"""The build selector must move, minimize, and resize in height only.

It was a fixed 730x550 frameless dialog: it could not be dragged, a taskbar
click could not minimize it on Windows, and a long build list could only be
scrolled, never given more room. Its height is now remembered between runs.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys  # noqa: E402

import pytest  # noqa: E402
from PyQt6.QtCore import Qt  # noqa: E402

import ui.dialogs.build_manager_dialog as bm  # noqa: E402

Dialog = bm.BuildManagerDialog


@pytest.fixture
def store(monkeypatch):
    """Back the dialog's config with an in-memory dict."""
    data = {"builds": [], "last_used_build_id": ""}

    def _save(new):
        data.clear()
        data.update(new)
        return True

    monkeypatch.setattr(bm, "load_user_config", lambda: dict(data))
    monkeypatch.setattr(bm, "save_user_config", _save)
    return data


def make(qapp):
    dlg = Dialog()
    qapp.processEvents()
    return dlg


def test_width_is_fixed_and_height_is_free(qapp, store):
    dlg = make(qapp)
    assert dlg.minimumWidth() == dlg.maximumWidth() == Dialog.WIDTH
    assert dlg.minimumHeight() == Dialog.MIN_HEIGHT
    assert dlg.maximumHeight() > Dialog.DEFAULT_HEIGHT
    assert dlg.height() == Dialog.DEFAULT_HEIGHT


def test_height_is_saved_on_close(qapp, store):
    dlg = make(qapp)
    dlg.resize(Dialog.WIDTH, 420)
    dlg.reject()
    assert store[Dialog.HEIGHT_KEY] == 420


def test_saved_height_is_restored(qapp, store):
    store[Dialog.HEIGHT_KEY] = 420
    assert make(qapp).height() == 420


@pytest.mark.parametrize("saved", [50, "junk", None])
def test_bad_saved_height_falls_back_to_a_usable_one(qapp, store, saved):
    store[Dialog.HEIGHT_KEY] = saved
    assert make(qapp).height() >= Dialog.MIN_HEIGHT


def test_saved_height_is_capped_to_the_screen(qapp, store):
    store[Dialog.HEIGHT_KEY] = 100_000
    dlg = make(qapp)
    assert dlg.height() <= dlg.screen().availableGeometry().height()


@pytest.mark.skipif(sys.platform != "win32", reason="WS_MINIMIZEBOX is Windows-only")
def test_selector_keeps_its_minimize_box_on_windows(qapp, store):
    assert make(qapp).windowFlags() & Qt.WindowType.WindowMinimizeButtonHint


def test_failed_config_read_does_not_wipe_builds(qapp, store, monkeypatch):
    """load_user_config() returns the bare defaults when the read fails (file
    locked by antivirus or a sync client); saving the height onto those would
    overwrite every build."""
    store["builds"] = [{"id": "A", "name": "Main", "path": "D:/x"}]
    dlg = make(qapp)
    saves = []
    monkeypatch.setattr(bm, "load_user_config", lambda: {"builds": []})
    monkeypatch.setattr(bm, "save_user_config", lambda data: saves.append(data))
    dlg.resize(Dialog.WIDTH, 420)
    dlg.reject()
    assert saves == []
