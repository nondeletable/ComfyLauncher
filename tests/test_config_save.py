"""Tests for atomic config saves and default-config isolation.

save_user_config writes through _write_verified, so a write that fails midway
leaves the previous config in place. load_user_config hands out deep copies of
DEFAULT_USER_CONFIG: mutating a nested list/dict of the result must not leak
into the module-level constant.
"""

import json
import os

import pytest

import config

GOOD = {"builds": [{"id": "b1", "path": "D:/ComfyUI"}], "theme": "light"}


@pytest.fixture
def cfg_path(tmp_path, monkeypatch):
    path = tmp_path / "appdata" / "user_config.json"
    monkeypatch.setattr(config, "USER_CONFIG_PATH", str(path))
    monkeypatch.setattr(config, "LEGACY_USER_CONFIG_PATH", str(tmp_path / "none"))
    monkeypatch.setattr(config, "backup_user_config", lambda: None)
    return path


@pytest.fixture
def logged(monkeypatch):
    messages = []
    monkeypatch.setattr(config, "log_event", messages.append)
    return messages


# ── Atomic save ───────────────────────────────


def test_failed_replace_keeps_previous_config(cfg_path, monkeypatch, logged):
    assert config.save_user_config(GOOD) is True

    def boom(src, dst):
        raise OSError("simulated crash during replace")

    monkeypatch.setattr(config.os, "replace", boom)

    assert config.save_user_config({"builds": []}) is False
    assert json.loads(cfg_path.read_text(encoding="utf-8")) == GOOD
    assert os.listdir(cfg_path.parent) == [cfg_path.name]  # no .tmp left over


def test_unserializable_data_keeps_previous_config(cfg_path, logged):
    assert config.save_user_config(GOOD) is True

    assert config.save_user_config({"bad": object()}) is False
    assert json.loads(cfg_path.read_text(encoding="utf-8")) == GOOD
    assert any("Failed to save config" in m for m in logged)
