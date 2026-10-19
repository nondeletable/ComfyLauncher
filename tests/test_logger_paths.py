"""The log directory must live inside the shared per-user app directory.

``utils/logger.py`` used to resolve the base itself
(``APPDATA or LOCALAPPDATA or ~``), so off Windows both variables were empty
and logs landed in a bare ``~/ComfyLauncher/logs`` instead of the app's
directory. Stage 1's path facade had missed this file because
``utils.platform_paths`` imports the logger.
"""

import importlib
import os
import sys

import pytest

import utils.logger as logger_mod
from utils.platform_paths import app_dir


def test_log_dir_is_inside_the_app_dir():
    assert logger_mod.LOG_DIR == os.path.join(app_dir(), "logs")
    assert logger_mod.LOG_FILE == os.path.join(app_dir(), "logs", "launcher.log")


@pytest.mark.skipif(sys.platform == "win32", reason="XDG is not a Windows concept")
def test_log_dir_follows_platform_config_home(monkeypatch, tmp_path):
    """Regression: no more logs in the home directory root.

    Linux honors ``XDG_CONFIG_HOME``; macOS deliberately ignores it and uses
    ``~/Library/Application Support`` instead (``utils.platform_paths.app_dir``).
    Asserting the macOS path here keeps that branch on a real code path.
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    # The app-level override outranks the platform default by design, so drop
    # it here: this test asserts what the *platform* branch resolves to.
    monkeypatch.delenv("COMFYLAUNCHER_CONFIG_HOME", raising=False)
    try:
        importlib.reload(logger_mod)
        if sys.platform == "darwin":
            base = os.path.join(
                os.path.expanduser("~"), "Library", "Application Support"
            )
        else:
            base = str(tmp_path)
        expected = os.path.join(base, "ComfyLauncher", "logs")
        assert logger_mod.LOG_DIR == expected
        assert os.path.isdir(expected)
        # The old behavior; asserting on the directory's absence instead would
        # fail on a machine where a previous version already created it.
        home_root = os.path.join(os.path.expanduser("~"), "ComfyLauncher", "logs")
        assert logger_mod.LOG_DIR != home_root
    finally:
        monkeypatch.undo()
        importlib.reload(logger_mod)


def test_platform_paths_has_no_module_level_logger_import():
    """The cycle is broken by importing log_event inside the function; a
    module-level import would make utils.logger unimportable."""
    source = open(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "utils",
            "platform_paths.py",
        ),
        encoding="utf-8",
    ).read()
    module_level = [
        line
        for line in source.splitlines()
        if line.startswith("from utils.logger")
        or line.startswith("import utils.logger")
    ]
    assert module_level == []
