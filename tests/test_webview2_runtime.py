"""WebView2 Runtime detection, per Microsoft's distribution guide.

A runtime counts as installed only with a real version: the registry ``pv``
value may be missing, empty, or "0.0.0.0" on a machine without it.
"""

import sys

import pytest

from utils import webview2_runtime as runtime

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")


@pytest.mark.parametrize(
    "value, real",
    [
        ("149.0.4022.98", True),
        ("0.0.0.0", False),
        ("", False),
        (" ", False),
        (None, False),
    ],
)
def test_only_a_real_version_counts(value, real):
    assert runtime._is_real_version(value) is real


def test_loader_answer_wins(monkeypatch):
    monkeypatch.setattr(runtime, "_version_from_loader", lambda: "1.2.3.4")
    monkeypatch.setattr(runtime, "_version_from_registry", lambda: pytest.fail())
    assert runtime.installed_version() == "1.2.3.4"


def test_loader_saying_none_is_trusted(monkeypatch):
    monkeypatch.setattr(runtime, "_version_from_loader", lambda: None)
    monkeypatch.setattr(runtime, "_version_from_registry", lambda: "1.2.3.4")
    assert runtime.installed_version() is None


def test_registry_is_the_fallback_when_the_loader_cannot_load(monkeypatch):
    def broken():
        raise OSError("WebView2Loader.dll not found")

    monkeypatch.setattr(runtime, "_version_from_loader", broken)
    monkeypatch.setattr(runtime, "_version_from_registry", lambda: "1.2.3.4")
    assert runtime.installed_version() == "1.2.3.4"


def test_registry_skips_placeholder_values(monkeypatch):
    import winreg

    values = iter(["0.0.0.0", "", "149.0.4022.98"])

    class Key:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(winreg, "OpenKey", lambda hive, path: Key())
    monkeypatch.setattr(winreg, "QueryValueEx", lambda key, name: (next(values), 1))
    assert runtime._version_from_registry() == "149.0.4022.98"


def test_registry_without_any_key_means_not_installed(monkeypatch):
    import winreg

    def missing(hive, path):
        raise FileNotFoundError

    monkeypatch.setattr(winreg, "OpenKey", missing)
    assert runtime._version_from_registry() is None


def test_bootstrapper_run_cleans_up_its_temp_folder(tmp_path, monkeypatch):
    folder = tmp_path / "comfylauncher-x"
    folder.mkdir()
    exe = folder / "MicrosoftEdgeWebview2Setup.exe"
    exe.write_bytes(b"")
    monkeypatch.setattr(
        runtime.subprocess, "run", lambda *a, **k: type("P", (), {"returncode": 0})()
    )
    assert runtime.run_bootstrapper(exe) == 0
    assert not folder.exists()


def test_bootstrapper_run_has_a_timeout(tmp_path, monkeypatch):
    seen = {}

    def run(args, **kwargs):
        seen.update(kwargs)
        raise runtime.subprocess.TimeoutExpired(args, kwargs["timeout"])

    monkeypatch.setattr(runtime.subprocess, "run", run)
    exe = tmp_path / "setup.exe"
    with pytest.raises(runtime.subprocess.TimeoutExpired):
        runtime.run_bootstrapper(exe)
    assert seen["timeout"] == runtime.INSTALL_TIMEOUT_S


def test_a_source_checkout_loads_the_vendored_dlls():
    assert runtime.DLL_DIR == runtime._ROOT / "vendor" / "webview2"
    assert runtime.LOADER_DLL.is_file()
