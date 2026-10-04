"""A broken custom theme never crashes the start or gets saved as the theme.

Regression: a theme imported without drag-text had None in its painted colors.
Apply saved it to the config first and only then repainted - QColor(None)
killed the launcher, and every start after died the same way before the main
window, because the config still named that theme.
"""

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

import config  # noqa: E402
from ui.theme.manager import ThemeManager  # noqa: E402
from ui.theme.theme_registry import ThemeRegistry  # noqa: E402
from ui.theme.tokens import DARK_THEME, THEMES  # noqa: E402

BROKEN = {**DARK_THEME, "icon_color_window": None, "accent": None}


@pytest.fixture
def setup(tmp_path, monkeypatch, qapp):
    """A themes folder with one good and one broken custom theme, loaded into
    a private registry, and a config file that names whatever the test wants."""
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()
    (themes_dir / "good.json").write_text(json.dumps(DARK_THEME), encoding="utf8")
    (themes_dir / "broken.json").write_text(json.dumps(BROKEN), encoding="utf8")

    themes = dict(THEMES)
    monkeypatch.setattr("ui.theme.theme_registry.THEMES", themes)
    monkeypatch.setattr("ui.theme.manager.THEMES", themes)
    monkeypatch.setattr(ThemeRegistry, "STORAGE_DIR", str(themes_dir))
    ThemeRegistry()

    cfg = tmp_path / "user_config.json"
    monkeypatch.setattr(config, "USER_CONFIG_PATH", str(cfg))
    monkeypatch.setattr("ui.theme.manager.CONFIG_PATH", str(cfg))

    def saved_theme(name):
        cfg.write_text(json.dumps({"theme": name, "builds": []}), encoding="utf-8")

    def theme_in_config():
        return json.loads(cfg.read_text(encoding="utf-8"))["theme"]

    return themes, saved_theme, theme_in_config


def test_start_falls_back_to_dark_on_a_broken_saved_theme(setup):
    themes, saved_theme, _ = setup
    assert "broken" not in themes
    saved_theme("broken")
    assert ThemeManager().name == "dark"


def test_start_falls_back_to_dark_on_a_missing_custom_theme(setup):
    _, saved_theme, _ = setup
    saved_theme("deleted_long_ago")
    assert ThemeManager().name == "dark"


def test_start_keeps_a_good_custom_theme(setup):
    _, saved_theme, _ = setup
    saved_theme("good")
    assert ThemeManager().name == "good"


def test_switch_refuses_a_broken_theme_and_saves_nothing(setup):
    themes, saved_theme, theme_in_config = setup
    saved_theme("dark")
    manager = ThemeManager()
    themes["broken"] = BROKEN

    with pytest.raises(ValueError, match="icon_color_window"):
        manager.switch("broken")

    assert manager.name == "dark"
    assert manager.colors is themes["dark"]
    assert theme_in_config() == "dark"


def test_switch_saves_only_after_the_theme_was_applied(setup, monkeypatch):
    _, saved_theme, theme_in_config = setup
    saved_theme("dark")
    manager = ThemeManager()

    def failing_apply():
        raise RuntimeError("repaint failed")

    monkeypatch.setattr(manager, "apply", failing_apply)
    with pytest.raises(RuntimeError):
        manager.switch("good")

    assert theme_in_config() == "dark"
    assert manager.name == "dark"
    assert manager.colors is THEMES["dark"]
