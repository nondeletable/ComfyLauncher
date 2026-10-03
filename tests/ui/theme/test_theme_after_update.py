"""The first start after updating from 1.7.0 or older keeps the user's theme.

Those versions kept user_config.json in the app folder; 1.8.0 moved it to
%APPDATA% and migrates it on the first config read. The theme manager is
created at import, before anything else reads the config, and used to open
the new location directly - found nothing there, and fell back to dark.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import config  # noqa: E402
from ui.theme.manager import ThemeManager  # noqa: E402


def test_theme_survives_the_config_move(tmp_path, monkeypatch, qapp):
    legacy = tmp_path / "app" / "user_config.json"
    legacy.parent.mkdir()
    legacy.write_text('{"theme": "light", "builds": []}', encoding="utf-8")
    new = tmp_path / "appdata" / "user_config.json"

    monkeypatch.setattr(config, "USER_CONFIG_PATH", str(new))
    monkeypatch.setattr(config, "LEGACY_USER_CONFIG_PATH", str(legacy))

    assert ThemeManager().name == "light"
    assert new.exists()


def test_a_junk_theme_value_falls_back_to_dark(tmp_path, monkeypatch, qapp):
    new = tmp_path / "user_config.json"
    new.write_text('{"theme": [], "builds": []}', encoding="utf-8")
    monkeypatch.setattr(config, "USER_CONFIG_PATH", str(new))
    assert ThemeManager().name == "dark"
