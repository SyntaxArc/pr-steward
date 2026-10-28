#!/usr/bin/env python3
"""Tick one checklist item in an issue body, safely.

Usage: tick.py ISSUE ITEM [--host gh|glab] [--repo OWNER/REPO]

ITEM is a 1-based number (all digits) or the exact item text. Numbers count every
checklist item (ticked or not) outside fenced code blocks, nested items included,
in document order. Text matches after stripping the `- [ ] ` prefix and whitespace;
with duplicate text the first unticked match is ticked. A text whose matches are all
ticked is left unchanged (idempotent).

Refuses to write when the fetched body is empty, the item is missing, or the item
count would change. After writing it reads the issue back and verifies the result.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ITEM_RE = re.compile(r"^(?P<lead>[ \t]*(?:[-*+]|\d+[.)])[ \t]+\[)(?P<mark>[ xX])(?P<tail>\][ \t]+)(?P<text>.*?)[ \t]*$")
FENCE_RE = re.compile(r"^[ \t]{0,3}(?P<fence>`{3,}|~{3,})")


class TickError(Exception):
    """Raised when a tick is refused."""


def find_items(body: str) -> list[tuple[int, str, bool]]:
    """Return (line index, text, ticked) for each checklist item outside fenced code blocks."""
    items: list[tuple[int, str, bool]] = []
    fence: str | None = None
    for index, line in enumerate(body.splitlines()):
        match = FENCE_RE.match(line)
        if match:
            marker = match.group("fence")
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        item = ITEM_RE.match(line)
        if item:
            items.append((index, item.group("text").strip(), item.group("mark") != " "))
    return items


def tick(body: str, item: int | str) -> str:
    """Return body with one item ticked; raise TickError when the tick is unsafe."""
    if not body.strip():
        raise TickError("refusing to tick: issue body is empty")
    items = find_items(body)
    if isinstance(item, str) and item.strip().isdigit():
        item = int(item.strip())
    if isinstance(item, int):
        if not 1 <= item <= len(items):
            raise TickError(f"item number {item} not found ({len(items)} checklist items)")
        target = items[item - 1]
    else:
        wanted = item.strip()
        matches = [entry for entry in items if entry[1] == wanted]
        if not matches:
            raise TickError(f"item text not found: {wanted!r}")
        unticked = [entry for entry in matches if not entry[2]]
        if not unticked:
            return body
        target = unticked[0]
    if target[2]:
        return body
    lines = body.splitlines(keepends=True)
    line = lines[target[0]]
    match = ITEM_RE.match(line.rstrip("\r\n"))
    if match is None:
        raise TickError("internal error: item line did not match")
    start = match.end("lead")
    lines[target[0]] = line[:start] + "x" + line[start + 1 :]
    new_body = "".join(lines)
    if len(find_items(new_body)) != len(items):
        raise TickError("refusing to write: checklist item count would change")
    return new_body


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise TickError(f"command failed: {' '.join(cmd)}: {result.stderr.strip()}")
    return result.stdout


def detect_host() -> str:
    url = run(["git", "remote", "get-url", "origin"]).strip()
    if "github.com" in url:
        return "gh"
    if "gitlab" in url:
        return "glab"
    raise TickError(f"cannot detect host from remote {url!r}; pass --host gh|glab")


def fetch(host: str, issue: str, repo: str | None) -> str:
    if host == "gh":
        cmd = ["gh", "issue", "view", issue, "--json", "body", "-q", ".body"]
        if repo:
            cmd += ["-R", repo]
        out = run(cmd)
        return out[:-1] if out.endswith("\n") else out
    cmd = ["glab", "issue", "view", issue, "-F", "json"]
    if repo:
        cmd += ["-R", repo]
    try:
        return str(json.loads(run(cmd)).get("description") or "")
    except json.JSONDecodeError as exc:
        raise TickError(f"cannot parse glab output: {exc}") from exc


def write(host: str, issue: str, repo: str | None, body: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8", newline="") as handle:
        handle.write(body)
        path = handle.name
    try:
        if host == "gh":
            cmd = ["gh", "issue", "edit", issue, "--body-file", path]
        else:
            cmd = ["glab", "issue", "update", issue, "--description", body]
        if repo:
            cmd += ["-R", repo]
        run(cmd)
    finally:
        Path(path).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tick one checklist item in an issue body.")
    parser.add_argument("issue")
    parser.add_argument("item", help="1-based number or exact item text")
    parser.add_argument("--host", choices=("gh", "glab"))
    parser.add_argument("--repo")
    args = parser.parse_args(argv)
    try:
        host = args.host or detect_host()
        before = fetch(host, args.issue, args.repo)
        if not before.strip():
            raise TickError("fetched body is empty; nothing written")
        item: int | str = int(args.item) if args.item.strip().isdigit() else args.item
        after = tick(before, item)
        if after == before:
            print(f"#{args.issue}: item already ticked, nothing written")
            return 0
        write(host, args.issue, args.repo, after)
        check = fetch(host, args.issue, args.repo)
        old_items, new_items = find_items(before), find_items(check)
        if len(old_items) != len(new_items):
            raise TickError(f"verify failed: item count {len(old_items)} -> {len(new_items)}")
        expected = [i for i, _ in enumerate(find_items(after)) if find_items(after)[i][2]]
        actual = [i for i, entry in enumerate(new_items) if entry[2]]
        if expected != actual:
            raise TickError("verify failed: ticked items differ from what was written")
    except TickError as exc:
        print(f"tick.py: {exc}", file=sys.stderr)
        return 1
    print(f"#{args.issue}: ticked and verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
