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


# ── Stage 3: startup_mode → extra_flags fold ──────────────────────────


def test_migrate_gpu_mode():
    b = {"id": "b", "startup_mode": "gpu", "extra_flags": []}
    config._migrate_build_flags(b)
    assert b["extra_flags"] == ["--windows-standalone-build"]
    assert "startup_mode" not in b


def test_migrate_cpu_mode():
    b = {"id": "b", "startup_mode": "cpu", "extra_flags": []}
    config._migrate_build_flags(b)
    assert b["extra_flags"] == ["--cpu", "--windows-standalone-build"]
    assert "startup_mode" not in b


def test_migrate_fast_fp16_mode():
    b = {"id": "b", "startup_mode": "fast_fp16", "extra_flags": []}
    config._migrate_build_flags(b)
    assert b["extra_flags"] == [
        "--windows-standalone-build",
        "--fast",
        "fp16_accumulation",
    ]
    assert "startup_mode" not in b


def test_migrate_custom_mode_keeps_flags_verbatim():
    b = {"id": "b", "startup_mode": "custom", "extra_flags": ["--port", "9000"]}
    config._migrate_build_flags(b)
    assert b["extra_flags"] == ["--port", "9000"]
    assert "startup_mode" not in b


def test_migrate_unknown_mode_falls_back_to_gpu():
    b = {"id": "b", "startup_mode": "weird", "extra_flags": []}
    config._migrate_build_flags(b)
    assert b["extra_flags"] == ["--windows-standalone-build"]


def test_migrate_preset_dedupes_hand_edited_extra_flags():
    # A hand-edited config may already carry a preset flag in extra_flags.
    b = {
        "id": "b",
        "startup_mode": "cpu",
        "extra_flags": ["--windows-standalone-build", "--lowvram"],
    }
    config._migrate_build_flags(b)
    assert b["extra_flags"] == ["--cpu", "--windows-standalone-build", "--lowvram"]


def test_migrate_is_idempotent():
    b = {"id": "b", "startup_mode": "gpu", "extra_flags": []}
    config._migrate_build_flags(b)
    once = list(b["extra_flags"])
    config._migrate_build_flags(b)
    assert b["extra_flags"] == once
    assert "startup_mode" not in b


def test_migrate_missing_startup_mode_only_ensures_extra_flags():
    b = {"id": "b"}
    config._migrate_build_flags(b)
    assert b["extra_flags"] == []
    assert "startup_mode" not in b


def test_load_user_config_migrates_builds(tmp_path, monkeypatch):
    new = tmp_path / "appdata" / "user_config.json"
    new.parent.mkdir(parents=True)
    new.write_text(
        '{"builds": [{"id": "x", "startup_mode": "fast_fp16", "extra_flags": []}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "USER_CONFIG_PATH", str(new))

    data = config.load_user_config()
    build = data["builds"][0]

    assert build["extra_flags"] == [
        "--windows-standalone-build",
        "--fast",
        "fp16_accumulation",
    ]
    assert "startup_mode" not in build
