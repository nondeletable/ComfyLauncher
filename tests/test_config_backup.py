"""Tests for the user-config backup outside %APPDATA%.

%APPDATA% does not survive a Windows reinstall, so every save is mirrored to
the app folder (when writable) or Documents, and the write is verified by
reading it back. On startup without a config, the newest backup is offered
for restore.
"""

import json
import os
import sys
import threading

import pytest

import config
import main
import ui.theme.manager as manager

CONFIG_WITH_BUILDS = {"builds": [{"id": "b1", "path": "D:/ComfyUI"}], "theme": "light"}


@pytest.fixture
def paths(tmp_path, monkeypatch):
    """Point the config, the legacy config and both backup dirs into tmp_path."""
    p = {
        "config": tmp_path / "appdata" / "user_config.json",
        "legacy": tmp_path / "internal" / "user_config.json",
        "app": tmp_path / "app" / "backup",
        "docs": tmp_path / "docs" / "ComfyLauncher" / "backup",
    }
    monkeypatch.setattr(config, "USER_CONFIG_PATH", str(p["config"]))
    monkeypatch.setattr(config, "LEGACY_USER_CONFIG_PATH", str(p["legacy"]))
    monkeypatch.setattr(config, "_app_backup_dir", lambda: str(p["app"]))
    monkeypatch.setattr(config, "_documents_backup_dir", lambda: str(p["docs"]))
    return p


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


# ── Location choice ───────────────────────────


def test_app_backup_dir_is_none_from_source(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert config._app_backup_dir() is None


@pytest.mark.parametrize("platform", ["linux", "darwin"])
def test_app_backup_dir_is_none_off_windows(platform, tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "ComfyLauncher"))
    assert config._app_backup_dir() is None


def test_app_backup_dir_is_next_to_exe_when_frozen(tmp_path, monkeypatch):
    exe = tmp_path / "Comfy Launcher" / "ComfyLauncher.exe"
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))
    assert config._app_backup_dir() == str(exe.parent / "backup")


def test_backup_goes_to_app_folder_when_writable(paths):
    _write_json(paths["config"], CONFIG_WITH_BUILDS)

    written = config.backup_user_config()

    assert written == str(paths["app"] / "user_config.json")
    assert (paths["app"] / "user_config.json").read_bytes() == paths[
        "config"
    ].read_bytes()
    assert not paths["docs"].exists()


def test_backup_falls_back_to_documents_when_app_folder_unwritable(
    paths, tmp_path, monkeypatch
):
    # A file where the app folder should be: makedirs/open cannot succeed.
    blocker = tmp_path / "readonly-app"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setattr(config, "_app_backup_dir", lambda: str(blocker / "backup"))
    _write_json(paths["config"], CONFIG_WITH_BUILDS)

    written = config.backup_user_config()

    assert written == str(paths["docs"] / "user_config.json")
    assert (paths["docs"] / "user_config.json").read_bytes() == paths[
        "config"
    ].read_bytes()


def test_backup_falls_back_when_app_folder_write_does_not_verify(paths, monkeypatch):
    real_read = config._read_bytes
    app_dir = str(paths["app"])

    def corrupting_read(path):
        if path.startswith(app_dir):
            return b"{}"
        return real_read(path)

    monkeypatch.setattr(config, "_read_bytes", corrupting_read)
    _write_json(paths["config"], CONFIG_WITH_BUILDS)

    written = config.backup_user_config()

    assert written == str(paths["docs"] / "user_config.json")


# ── Verify on write ───────────────────────────


def test_failed_verification_keeps_the_previous_backup(paths, monkeypatch):
    target = paths["app"] / "user_config.json"
    _write_json(target, {"builds": [{"id": "old"}]})
    previous = target.read_bytes()

    real_read = config._read_bytes
    monkeypatch.setattr(
        config,
        "_read_bytes",
        lambda p: b"garbage" if p.endswith(".tmp") else real_read(p),
    )

    assert config._write_verified(str(target), b'{"builds": [{"id": "new"}]}') is False
    assert target.read_bytes() == previous
    assert not list(paths["app"].glob("*.tmp"))


def test_write_verified_round_trips(paths):
    target = paths["app"] / "user_config.json"
    raw = json.dumps(CONFIG_WITH_BUILDS).encode("utf-8")

    assert config._write_verified(str(target), raw) is True
    assert target.read_bytes() == raw
    assert not list(paths["app"].glob("*.tmp"))


