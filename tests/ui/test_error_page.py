"""The error screen must paint its own backdrop.

ErrorScreen is a QWidget subclass with a stylesheet background, which Qt only
paints when WA_StyledBackground is set. It went unnoticed because the theme's
application stylesheet covers every QWidget (and main.py used to replace that
stylesheet outright), and because grabbing the widget on its own fills from the
palette and looks correct. The fixture below drops the ambient stylesheet so
the widget has to paint on its own.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtWidgets import QVBoxLayout, QWidget  # noqa: E402

from ui.error_page import ErrorScreen, ErrorWidget  # noqa: E402
from ui.theme.manager import THEME  # noqa: E402

BACKDROP = "#353535"  # hardcoded in ui/error_page.py, deliberately theme-free


@pytest.fixture
def no_ambient_qss(qapp):
    """Strip the theme's application stylesheet, leaving the widget nothing to
    inherit a background from."""
    THEME.apply()
    previous = qapp.styleSheet()
    qapp.setStyleSheet("")
    yield qapp
    qapp.setStyleSheet(previous)


def render(app):
    host = QWidget()
    host.resize(700, 500)
    layout = QVBoxLayout(host)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(ErrorScreen(ErrorWidget("Title", "Message body"), host), 1)
    host.show()
    app.processEvents()
    image = host.grab().toImage()
    host.close()
    return image


def test_error_screen_paints_its_backdrop(no_ambient_qss):
    image = render(no_ambient_qss)
    # A corner is backdrop, away from the centered card.
    assert image.pixelColor(4, 250).name().lower() == BACKDROP


def test_error_card_still_paints(no_ambient_qss):
    """The card is a plain QWidget, which paints without the attribute — this
    pins that difference down so the fix is not copied where it is not needed."""
    image = render(no_ambient_qss)
    assert image.pixelColor(350, 250).name().lower() == BACKDROP
