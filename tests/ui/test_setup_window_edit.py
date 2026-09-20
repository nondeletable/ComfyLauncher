"""Tests for editing a build in SetupWindow.

Two regressions are covered:

* Save was disabled when the edit dialog opened, because ``_update_ok_state``
  ran once in the prefill block *before* ``ok_btn`` existed (a no-op) and the
  button was then hard-disabled. The user had to touch a field to enable Save.
* Saving an edit must update the build in place, not append a second one.

The dialog is a QWidget, so an offscreen QApplication is spun up once.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

import ui.dialogs.setup_window as sw  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def stub_config(monkeypatch):
    """Back SetupWindow's load/save with an in-memory config and accept any path."""
    store = {
        "builds": [
            {
                "id": "AAA",
                "name": "ComfyUI",
                "path": "C:/x",
                "icon_id": "d1",
                "extra_flags": ["--cpu"],
            }
        ],
        "last_used_build_id": "AAA",
    }

    def _load():
        return {
            "builds": [dict(b) for b in store["builds"]],
            "last_used_build_id": store["last_used_build_id"],
        }

    def _save(data):
        store["builds"] = data.get("builds", [])
        store["last_used_build_id"] = data.get("last_used_build_id", "")
        return True

    monkeypatch.setattr(sw, "load_user_config", _load)
    monkeypatch.setattr(sw, "save_user_config", _save)
    monkeypatch.setattr(sw, "is_valid_comfyui_build", lambda p: True)
    monkeypatch.setattr(sw, "detect_build_type", lambda p: "portable")
    return store


def test_edit_mode_enables_save_immediately(app, stub_config):
    build = stub_config["builds"][0]
    dlg = sw.SetupWindow(None, build=build, mode=sw.SetupMode.MANAGER)

    assert dlg.edit_build_id == "AAA"
    assert dlg.name_edit.text() == "ComfyUI"
    # Save is usable at once — no need to touch a field first.
    assert dlg.ok_btn.isEnabled() is True


def test_add_mode_save_disabled_until_named(app, stub_config):
    dlg = sw.SetupWindow(None, build=None, mode=sw.SetupMode.MANAGER)
    # No name yet, so Save stays disabled.
    assert dlg.ok_btn.isEnabled() is False


def test_edit_updates_in_place_no_duplicate(app, stub_config):
    build = stub_config["builds"][0]
    dlg = sw.SetupWindow(None, build=build, mode=sw.SetupMode.MANAGER)

    dlg.flags_edit.setText("--cpu --lowvram")
    dlg._accept()

    assert len(stub_config["builds"]) == 1
    updated = stub_config["builds"][0]
    assert updated["id"] == "AAA"
    assert updated["extra_flags"] == ["--cpu", "--lowvram"]
