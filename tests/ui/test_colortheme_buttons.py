"""The Select / Download buttons must fit their labels on any font.

Regression: both were pinned with setFixedSize(80, 35). 80 px fits them in
Segoe UI on Windows but is exactly the width "Download" needs in the default
Linux sans — so the label was clipped there. Width is now a floor, not a cap.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtGui import QFont  # noqa: E402

from ui.settings.page_colortheme import ColorThemesPage  # noqa: E402


@pytest.fixture
def page(qapp):
    widget = ColorThemesPage()
    yield widget
    widget.close()


def test_buttons_are_not_width_capped(page):
    for btn in (page.btn_select, page.btn_download):
        assert btn.minimumWidth() == 80
        assert btn.maximumWidth() > 80, "a fixed width clips wider fonts"
        assert btn.height() == 35 or btn.minimumHeight() == 35


def test_a_wider_font_widens_the_button_instead_of_clipping(page):
    """The failure mode was silent: only the label's tail went missing."""
    before = page.btn_download.sizeHint().width()
    page.btn_download.setFont(QFont(page.btn_download.font().family(), 16))
    after = page.btn_download.sizeHint().width()
    assert after > before
    assert page.btn_download.maximumWidth() >= after
