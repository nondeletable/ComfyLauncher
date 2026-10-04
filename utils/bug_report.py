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
import ipaddress
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


# Where a path component ends in log text.
_END = r"(?=$|[\\/\s,;'\"()\[\]=])"
# One folder name: stops at separators and the punctuation that ends a path in
# a log line, capped so a runaway match cannot swallow the rest of the line.
# Spaces are allowed only when the path visibly goes on after the name.
_NAME = r"[^\\/:*?\"<>|\r\n,;']{1,64}?(?=[\\/])|[^\\/:*?\"<>|\s,;']{1,64}"
# C:\Users\, c:/users/, \\SERVER\c$\Users\, //server/c$/Users/
_PROFILE_ROOT = r"(?:\b[A-Za-z]:|(?:\\\\|//)[^\\/\s]+[\\/]+[A-Za-z]\$)[\\/]+Users[\\/]+"
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_IPV4_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?!\w|\.\d)")
_IPV6_RE = re.compile(r"(?<![\w:.])[0-9A-Fa-f:]{2,39}(?![\w:])")
_KEEP_IPS = {"127.0.0.1", "0.0.0.0", "::1", "::"}


def _ipv4_repl(m: re.Match) -> str:
    ip = m.group(0)
    if ip in _KEEP_IPS or ip.startswith("127."):
        return ip
    if any(int(octet) > 255 for octet in ip.split(".")):
        return ip  # a version number, not an address
    return "<ip>"


def _ipv6_repl(m: re.Match) -> str:
    text = m.group(0)
    if text.count(":") < 2 or text in _KEEP_IPS:
        return text
    try:
        ipaddress.IPv6Address(text)
    except ValueError:
        return text  # a timestamp, a C++ scope, anything else with colons
    return "<ip>"


def _word(name: str) -> str:
    return r"(?<![\w-])" + re.escape(name) + r"(?![\w-])"


class Scrubber:
    r"""Removes personal data from report text.

    Replaced: the home folder (also by its 8.3 short name, ``JANE~1``), the
    owner of any other profile folder (``X:\Users\<name>``,
    ``\\server\c$\Users\<name>``, ``/home/<name>``, ``/Users/<name>``), the
    OneDrive organisation folder, the user, computer and domain names,
    ``DOMAIN\account`` pairs, e-mail addresses and IP addresses other than
    loopback and ``0.0.0.0``.
    """

    def __init__(
        self,
        home: str | None,
        user: str | None,
        host: str | None,
        domains: tuple[str, ...] = (),
    ):
        self._rules: list[tuple[re.Pattern, object]] = [
            (_EMAIL_RE, "<email>"),
            (_IPV4_RE, _ipv4_repl),
            (_IPV6_RE, _ipv6_repl),
        ]
        home_token = "%USERPROFILE%" if sys.platform == "win32" else "~"

        parts = [p for p in re.split(r"[\\/]+", home or "") if p]
        # A bare drive or "/" is no home folder worth replacing.
        if len(parts) >= 2:
            *parents, last = parts
            lead = r"[\\/]+" if (home or "").startswith(("/", "\\")) else ""
            last_re = re.escape(last)
            short = re.sub(r"\W", "", last)[:6]
            if short:
                last_re = f"(?:{last_re}|{re.escape(short)}~\\d+)"
            pattern = (
                r"(?<![\w.~$-])"
                + lead
                + "".join(re.escape(p) + r"[\\/]+" for p in parents)
                + last_re
                + _END
            )
            self._rules.append((re.compile(pattern, re.IGNORECASE), home_token))

        self._rules += [
            (
                re.compile(r"(OneDrive - )[^\\/\r\n\"',;]{1,64}", re.IGNORECASE),
                r"\1<org>",
            ),
            (
                re.compile(f"({_PROFILE_ROOT})(?:{_NAME})", re.IGNORECASE),
                r"\1<user>",
            ),
            (
                # Not after "C:" or "c$": those are Windows profiles, done above.
                re.compile(r"(?<![:$])(/(?:home|Users)/)[^/\s,;'\"]{1,64}"),
                r"\1<user>",
            ),
        ]

        domains = tuple(d for d in domains if d and len(d) >= 2)
        for d in domains:
            # DOMAIN\account names an account even when it is not ours.
            self._rules.append(
                (
                    re.compile(_word(d) + r"\\[\w.$-]+", re.IGNORECASE),
                    r"<domain>\\<user>",
                )
            )
        names = [(user, "<user>"), (host, "<host>")] + [
            (d, "<domain>") for d in domains
        ]
        for name, token in names:
            if name and len(name) >= 2:
                self._rules.append((re.compile(_word(name), re.IGNORECASE), token))

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
        domains = tuple(os.environ.get(k, "") for k in ("USERDOMAIN", "USERDNSDOMAIN"))
        return cls(os.path.expanduser("~"), user, host, domains)

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
            timeout=2,
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


def _write_new(text: str, directory: str) -> str:
    """Write under a fresh name - an existing file is never overwritten."""
    stem = report_filename()[: -len(".txt")]
    for n in range(1, 100):
        path = os.path.join(directory, f"{stem}.txt" if n == 1 else f"{stem}-{n}.txt")
        try:
            with open(path, "x", encoding="utf-8", newline="\n") as f:
                f.write(text)
            return path
        except FileExistsError:
            continue
    raise FileExistsError(f"no free report name in {directory}")


def save_report(text: str, directory: str | None = None) -> str:
    """Write the report and return its path. Raises OSError on failure.

    Without ``directory`` it goes to the desktop, or to the home folder when
    the desktop cannot be written to.
    """
    if directory:
        return _write_new(text, directory)
    try:
        return _write_new(text, default_save_dir())
    except OSError:
        return _write_new(text, os.path.expanduser("~"))


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

    def finish(cut: str) -> str:
        # A cut inside the code block must not leave it open.
        if cut.count("```") % 2:
            cut += "\n```"
        return cut + note

    lines = body.split("\n")
    while len(lines) > 1 and len(build(finish("\n".join(lines)))) > limit:
        lines.pop()
    cut = "\n".join(lines)
    while cut and len(build(finish(cut))) > limit:
        cut = cut[: len(cut) * 3 // 4]
    return build(finish(cut))


def issue_title(report_text: str) -> str:
    """Title from the Error line of the report as the user left it.

    Taken from the shown (scrubbed, maybe edited) text rather than the raw
    error, so the public title holds nothing the user has not seen.
    """
    summary = extract_section(report_text, SECTION_SUMMARY)
    m = re.search(r"^Error:[ \t]*(.*)$", summary, re.MULTILINE)
    error = m.group(1).strip() if m else ""
    if error == "(none)":
        error = ""
    title = f"[Report] {error}" if error else "[Report] Problem report"
    return title if len(title) <= 100 else title[:97] + "..."


def issue_body(report_text: str, filename: str) -> str:
    summary = extract_section(report_text, SECTION_SUMMARY)
    return (
        f"Full report: drag `{filename}` from your desktop into this issue.\n\n"
        f"```\n{summary}\n```\n"
    )
