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

Create the venv **in the repo root** (named `.venv`, matching the Windows setup):

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

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
   default "ask on exit":
   - close (✕) → **Yes** → window closes, **no abort/segfault** in the console;
   - close (✕) → **No** → window stays alive and usable; repeat once more.
   Background: QtWebEngine aborts if its profile is released before the page. The
   fix calls `_shutdown_webview()` before every `event.accept()`
   (`ui/browser.py`), guarded by `_alive()` in `QtWebEngineView`. Covered by
   `tests/ui/test_browser_close.py`, but this path had never run live on
   QtWebEngine — that's what we're confirming.

Run the tests too:

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

Rough estimate was ~200–280 MB (QtWebEngine bundles its own Chromium). The Windows
build is lighter because WebView2 is a system component — note that in the notes.

### Test the AppImage

```bash
chmod +x ComfyLauncher-x86_64.AppImage
./ComfyLauncher-x86_64.AppImage
```

Repeat the §2 checklist (start, engine, canvas, **Yes/No close**) against the
packaged build — bundled Qt can behave differently from a source run.

## 4. Troubleshooting

- **AppImage won't run: "dlopen(): error loading libfuse.so.2"** — install FUSE 2:
  `sudo apt install libfuse2` (Ubuntu 24.04 ships FUSE 3 by default). Or run
  extracted: `./ComfyLauncher-x86_64.AppImage --appimage-extract-and-run`.
- **QtWebEngine aborts / blank web view in the AppImage** — the sandbox: `AppRun`
  already exports `QTWEBENGINE_DISABLE_SANDBOX=1`. If it still fails, run from a
  terminal and read the Chromium error.
- **Missing system libs at startup** (e.g. `libnss3`, `libnspr4`, `libxcb-*`,
  `libxkbcommon`) — QtWebEngine/Qt xcb need them present. On a minimal box:
  `sudo apt install libnss3 libxcb-cursor0 libxkbcommon-x11-0`. These are runtime
  system deps, not bundled.
- **Splash video is silent/black** — the app forces the ffmpeg media backend
  (`QT_MEDIA_BACKEND=ffmpeg` in `main.py`); if QtMultimedia's ffmpeg libs didn't
  bundle, the splash may degrade. Non-blocking for the port; note it and move on.
- **Wayland oddities** — QtWebEngine works on X11 and Wayland; if something looks
  wrong under Wayland, retry with `QT_QPA_PLATFORM=xcb ./ComfyLauncher-x86_64.AppImage`
  to isolate whether it's Wayland-specific.

## 5. Status / not done

- The AppImage recipe was authored on Windows (can't be test-built there). First
  run on Linux may need library tweaks — see §4.
- No `.desktop` desktop-integration/auto-update, no code signing. Out of scope for
  1.9.0.
- After this passes: PR `feature/linux-port` → `master`, bump `version.py` to
  1.9.0, then build Win exe/zip + this AppImage, tag `v1.9.0`, publish.
