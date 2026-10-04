"""Detect and install the Microsoft Edge WebView2 Runtime (Windows only).

The launcher's web view on Windows is WebView2, which needs the Evergreen
Runtime installed system-wide. Without it the window cannot show ComfyUI and
the app failed with a raw error, so users simply uninstalled it.

Detection follows Microsoft's "Distribute your app and the WebView2 Runtime"
guide: ask the bundled WebView2Loader.dll first (it also sees Edge Beta/Dev/
Canary), and fall back to the ``pv`` registry values if the loader itself
cannot be loaded.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import requests

BOOTSTRAPPER_URL = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
DOWNLOAD_PAGE_URL = "https://developer.microsoft.com/microsoft-edge/webview2/"
# The bootstrapper downloads the whole runtime itself; a dead network must not
# leave the uncloseable "Installing..." box up forever.
INSTALL_TIMEOUT_S = 15 * 60

_ROOT = Path(__file__).resolve().parent.parent
_BUNDLED_DLL_DIR = _ROOT / "ui" / "webview2_dll"
# A frozen build carries the SDK DLLs in ui/webview2_dll; a source checkout
# has them in vendor/webview2.
DLL_DIR = (
    _BUNDLED_DLL_DIR if _BUNDLED_DLL_DIR.is_dir() else _ROOT / "vendor" / "webview2"
)
LOADER_DLL = DLL_DIR / "WebView2Loader.dll"

_CLIENT_KEY = r"Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
_REGISTRY_KEYS = (
    ("HKEY_LOCAL_MACHINE", rf"SOFTWARE\WOW6432Node\{_CLIENT_KEY}"),
    ("HKEY_LOCAL_MACHINE", rf"SOFTWARE\{_CLIENT_KEY}"),
    ("HKEY_CURRENT_USER", rf"Software\{_CLIENT_KEY}"),
)


def _is_real_version(value) -> bool:
    return isinstance(value, str) and value.strip() not in ("", "0.0.0.0")


def _version_from_loader() -> str | None:
    """Version string from the loader, or None if no runtime was found.

    Raises OSError when the loader DLL itself cannot be loaded.
    """
    import ctypes
    from ctypes import wintypes

    loader = ctypes.WinDLL(str(LOADER_DLL))
    fn = loader.GetAvailableCoreWebView2BrowserVersionString
    fn.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)]
    fn.restype = ctypes.c_long

    out = ctypes.c_void_p()
    if fn(None, ctypes.byref(out)) != 0 or not out.value:
        return None
    try:
        version = ctypes.wstring_at(out.value)
    finally:
        ctypes.windll.ole32.CoTaskMemFree(out)
    return version if _is_real_version(version) else None


def _version_from_registry() -> str | None:
    import winreg

    for hive_name, path in _REGISTRY_KEYS:
        hive = getattr(winreg, hive_name)
        try:
            with winreg.OpenKey(hive, path) as key:
                value, _ = winreg.QueryValueEx(key, "pv")
        except OSError:
            continue
        if _is_real_version(value):
            return value
    return None


def installed_version() -> str | None:
    """The installed WebView2 Runtime version, or None if there is none."""
    try:
        return _version_from_loader()
    except OSError:
        return _version_from_registry()


def download_bootstrapper(timeout: float = 60) -> Path:
    """Download Microsoft's ~2 MB Evergreen bootstrapper into a temp folder."""
    response = requests.get(BOOTSTRAPPER_URL, timeout=timeout)
    response.raise_for_status()
    target = (
        Path(tempfile.mkdtemp(prefix="comfylauncher-"))
        / "MicrosoftEdgeWebview2Setup.exe"
    )
    target.write_bytes(response.content)
    return target


def run_bootstrapper(path: Path) -> int:
    """Run the bootstrapper silently and wait; returns its exit code.

    Raises ``subprocess.TimeoutExpired`` (after killing it) if it hangs.

    Not elevated, it installs the runtime per-user (no UAC prompt); Microsoft
    replaces that with a per-machine install when Edge's updater is present.
    """
    try:
        return subprocess.run(
            [str(path), "/silent", "/install"],
            check=False,
            timeout=INSTALL_TIMEOUT_S,
        ).returncode
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)
