import json

import pytest

from ui.theme.tokens import DARK_THEME


@pytest.fixture
def registry(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "ui.theme.theme_registry.ThemeRegistry.STORAGE_DIR", str(tmp_path)
    )
    fake_themes = {}
    monkeypatch.setattr("ui.theme.theme_registry.THEMES", fake_themes)

    from ui.theme.theme_registry import ThemeRegistry

    return ThemeRegistry()


def test_theme_exists_returns_name_when_found(registry, monkeypatch):
    fake_themes = {"dark": {"bg": "#000"}}
    monkeypatch.setattr("ui.theme.theme_registry.THEMES", fake_themes)
    result = registry.theme_exists({"bg": "#000"})
    assert result == "dark"


def test_theme_exists_returns_none_when_not_found(registry, monkeypatch):
    fake_themes = {"dark": {"bg": "#000"}}
    monkeypatch.setattr("ui.theme.theme_registry.THEMES", fake_themes)
    result = registry.theme_exists({"bg": "#ffffff"})

    assert result is None


def test_add_custom_returns_name(registry, monkeypatch):
    fake_themes = {}
    monkeypatch.setattr("ui.theme.theme_registry.THEMES", fake_themes)
    result = registry.add_custom("name_string", {})

    assert result == "name_string"


def test_add_custom_returns_name_andone(registry, monkeypatch):
    fake_themes = {"name_string": {"bg": "#000"}}
    monkeypatch.setattr("ui.theme.theme_registry.THEMES", fake_themes)
    result = registry.add_custom("name_string", {})

    assert result == "name_string-1"


def test_load_existing_loads_themes_when_files_exist(registry, tmp_path, monkeypatch):
    theme_file = tmp_path / "my_theme.json"
    theme_file.write_text(json.dumps(DARK_THEME), encoding="utf8")

    fake_themes = {}
    monkeypatch.setattr("ui.theme.theme_registry.THEMES", fake_themes)
    monkeypatch.setattr(
        "ui.theme.theme_registry.ThemeRegistry.STORAGE_DIR", str(tmp_path)
    )

    registry._load_existing()

    assert fake_themes == {"my_theme": DARK_THEME}


def test_load_existing_loads_themes_when_files_no_exist(
    registry, tmp_path, monkeypatch
):
    fake_themes = {}
    monkeypatch.setattr("ui.theme.theme_registry.THEMES", fake_themes)
    monkeypatch.setattr(
        "ui.theme.theme_registry.ThemeRegistry.STORAGE_DIR", str(tmp_path)
    )

    registry._load_existing()

    assert fake_themes == {}


def test_load_existing_loads_themes_when_file_name_matches(
    registry, tmp_path, monkeypatch
):
    theme_file = tmp_path / "my_theme.json"
    theme_file.write_text('{"bg": "#111"}', encoding="utf8")
    fake_themes = {"my_theme": {"bg": "#000"}}
    monkeypatch.setattr("ui.theme.theme_registry.THEMES", fake_themes)

    registry._load_existing()

    assert fake_themes == {"my_theme": {"bg": "#000"}}


def test_load_existing_loads_themes_when_file_no_valid(registry, tmp_path, monkeypatch):
    theme_file = tmp_path / "my_theme.json"
    theme_file.write_text("это не json", encoding="utf8")
    logged = []
    monkeypatch.setattr(
        "ui.theme.theme_registry.log_event", lambda msg: logged.append(msg)
    )

    registry._load_existing()

    assert len(logged) > 0


# ─── A saved theme that would crash the app is skipped at load ───


def _broken(**changes):
    theme = {k: v for k, v in DARK_THEME.items() if k != "warning"}
    theme.update(changes)
    return {k: v for k, v in theme.items() if v != "DROP"}


@pytest.mark.parametrize(
    "theme",
    [
        _broken(icon_color_window=None),
        _broken(accent="not a color"),
        _broken(bg_header="DROP"),
        _broken(warning=None),
        [1, 2],
    ],
)
def test_load_existing_skips_a_broken_theme(registry, tmp_path, monkeypatch, theme):
    (tmp_path / "broken.json").write_text(json.dumps(theme), encoding="utf8")
    fake_themes = {}
    logged = []
    monkeypatch.setattr("ui.theme.theme_registry.THEMES", fake_themes)
    monkeypatch.setattr(
        "ui.theme.theme_registry.log_event", lambda msg: logged.append(msg)
    )

    registry._load_existing()

    assert fake_themes == {}
    assert any("broken.json" in m for m in logged)


def test_theme_problems_tolerates_stylesheet_only_nulls():
    """Themes from comfyui-themes.com lack a few stylesheet-only colors, and
    those imported before validation existed carry them as null and no
    "warning" - they work today and must keep loading."""
    from ui.theme.theme_registry import theme_problems

    theme = _broken(bg_hover=None, popup_bg=None, popup_text=None)
    assert theme_problems(theme) == []
    assert theme_problems(_broken(text_disabled="DROP")) == []
    assert theme_problems(DARK_THEME) == []


@pytest.mark.parametrize("error", [None, "", "DROP"])
def test_load_existing_repairs_a_theme_without_an_error_color(
    registry, tmp_path, monkeypatch, error
):
    """Older imports saved "error": null; the importer fills it from the dark
    theme today, so loading does the same instead of dropping the theme."""
    (tmp_path / "old.json").write_text(json.dumps(_broken(error=error)), "utf8")
    fake_themes = {}
    monkeypatch.setattr("ui.theme.theme_registry.THEMES", fake_themes)

    registry._load_existing()

    assert fake_themes["old"]["error"] == DARK_THEME["error"]
