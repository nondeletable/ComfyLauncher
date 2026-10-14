# ComfyLauncher — Linux build & test (1.9.0)

Self-contained guide for building the Linux **AppImage** and verifying the Linux
port. This file is committed to the repo on purpose — `CLAUDE.md` / `PROGRESS.md`
are gitignored and are **not** present in a fresh clone, so everything you need is
here.

> The Linux port ships as **1.9.0**. Windows keeps WebView2; Linux/macOS use
> **QtWebEngine** (`QWebEngineView`). The engine lives behind `ui/webview/`
> (`factory.create_webview()` dispatches by platform).

## 0. Where the code is

The port is **merged into `master`** (PR #57, 2026-09-21), so a plain clone is
all you need:

```bash
git clone https://github.com/nondeletable/ComfyLauncher
cd ComfyLauncher
```

The `feature/linux-port` branch still exists but is now redundant — build from
`master`.

## 1. Environment

### Build on Ubuntu 22.04 — not on anything newer

The AppImage carries its own libraries but **takes glibc from the user's
system**, and it starts only where glibc is at least as new as on the build
machine. v1.9.0 was built on Ubuntu 24.04 and needs `GLIBC_2.38`, so it dies on
22.04 at once — `libpython3.12.so: version 'GLIBC_2.38' not found` — which is
how the AppImage catalog (it tests on `ubuntu-22.04`) rejected it.

22.04 is also the floor: the PyQt6 6.11 wheels are `manylinux_2_34`, so Qt
itself needs glibc 2.34+ and an older system cannot run the launcher anyway.

**The release build runs on GitHub Actions**: `.github/workflows/appimage.yml`
(Actions → AppImage → Run workflow; it also runs on PRs that touch
`packaging/linux/`). The AppImage is attached to the run as the
`ComfyLauncher-AppImage` artifact. Building by hand works the same on a 22.04
machine or container, with Python 3.11+ that was itself built for 22.04 (e.g.
the deadsnakes PPA) — not a 24.04 interpreter copied over.

`build_appimage.sh` checks this itself: after PyInstaller it reads the glibc
requirement of every bundled binary (`check_glibc.py`) and stops if any needs
more than `GLIBC_MAX` (default 2.35). The check needs `readelf` (binutils).

### System packages — do this first

```bash
sudo apt install -y libxcb-cursor0
```

`libxcb-cursor0` is a **build-machine requirement, not just a runtime one.**
PyInstaller bundles system `.so` files by copying them from the machine it runs
on. Without this package the build still succeeds, but `libxcb-cursor.so.0` never
makes it into the AppImage — the log carries four `Library not found` warnings
(`libqxcb.so`, `libQt6XcbQpa.so.6`, and the two `xcbglintegrations` plugins) — and
the result refuses to start on any X11 desktop with `could not load the Qt
platform plugin "xcb"`. On a Wayland session the gap is invisible, because the
wayland plugin is used instead, so local testing will not catch it. Learned the
hard way on 2026-09-21.

### Virtualenv

Create the venv **in the repo root** (named `.venv`, matching the Windows setup):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.11 or newer. Ubuntu 22.04 ships 3.10, so take 3.12 from
`actions/setup-python` (CI) or the deadsnakes PPA. Running from source on a
24.04 machine with its own 3.12.3 is fine — only the AppImage build has to
happen on 22.04.

`requirements.txt` is split per-OS. On Linux this installs **PyQt6 6.11.0 +
PyQt6-WebEngine 6.11.0** (the win32-only WebView2 stack — `pythonnet`, `pywin32` —
is skipped). 6.11 is required: 6.6.1 ships Chromium 112 (≈21 fps on the litegraph
canvas), 6.11 ships Chromium 140 (≈56 fps).

## 2. Run from source & verify (do this before building the AppImage)

```bash
python main.py
```

Checklist — this is the real point of the Linux trip:

1. **Setup Window** appears → point it at an installed **Linux** ComfyUI (portable
   dir with `main.py`, or one with a `.venv`/`venv` beside it). The launcher itself
   ships no ComfyUI — without one, startup stops at the Setup Window.
2. **Engine is QtWebEngine, not the placeholder.** If you see a bare fallback page,
   `create_webview()` fell back — check the log for `⚠️ QtWebEngine unavailable`.
3. **litegraph canvas** — zoom/pan should feel smooth (the reason QtWebEngine was
   chosen on a real GPU).
4. **Window close — the critical case (an exit-crash fix lives here).** With the
   default "ask on exit" the dialog has **three** buttons, and **two of them
   exit** — so there are two paths to check for the abort, not one:
   - ✕ → **Yes** → ComfyUI is stopped, the window closes, **no abort/segfault**;
   - ✕ → **No** → the window closes but **ComfyUI keeps running**. A second,
     separate exit path. Confirm the server survived: `pgrep -f ComfyUI/main.py`
     should still find it and port 8188 stay open.
   - ✕ → **Cancel** → nothing exits; the window stays alive and usable. Repeat
     once more, then poke the UI to be sure it is not wedged.
   Background: QtWebEngine aborts if its profile is released before the page. The
   fix calls `_shutdown_webview()` before every `event.accept()`
   (`ui/browser.py`), guarded by `_alive()` in `QtWebEngineView`. Covered by
   `tests/ui/test_browser_close.py`. Confirmed live on QtWebEngine 6.11 on
   2026-09-21 — all three paths, from source and from the AppImage, every exit
   clean.

Run the tests too (`pytest` is not in `requirements.txt` — `pip install pytest`
into the venv first):

```bash
pytest -q
```

## 3. Build the AppImage

```bash
cd packaging/linux
bash build_appimage.sh
```

(`bash …` avoids depending on the executable bit, which can be lost when the file
is committed from Windows; `chmod +x build_appimage.sh` then `./build_appimage.sh`
works too.)

The script: PyInstaller onedir build → assembles `ComfyLauncher.AppDir` (AppRun +
`.desktop` + icon) → downloads `appimagetool` (once, into this folder) → emits
`packaging/linux/ComfyLauncher-x86_64.AppImage` and prints its size.

**PyInstaller is invoked via CLI flags, not a `.spec`** — `*.spec` is gitignored,
so keeping the config in the script is what makes it ship in the repo. Its PyQt6
hooks bundle `QtWebEngineProcess`, Chromium resources, ICU data, locales and
translations automatically.

### Measure the size (goes into release notes)

```bash
ls -lh packaging/linux/ComfyLauncher-x86_64.AppImage
```

**Measured: 210 MB** — 2026-09-21, Ubuntu 24.04 / Python 3.12.3 / Qt 6.11.0 (the 1.9.0 build),
inside the ~200–280 MB estimate (QtWebEngine bundles its own Chromium). The
Windows build is lighter because WebView2 is a system component — note that in
the notes.

### Test the AppImage

```bash
chmod +x ComfyLauncher-x86_64.AppImage
./ComfyLauncher-x86_64.AppImage
```

Repeat the §2 checklist (start, engine, canvas, and **all three close paths —
Yes / No / Cancel**) against the packaged build — bundled Qt can behave
differently from a source run.

## 4. Troubleshooting

- **FUSE — not an issue in practice.** The runtime embedded by current
  `appimagetool` works on FUSE 3, so **libfuse2 is not required**. Verified on
  Ubuntu 24.04 with FUSE 3 only: `--appimage-mount` succeeded, no libfuse error.
  Should an older runtime ever complain with `dlopen(): error loading
  libfuse.so.2`, either `sudo apt install libfuse2t64` or run extracted:
  `./ComfyLauncher-x86_64.AppImage --appimage-extract-and-run`.
- **QtWebEngine aborts / blank web view in the AppImage** — the sandbox: `AppRun`
  already exports `QTWEBENGINE_DISABLE_SANDBOX=1`. If it still fails, run from a
  terminal and read the Chromium error.
- **Missing system libs at startup** — check the build log for `Library not
  found` warnings first. Each one is a library PyInstaller could not copy because
  it was absent from the build machine (see §1), and it will be missing from the
  AppImage for every user. Built on a properly prepared machine, the AppImage's
  only external dependencies are glibc and the graphics stack — `libGL`,
  `libGLX`, `libEGL`, `libGLdispatch`, `libdrm`, `libgbm`, `libwayland-*`,
  `libxcb`, `libxcb-dri3`, and the C++ runtime `libstdc++` / `libgcc_s` — which
  *must* come from the system and must not be bundled, since they have to match
  the installed GPU driver and Wayland compositor. PyInstaller copies some of
  these in as transitive dependencies, so `build_appimage.sh` (step 1b) deletes
  them from the bundle after the build: a bundled copy shadows the host one and
  breaks the Mesa VAAPI driver on newer systems (the driver wants a newer
  `libstdc++` than the 22.04 one; EGL/GBM init then fails and the process aborts
  at startup — seen on Ubuntu 26.04). Dropping `libstdc++` / `libgcc_s` is safe:
  the Qt 6.11 wheels need at most `GLIBCXX_3.4.29` / `CXXABI_1.3.13`, which the
  22.04 build floor already provides. On a 24.04 machine `libtiff.so.5` stays unresolved
  (24.04 ships `libtiff.so.6`); on 22.04 it is present. Either way it only
  affects Qt's TIFF image plugin, and the launcher never loads a TIFF. The CI
  workflow lists every such warning as an annotation on the run.
- **`version 'GLIBC_2.xx' not found` at startup** — the AppImage was built on a
  newer system than the one running it. Rebuild on 22.04 (see §1);
  `check_glibc.py` names the files that need the newer glibc.
- **Splash video is silent/black** — the app forces the ffmpeg media backend
  (`QT_MEDIA_BACKEND=ffmpeg` in `main.py`); if QtMultimedia's ffmpeg libs didn't
  bundle, the splash may degrade. Non-blocking for the port; note it and move on.
- **Wayland oddities** — QtWebEngine works on X11 and Wayland; if something looks
  wrong under Wayland, retry with `QT_QPA_PLATFORM=xcb ./ComfyLauncher-x86_64.AppImage`
  to isolate whether it's Wayland-specific.

## 5. Status / not done

- ~~The AppImage recipe was authored on Windows (can't be test-built there).
  First run on Linux may need library tweaks.~~ **Done 2026-09-21:** built and
  run on Ubuntu 24.04 under both Wayland and X11 — 210 MB, starts, renders, all
  three exit paths clean, 129 tests green. The one tweak needed was
  `libxcb-cursor0` on the build machine, now documented in §1.
- No `.desktop` desktop-integration/auto-update, no code signing. Out of scope for
  1.9.0.
- ~~After this passes: PR `feature/linux-port` → `master`, bump `version.py` to
  1.9.0.~~ **Done 2026-09-21:** merged as PR #57, `version.py` is 1.9.0, and the
  AppImage was rebuilt from the merged tree (1.9.0 verified inside the bundle).
  Remaining for the release: Windows exe/zip, tag `v1.9.0`, publish, then
  `gh release upload v1.9.0 packaging/linux/ComfyLauncher-x86_64.AppImage`.
