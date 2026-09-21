# Web-view bench

Measures how well each web engine on this machine renders a ComfyUI-shaped
node graph: hundreds of node boxes and bezier links on a canvas, with a
scripted zoom/pan pass over them. Every engine gets the identical scene in an
identical 1280x720 backing store, so the numbers are comparable.

It answers the only two questions the engine choice turns on: **frames per
second** on a heavy graph, and **memory**, which is what the launcher sells.

This is a development tool. It is not imported by the app and is not shipped.

## Run it

    python tools/webview_bench/run.py --all

`--all` uses every engine it can find: WebView2 on Windows (the launcher's own
widget, so the number describes what ships today), QtWebEngine if
`PyQt6-WebEngine` is installed, and whichever of Edge / Chrome / Chromium /
Firefox is on the machine as a "real browser" reference.

Useful switches:

    --engine webview2      one engine (repeatable)
    --nodes 600            graph size; raise it until fps drops below 60
    --repeat 3             runs per engine, the table reports the median
    --json runs.jsonl      keep the raw per-run numbers

## Comparing a newer Qt without touching .venv

The Chromium inside QtWebEngine is pinned to the PyQt6 version, and that
Chromium is what decides the frame rate. To measure a different one, build a
throwaway environment and point the bench at it:

    python tools/webview_bench/run.py --bootstrap C:\tmp\qt611
    C:\tmp\qt611\Scripts\python.exe tools\webview_bench\run.py --engine qtwebengine

`--bootstrap` installs the four Qt packages as one pinned set on purpose: pip
resolves `PyQt6-Qt6` and `PyQt6-WebEngine-Qt6` independently, and a mismatched
pair fails at import with a missing `libQt6Qml*` / `Qt6Qml*.dll`.

## Reading the table

| column | meaning |
|-----------|---------|
| fps | higher is better; 60 is the vsync ceiling, not a limit of the engine |
| draw ms | time spent inside the canvas calls |
| frame p95 | the worst frames — an exact multiple of 16.7 ms means whole frames are being dropped |
| RSS MB | peak memory of the engine's entire process tree |

A low `draw ms` next to a low `fps` is the interesting case: the engine is
keeping up with the drawing but failing to get frames on screen.

## Caveats

- The scene is litegraph-*shaped*, not ComfyUI itself. Comparisons between
  engines are sound; the absolute fps is not ComfyUI's fps.
- Results are only comparable within one machine and one session. Anything
  else competing for the GPU moves them.
- Each browser run uses a throwaway profile in a plain visible folder under
  your home directory, removed afterwards. It has to live there: a
  snap-packaged browser sees a private `/tmp` and cannot read hidden folders
  under `$HOME`, and quits instead of starting.
