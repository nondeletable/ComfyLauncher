# ComfyLauncher — Linux build & test (1.9.0)

Self-contained guide for building the Linux **AppImage** and verifying the Linux
port. This file is committed to the repo on purpose — `CLAUDE.md` / `PROGRESS.md`
are gitignored and are **not** present in a fresh clone, so everything you need is
here.

> The Linux port ships as **1.9.0**. Windows keeps WebView2; Linux/macOS use
> **QtWebEngine** (`QWebEngineView`). The engine lives behind `ui/webview/`
> (`factory.create_webview()` dispatches by platform).

## 0. Where the code is

The port is on branch **`feature/linux-port`** (not yet merged to `master`):

```bash
git clone https://github.com/nondeletable/ComfyLauncher
cd ComfyLauncher
git checkout feature/linux-port
```

## 1. Environment

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

Python 3.11 or newer. Ubuntu 24.04 ships 3.12 and has no `python3.11` package;
3.12.3 is verified — 129 tests green, AppImage built and run.

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

**Measured: 210 MB** — 2026-09-21, Ubuntu 24.04 / Python 3.12.3 / Qt 6.11.0,
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
  `libGLX`, `libEGL`, `libGLdispatch`, `libdrm`, `libxcb`, `libxcb-dri3` — which
  *must* come from the system and must not be bundled, since they have to match
  the installed GPU driver. One warning is expected and harmless: `libtiff.so.5`
  stays unresolved on Ubuntu 24.04 (which ships `libtiff.so.6`); it only disables
  Qt's TIFF image plugin and the launcher never loads a TIFF.
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
- After this passes: PR `feature/linux-port` → `master`, bump `version.py` to
  1.9.0, then build Win exe/zip + this AppImage, tag `v1.9.0`, publish.
