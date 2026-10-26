# ComfyLauncher — macOS build & test (1.10.0)

Self-contained guide for building the macOS **.app / .dmg** and verifying the
macOS port. This file is committed to the repo on purpose — `CLAUDE.md` /
`PROGRESS.md` are gitignored and are **not** present in a fresh clone, so
everything you need is here.

> On macOS and Linux the app uses **QtWebEngine** (`QWebEngineView`); Windows
> keeps WebView2. The engine lives behind `ui/webview/`
> (`factory.create_webview()` dispatches by platform).

## 0. Where the code is

The macOS packaging lives in `packaging/macos/`, next to the Windows and Linux
setups:

```bash
git clone https://github.com/nondeletable/ComfyLauncher
cd ComfyLauncher
```

## 1. Environment

### macOS 13 (Ventura) or newer, Apple Silicon only

`LSMinimumSystemVersion` is **13.0**, set in `packaging/macos/ComfyLauncher.spec`
via `BUNDLE(info_plist=…)`. That is the floor Qt 6.11 supports.

The bundle is **arm64-only by design**: PyInstaller follows the running
interpreter's architecture, so an Intel or universal2 bundle cannot be produced
from this tree. Intel macOS support is out of scope. The build script refuses to
run when the interpreter reports anything other than `arm64`.

Nothing needs `apt`, Homebrew, or Xcode project files: `codesign`, `ditto` and
`hdiutil` are part of macOS. If `codesign` is somehow absent, install the
Command Line Tools (`xcode-select --install`).

### Virtualenv

Create the venv **in the repo root** (named `.venv`, matching the Windows and
Linux setups):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.11 or newer (3.11.15 was used for the 1.10.0 build). On macOS
`requirements.txt` installs **PyQt6 6.11.0 + PyQt6-WebEngine 6.11.0** and skips
the win32-only WebView2 stack (`pythonnet`, `pywin32`). 6.11 is required: 6.6.1
ships Chromium 112 (≈21 fps on the litegraph canvas), 6.11 ships Chromium 140
(≈56 fps).

`QTWEBENGINE_DISABLE_SANDBOX=1` is **not** needed here, unlike the Linux
AppImage — Chromium's sandbox works on macOS. It was measured: the QtWebEngine
tests pass without it.

## 2. Run from source & verify (do this before building)

```bash
python main.py
```

Checklist — this is the real point of the macOS trip. Everything below was
verified on macOS 27.0.1 on 2026-10-19/20:

1. **Setup Window** appears → point it at an installed **macOS** ComfyUI
   (portable dir with `main.py`, or one with a `.venv`/`venv` beside it). The
   launcher ships no ComfyUI.
2. **Engine is QtWebEngine, not the placeholder.** A bare fallback page means
   `create_webview()` fell back — check the log for `⚠️ QtWebEngine unavailable`.
3. **Window chrome**: the frameless window's rounded-corner mask renders cleanly
   on cocoa (no black corners), `startSystemMove()` drags the window, and the
   edges resize. Verified normal.
4. **Title bar**: macOS shows the Windows-style custom controls on the right and
   no traffic lights. This is deliberate (the existing header is reused), but it
   remains a UX decision for the maintainer — see §5.
5. **Splash video** plays (the app forces `QT_MEDIA_BACKEND=ffmpeg` in `main.py`).
6. **Settings → Color Theme**: `Select` and `Download` are not clipped. Upstream
   already fixed this with `setMinimumWidth(80)`; no macOS change needed.
7. **Window close — the critical case.** With the default "ask on exit" the
   dialog has three buttons:
   - ✕ → **Yes** → ComfyUI is stopped, the window closes, no abort;
   - ✕ → **Cancel** → nothing exits, the UI stays usable;
   - ✕ → **No** → the window closes but **ComfyUI is supposed to keep running**.
     It currently does **not**: `utils/process_launch.py` uses a pipe on POSIX,
     so the child gets SIGPIPE when the launcher exits. That is an upstream bug
     affecting Linux too, and is being fixed separately.

