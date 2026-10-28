#!/usr/bin/env python3
"""Check manifest versions match, skills have valid frontmatter, and templates referenced by skills exist."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
HEADING_RE = re.compile(r"^## \[(\d+)\.(\d+)\.(\d+)\](.*)$", re.MULTILINE)
PLUGIN_ROOT_PATH_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"']+)")
DATED_RE = re.compile(r"^ - \d{4}-\d{2}-\d{2}\s*$")


def parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def check_changelog(text: str, version: str) -> list[str]:
    """Check the changelog has a dated section for version, no newer release, and descending order."""
    errors: list[str] = []
    current = parse_version(version)
    found: list[tuple[int, ...]] = []
    for match in HEADING_RE.finditer(text):
        found.append((int(match.group(1)), int(match.group(2)), int(match.group(3))))
        if found[-1] == current and not DATED_RE.match(match.group(4)):
            errors.append(f"CHANGELOG.md section for {version} has no date (expected '## [{version}] - YYYY-MM-DD')")
    if current not in found:
        errors.append(f"CHANGELOG.md has no section for {version}")
    if found and max(found) > current:
        latest = ".".join(map(str, max(found)))
        errors.append(f"plugin version {version} is lower than changelog version {latest}")
    if any(a <= b for a, b in zip(found, found[1:])):
        errors.append("CHANGELOG.md versions are not in strictly descending order")
    return errors


def hook_commands(node: object) -> list[str]:
    """Collect every 'command' string in a parsed hooks file."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "command" and isinstance(value, str):
                found.append(value)
            else:
                found.extend(hook_commands(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(hook_commands(item))
    return found


def check_hooks(path: Path, root: Path) -> list[str]:
    """Check the hooks file parses as JSON and every command script it references exists."""
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        return [f"{path.name}: cannot parse as JSON ({exc})"]
    errors: list[str] = []
    for command in hook_commands(data):
        for relative in PLUGIN_ROOT_PATH_RE.findall(command):
            if not (root / relative).is_file():
                errors.append(f"{path.name}: hook script {relative} does not exist")
    return errors


def check_untrusted_text_link(text: str) -> list[str]:
    """Check a skill body links reference/untrusted-text.md."""
    return [] if "untrusted-text.md" in text else ["does not link reference/untrusted-text.md"]


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
        if "host-commands.md" not in text:
            errors.append(f"{skill}: does not link reference/host-commands.md")
        errors.extend(f"{skill}: {problem}" for problem in check_untrusted_text_link(text))
    if not (ROOT / "reference/host-commands.md").exists():
        errors.append("reference/host-commands.md missing")
    if not (ROOT / "reference/untrusted-text.md").exists():
        errors.append("reference/untrusted-text.md missing")
    changelog = ROOT / "CHANGELOG.md"
    if changelog.exists():
        errors.extend(check_changelog(changelog.read_text(), plugin["version"]))
    hooks = ROOT / "hooks/hooks.json"
    if hooks.exists():
        errors.extend(check_hooks(hooks, ROOT))
    else:
        errors.append("hooks/hooks.json missing")
    return errors


if __name__ == "__main__":
    problems = check()
    for problem in problems:
        print(f"error: {problem}")
    sys.exit(1 if problems else 0)
