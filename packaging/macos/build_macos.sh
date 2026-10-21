#!/usr/bin/env bash
#
# Build a macOS .app bundle of ComfyLauncher (QtWebEngine engine).
#
# Run this ON macOS only, on Apple Silicon. The bundle is arm64-only by design
# (plan §7-4): PyInstaller follows the running interpreter's architecture, so an
# Intel or universal2 bundle cannot be produced here. Intel macOS support is out
# of scope for this port; the release build runs on GitHub Actions (Task 7).
#
# Usage:
#   cd packaging/macos
#   ./build_macos.sh
#
# Prerequisites:
#   - the project's venv with `pip install -r requirements.txt` done
#     (PyInstaller and PyQt6-WebEngine come from it; see the PYTHON note below)
#   - an arm64 Python in that venv, otherwise the arch check stops the build
#
# Output: <repo root>/dist/ComfyLauncher.app
#
# The script repairs the QtWebEngineCore.framework layout and then applies the
# ad-hoc signature (codesign -s -), inside out. PyInstaller signs the bundle on
# its own, but only before this script rearranges the framework, which leaves
# both the framework and the app seal stale; see the signing section below.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

APP_NAME="ComfyLauncher"
SPEC="${SCRIPT_DIR}/${APP_NAME}.spec"
APP="${REPO_ROOT}/dist/${APP_NAME}.app"

if [ "$(uname -s)" != "Darwin" ]; then
    echo "ERROR: this script builds a macOS .app and runs on macOS only." >&2
    exit 1
fi

# Prefer the project's venv: the repo convention is .venv/bin/python3 (the bare
# `python` name resolves oddly in some shells here), and the plain `python3` on
# PATH is easily a different, unrelated interpreter. PYTHON overrides.
if [ -z "${PYTHON:-}" ]; then
    if [ -x "${REPO_ROOT}/.venv/bin/python3" ]; then
        PYTHON="${REPO_ROOT}/.venv/bin/python3"
    else
        PYTHON="python3"
    fi
fi

ARCH="$("${PYTHON}" -c 'import platform; print(platform.machine())' 2>/dev/null || true)"
if [ "${ARCH}" != "arm64" ]; then
    echo "ERROR: interpreter reports '${ARCH}', not arm64 — the macOS port is arm64-only." >&2
    echo "       Interpreter: ${PYTHON}" >&2
    exit 1
fi

if ! "${PYTHON}" -c "import PyInstaller" >/dev/null 2>&1; then
    echo "ERROR: PyInstaller not importable with ${PYTHON}." >&2
    echo "       Run pip install -r requirements.txt in the project venv first." >&2
    exit 1
fi
if ! "${PYTHON}" -c "import PyQt6.QtWebEngineWidgets" >/dev/null 2>&1; then
    echo "ERROR: PyQt6-WebEngine not importable — the macOS engine is missing." >&2
    echo "       Check requirements.txt installed the non-win32 Qt 6.11 wheels." >&2
    exit 1
fi

echo "==> repo root: ${REPO_ROOT}"
echo "==> python:    ${PYTHON} (${ARCH})"

# --- 1. PyInstaller -------------------------------------------------------
# Run from the repo root with the default --distpath: PyInstaller writes dist/
# and build/ into the current directory, and the spec resolves its own paths
# from its own location, so the two can never disagree.
echo "==> running PyInstaller (${SPEC})…"
cd "${REPO_ROOT}"
rm -rf "${APP}"
"${PYTHON}" -m PyInstaller "${SPEC}" --noconfirm --clean

if [ ! -d "${APP}" ]; then
    echo "ERROR: expected bundle ${APP} was not produced." >&2
    exit 1
fi

