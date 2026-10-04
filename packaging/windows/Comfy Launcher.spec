# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the Windows build (onedir, windowed).
#
# Usage, from the repo root with the project's venv:
#   pyinstaller "packaging/windows/Comfy Launcher.spec"
#
# Output: dist/Comfy Launcher/ (exe + _internal). Paths below are resolved
# from this file's location, so the build does not depend on the machine.
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, '..', '..'))
WEBVIEW2 = os.path.join(ROOT, 'vendor', 'webview2')


a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[],
    binaries=[(os.path.join(WEBVIEW2, 'Microsoft.Web.WebView2.Core.dll'), 'ui\\webview2_dll'), (os.path.join(WEBVIEW2, 'Microsoft.Web.WebView2.WinForms.dll'), 'ui\\webview2_dll'), (os.path.join(WEBVIEW2, 'WebView2Loader.dll'), 'ui\\webview2_dll')],
    datas=[(os.path.join(ROOT, 'assets'), 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Comfy Launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(ROOT, 'assets', 'icons', 'icon.ico')],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Comfy Launcher',
)
