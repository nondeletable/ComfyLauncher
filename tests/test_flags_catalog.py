"""Tests for the bundled startup-flags catalog and its loader."""

import json

from utils.flags_catalog import load_flags_catalog, iter_flags

VALID_TYPES = {"bool", "value", "choice"}


def test_catalog_loads_and_is_nonempty():
    cat = load_flags_catalog()
    assert isinstance(cat, dict)
    assert isinstance(cat["groups"], list)
    assert len(cat["groups"]) > 0
    assert sum(len(g["flags"]) for g in cat["groups"]) > 0


def test_every_flag_is_well_formed():
    for f in iter_flags():
        assert f["flag"].startswith("--"), f
        assert f["type"] in VALID_TYPES, f
        assert f["description"], f
        if f["type"] == "bool":
            # a toggle carries no value metadata
            assert f["value_type"] is None, f
            assert f["choices"] is None, f
            assert f["default"] is None, f
        elif f["type"] == "value":
            assert f["value_type"] in {"int", "float", "str"}, f
        elif f["type"] == "choice":
            assert isinstance(f["choices"], list) and f["choices"], f


def test_preset_flags_are_covered():
    flags = {f["flag"] for f in iter_flags()}
    # flags the old LAUNCH_PRESETS relied on must be discoverable in the picker
    assert "--cpu" in flags
    assert "--fast" in flags
    # the always-on base flag stays out of the picker (it lives in the field)
    assert "--windows-standalone-build" not in flags


def test_exclusive_groups_present():
    # mutually-exclusive metadata must survive generation (used to de-select siblings)
    groups = {f["exclusive_group"] for f in iter_flags() if f["exclusive_group"]}
    assert "vram_group" in groups


def test_missing_file_returns_empty(tmp_path):
    cat = load_flags_catalog(str(tmp_path / "nope.json"))
    assert cat == {"groups": []}


def test_malformed_file_returns_empty(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert load_flags_catalog(str(bad)) == {"groups": []}


def test_non_dict_json_returns_empty(tmp_path):
    arr = tmp_path / "arr.json"
    arr.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    assert load_flags_catalog(str(arr)) == {"groups": []}
