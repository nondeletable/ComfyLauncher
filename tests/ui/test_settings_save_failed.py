"""A settings page must tell the user when the config could not be written.

save_user_config() never raises - it returns False - and the settings pages
ignored that: Apply reported success and cleared the dirty state, and a deleted
build vanished from the list while staying in the file.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

import ui.settings.page_behavior as behavior  # noqa: E402
import ui.settings.page_build as build  # noqa: E402
import ui.settings.page_startapp as startapp  # noqa: E402


@pytest.fixture
def failing_save(monkeypatch):
    """Make every save fail and record the warnings and info boxes shown."""
    shown = {"failed": 0, "info": 0}

    def failed(parent):
        shown["failed"] += 1

    def info(*a):
        shown["info"] += 1

    for module in (behavior, build, startapp):
        monkeypatch.setattr(module, "save_user_config", lambda cfg: False)
        monkeypatch.setattr(module.MB, "save_failed", staticmethod(failed))
        monkeypatch.setattr(module.MB, "info", staticmethod(info))
    return shown


@pytest.mark.parametrize(
    "page_cls",
    [behavior.BehaviorSettingsPage, startapp.StartAppSettingsPage],
)
def test_apply_reports_a_failed_save(qapp, failing_save, page_cls):
    page = page_cls()
    page._set_dirty(True)
    assert page.apply() is False
    assert page.is_dirty()
    assert failing_save == {"failed": 1, "info": 0}


def test_deleting_a_build_reports_a_failed_save(qapp, failing_save, monkeypatch):
    page = build.BuildSettingsPage()
    refreshed = []
    monkeypatch.setattr(page, "_refresh_builds_list", lambda: refreshed.append(1))
    monkeypatch.setattr(build.MB, "ask_yes_no", staticmethod(lambda *a: True))
    page._on_delete_build({"id": "A", "name": "Main"})
    assert failing_save["failed"] == 1
    assert refreshed == []
