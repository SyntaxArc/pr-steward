#!/usr/bin/env python3
"""Check manifest versions match, skills have valid frontmatter, and templates referenced by skills exist."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")


def check() -> list[str]:
    errors: list[str] = []
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    for entry in market["plugins"]:
        if entry["version"] != plugin["version"]:
            errors.append(f"marketplace version {entry['version']} != plugin version {plugin['version']}")
        if entry["name"] != plugin["name"]:
            errors.append(f"marketplace plugin name {entry['name']} != {plugin['name']}")
    for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
        text = skill.read_text()
        match = re.search(r"^name:\s*(\S+)", text, re.MULTILINE)
        if not match or match.group(1) != skill.parent.name or not NAME_RE.match(match.group(1)):
            errors.append(f"{skill}: frontmatter name missing or != directory name")
        if not re.search(r"^description:", text, re.MULTILINE):
            errors.append(f"{skill}: description missing")
    changelog = ROOT / "CHANGELOG.md"
    if changelog.exists() and f"## [{plugin['version']}]" not in changelog.read_text():
        errors.append(f"CHANGELOG.md has no section for {plugin['version']}")
    return errors


if __name__ == "__main__":
    problems = check()
    for problem in problems:
        print(f"error: {problem}")
    sys.exit(1 if problems else 0)
