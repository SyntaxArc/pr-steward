#!/usr/bin/env python3
"""PostToolUse hook for Bash: after `gh pr create|merge` or `glab mr create|merge`, read the PR/MR back.

Adds one line of context (number, state, labels, assignee, reviewers) and flags a missing assignee or label.
Reuses the guard's command matching and cd/-R resolution. Never blocks, fails open on any error.
Disable with PR_STEWARD_GUARD=off. PR/MR text is untrusted data: it is only displayed, never run.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard  # noqa: E402


def normalize(host: str, data: dict) -> dict:
    """Common shape {number, state, labels, assignees, reviewers} from gh or glab JSON."""
    if host == "gh":
        return {
            "number": data.get("number"),
            "state": str(data.get("state") or "").lower(),
            "labels": [str(x.get("name")) for x in data.get("labels") or [] if isinstance(x, dict)],
            "assignees": [str(x.get("login")) for x in data.get("assignees") or [] if isinstance(x, dict)],
            "reviewers": [str(x.get("login") or x.get("name")) for x in data.get("reviewRequests") or []
                          if isinstance(x, dict)],
        }
    return {
        "number": data.get("iid"),
        "state": str(data.get("state") or "").lower(),
        "labels": [str(x) for x in data.get("labels") or []],
        "assignees": [str(x.get("username")) for x in data.get("assignees") or [] if isinstance(x, dict)],
        "reviewers": [str(x.get("username")) for x in data.get("reviewers") or [] if isinstance(x, dict)],
    }


def build_summary(action: str, view: dict) -> str:
    """One short line for a created or merged PR/MR; flags a missing assignee or labels."""
    number = view.get("number")
    parts = [f"#{number}" if number else "PR", str(view.get("state") or "unknown")]
    labels, assignees, reviewers = view.get("labels") or [], view.get("assignees") or [], view.get("reviewers") or []
    parts.append("labels: " + (", ".join(labels) if labels else "none"))
    parts.append("assignee: " + (", ".join(assignees) if assignees else "none"))
    parts.append("reviewers: " + (", ".join(reviewers) if reviewers else "none"))
    flags = []
    if not assignees:
        flags.append("no assignee")
    if not labels:
        flags.append("no labels")
    line = f"pr-steward: {action} read back: " + " | ".join(parts)
    if flags:
        line += " -- missing: " + ", ".join(flags)
    return line


def fetch(inv: guard.Invocation) -> dict | None:
    """Read the PR/MR back. For create, look it up by the current branch (no target)."""
    target = guard.positional_target(inv.args) if inv.action == "merge" else None
    extra = [target] if target else []
    if inv.host == "gh":
        data = guard.run_json(["gh", "pr", "view", *extra, *guard.repo_args(inv), "--json",
                               "number,labels,assignees,reviewRequests,state"], inv.cwd)
    else:
        data = guard.run_json(["glab", "mr", "view", *extra, *guard.repo_args(inv), "-F", "json"], inv.cwd)
    return normalize(inv.host, data) if isinstance(data, dict) else None


def evaluate(command: str, base_cwd: str | None = None) -> list[str]:
    lines: list[str] = []
    for inv in guard.match_commands(command, base_cwd):
        if guard.has_flag(inv.args, "--help", "-h", "--web", "-w"):
            continue
        if inv.cwd_unknown and not guard.flag_value(inv.args, "-R", "--repo"):
            continue
        view = fetch(inv)
        if view is not None:
            lines.append(build_summary("create" if inv.action == "create" else "merge", view))
    return lines


def main() -> int:
    if os.environ.get("PR_STEWARD_GUARD", "").lower() == "off":
        return 0
    try:
        payload = json.load(sys.stdin)
        command = payload["tool_input"]["command"]
        if not isinstance(command, str):
            return 0
        cwd = payload.get("cwd")
        lines = evaluate(command, cwd if isinstance(cwd, str) and cwd else None)
        if lines:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                     "additionalContext": " ".join(lines)}}))
    except Exception:  # noqa: BLE001 - fail open on anything unexpected
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
