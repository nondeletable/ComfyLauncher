"""The About logo loops an animated WebP through QMovie, not a QMediaPlayer.

The logo used to be a 1520x1520 60 fps H.264 video in a QVideoWidget: the
first visit to About paid ~300 ms for the multimedia backend, and headless runs
could die in the decoder.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtGui import QMovie  # noqa: E402

from ui.settings import page_about  # noqa: E402
from ui.settings.page_about import AnimatedLogo  # noqa: E402


@pytest.fixture
def logo(qapp):
    w = AnimatedLogo()
    yield w
    w.deleteLater()


def test_the_bundled_animation_loads_with_all_its_frames(logo):
    assert logo.movie.isValid()
    assert logo.movie.frameCount() > 1
    assert not logo.background.isNull()


def test_plays_only_while_shown(logo):
    assert logo.movie.state() == QMovie.MovieState.NotRunning
    logo.show()
    assert logo.movie.state() == QMovie.MovieState.Running
    logo.hide()
    assert logo.movie.state() == QMovie.MovieState.NotRunning


def test_paints_the_current_frame_over_the_backdrop(logo):
    logo.show()
    image = logo.grab().toImage()
    inset = (AnimatedLogo.SIZE - AnimatedLogo.ANIM_SIZE) // 2
    orange = [
        (x, y)
        for x in range(inset, inset + AnimatedLogo.ANIM_SIZE)
        for y in range(inset, inset + AnimatedLogo.ANIM_SIZE)
        if image.pixelColor(x, y).red() > 200 and image.pixelColor(x, y).blue() < 100
    ]
    assert orange


@pytest.mark.parametrize("content", [None, b"RIFF0000WEBPjunk"])
def test_an_unloadable_animation_is_logged_and_leaves_the_backdrop(
    qapp, monkeypatch, tmp_path, content
):
    path = tmp_path / "menu_anim.webp"
    if content is not None:
        path.write_bytes(content)
    logs = []
    monkeypatch.setattr(page_about, "ABOUT_LOGO_ANIM", str(path))
    monkeypatch.setattr(page_about, "log_event", logs.append)

    w = AnimatedLogo()
    w.show()
    image = w.grab().toImage()
    w.deleteLater()

    assert len(logs) == 1 and str(path) in logs[0]
    assert not image.isNull()


def test_a_loadable_animation_logs_nothing(qapp, monkeypatch):
    logs = []
    monkeypatch.setattr(page_about, "log_event", logs.append)
    AnimatedLogo().deleteLater()
    assert logs == []
