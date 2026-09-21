"""The internal console must show ComfyUI's text, not its colour codes.

ComfyUI colours its log levels, so the pipe carries sequences like
``\x1b[32m[INFO]\x1b[0m``. A terminal turns those into colour; the in-app
console rendered them literally, scattering litter through readable output.
"""

import io

from launcher import _read_process_output
from utils.console_buffer import ConsoleBuffer, strip_ansi


class _FakeProc:
    """Minimal stand-in for subprocess.Popen exposing only .stdout."""

    def __init__(self, stdout):
        self.stdout = stdout


def setup_function(_):
    ConsoleBuffer.clear()


def test_a_real_comfyui_line_loses_its_colour_codes():
    # Copied verbatim from this machine's ComfyUI startup log.
    ConsoleBuffer.add("\x1b[32m[INFO]\x1b[0m Total VRAM 15204 MB\n")
    assert ConsoleBuffer.get_all() == "[INFO] Total VRAM 15204 MB\n"


def test_the_reader_strips_colour_end_to_end():
    raw = "\x1b[32m[INFO]\x1b[0m starting\n\x1b[31m[ERROR]\x1b[0m bad\n"
    _read_process_output(_FakeProc(io.StringIO(raw)))
    assert ConsoleBuffer.get_all() == "[INFO] starting\n[ERROR] bad\n"


def test_cursor_moves_and_window_titles_go_too():
    """tqdm-style cursor control and OSC titles are litter in a text widget."""
    assert strip_ansi("\x1b[2K\x1b[1Gloading") == "loading"
    assert strip_ansi("\x1b]0;ComfyUI\x07ready") == "ready"


def test_plain_text_is_untouched():
    text = "Custom Node loaded — 中文, 100% [=====>]\n"
    assert strip_ansi(text) == text


def test_a_bare_bracket_is_not_mistaken_for_an_escape():
    """Only a real ESC introduces a sequence; ComfyUI's [INFO] must survive."""
    assert strip_ansi("[INFO] progress [32m] done") == "[INFO] progress [32m] done"
