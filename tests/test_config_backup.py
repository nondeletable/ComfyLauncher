"""Tests for the user-config backup outside %APPDATA%.

%APPDATA% does not survive a Windows reinstall, so every save is mirrored to
the app folder (when writable) or Documents, and the write is verified by
reading it back. On startup without a config, the newest backup is offered
for restore.
"""

import json
import sys

import pytest

import config

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


def test_app_backup_dir_is_next_to_exe_when_frozen(tmp_path, monkeypatch):
    exe = tmp_path / "Comfy Launcher" / "ComfyLauncher.exe"
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
    assert not (paths["app"] / "user_config.json.tmp").exists()


def test_write_verified_round_trips(paths):
    target = paths["app"] / "user_config.json"
    raw = json.dumps(CONFIG_WITH_BUILDS).encode("utf-8")

    assert config._write_verified(str(target), raw) is True
    assert target.read_bytes() == raw
    assert not (paths["app"] / "user_config.json.tmp").exists()


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
