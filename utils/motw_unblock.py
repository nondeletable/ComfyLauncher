"""Strip Mark-of-the-Web from bundled DLLs so .NET can load them.

Importing this module performs the cleanup as a side effect. It MUST be
imported before anything that triggers a CLR assembly load (pythonnet or
WebView2) — i.e. before ``ui.browser``.

Why: when the app is shipped as a ZIP, Windows Explorer tags every extracted
file with a ``Zone.Identifier`` ("came from another computer") stream. .NET
then refuses to load managed assemblies — pythonnet's ``Python.Runtime.dll``
and WebView2's managed wrappers — and startup crashes with
"Failed to resolve Python.Runtime.Loader.Initialize". Native ``LoadLibrary``
is unaffected, so we only need the ``.dll`` streams gone before the first CLR
assembly load. The installer build never hits this (it writes clean files),
but the ZIP build does.
"""

import os
import sys


def unblock_bundled_dlls() -> None:
    """Remove the Zone.Identifier stream from every bundled ``.dll``.

    Runs only in a frozen build on Windows; a dev run has no MOTW. Best-effort:
    any failure to remove a stream is ignored (missing stream, permissions).
    """
    if os.name != "nt":
        return
    base = getattr(sys, "_MEIPASS", None)
    if not base:  # not frozen — nothing was extracted from a ZIP
        return
    for root, _dirs, files in os.walk(base):
        for name in files:
            if name.lower().endswith(".dll"):
                try:
                    os.remove(os.path.join(root, name) + ":Zone.Identifier")
                except OSError:
                    pass


unblock_bundled_dlls()
