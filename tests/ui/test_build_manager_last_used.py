"""Editing or adding a build in the selector must not mark it as last used.

The selector opened SetupWindow in its default MANAGER mode, which writes the
saved build into ``last_used_build_id`` and ``comfyui_path``. Edit build B and
close the selector without launching, and the next start showed B as
"(last used)" although it never ran.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

import ui.dialogs.build_manager_dialog as bm  # noqa: E402
import ui.dialogs.setup_window as sw  # noqa: E402


@pytest.fixture
def store(monkeypatch):
    """One in-memory config shared by the selector and SetupWindow."""
    data = {
        "builds": [
            {"id": "A", "name": "A", "path": "C:/a", "icon_id": "d1"},
            {"id": "B", "name": "B", "path": "C:/b", "icon_id": "d1"},
        ],
        "last_used_build_id": "A",
        "comfyui_path": "C:/a",
    }

    def _load():
        return {
            **data,
            "builds": [dict(b) for b in data["builds"]],
        }

    def _save(new):
        data.clear()
        data.update(new)
        return True

    for mod in (bm, sw):
        monkeypatch.setattr(mod, "load_user_config", _load)
        monkeypatch.setattr(mod, "save_user_config", _save)
    monkeypatch.setattr(sw, "is_valid_comfyui_build", lambda p: True)
    monkeypatch.setattr(sw, "detect_build_type", lambda p: "portable")
    return data


@pytest.fixture
def saving_setup(monkeypatch):
    """Make SetupWindow.exec() fill the fields from the returned dict and press Save."""
    edits = {}

    def _exec(self):
        for field, value in edits.items():
            getattr(self, field).setText(value)
        self._accept()
        return self.result()

    monkeypatch.setattr(sw.SetupWindow, "exec", _exec)
    return edits


def build(store, build_id):
    return next(b for b in store["builds"] if b["id"] == build_id)


def test_editing_another_build_keeps_last_used(qapp, store, saving_setup):
    dlg = bm.BuildManagerDialog()
    saving_setup["path_edit"] = "C:/b2"
    dlg._edit_build(build(store, "B"))
    assert build(store, "B")["path"] == "C:/b2"
    assert store["last_used_build_id"] == "A"
    assert store["comfyui_path"] == "C:/a"
    assert dlg.last_used_id == "A"


def test_adding_a_build_keeps_last_used(qapp, store, saving_setup):
    dlg = bm.BuildManagerDialog()
    saving_setup["path_edit"] = "C:/c"
    saving_setup["name_edit"] = "C"
    dlg._add_build()
    assert [b["name"] for b in store["builds"]] == ["A", "B", "C"]
    assert store["last_used_build_id"] == "A"
    assert store["comfyui_path"] == "C:/a"


def test_editing_the_last_used_build_moves_comfyui_path(qapp, store, saving_setup):
    # comfyui_path mirrors the last-used build; the start-up check reads it.
    dlg = bm.BuildManagerDialog()
    saving_setup["path_edit"] = "C:/a2"
    dlg._edit_build(build(store, "A"))
    assert store["last_used_build_id"] == "A"
    assert store["comfyui_path"] == "C:/a2"


def test_legacy_config_finds_the_last_used_build_by_path(qapp, store, saving_setup):
    # configs from before last_used_build_id know the current build by path only
    del store["last_used_build_id"]
    dlg = bm.BuildManagerDialog()
    saving_setup["path_edit"] = "C:/a2"
    dlg._edit_build(build(store, "A"))
    assert store["comfyui_path"] == "C:/a2"
