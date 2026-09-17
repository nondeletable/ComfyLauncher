"""Cross-platform ComfyUI interpreter resolution.

Decides which Python runs the build's ``main.py`` and how to build its launch
environment. There are three kinds of interpreter, each with its own env recipe:

- ``embedded`` — the Windows portable ``python_embeded`` sibling of the build.
  It has no site configuration of its own, so it needs ``PYTHONHOME`` +
  ``PYTHONPATH`` set and its folder prepended to ``PATH`` — exactly as the
  launcher did before.
- ``venv`` — a virtual environment (``bin/python`` on posix, ``Scripts/python.exe``
  on Windows). It configures itself via ``pyvenv.cfg``; setting ``PYTHONHOME``
  would break it, so we set nothing.
- ``system`` — ``python3`` / ``python`` on ``PATH``. Nothing special.

Autodetect is the default when the user has not chosen a source explicitly.
Windows keeps its historical order (embedded → system): a venv is never picked
silently there. Linux/macOS have no embedded Python, so venv → system is the
only sensible default. A future explicit-choice feature will override autodetect
by taking a user-provided interpreter path.
"""

from __future__ import annotations

import os
import sys
import shutil
from dataclasses import dataclass


@dataclass
class Interpreter:
    exe: str
    kind: str  # "embedded" | "venv" | "system"
    home: str | None = None  # embedded only: the python_embeded directory


def _venv_python(root: str) -> str | None:
    """Return the interpreter path inside a venv rooted at ``root``, or None."""
    if sys.platform == "win32":
        cand = os.path.join(root, "Scripts", "python.exe")
    else:
        cand = os.path.join(root, "bin", "python")
    return cand if os.path.exists(cand) else None


def _find_embedded(base_dir: str) -> Interpreter | None:
    """Windows portable ``python_embeded`` (both legacy spellings)."""
    for name in ("python_embeded", "python_embedded"):
        cand = os.path.join(base_dir, name, "python.exe")
        if os.path.exists(cand):
            return Interpreter(exe=cand, kind="embedded", home=os.path.dirname(cand))
    return None


def _find_venv(comfy_path: str, base_dir: str) -> Interpreter | None:
    """A venv inside the build folder or next to it."""
    for root in (
        os.path.join(comfy_path, ".venv"),
        os.path.join(comfy_path, "venv"),
        os.path.join(base_dir, ".venv"),
        os.path.join(base_dir, "venv"),
    ):
        exe = _venv_python(root)
        if exe:
            return Interpreter(exe=exe, kind="venv")
    return None


def _system() -> Interpreter:
    """The interpreter on ``PATH`` (last-resort default)."""
    if sys.platform == "win32":
        return Interpreter(exe="python", kind="system")
    exe = shutil.which("python3") or shutil.which("python") or "python3"
    return Interpreter(exe=exe, kind="system")


def resolve_interpreter(comfy_path: str) -> Interpreter:
    """Pick the interpreter for the build at ``comfy_path`` via autodetect.

    Windows: embedded → system. Other platforms: venv → system.
    """
    base_dir = os.path.dirname(comfy_path)
    if sys.platform == "win32":
        return _find_embedded(base_dir) or _system()
    return _find_venv(comfy_path, base_dir) or _system()


def build_env(
    interp: Interpreter, comfy_path: str, base_env: dict | None = None
) -> dict:
    """Build the launch environment for ``interp``.

    Always forces unbuffered UTF-8 output. Only an ``embedded`` interpreter gets
    ``PYTHONHOME`` / ``PYTHONPATH`` and a ``PATH`` prepend; ``venv`` and
    ``system`` interpreters are left to configure themselves.
    """
    env = dict(base_env if base_env is not None else os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    if interp.kind == "embedded" and interp.home:
        env["PYTHONHOME"] = interp.home
        env["PYTHONPATH"] = comfy_path
        env["PATH"] = interp.home + os.pathsep + env.get("PATH", "")

    return env
