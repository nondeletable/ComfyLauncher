"""Bug report: collect, scrub and render the plain-text report.

No Qt here, so it can be tested on its own and used from the exception hook
before a QApplication exists. The report is a single UTF-8 ``.txt`` file split
into sections; nothing is ever archived (a zip is a risk both for the server
that would unpack it and for the developer who opens it).

Personal data is scrubbed *before* the text is shown to the user: the home
folder becomes ``%USERPROFILE%`` (``~`` off Windows), other profile folders
lose their owner's name, and the user and machine names become ``<user>`` and
``<host>``. The config loses keys that say nothing about the problem.
"""

from __future__ import annotations

import getpass
import json
import os
import platform
import re
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote

from version import __version__

GITHUB_REPO = "nondeletable/ComfyLauncher"
GITHUB_LABELS = "bug,report"
DISCORD_INVITE = "https://discord.gg/QkHc9tG74p"

LOG_TAIL_LINES = 2000
# GitHub refuses URLs past ~8 KB; the margin leaves room for browsers and the
# OS hand-off, which have their own, lower ceilings.
MAX_ISSUE_URL = 6000

SECTION_SUMMARY = "SUMMARY"
SECTION_TRACEBACK = "TRACEBACK"
SECTION_LOG = "LAUNCHER LOG"
SECTION_CONSOLE = "COMFYUI CONSOLE"
SECTION_CONFIG = "CONFIG"
OPTIONAL_SECTIONS = (SECTION_LOG, SECTION_CONSOLE, SECTION_CONFIG)

SOURCES = {
    "error_screen": "Error screen",
    "exception": "Unhandled exception",
    "manual": "Reported manually",
}

# Keys dropped from the config: caching and bookkeeping, no use for a diagnosis.
_CONFIG_DROP_KEYS = ("update_etag", "last_update_check")

_HEADER_RE = re.compile(r"^== (.+?) ==$", re.MULTILINE)