# --- 2. QtWebEngine framework layout repair -------------------------------
# The PyQt6 6.11 wheels ship a non-standard QtWebEngineCore.framework: Helpers/
# and Resources/ are real directories at the framework root, Versions/A/ holds
# only the binary, and there is no Versions/Current. PyInstaller 6.10 re-lays
# that out as
#
#     Helpers   -> Versions/Current/Helpers
#     Resources -> Versions/Current/Resources
#     Versions/Current -> A
#     Versions/Resources/{Helpers,Resources}/   <- where the real files land
#
# while only Versions/A/Resources receives anything (the version Info.plist);
# Versions/A/Helpers is not created at all. Both framework-root symlinks
# therefore dangle, and Qt fails in two different ways depending on how far it
# gets:
#
#   helper     Qt searches
#                  <framework>/Helpers/QtWebEngineProcess.app/Contents/MacOS/QtWebEngineProcess
#              finds nothing and silently falls back to its placeholder page:
#              the app starts, shows a window, the ComfyUI UI never renders.
#   resources  Qt searches <framework>/Resources for icudtl.dat, *.pak and
#              qtwebengine_locales, finds none, and aborts the whole process
#              (SIGABRT, exit 134) with
#                  The following paths were searched for Qt WebEngine resources: …
#                  but could not find any.
#
# The fix is to move the real payload into Versions/A/ and drop the bogus
# Versions/Resources directory, which leaves a standard framework:
#
#     Helpers   -> Versions/Current/Helpers    (real directory)
#     Resources -> Versions/Current/Resources  (real directory)
#     Versions/Current -> A
#
# Do not "repair" this by symlinking from Versions/A back into Versions/Resources
# (the first version of this script did). Qt then works, but codesign does not:
# `codesign --verify --deep --strict` reports
#     invalid destination for symbolic link in bundle
# and turns every resource reached through those links into "file modified", so
# the bundle never passes Task 5. Prevented by keeping the payload real.
#
# Do NOT validate this with `PYTHONPATH=<bundle>/Contents/Frameworks python3 …`.
# The bundle ships no PyQt6/__init__.py (it lives in the PYZ archive), so a plain
# interpreter records that directory as a namespace portion, keeps searching and
# ends up importing the venv's PyQt6 — whose wheel layout is unbroken. Verified
# 2026-10-20: PyQt6.__file__ resolved to .venv/lib/.../PyQt6/__init__.py, i.e.
# that harness never exercised the bundle at all. It reported the resource repair
# as unnecessary; launching Contents/MacOS/ComfyLauncher itself proved the
# opposite. Only a launch of the real bundle counts as evidence.
#
# Guarded and re-runnable, so it becomes a no-op once PyInstaller lays this out
# correctly. It must run before the signing pass below: rearranging the bundle
# afterwards invalidates the signature just applied.
FW="${APP}/Contents/Frameworks/PyQt6/Qt6/lib/QtWebEngineCore.framework"

CURRENT="$(readlink "${FW}/Versions/Current" || true)"
CUR="${FW}/Versions/${CURRENT}"

if [ -n "${CURRENT}" ] && [ -d "${CUR}" ] && [ -d "${FW}/Versions/Resources" ]; then
    if [ -d "${FW}/Versions/Resources/Helpers" ]; then
        echo "==> normalizing QtWebEngine helper lookup (Versions/${CURRENT}/Helpers)…"
        rm -rf "${CUR}/Helpers"
        mv "${FW}/Versions/Resources/Helpers" "${CUR}/Helpers"
    fi
    if [ -d "${FW}/Versions/Resources/Resources" ]; then
        echo "==> normalizing QtWebEngine resources (Versions/${CURRENT}/Resources)…"
        # Only the version Info.plist is there, and the moved directory carries
        # the same one, so replacing it wholesale is safe and keeps this simple.
        rm -rf "${CUR}/Resources"
        mv "${FW}/Versions/Resources/Resources" "${CUR}/Resources"
    fi
    rmdir "${FW}/Versions/Resources" 2>/dev/null || true
fi

# --- 3. ad-hoc code signing (inside out) ----------------------------------
# Apple deprecated `codesign --deep` for signing, so the nested code is signed
# first and its container last. PyInstaller already ad-hoc signed everything,
# but before the repair above; moving the payload invalidated the framework seal
# and, through it, the app seal. Re-signing the whole tree from scratch would be
# pointless — only the framework and the app that seals it are stale.
HELPER_APP="${CUR}/Helpers/QtWebEngineProcess.app"
echo "==> signing ad-hoc (helper, framework, app)…"
codesign --force --sign - "${HELPER_APP}"
codesign --force --sign - "${FW}"
codesign --force --sign - "${APP}"

# --- 4. bundle verification ----------------------------------------------
# Asserted at the paths Qt actually queries. Checking by filename anywhere in the
# bundle is not enough — `find -name QtWebEngineProcess` passed on the broken
# bundle, because the helper was present but unreachable.
echo "==> verifying Qt can reach its helper process and its resources…"
MISSING=0
for RELPATH in \
    "Helpers/QtWebEngineProcess.app/Contents/MacOS/QtWebEngineProcess" \
    "Resources/icudtl.dat" \
    "Resources/qtwebengine_resources.pak" \
    "Resources/qtwebengine_locales"
do
    if [ -e "${FW}/${RELPATH}" ]; then
        echo "    ok: ${RELPATH}"
    else
        echo "    UNREACHABLE: ${FW}/${RELPATH}" >&2
        MISSING=1
    fi
done
if [ "${MISSING}" -ne 0 ]; then
    echo "ERROR: this bundle would start with a dead QtWebEngine — a placeholder page at best, SIGABRT at worst." >&2
    exit 1
fi

echo "==> verifying the ad-hoc signature (deep, strict)…"
if ! codesign --verify --deep --strict "${APP}"; then
    echo "ERROR: signature verification failed — the nested code is not signed inside out." >&2
    exit 1
fi
echo "    ok: deep-strict verification passed"

echo "==> done:"
du -sh "${APP}"
