#!/usr/bin/env bash
#
# Build a Linux AppImage of ComfyLauncher (QtWebEngine engine).
#
# Run this ON LINUX only (Ubuntu 24.04 LTS target). An AppImage bundles Linux
# .so libraries and is assembled by appimagetool, which does not run on Windows.
#
# Usage:
#   cd packaging/linux
#   ./build_appimage.sh
#
# Prerequisites (see BUILD.md):
#   - the project's venv activated with `pip install -r requirements.txt` done
#   - libfuse2 installed (to run the resulting AppImage; older AppImage runtime)
#   - internet access (downloads appimagetool once, into this folder)
#
# Output: packaging/linux/ComfyLauncher-x86_64.AppImage
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

APP_NAME="ComfyLauncher"
DIST_DIR="${REPO_ROOT}/dist/${APP_NAME}"
APPDIR="${SCRIPT_DIR}/${APP_NAME}.AppDir"
ICON_SRC="${REPO_ROOT}/assets/icons/icon.png"
OUTPUT="${SCRIPT_DIR}/${APP_NAME}-x86_64.AppImage"
APPIMAGETOOL="${SCRIPT_DIR}/appimagetool-x86_64.AppImage"

echo "==> repo root: ${REPO_ROOT}"

# --- sanity checks --------------------------------------------------------
if ! python -c "import PyInstaller" >/dev/null 2>&1; then
    echo "ERROR: PyInstaller not importable. Activate the venv and run" >&2
    echo "       pip install -r requirements.txt first." >&2
    exit 1
fi
if ! python -c "import PyQt6.QtWebEngineWidgets" >/dev/null 2>&1; then
    echo "ERROR: PyQt6-WebEngine not importable — the Linux engine is missing." >&2
    echo "       Check requirements.txt installed the non-win32 Qt 6.11 wheels." >&2
    exit 1
fi
if [ ! -f "${ICON_SRC}" ]; then
    echo "ERROR: icon not found at ${ICON_SRC}" >&2
    exit 1
fi

# --- 1. PyInstaller onedir build -----------------------------------------
# CLI flags (not a .spec) on purpose: *.spec is gitignored, so keeping the
# build config here means it actually ships in the repo. PyInstaller's PyQt6
# hooks pull in QtWebEngineProcess, the Chromium resources, ICU data, locales
# and translations automatically.
echo "==> running PyInstaller (onedir)…"
cd "${REPO_ROOT}"
rm -rf build "dist/${APP_NAME}"
python -m PyInstaller main.py \
    --name "${APP_NAME}" \
    --noconfirm \
    --clean \
    --noconsole \
    --add-data "assets:assets" \
    --hidden-import PyQt6.QtWebEngineWidgets \
    --hidden-import PyQt6.QtWebEngineCore \
    --exclude-module clr \
    --exclude-module pythonnet \
    --exclude-module win32gui \
    --exclude-module win32con \
    --exclude-module win32api \
    --exclude-module pywintypes

if [ ! -x "${DIST_DIR}/${APP_NAME}" ]; then
    echo "ERROR: expected executable ${DIST_DIR}/${APP_NAME} was not produced." >&2
    exit 1
fi

# --- 2. assemble the AppDir ----------------------------------------------
echo "==> assembling AppDir…"
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

cp -r "${DIST_DIR}" "${APPDIR}/usr/bin/${APP_NAME}"

cp "${SCRIPT_DIR}/AppRun" "${APPDIR}/AppRun"
chmod +x "${APPDIR}/AppRun"

cp "${SCRIPT_DIR}/comfylauncher.desktop" "${APPDIR}/comfylauncher.desktop"
cp "${ICON_SRC}" "${APPDIR}/comfylauncher.png"
cp "${ICON_SRC}" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/comfylauncher.png"

# --- 3. fetch appimagetool (once) ----------------------------------------
if [ ! -f "${APPIMAGETOOL}" ]; then
    echo "==> downloading appimagetool…"
    URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
    if command -v wget >/dev/null 2>&1; then
        wget -q -O "${APPIMAGETOOL}" "${URL}"
    else
        curl -fsSL -o "${APPIMAGETOOL}" "${URL}"
    fi
    chmod +x "${APPIMAGETOOL}"
fi

# --- 4. build the AppImage -----------------------------------------------
echo "==> running appimagetool…"
rm -f "${OUTPUT}"
# ARCH is required by appimagetool's continuous build.
# --appimage-extract-and-run avoids needing FUSE just to run the tool itself.
ARCH=x86_64 "${APPIMAGETOOL}" --appimage-extract-and-run "${APPDIR}" "${OUTPUT}"

echo
echo "==> done:"
ls -lh "${OUTPUT}"