class Scrubber:
    """Replaces the home folder, profile folders, user and host names."""

    def __init__(self, home: str | None, user: str | None, host: str | None):
        self._rules: list[tuple[re.Pattern, str]] = []
        home_token = "%USERPROFILE%" if sys.platform == "win32" else "~"

        parts = [p for p in re.split(r"[\\/]+", home or "") if p]
        # A bare drive or "/" is no home folder worth replacing.
        if len(parts) >= 2:
            lead = r"[\\/]+" if (home or "").startswith(("/", "\\")) else ""
            pattern = lead + r"[\\/]+".join(re.escape(p) for p in parts)
            self._rules.append(
                (re.compile(pattern + r"(?![\w.-])", re.IGNORECASE), home_token)
            )

        # Any other profile folder (another account, an 8.3 short name).
        self._rules.append(
            (
                re.compile(r"(\b[A-Za-z]:[\\/]+Users[\\/]+)[^\\/:*?\"<>|\r\n]+"),
                r"\1<user>",
            )
        )
        self._rules.append((re.compile(r"(/home/)[^/\s]+"), r"\1<user>"))

        for name, token in ((user, "<user>"), (host, "<host>")):
            if name and len(name) >= 2:
                self._rules.append(
                    (
                        re.compile(
                            r"(?<![\w-])" + re.escape(name) + r"(?![\w-])",
                            re.IGNORECASE,
                        ),
                        token,
                    )
                )

    @classmethod
    def for_current_user(cls) -> "Scrubber":
        try:
            user = getpass.getuser()
        except Exception:
            user = os.environ.get("USERNAME") or os.environ.get("USER")
        try:
            host = socket.gethostname()
        except Exception:
            host = os.environ.get("COMPUTERNAME")
        return cls(os.path.expanduser("~"), user, host)

    def __call__(self, text: str) -> str:
        for pattern, repl in self._rules:
            text = pattern.sub(repl, text)
        return text

    def scrub_data(self, value):
        """Scrub every string inside JSON-like data (keys included)."""
        if isinstance(value, str):
            return self(value)
        if isinstance(value, dict):
            return {self(str(k)): self.scrub_data(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.scrub_data(v) for v in value]
        return value


@dataclass
class BugReport:
    source: str
    summary: list[tuple[str, str]]
    traceback: str = ""
    sections: dict[str, str] = field(default_factory=dict)
    created: datetime = field(default_factory=datetime.now)


# ── Collecting ────────────────────────────────────────────────────────────


def _read_config(path: str) -> tuple[dict | None, str]:
    """The raw config as stored, without the app's defaults or migrations."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), ""
    except FileNotFoundError:
        return None, "(no config file)"
    except Exception as e:
        return None, f"(config could not be read: {type(e).__name__}: {e})"


def _selected_build(cfg: dict) -> dict | None:
    builds = cfg.get("builds") or []
    last_id = cfg.get("last_used_build_id")
    for b in builds:
        if isinstance(b, dict) and b.get("id") == last_id:
            return b
    return None


def _build_python_version(exe: str) -> str:
    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        out = subprocess.run(
            [exe, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            **kwargs,
        )
        return (out.stdout or out.stderr).strip() or "unknown"
    except Exception as e:
        return f"unknown ({type(e).__name__})"


def _build_info(comfy_path: str) -> tuple[str, str]:
    """Build type and the version of the Python that runs it."""
    if not comfy_path:
        return "no build selected", "unknown"
    try:
        from utils.build_validation import detect_build_type
        from utils.python_resolver import resolve_interpreter

        interp = resolve_interpreter(comfy_path)
        kind = f"{detect_build_type(comfy_path)}, interpreter: {interp.kind}"
        return kind, _build_python_version(interp.exe)
    except Exception as e:
        return f"unknown ({type(e).__name__})", "unknown"


def _webview2_version() -> str:
    if sys.platform != "win32":
        return "n/a (QtWebEngine)"
    try:
        # Lives in a separate change; the report degrades gracefully without it.
        from utils.webview2_runtime import installed_version  # type: ignore

        return installed_version() or "not installed"
    except Exception:
        return "unknown"


def _os_line() -> str:
    if sys.platform == "win32":
        return f"Windows {platform.release()} (build {platform.version()})"
    try:
        name = platform.freedesktop_os_release().get("PRETTY_NAME", "")
    except Exception:
        name = ""
    return f"{name or platform.system()} (kernel {platform.release()})"


def _tail(path: str, lines: int) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.readlines()
    except FileNotFoundError:
        return "(no log file)"
    except Exception as e:
        return f"(log could not be read: {type(e).__name__}: {e})"
    return "".join(content[-lines:])


def collect_report(
    source: str,
    error_text: str = "",
    traceback_text: str = "",
    scrubber: Scrubber | None = None,
) -> BugReport:
    """Gather everything for a report. Never raises on missing data."""
    from config import USER_CONFIG_PATH
    from utils.console_buffer import ConsoleBuffer
    from utils.logger import LOG_FILE

    scrub = scrubber or Scrubber.for_current_user()
    cfg, cfg_error = _read_config(USER_CONFIG_PATH)
    cfg_dict = cfg if isinstance(cfg, dict) else {}

    build = _selected_build(cfg_dict) or {}
    comfy_path = cfg_dict.get("comfyui_path") or build.get("path") or ""
    build_type, build_python = _build_info(comfy_path)
    flags = build.get("extra_flags") or []
    show_cmd = cfg_dict.get("show_cmd", True)

    summary = [
        ("Launcher version", __version__),
        ("OS", _os_line()),
        ("Architecture", platform.machine() or "unknown"),
        ("Launcher Python", platform.python_version()),
        ("WebView2 Runtime", _webview2_version()),
        ("ComfyUI build", build_type),
        ("Build Python", build_python),
        ("Launch flags", " ".join(str(f) for f in flags) or "(none)"),
        ("Console", "external window" if show_cmd else "internal"),
        ("Theme", str(cfg_dict.get("theme") or "dark")),
        ("Where", SOURCES.get(source, source)),
        ("Error", error_text or "(none)"),
    ]
    summary = [(k, scrub(v)) for k, v in summary]

    if cfg is not None:
        clean = {k: v for k, v in cfg_dict.items() if k not in _CONFIG_DROP_KEYS}
        config_text = json.dumps(scrub.scrub_data(clean), indent=2, ensure_ascii=False)
    else:
        config_text = cfg_error

    console = ConsoleBuffer.get_all()
    sections = {
        SECTION_LOG: scrub(_tail(LOG_FILE, LOG_TAIL_LINES)),
        SECTION_CONSOLE: scrub(console) if console else "",
        SECTION_CONFIG: config_text,
    }
    return BugReport(
        source=source,
        summary=summary,
        traceback=scrub(traceback_text),
        sections=sections,
    )


# ── Rendering ─────────────────────────────────────────────────────────────


def _header(name: str) -> str:
    return f"== {name} =="


def render_report(
    report: BugReport, include: set[str] | None = None, comment: str = ""
) -> str:
    """Plain text with one ``== NAME ==`` header per section.

    ``include`` picks the optional sections (log, console, config); None keeps
    them all. An empty section is still listed, so the reader can tell "empty"
    from "left out".
    """
    include = set(OPTIONAL_SECTIONS) if include is None else include
    width = max(len(k) for k, _ in report.summary)
    lines = [
        "Comfy Launcher bug report",
        f"Created: {report.created.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        _header(SECTION_SUMMARY),
    ]
    lines += [f"{k + ':':<{width + 2}}{v}" for k, v in report.summary]
    lines += ["", "Comment:", comment.strip() or "(none)", ""]

    if report.traceback:
        lines += [_header(SECTION_TRACEBACK), report.traceback.rstrip(), ""]

    for name in OPTIONAL_SECTIONS:
        if name not in include:
            continue
        body = report.sections.get(name, "").rstrip()
        title = f"{name} (last {LOG_TAIL_LINES} lines)" if name == SECTION_LOG else name
        lines += [_header(title), body or "(empty)", ""]

    return "\n".join(lines).rstrip() + "\n"


def extract_section(text: str, name: str) -> str:
    """The body of one ``== NAME ==`` section of a rendered report, or ''."""
    for m in _HEADER_RE.finditer(text):
        if m.group(1).split(" (")[0] != name:
            continue
        nxt = _HEADER_RE.search(text, m.end())
        return text[m.end() : nxt.start() if nxt else len(text)].strip("\n")
    return ""


# ── Delivering ────────────────────────────────────────────────────────────


def report_filename(now: datetime | None = None) -> str:
    now = now or datetime.now()
    return f"comfylauncher-report-{now.strftime('%Y%m%d-%H%M%S')}.txt"


def default_save_dir() -> str:
    """The desktop (where the user finds the file to attach), else home."""
    if sys.platform == "win32":
        try:
            import ctypes

            buf = ctypes.create_unicode_buffer(260)
            # CSIDL_DESKTOPDIRECTORY follows a desktop moved to OneDrive.
            if ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, buf) == 0:
                if os.path.isdir(buf.value):
                    return buf.value
        except Exception:
            pass
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    return desktop if os.path.isdir(desktop) else os.path.expanduser("~")


def save_report(text: str, directory: str | None = None) -> str:
    """Write the report and return its path. Raises OSError on failure."""
    directory = directory or default_save_dir()
    path = os.path.join(directory, report_filename())
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def github_issue_url(title: str, body: str, limit: int = MAX_ISSUE_URL) -> str:
    """A prefilled new-issue URL that stays under ``limit`` characters.

    The body is cut line by line (then character by character) until the
    encoded URL fits; the full text is in the attached file anyway.
    """
    base = f"https://github.com/{GITHUB_REPO}/issues/new"

    def build(b: str) -> str:
        return (
            f"{base}?title={quote(title, safe='')}"
            f"&labels={quote(GITHUB_LABELS, safe=',')}"
            f"&body={quote(b, safe='')}"
        )

    url = build(body)
    if len(url) <= limit:
        return url

    note = "\n\n(cut to fit the link - the full text is in the attached file)"
    lines = body.split("\n")
    while len(lines) > 1 and len(build("\n".join(lines) + note)) > limit:
        lines.pop()
    cut = "\n".join(lines)
    while cut and len(build(cut + note)) > limit:
        cut = cut[: len(cut) * 3 // 4]
    return build(cut + note)


def issue_title(error_text: str) -> str:
    first = (error_text or "").strip().splitlines()
    title = f"[Report] {first[0]}" if first else "[Report] Problem report"
    return title if len(title) <= 100 else title[:97] + "..."


def issue_body(report_text: str, filename: str) -> str:
    summary = extract_section(report_text, SECTION_SUMMARY)
    return (
        f"Full report: drag `{filename}` from your desktop into this issue.\n\n"
        f"```\n{summary}\n```\n"
    )
