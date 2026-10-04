"""Importing a theme file that can't be used shows why and changes nothing.

Regression: _load_custom_theme let the importer's exceptions escape a Qt slot,
and PyQt6 aborts the process on that - no closeEvent, so the build's patched
main.py was never restored and ComfyUI kept running orphaned. A file missing
drag-text was imported "fine" and crashed the launcher once applied.
"""

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

import ui.settings.page_colortheme as page_module  # noqa: E402
from ui.theme.theme_registry import ThemeRegistry  # noqa: E402
from ui.theme.tokens import THEMES  # noqa: E402


@pytest.fixture
def themes_dir(tmp_path, monkeypatch):
    """Imported themes land here, not in the session's shared themes folder."""
    path = tmp_path / "themes"
    path.mkdir()
    monkeypatch.setattr(ThemeRegistry, "STORAGE_DIR", str(path))
    return path


@pytest.fixture
def page(qapp, monkeypatch, themes_dir):
    saved = dict(THEMES)
    warnings = []
    monkeypatch.setattr(
        page_module.MB, "warning", staticmethod(lambda *a: warnings.append(a))
    )
    widget = page_module.ColorThemesPage()
    widget.warnings = warnings
    yield widget
    widget.close()
    THEMES.clear()
    THEMES.update(saved)


def _import(page, monkeypatch, tmp_path, content, filename="my theme.json"):
    path = tmp_path / filename
    path.write_text(content, encoding="utf8")
    monkeypatch.setattr(
        page_module.QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a: (str(path), "")),
    )
    page._load_custom_theme()


@pytest.mark.parametrize(
    "content",
    [
        "{bad",
        "[1, 2]",
        json.dumps(
            {"colors": {"comfy_base": {"bg-color": "#000", "fg-color": "#fff"}}}
        ),
        json.dumps(
            {
                "colors": {
                    "comfy_base": {
                        "bg-color": "#000",
                        "fg-color": "#fff",
                        "drag-text": "not a color",
                    }
                }
            }
        ),
    ],
)
def test_a_broken_file_is_refused_with_a_message(
    page, monkeypatch, tmp_path, themes_dir, content
):
    themes_before = dict(THEMES)
    cards_before = set(page.cards)

    _import(page, monkeypatch, tmp_path, content)

    assert len(page.warnings) == 1
    _, title, text = page.warnings[0]
    assert title == "Theme not imported"
    assert "my theme.json" in text
    assert THEMES == themes_before
    assert os.listdir(themes_dir) == []
    assert set(page.cards) == cards_before
    assert not page.is_dirty()


def test_a_good_file_is_imported_and_selected(page, monkeypatch, tmp_path, themes_dir):
    base = {"bg-color": "#101010", "fg-color": "#eee", "drag-text": "#abc"}
    _import(
        page,
        monkeypatch,
        tmp_path,
        json.dumps({"colors": {"comfy_base": base}}),
        filename="Fine.json",
    )

    assert page.warnings == []
    assert page.selected_theme == "fine"
    assert THEMES["fine"]["icon_color_window"] == "#aabbcc"
    assert os.listdir(themes_dir) == ["fine.json"]


def test_a_theme_that_fails_to_apply_says_so(page, monkeypatch):
    def broken_switch(name):
        raise ValueError(f"Theme '{name}' is broken: \"accent\" is not a color")

    monkeypatch.setattr(page_module.THEME, "switch", broken_switch)
    page.selected_theme = "light"

    assert page.apply() is False
    assert len(page.warnings) == 1
    assert page.warnings[0][1] == "Theme not applied"
    assert "accent" in page.warnings[0][2]
