# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the macOS build (app bundle, arm64).
#
# Usage, from the repo root with the project's venv:
#   pyinstaller packaging/macos/ComfyLauncher.spec
# or, which does the same plus the bundle checks:
#   bash packaging/macos/build_macos.sh
#
# A committed .spec, unlike the Linux build which puts its PyInstaller config in
# build_appimage.sh: on macOS BUNDLE() is what turns the collected folder into
# ComfyLauncher.app, and info_plist is the only place the bundle metadata keys
# can be set. The .gitignore already carries the same exception for
# packaging/windows/*.spec, so a spec in packaging/ is deliberate here too.
#
# Output: <repo root>/dist/ComfyLauncher.app — PyInstaller writes dist/ and
# build/ into the current directory, as on Windows and Linux. Paths below are
# resolved from this file's location, so that holds wherever it is invoked from.
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))

# version.py is the single source of truth for the release number. It has to be
# passed explicitly: BUNDLE() defaults CFBundleShortVersionString to "0.0.0".
_version_ns = {}
with open(os.path.join(ROOT, "version.py"), encoding="utf-8") as _fh:
    exec(_fh.read(), _version_ns)
VERSION = _version_ns["__version__"]


a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(ROOT, "assets"), "assets"),
        (os.path.join(ROOT, "packaging", "windows", "THIRD-PARTY-NOTICES.txt"), "."),
    ],
    # The PyQt6 hooks bundle QtWebEngineProcess, the Chromium resources, ICU
    # data and the locales; these two are the modules the app imports but does
    # not reference literally anywhere the analysis can see.
    hiddenimports=[
        "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtWebEngineCore",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Windows-only dependencies of ui/webview2_widget.py. Not installed off
    # Windows, so excluding them only keeps the analysis from chasing them.
    excludes=[
        "clr",
        "pythonnet",
        "win32gui",
        "win32con",
        "win32api",
        "pywintypes",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ComfyLauncher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # No console window: the launcher is a GUI app, its own console dialog shows
    # the ComfyUI output.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    # arm64-only on purpose (plan §7-4): None follows the running interpreter, so
    # this can never produce a cross-arch or universal2 (double-size) bundle.
    # Intel macOS support is out of scope for this port.
    target_arch=None,
    # Ad-hoc signing is added in Task 5 via the build script; leaving these None
    # keeps PyInstaller from signing with an identity we do not have.
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ComfyLauncher",
)
app = BUNDLE(
    coll,
    name="ComfyLauncher.app",
    # No icon yet: assets/ has icon.png (256x256) but no .icns, and an .icns
    # built from a 256px source is blurry on Retina. None makes BUNDLE() fall
    # back to PyInstaller's own icon. Task 4 owns the real one.
    icon=None,
    version=VERSION,
    # Reverse-DNS of the upstream owner (github.com/nondeletable). Task 4's
    # CFBundleIdentifier has to match this; the maintainer may want a different
    # value, it is a placeholder until they say so.
    bundle_identifier="com.nondeletable.ComfyLauncher",
    info_plist={
        # Empty so far: PyInstaller already sets CFBundleExecutable,
        # CFBundleIdentifier, CFBundleName, CFBundleDisplayName,
        # CFBundleShortVersionString and NSHighResolutionCapable. Task 4 adds
        # CFBundleIconFile and LSMinimumSystemVersion here.
    },
)
