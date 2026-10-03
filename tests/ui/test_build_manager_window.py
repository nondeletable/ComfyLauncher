"""The build selector must minimize from a taskbar click on Windows.

As a frameless dialog it lost WS_MINIMIZEBOX, so a taskbar click could not
minimize it.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys  # noqa: E402

import pytest  # noqa: E402
from PyQt6.QtCore import Qt  # noqa: E402

import ui.dialogs.build_manager_dialog as bm  # noqa: E402

Dialog = bm.BuildManagerDialog


@pytest.fixture
def store(monkeypatch):
    """Back the dialog's config with an in-memory dict."""
    data = {"builds": [], "last_used_build_id": ""}
    monkeypatch.setattr(bm, "load_user_config", lambda: dict(data))
    return data


def make(qapp):
    dlg = Dialog()
    qapp.processEvents()
    return dlg


@pytest.mark.skipif(sys.platform != "win32", reason="WS_MINIMIZEBOX is Windows-only")
def test_selector_keeps_its_minimize_box_on_windows(qapp, store):
    assert make(qapp).windowFlags() & Qt.WindowType.WindowMinimizeButtonHint
