"""Fail the build if anything in the AppDir needs a newer glibc than allowed.

An AppImage carries its own libraries but takes glibc from the system it runs
on. Every bundled binary records the glibc versions it was linked against, and
the newest of them is the oldest system the AppImage can start on. A build made
on Ubuntu 24.04 needs GLIBC_2.38 and dies at once on 22.04 — which is what the
AppImage catalog tests on, and what v1.9.0 shipped by mistake.

Usage: python check_glibc.py <AppDir> [max_version]   (default max: 2.35)
Needs `readelf` (binutils). Exit code 1 lists every offending file.
"""

import os
import re
import subprocess
import sys

DEFAULT_MAX = "2.35"  # glibc of Ubuntu 22.04, the oldest system Qt 6.11 runs on
NEEDS = re.compile(r"Name: GLIBC_([0-9.]+)")


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def _is_elf(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(4) == b"\x7fELF"
    except OSError:
        return False


def required_glibc(path: str) -> str | None:
    """Newest GLIBC_x.y the file needs, or None if it needs none."""
    out = subprocess.run(
        ["readelf", "-V", "--wide", path],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    found = NEEDS.findall(out)
    return max(found, key=_version) if found else None


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        return 2
    appdir = sys.argv[1]
    limit = sys.argv[2] if len(sys.argv) == 3 else DEFAULT_MAX

    newest = "0"
    offenders = []
    for root, _dirs, files in os.walk(appdir):
        for name in files:
            path = os.path.join(root, name)
            if os.path.islink(path) or not _is_elf(path):
                continue
            needed = required_glibc(path)
            if needed is None:
                continue
            if _version(needed) > _version(newest):
                newest = needed
            if _version(needed) > _version(limit):
                offenders.append((needed, os.path.relpath(path, appdir)))

    if offenders:
        print(f"ERROR: bundled files need glibc newer than {limit}:", file=sys.stderr)
        for needed, path in sorted(offenders, key=lambda o: _version(o[0])):
            print(f"  GLIBC_{needed}  {path}", file=sys.stderr)
        print(
            "Build on Ubuntu 22.04 (see packaging/linux/BUILD.md), "
            "not on a newer system.",
            file=sys.stderr,
        )
        return 1

    print(f"glibc check: newest requirement is GLIBC_{newest} (limit {limit}) - ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