Run the tests too (`pytest` is not in `requirements.txt` — `pip install pytest
pytest-qt` into the venv first):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python3 -m pytest -q
```

**Measured: 451 passed, 16 skipped** (2026-10-21, macOS 27.0.1 / Python 3.11.15).
`QT_QPA_PLATFORM=offscreen` is used exactly as on the Linux job; QtWebEngine
still initialises.

> **Do not run pytest on an older branch.** `conftest.py` relies on
> `COMFYLAUNCHER_CONFIG_HOME` to redirect the config dir. Without it, the suite
> writes `ask_on_exit: false` into the real
> `~/Library/Application Support/ComfyLauncher/user_config.json`, which silently
> removes the exit dialog. This actually happened during the port.

## 3. Build the .app and the .dmg

```bash
bash packaging/macos/build_macos.sh
```

(`bash …` avoids depending on the executable bit, which can be lost when the
file is committed from Windows/Windows-mounted filesystems.)

The script, in order:

1. PyInstaller with the **committed** `packaging/macos/ComfyLauncher.spec`.
2. Repairs the `QtWebEngineCore.framework` layout PyInstaller 6.10 produces
   (§4 explains why).
3. Signs ad-hoc (`codesign -s -`) **inside out** — helper app, framework, then
   the bundle. PyInstaller signs too, but before step 2 rearranges the framework,
   so both seals are stale by then.
4. Asserts the four paths Qt actually queries (helper binary, `icudtl.dat`,
   `qtwebengine_resources.pak`, `qtwebengine_locales`) and fails the build if any
   is unreachable.
5. Verifies with `codesign --verify --deep --strict`.
6. Builds `packaging/macos/ComfyLauncher-<version>-arm64.dmg` with `ditto` (keeps
   symlinks/xattrs), adds the `/Applications` drop target, mounts the image back
   and re-runs the signature check on what is inside it.

**Measured (2026-10-21, macOS 27.0.1 / Python 3.11.15 / Qt 6.11.0):**

| Artifact | Size |
|---|---|
| `dist/ComfyLauncher.app` | **472 MB** |
| `packaging/macos/ComfyLauncher-1.10.0-arm64.dmg` | **212 MB** |

QtWebEngine bundles its own Chromium, hence the size — comparable to the 210 MB
Linux AppImage. `dist/` and `build/` are written to the **repo root**, as on
Windows/Linux; `*.dmg` is gitignored on purpose.

### Why the spec is committed

`BUNDLE()` is what turns the collected folder into `ComfyLauncher.app`, and
`info_plist` is the only place the bundle metadata keys can be set. `.gitignore`
already carries the same exception for `packaging/windows/*.spec`, so a spec in
`packaging/` is deliberate. Paths inside it resolve from the spec's own location,
so it works wherever PyInstaller is invoked from.

`bundle_identifier` is `com.nondeletable.ComfyLauncher` (reverse-DNS of
`github.com/nondeletable`). This value was never defined anywhere before; the
maintainer confirmed it on 2026-10-20.

The icon is `assets/icons/icon.icns`, produced from the 256 px source art by
tracing the raster into vectors and rasterising every slot (16 px … 1024 px)
from the SVG. Measured error against the original is RMSE 2.61/255, with a 1 px
edge transition at 1024 px where plain upscaling gives 6 px. The tracing
toolchain is not part of this PR.

### Test the .dmg

```bash
hdiutil attach -nobrowse packaging/macos/ComfyLauncher-1.10.0-arm64.dmg
cp -R /Volumes/ComfyLauncher/ComfyLauncher.app /Applications/
hdiutil detach /Volumes/ComfyLauncher
open /Applications/ComfyLauncher.app
```

Repeat the §2 checklist against the packaged build — bundled Qt can behave
differently from a source run.

## 4. Troubleshooting

- **The window opens but the page is a bare placeholder** — the
  QtWebEngine helper is unreachable. Qt prints `could not find it` and silently
  falls back, so the build log looks clean. Run the four assertions from §3 by
  hand.
- **The app aborts at startup (SIGABRT, exit 134)** — the Chromium resources are
  unreachable. Qt prints `The following paths were searched for Qt WebEngine
  resources: … but could not find any`.
  Both symptoms share one root cause: the PyQt6 6.11 wheel ships
  `Helpers/` and `Resources/` as real directories at the framework root, and
  PyInstaller 6.10 normalises that into root symlinks pointing at
  `Versions/Current/*` while moving the payload into a `Versions/Resources`
  pseudo-version. Both links then dangle. The script moves the payload into
  `Versions/A` and drops `Versions/Resources`.
- **`codesign --verify --deep --strict` fails with `invalid destination for
  symbolic link in bundle`** — someone "repaired" the layout by symlinking from
  `Versions/A` back into `Versions/Resources`. Qt works then, but codesign
  rejects every file reached through those links and the bundle can never be
  signed. Keep the payload real; that is what step 2 does.
- **A downloaded .dmg is blocked by Gatekeeper** — the signature is ad-hoc, not
  Developer ID. Use right-click → **Open**, or System Settings → Privacy &
  Security → **Open Anyway**. Notarisation is not done (§5). A locally built
  bundle in `dist/` carries no quarantine attribute and opens normally.
- **Verifying the bundle "works" with `PYTHONPATH`** — don't. The bundle ships no
  `PyQt6/__init__.py` (it lives in the PYZ archive), so a plain interpreter
  records `Contents/Frameworks` as a namespace portion, keeps searching and
  imports the **venv's** PyQt6, whose wheels are fine. This produced a false
  "engine works" verdict on 2026-10-20 and cost a debugging round. Only launching
  `Contents/MacOS/ComfyLauncher` itself counts as evidence.
- **`CFBundleShortVersionString` is `0.0.0`** — `version.py` was not passed to
  `BUNDLE(version=…)`. The spec reads it; a hand-written `pyinstaller` invocation
  without the spec does not.
- **Splash video is silent/black** — the app forces the ffmpeg media backend; if
  QtMultimedia's ffmpeg libs did not bundle, the splash degrades. Non-blocking.
- **Tests fail on macOS with a log-path assertion** — the checkout predates
  macOS support. `utils/platform_paths.py` deliberately ignores `XDG_CONFIG_HOME`
  on darwin, while the old test asserted it was followed.

## 5. Status / not done

- **CI**: `.github/workflows/ci.yaml` runs `lint`, `test` and `test-macos`
  (`macos-latest`, Python 3.11, no apt step). `macos-latest` is arm64, the same
  architecture this bundle targets.
- **No Developer ID, no notarisation.** Distribution is ad-hoc signed
  (`codesign -s -`), which is enough to run locally and satisfies deep-strict
  verification, but downloadable builds trigger Gatekeeper's "Open Anyway" flow.
  A Developer ID certificate (paid Apple account) is required to go further.
- **arm64 only.** Intel/universal2 is out of scope; the script refuses to build
  on an x86_64 interpreter.
- **DMG cosmetics** are minimal: the app plus an `/Applications` symlink, no
  background image and no fixed window layout.
- **Title bar** still uses the Windows-style custom controls on macOS, so the
  header stays identical across platforms. Revisit if a native title bar is
  wanted.
- **`✕ → No` does not keep ComfyUI alive yet**, as described in §2 — the fix is a
  separate change.
- **README roadmap** leaves `Port to macOS` unchecked until the first macOS
  build ships. Two optional follow-ups are intentionally **not** here:
  `LAUNCH_PRESETS` platform gating and the `Segoe UI` tooltip font in `main.py`
  (both affect Linux equally, so they belong in their own PRs).
