"""Shared Qt fixtures.

One QApplication for the whole test session, kept alive by a module-level
reference. Per-module QApplication fixtures let the C++ application be
destroyed when that module finishes, which takes the ThemeManager singleton's
C++ object with it — every later test touching a Qt signal on THEME then dies
with "wrapped C/C++ object of type ThemeManager has been deleted".
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

_APP: QApplication | None = None


@pytest.fixture(scope="session", autouse=True)
def qapp():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP
