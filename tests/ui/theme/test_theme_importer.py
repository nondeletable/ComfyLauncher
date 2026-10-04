import pytest

from ui.theme.tokens import DARK_THEME
from ui.theme.theme_importer import (
    ThemeImporter,
    _rgba_to_hex,
    _normalize_color,
    _lighten,
    _inverse_bw,
    ThemeImportError,
)


def test_rgba_to_hex_valid():
    result = _rgba_to_hex("rgba(40,42,54,0.95)")
    assert result == "#282A36"


def test_rgba_to_hex_no_valid():
    result = _rgba_to_hex("rgba(40,42)")
    assert result == "#000000"


def test_normalize_color_returns_none():
    result = _normalize_color("tu_040x42")
    assert result is None


def test_normalize_color_returns_hex():
    result = _normalize_color("#282A36")
    assert result == "#282A36"


def test_normalize_color_returns_again():
    result = _normalize_color("rgba(40,42,54,0.95)")
    assert result == "#282A36"


def test_lighten_no_valid():
    result = _lighten("000000")
    assert result == "000000"


def test_lighten_valid():
    result = _lighten("#353535")
    assert result == "#535353"


def test_inverse_bw_no_valid():
    result = _inverse_bw("000000")
    assert result == "#000000"


def test_invers_bw_if_light():
    result = _inverse_bw("#FFF5D6")
    assert result == "#000000"


def test_invers_bw_if_dark():
    result = _inverse_bw("#5E0000")
    assert result == "#FFFFFF"


@pytest.fixture
def importer():
    return ThemeImporter()


def test_load_json_valid(importer, tmp_path):
    theme_file = tmp_path / "theme.json"
    theme_file.write_text('{"colors": {}}', encoding="utf8")

    result = importer._load_json(str(theme_file))

    assert result == {"colors": {}}


def test_load_json_broken(importer, tmp_path):
    theme_file = tmp_path / "theme.json"
    theme_file.write_text("это не json", encoding="utf8")
    with pytest.raises(Exception):
        importer._load_json(str(theme_file))


def test_load_json_empty(importer):
    with pytest.raises(Exception):
        importer._load_json("несуществующий/путь/theme.json")


def test_extract_comfy_base_keys(importer):
    result = importer._extract_comfy_base({"colors": {"comfy_base": {"bg": "#000"}}})
    assert result == {"bg": "#000"}


def test_extract_comfy_base_no_keys(importer):
    result = importer._extract_comfy_base({})
    assert result == {}


def test_map_to_tokens_key_not_fit(importer):
    result = importer._map_to_tokens({"не подходит": "#000000"})
    assert result["bg_header"] is None


def test_map_to_tokens_key_fit_value_valid(importer):
    result = importer._map_to_tokens({"bg-color": "#010101"})
    assert result["bg_header"] == "#010101"


def test_map_to_tokens_key_fit_value_no_valid(importer):
    result = importer._map_to_tokens({"bg-color": "rgba(1,1,1,1)"})
    assert result["bg_header"] == "#010101"


# ─── A file that is not a usable theme is refused with a reason ───
# Regression: the importer used to raise raw JSONDecodeError / AttributeError /
# ValueError into a Qt slot (PyQt aborts the process on that), or to return a
# theme full of None that crashed the launcher once applied - and on every
# start after, since the theme was already saved.

VALID_BASE = {"bg-color": "#202020", "fg-color": "#fff", "drag-text": "#ccc"}


def _theme_file(tmp_path, content):
    path = tmp_path / "theme.json"
    path.write_text(content, encoding="utf8")
    return str(path)


def _comfy(base):
    import json

    return json.dumps({"colors": {"comfy_base": base}})


@pytest.mark.parametrize(
    "content, reason",
    [
        ("{bad", "not valid JSON"),
        ("", "not valid JSON"),
        ("[1, 2]", "colors.comfy_base"),
        ('{"x": 1}', "colors.comfy_base"),
        ('{"colors": []}', "colors.comfy_base"),
        ('{"colors": {"comfy_base": "dark"}}', "colors.comfy_base"),
        ('{"colors": {"comfy_base": {}}}', "colors.comfy_base"),
    ],
)
def test_load_refuses_a_file_that_is_not_a_theme(importer, tmp_path, content, reason):
    with pytest.raises(ThemeImportError, match=reason):
        importer.load(_theme_file(tmp_path, content))


def test_load_refuses_a_file_that_cannot_be_read(importer):
    with pytest.raises(ThemeImportError, match="could not be read"):
        importer.load("несуществующий/путь/theme.json")


@pytest.mark.parametrize("key", ["bg-color", "fg-color", "drag-text"])
def test_load_refuses_a_theme_without_a_required_color(importer, tmp_path, key):
    base = {k: v for k, v in VALID_BASE.items() if k != key}
    with pytest.raises(ThemeImportError, match=f"missing: {key}"):
        importer.load(_theme_file(tmp_path, _comfy(base)))


def test_load_refuses_a_required_color_set_to_null(importer, tmp_path):
    base = {**VALID_BASE, "drag-text": None}
    with pytest.raises(ThemeImportError, match="missing: drag-text"):
        importer.load(_theme_file(tmp_path, _comfy(base)))


@pytest.mark.parametrize(
    "value", ["red", "#12", "#abcd", "#zzzzzz", "", 42, [1, 2], "rgb(300, 0, 0)"]
)
def test_load_refuses_a_bad_color_string(importer, tmp_path, value):
    base = {**VALID_BASE, "border-color": value}
    with pytest.raises(ThemeImportError, match="border-color"):
        importer.load(_theme_file(tmp_path, _comfy(base)))


def test_load_accepts_short_hex_and_fills_the_painted_colors(importer, tmp_path):
    theme = importer.load(_theme_file(tmp_path, _comfy(VALID_BASE)))
    assert theme["bg_header"] == "#202020"
    assert theme["text_primary"] == "#ffffff"
    assert theme["icon_color_window"] == "#cccccc"
    assert theme["accent"] == "#cccccc"
    assert theme["error"] == DARK_THEME["error"]


def test_load_keeps_an_unknown_key_out_of_the_check(importer, tmp_path):
    """Palettes carry plenty of keys the launcher never reads (bar-shadow is
    "rgba(16, 16, 16, 0.5) 0 0 0.5rem" in ComfyUI's own) - they must not fail it."""
    base = {**VALID_BASE, "bar-shadow": "rgba(16, 16, 16, 0.5) 0 0 0.5rem"}
    base["tr-even-bg-color"] = "not a color"
    assert importer.load(_theme_file(tmp_path, _comfy(base)))["bg_header"]


@pytest.mark.parametrize(
    "value, expected",
    [
        ("#abc", "#aabbcc"),
        ("#AABBCC", "#AABBCC"),
        ("#11223344", "#112233"),
        ("rgb(1, 2, 3)", "#010203"),
        (None, None),
        (7, None),
    ],
)
def test_normalize_color_forms(value, expected):
    assert _normalize_color(value) == expected
