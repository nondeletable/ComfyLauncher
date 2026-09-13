"""Tests for the flags picker model: parse/build round-trip, toggling,
exclusive groups, value/choice defaults and quick presets.

The dialog is a QWidget, so an offscreen QApplication is spun up once.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from ui.dialogs.flags_picker_dialog import FlagsPickerDialog  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def make(app, text=""):
    return FlagsPickerDialog(flags_text=text)


def test_roundtrip_preserves_unknown_tokens(app):
    text = "--windows-standalone-build --fast fp16_accumulation"
    d = make(app, text)
    # --fast is a known bool; the base flag and fp16_accumulation are unknown,
    # preserved verbatim and in place.
    assert d._build_string() == text
    assert d._is_active("--fast") is True
    assert d._is_active("--cpu") is False


def test_toggle_adds_and_removes(app):
    d = make(app, "")
    d._toggle("--lowvram")
    assert d._is_active("--lowvram") is True
    assert d._build_string() == "--lowvram"
    d._toggle("--lowvram")
    assert d._is_active("--lowvram") is False
    assert d._build_string() == ""


def test_exclusive_group_evicts_siblings(app):
    d = make(app, "")
    d._add("--lowvram")
    d._add("--cpu")  # same vram_group -> evicts --lowvram
    assert d._is_active("--cpu") is True
    assert d._is_active("--lowvram") is False


def test_value_flag_uses_default_then_edit(app):
    d = make(app, "")
    d._add("--port")
    assert d._build_string() == "--port 8188"
    d._on_value_edited("--port", "9000")
    assert d._build_string() == "--port 9000"


def test_value_flag_bare_when_value_cleared(app):
    d = make(app, "")
    d._add("--listen")
    assert d._build_string() == "--listen 0.0.0.0"
    d._on_value_edited("--listen", "")
    assert d._build_string() == "--listen"


def test_choice_flag_defaults_to_first_or_default(app):
    d = make(app, "")
    d._add("--preview-method")
    assert d._build_string() == "--preview-method auto"


def test_preset_additive_and_dedup(app):
    d = make(app, "--windows-standalone-build")
    d._apply_preset(["--cpu"])
    d._apply_preset(["--cpu"])  # dedup: no second --cpu
    assert d._build_string().split().count("--cpu") == 1
    assert d._is_active("--cpu") is True


def test_parse_value_flag_with_value(app):
    d = make(app, "--port 7000")
    assert d._is_active("--port") is True
    assert d._value_of("--port") == "7000"
    assert d._build_string() == "--port 7000"
