#!/usr/bin/env python3
"""Union-resolve append-only merge conflicts (changelog bullets, markdown table rows).

Usage: union_resolve.py FILE [FILE...]
Rewrites each file in place with both sides of every conflict kept, ours first.
Exits 2 and leaves the file untouched when a conflict is not append-only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

START = "<<<<<<< "
BASE = "||||||| "
MIDDLE = "======="
END = ">>>>>>> "
APPEND_ONLY_RE = re.compile(r"^(\s*[-*+]\s|\s*\|)")


class ConflictError(Exception):
    """A conflict that is not append-only and needs a human."""


def check_append_only(lines: list[str], side: str) -> None:
    """Raise ConflictError when a side holds anything but bullet or table-row lines."""
    for line in lines:
        if line.strip() and not APPEND_ONLY_RE.match(line):
            raise ConflictError(f"{side} side is not append-only: {line.rstrip()!r}")


def resolve_text(text: str) -> str:
    """Return text with every conflict replaced by ours then theirs; raise ConflictError if any is not append-only."""
    out: list[str] = []
    ours: list[str] = []
    theirs: list[str] = []
    state = "text"
    for line in text.splitlines(keepends=True):
        if state == "text":
            if line.startswith(START):
                state = "ours"
                ours, theirs = [], []
            else:
                out.append(line)
        elif state == "ours":
            if line.startswith(BASE):
                state = "base"
            elif line.rstrip("\r\n") == MIDDLE:
                state = "theirs"
            else:
                ours.append(line)
        elif state == "base":
            if line.rstrip("\r\n") == MIDDLE:
                state = "theirs"
        elif line.startswith(END):
            check_append_only(ours, "ours")
            check_append_only(theirs, "theirs")
            if ours and not ours[-1].endswith("\n"):
                ours[-1] += "\n"
            out.extend(ours + theirs)
            state = "text"
        else:
            theirs.append(line)
    if state != "text":
        raise ConflictError("unterminated conflict block")
    return "".join(out)


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: union_resolve.py FILE [FILE...]", file=sys.stderr)
        return 64
    resolved: dict[Path, str] = {}
    for name in argv:
        path = Path(name)
        try:
            resolved[path] = resolve_text(path.read_text())
        except (ConflictError, OSError) as exc:
            print(f"cannot union-resolve {name}: {exc}", file=sys.stderr)
            return 2
    for path, text in resolved.items():
        path.write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
