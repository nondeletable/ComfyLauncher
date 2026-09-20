"""Shared Qt fixtures.

One QApplication for the whole test session, kept alive by a module-level
reference. Per-module QApplication fixtures let the C++ application be
destroyed when that module finishes, which takes the ThemeManager singleton's
C++ object with it — every later test touching a Qt signal on THEME then dies
with "wrapped C/C++ object of type ThemeManager has been deleted".
"""

import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Point the app's per-user directory at a throwaway one, before anything
# imports config.py (it resolves APP_DATA_DIR at import time). Without this the
# suite reads — and, through ComfyBrowser.closeEvent, *writes* — the developer's
# real user_config.json: whatever builds and exit settings happen to be there
# steer the tests, and the tests steer them back.
_TEST_APP_DIR = tempfile.mkdtemp(prefix="comfylauncher-tests-")
os.environ["XDG_CONFIG_HOME"] = _TEST_APP_DIR  # Linux
os.environ["APPDATA"] = _TEST_APP_DIR  # Windows

import pytest  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

_APP: QApplication | None = None


@pytest.fixture(scope="session", autouse=True)
def quiet_exit_config():
    """Give the isolated config an answer for ComfyBrowser's exit prompt.

    ``closeEvent`` opens a modal "Shut down ComfyUI server?" box whenever
    ``ask_on_exit`` is set, and ``exec()`` on a headless run waits forever — any
    test that closes the main window hangs. The default for the key is True, so
    the isolated directory needs this written out explicitly.
    """
    import json

    from config import USER_CONFIG_PATH

    os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
    with open(USER_CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump({"ask_on_exit": False, "exit_mode": "never_stop"}, fh)
    yield


@pytest.fixture(scope="session", autouse=True)
def qapp():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP
