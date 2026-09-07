"""Tests for user-config location, migration and save error reporting (#38-A).

The config moved from the in-app folder to %APPDATA% so it stays writable for
all-users (Program Files) installs. save_user_config now returns a bool so the
UI can surface failures instead of closing silently.
"""

import json

import config


def test_save_success_creates_dir_and_file(tmp_path, monkeypatch):
    target = tmp_path / "appdata" / "user_config.json"
    monkeypatch.setattr(config, "USER_CONFIG_PATH", str(target))

    assert config.save_user_config({"a": 1}) is True
    assert target.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == {"a": 1}


def test_save_failure_returns_false(tmp_path, monkeypatch):
    # Make the parent a real file so os.makedirs / open cannot succeed.
    blocker = tmp_path / "afile"
    blocker.write_text("x", encoding="utf-8")
    target = blocker / "nope" / "user_config.json"
    monkeypatch.setattr(config, "USER_CONFIG_PATH", str(target))

    assert config.save_user_config({"a": 1}) is False


def test_migration_copies_when_new_absent(tmp_path, monkeypatch):
    legacy = tmp_path / "legacy" / "user_config.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"builds": [{"id": "x"}]}', encoding="utf-8")
    new = tmp_path / "appdata" / "user_config.json"

    monkeypatch.setattr(config, "USER_CONFIG_PATH", str(new))
    monkeypatch.setattr(config, "LEGACY_USER_CONFIG_PATH", str(legacy))

    config._migrate_legacy_config()

    assert new.exists()
    assert json.loads(new.read_text(encoding="utf-8"))["builds"][0]["id"] == "x"


def test_migration_does_not_clobber_existing(tmp_path, monkeypatch):
    legacy = tmp_path / "legacy.json"
    legacy.write_text('{"from": "legacy"}', encoding="utf-8")
    new = tmp_path / "new.json"
    new.write_text('{"from": "new"}', encoding="utf-8")

    monkeypatch.setattr(config, "USER_CONFIG_PATH", str(new))
    monkeypatch.setattr(config, "LEGACY_USER_CONFIG_PATH", str(legacy))

    config._migrate_legacy_config()

    assert json.loads(new.read_text(encoding="utf-8")) == {"from": "new"}


def test_load_migrates_then_returns_builds(tmp_path, monkeypatch):
    legacy = tmp_path / "legacy" / "user_config.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"builds": [{"id": "keep-me"}]}', encoding="utf-8")
    new = tmp_path / "appdata" / "user_config.json"

    monkeypatch.setattr(config, "USER_CONFIG_PATH", str(new))
    monkeypatch.setattr(config, "LEGACY_USER_CONFIG_PATH", str(legacy))

    data = config.load_user_config()

    assert new.exists()
    assert data["builds"][0]["id"] == "keep-me"


def test_load_creates_defaults_when_none(tmp_path, monkeypatch):
    new = tmp_path / "appdata" / "user_config.json"
    legacy = tmp_path / "legacy" / "user_config.json"  # absent

    monkeypatch.setattr(config, "USER_CONFIG_PATH", str(new))
    monkeypatch.setattr(config, "LEGACY_USER_CONFIG_PATH", str(legacy))

    data = config.load_user_config()

    assert new.exists()
    assert "builds" in data
