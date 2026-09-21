# Copy-paste commands

Everything needed to run the web-view bench, per OS. Copy one block at a time.
Run them from the repository root. What the numbers mean is in `README.md`.

---

## Windows

### 1. Measure the engine that ships today (WebView2) + any browser found

Nothing to install — this uses the project's own `.venv` and the launcher's
own WebView2 widget.

```
.venv\Scripts\python tools\webview_bench\run.py --all
```

### 2. Build a throwaway environment with the newest Qt

Does not touch `.venv`. Downloads about 200 MB.

```
.venv\Scripts\python tools\webview_bench\run.py --bootstrap C:\tmp\qt611
```

### 3. Measure the candidate engine (QtWebEngine on the new Qt)

```
C:\tmp\qt611\Scripts\python.exe tools\webview_bench\run.py --engine qtwebengine
```

### 4. Compare the two tables: fps and RSS MB

If step 3 gives no fewer frames than step 1 at less memory, the candidate wins.

### 5. Clean up when done

```
rmdir /s /q C:\tmp\qt611
```

### If every engine sits at 60 fps

The graph is too small to separate them. Raise it and rerun steps 1 and 3:

```
.venv\Scripts\python tools\webview_bench\run.py --all --nodes 1500
```

```
C:\tmp\qt611\Scripts\python.exe tools\webview_bench\run.py --engine qtwebengine --nodes 1500
```

---

## Linux

### 1. Measure every engine present

```
.venv/bin/python tools/webview_bench/run.py --all
```

### 2. Build a throwaway environment with the newest Qt

```
.venv/bin/python tools/webview_bench/run.py --bootstrap /tmp/qt611
```

### 3. Measure the candidate engine

```
/tmp/qt611/bin/python tools/webview_bench/run.py --engine qtwebengine
```

### 4. Clean up when done

```
rm -rf /tmp/qt611
```

---

## Other switches

Keep the raw per-run numbers instead of just the median table:

```
.venv/bin/python tools/webview_bench/run.py --all --json runs.jsonl
```

Run a single engine, more times, for a steadier median:

```
.venv/bin/python tools/webview_bench/run.py --engine webview2 --repeat 5
```

Engine names: `webview2`, `qtwebengine`, `edge`, `chrome`, `chromium`, `firefox`.