def test_concurrent_backups_do_not_collide(paths):
    _write_json(paths["config"], CONFIG_WITH_BUILDS)
    results = []
    threads = [
        threading.Thread(target=lambda: results.append(config.backup_user_config()))
        for _ in range(8)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results == [str(paths["app"] / "user_config.json")] * 8
    assert not list(paths["app"].glob("*.tmp"))


def test_backup_returns_none_when_no_location_verifies(paths, monkeypatch):
    monkeypatch.setattr(config, "_write_verified", lambda path, raw: False)
    _write_json(paths["config"], CONFIG_WITH_BUILDS)

    assert config.backup_user_config() is None


# ── What gets backed up ───────────────────────


def test_config_without_builds_does_not_overwrite_backup(paths):
    target = paths["app"] / "user_config.json"
    _write_json(target, CONFIG_WITH_BUILDS)
    previous = target.read_bytes()
    _write_json(paths["config"], {"builds": []})

    assert config.backup_user_config() is None
    assert target.read_bytes() == previous


def test_missing_config_is_not_backed_up(paths):
    assert config.backup_user_config() is None
    assert not paths["app"].exists()


def test_save_user_config_mirrors_to_backup(paths):
    assert config.save_user_config(CONFIG_WITH_BUILDS) is True

    backup = paths["app"] / "user_config.json"
    assert backup.read_bytes() == paths["config"].read_bytes()


def test_save_user_config_succeeds_even_if_backup_fails(paths, monkeypatch):
    monkeypatch.setattr(config, "_backup_paths", lambda: [])

    assert config.save_user_config(CONFIG_WITH_BUILDS) is True


# ── Restore offer ─────────────────────────────


def _set_mtime(path, ts):
    os.utime(path, (ts, ts))


def test_restore_offered_when_config_missing_and_backup_exists(paths):
    _write_json(paths["docs"] / "user_config.json", CONFIG_WITH_BUILDS)

    assert config.user_config_restore_candidate() == str(
        paths["docs"] / "user_config.json"
    )


def test_restore_not_offered_when_config_has_builds(paths):
    _write_json(paths["config"], {"builds": [{"id": "current"}]})
    _write_json(paths["app"] / "user_config.json", CONFIG_WITH_BUILDS)

    assert config.user_config_restore_candidate() is None


def test_restore_offered_over_a_default_config_without_builds(paths):
    # The first load_user_config() writes the defaults when nothing is there;
    # that must not hide the backup.
    _write_json(paths["config"], config.DEFAULT_USER_CONFIG)
    _write_json(paths["app"] / "user_config.json", CONFIG_WITH_BUILDS)

    assert config.user_config_restore_candidate() == str(
        paths["app"] / "user_config.json"
    )


def test_restore_not_offered_over_a_config_emptied_by_the_user(paths):
    emptied = dict(config.DEFAULT_USER_CONFIG, theme="light")
    _write_json(paths["config"], emptied)
    _write_json(paths["app"] / "user_config.json", CONFIG_WITH_BUILDS)

    assert config.user_config_restore_candidate() is None


def test_restore_not_offered_over_an_unreadable_config(paths):
    # A directory in place of the file: it exists, but open() fails.
    paths["config"].mkdir(parents=True)
    _write_json(paths["app"] / "user_config.json", CONFIG_WITH_BUILDS)

    assert config.user_config_restore_candidate() is None


def test_restore_not_offered_over_a_corrupt_config(paths):
    paths["config"].parent.mkdir(parents=True)
    paths["config"].write_text("{not json", encoding="utf-8")
    _write_json(paths["app"] / "user_config.json", CONFIG_WITH_BUILDS)

    assert config.user_config_restore_candidate() is None


def test_restore_not_offered_without_backup(paths):
    assert config.user_config_restore_candidate() is None


def test_restore_not_offered_for_backup_without_builds(paths):
    _write_json(paths["app"] / "user_config.json", {"builds": []})

    assert config.user_config_restore_candidate() is None


def test_restore_offers_the_newest_backup(paths):
    app = paths["app"] / "user_config.json"
    docs = paths["docs"] / "user_config.json"
    _write_json(app, CONFIG_WITH_BUILDS)
    _write_json(docs, CONFIG_WITH_BUILDS)
    _set_mtime(app, 1_000_000)
    _set_mtime(docs, 2_000_000)

    assert config.user_config_restore_candidate() == str(docs)


def test_legacy_config_wins_over_older_backup(paths):
    backup = paths["app"] / "user_config.json"
    _write_json(backup, CONFIG_WITH_BUILDS)
    _write_json(paths["legacy"], CONFIG_WITH_BUILDS)
    _set_mtime(backup, 1_000_000)
    _set_mtime(paths["legacy"], 2_000_000)

    assert config.user_config_restore_candidate() is None


def test_newer_legacy_config_without_builds_does_not_hide_backup(paths):
    backup = paths["app"] / "user_config.json"
    _write_json(backup, CONFIG_WITH_BUILDS)
    _write_json(paths["legacy"], {"builds": []})
    _set_mtime(backup, 1_000_000)
    _set_mtime(paths["legacy"], 2_000_000)

    assert config.user_config_restore_candidate() == str(backup)


def test_backup_newer_than_stale_legacy_config_is_offered(paths):
    backup = paths["app"] / "user_config.json"
    _write_json(backup, CONFIG_WITH_BUILDS)
    _write_json(paths["legacy"], {"builds": [{"id": "stale"}]})
    _set_mtime(paths["legacy"], 1_000_000)
    _set_mtime(backup, 2_000_000)

    assert config.user_config_restore_candidate() == str(backup)


# ── Restore ───────────────────────────────────


def test_restore_copies_backup_into_appdata(paths):
    backup = paths["docs"] / "user_config.json"
    _write_json(backup, CONFIG_WITH_BUILDS)

    assert config.restore_user_config(str(backup)) is True
    assert paths["config"].read_bytes() == backup.read_bytes()
    assert config.load_user_config()["builds"][0]["id"] == "b1"


def test_restore_reports_failure_when_backup_unreadable(paths):
    assert config.restore_user_config(str(paths["docs"] / "missing.json")) is False
    assert not paths["config"].exists()


def test_restore_keeps_the_replaced_config_aside(paths):
    backup = paths["docs"] / "user_config.json"
    _write_json(backup, CONFIG_WITH_BUILDS)
    _write_json(paths["config"], config.DEFAULT_USER_CONFIG)
    replaced = paths["config"].read_bytes()

    assert config.restore_user_config(str(backup)) is True
    aside = paths["config"].parent / "user_config.json.before-restore"
    assert aside.read_bytes() == replaced
    assert paths["config"].read_bytes() == backup.read_bytes()


def test_restore_aborts_when_the_current_config_cannot_be_kept(paths, monkeypatch):
    backup = paths["docs"] / "user_config.json"
    _write_json(backup, CONFIG_WITH_BUILDS)
    _write_json(paths["config"], config.DEFAULT_USER_CONFIG)
    before = paths["config"].read_bytes()
    real_write = config._write_verified
    monkeypatch.setattr(
        config,
        "_write_verified",
        lambda p, raw: False if p.endswith(".before-restore") else real_write(p, raw),
    )

    assert config.restore_user_config(str(backup)) is False
    assert paths["config"].read_bytes() == before


def test_restore_refuses_a_backup_without_builds(paths):
    backup = paths["docs"] / "user_config.json"
    _write_json(backup, {"builds": []})

    assert config.restore_user_config(str(backup)) is False
    assert not paths["config"].exists()


def test_theme_reload_picks_up_restored_config(paths, monkeypatch):
    original = manager.THEME.name
    _write_json(paths["config"], {"theme": "dracula"})
    monkeypatch.setattr(manager, "CONFIG_PATH", str(paths["config"]))
    try:
        manager.THEME.reload()
        assert manager.THEME.name == "dracula"
        assert manager.THEME.colors is manager.THEMES["dracula"]
    finally:
        monkeypatch.undo()
        manager.THEME.reload()
        assert manager.THEME.name == original


# ── Startup dialog ────────────────────────────


def test_declining_the_offer_leaves_the_config_alone(paths, monkeypatch):
    _write_json(paths["app"] / "user_config.json", CONFIG_WITH_BUILDS)
    asked = []
    monkeypatch.setattr(
        main.MessageBox, "ask_yes_no", lambda *a: asked.append(a) or False
    )

    main.offer_config_restore()

    assert len(asked) == 1
    assert not paths["config"].exists()
    # The declined backup is kept under another name, out of the save path.
    assert not (paths["app"] / "user_config.json").exists()
    aside = list(paths["app"].glob("user_config.declined-*.json"))
    assert len(aside) == 1
    assert json.loads(aside[0].read_text(encoding="utf-8")) == CONFIG_WITH_BUILDS
    assert config.user_config_restore_candidate() is None


def test_accepting_the_offer_restores_and_reloads_theme(paths, monkeypatch):
    _write_json(paths["app"] / "user_config.json", CONFIG_WITH_BUILDS)
    reloaded = []
    monkeypatch.setattr(main.MessageBox, "ask_yes_no", lambda *a: True)
    monkeypatch.setattr(main.THEME, "reload", lambda: reloaded.append(True))
    monkeypatch.setattr(main.THEME, "apply", lambda: None)

    main.offer_config_restore()

    assert json.loads(paths["config"].read_text(encoding="utf-8")) == (
        CONFIG_WITH_BUILDS
    )
    assert reloaded == [True]


def test_no_dialog_without_a_backup(paths, monkeypatch):
    monkeypatch.setattr(
        main.MessageBox,
        "ask_yes_no",
        lambda *a: pytest.fail("restore offered without a backup"),
    )

    main.offer_config_restore()


def test_theme_switch_reaches_the_backup(paths, monkeypatch):
    _write_json(paths["config"], CONFIG_WITH_BUILDS)
    monkeypatch.setattr(manager, "CONFIG_PATH", str(paths["config"]))
    monkeypatch.setattr(manager.THEME, "_active_name", "obsidian_orange")

    manager.THEME._save_last_theme()

    backup = json.loads((paths["app"] / "user_config.json").read_text("utf-8"))
    assert backup["theme"] == "obsidian_orange"
    assert backup["builds"] == CONFIG_WITH_BUILDS["builds"]
