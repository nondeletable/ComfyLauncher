#!/usr/bin/env bash
#
# Build a Linux AppImage of ComfyLauncher (QtWebEngine engine).
#
# Run this ON LINUX only, on Ubuntu 22.04. An AppImage bundles Linux .so
# libraries and is assembled by appimagetool, which does not run on Windows.
# The bundle takes glibc from the user's system, so it starts only on systems
# as new as the build machine or newer: built on 24.04 it dies on 22.04.
# 22.04 is also the floor — the Qt 6.11 wheels need glibc 2.34. The release
# build runs on GitHub Actions (.github/workflows/appimage.yml).
#
# Usage:
#   cd packaging/linux
#   ./build_appimage.sh
#
# Prerequisites (see BUILD.md):
#   - the project's venv activated with `pip install -r requirements.txt` done
#   - readelf (binutils), for the glibc check
#   - internet access (downloads appimagetool once, into this folder)
#
# Output: packaging/linux/ComfyLauncher-x86_64.AppImage
#
# GLIBC_MAX (default 2.35, Ubuntu 22.04) is the newest glibc the bundle may
# need; the build stops if any bundled file needs more.
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
GLIBC_MAX="${GLIBC_MAX:-2.35}"

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
if ! command -v readelf >/dev/null 2>&1; then
    echo "ERROR: readelf not found - install binutils (needed for the glibc check)." >&2
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

# --- 1b. drop host-provided graphics / driver libraries ------------------
# These must match the running GPU driver and Wayland compositor, so they have
# to come from the user's system, not the bundle (BUILD.md §4). PyInstaller
# copies some in as transitive dependencies; a bundled copy then shadows the
# host one and breaks the Mesa VAAPI driver on newer systems — the driver wants
# a newer libstdc++ than the bundled one ("CXXABI_x.y.z not found"), EGL/GBM
# init then fails, and QtWebEngine and the splash's QQuickWidget abort the
# process (SIGABRT at startup on Ubuntu 26.04).
#
# libstdc++/libgcc_s are safe to drop: the Qt 6.11 wheels need at most
# GLIBCXX_3.4.29 / CXXABI_1.3.13, which the 22.04 build floor already provides,
# so the host's own (equal or newer) copy always satisfies them. The loader
# finds them on the default system path once they are gone from $ORIGIN.
echo "==> removing host-provided graphics/driver libraries from the bundle…"
host_libs=(
    "libstdc++.so*"
    "libgcc_s.so*"
    "libgbm.so*"
    "libwayland-client.so*"
    "libwayland-cursor.so*"
    "libwayland-egl.so*"
    "libwayland-server.so*"
    "libdrm.so*"
    "libGL.so*"
    "libGLX.so*"
    "libGLdispatch.so*"
    "libEGL.so*"
)
for pat in "${host_libs[@]}"; do
    find "${DIST_DIR}" -type f -name "${pat}" -print -delete
done

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

# --- 3. glibc check -------------------------------------------------------
# Before packing, so a build that would not start on Ubuntu 22.04 never
# becomes an AppImage at all.
echo "==> checking the glibc the bundle needs (limit ${GLIBC_MAX})…"
python "${SCRIPT_DIR}/check_glibc.py" "${APPDIR}" "${GLIBC_MAX}"

# --- 4. fetch appimagetool (once) ----------------------------------------
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

# --- 5. build the AppImage -----------------------------------------------
echo "==> running appimagetool…"
rm -f "${OUTPUT}"
# ARCH is required by appimagetool's continuous build.
# --appimage-extract-and-run avoids needing FUSE just to run the tool itself.
ARCH=x86_64 "${APPIMAGETOOL}" --appimage-extract-and-run "${APPDIR}" "${OUTPUT}"

echo
echo "==> done:"
ls -lh "${OUTPUT}"
