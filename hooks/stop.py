#!/usr/bin/env python3
"""Stop hook: a short, non-blocking warning at the end of a turn.

Warns, on a feature branch only, about unpushed commits, an open PR whose linked `Closes #N` issue still has
unticked items, and leftover worktrees under a temp/scratch path. Silent when there is nothing to say.
Exits at once when `stop_hook_active` is set (no loops), keeps every subprocess short (about 5s in total) and
fails open. Disable with PR_STEWARD_GUARD=off.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard  # noqa: E402

BUDGET = 5.0
MAIN_BRANCHES = {"main", "master"}
SCRATCH_PREFIXES = ("/tmp/", "/var/tmp/", "/private/tmp/", "/private/var/folders/")
SCRATCH_RE = re.compile(r"(^|/)(scratch(pad)?|tmp|temp)(/|$)", re.I)


def is_feature_branch(branch: str) -> bool:
    return bool(branch) and branch not in MAIN_BRANCHES and not branch.startswith("release/")


def is_scratch_path(path: str) -> bool:
    return path.startswith(SCRATCH_PREFIXES) or bool(SCRATCH_RE.search(path))


def parse_worktrees(porcelain: str) -> list[str]:
    return [line[len("worktree "):] for line in porcelain.splitlines() if line.startswith("worktree ")]


def build_warnings(branch: str, unpushed: int | None, pr: dict | None, issue_bodies: dict[int, str],
                   worktrees: list[str]) -> list[str]:
    """Pure: warnings from plain inputs. unpushed is None when the branch has no upstream."""
    if not is_feature_branch(branch):
        return []
    warnings: list[str] = []
    if unpushed is None:
        warnings.append(f"branch {branch} has no upstream (unpushed commits)")
    elif unpushed > 0:
        warnings.append(f"{unpushed} unpushed commit(s) on {branch}")
    if pr and str(pr.get("state") or "").upper() == "OPEN":
        closes, _ = guard.references(str(pr.get("body") or ""))
        for problem in guard.checklist_problems(sorted(set(closes)), issue_bodies):
            warnings.append(f"PR #{pr.get('number')}: {problem}")
    leftovers = [w for w in worktrees if is_scratch_path(w)]
    if leftovers:
        shown = ", ".join(leftovers[:3]) + (f" +{len(leftovers) - 3} more" if len(leftovers) > 3 else "")
        warnings.append(f"leftover scratch worktree(s): {shown}")
    return warnings


def build_message(warnings: list[str]) -> str:
    return "pr-steward: " + "; ".join(warnings) if warnings else ""


class Runner:
    """Runs short subprocesses inside one shared time budget."""

    def __init__(self, cwd: str, budget: float = BUDGET) -> None:
        self.cwd, self.deadline = cwd, time.monotonic() + budget

    def run(self, cmd: list[str]) -> str | None:
        left = self.deadline - time.monotonic()
        if left <= 0.2:
            return None
        try:
            done = subprocess.run(cmd, capture_output=True, text=True, timeout=min(left, 2.5), cwd=self.cwd)
        except (OSError, subprocess.SubprocessError):
            return None
        return done.stdout if done.returncode == 0 else None

    def json(self, cmd: list[str]) -> object | None:
        out = self.run(cmd)
        try:
            return json.loads(out) if out else None
        except ValueError:
            return None


def gather(cwd: str) -> list[str]:
    runner = Runner(cwd)
    branch = (runner.run(["git", "branch", "--show-current"]) or "").strip()
    if not is_feature_branch(branch):
        return []
    count = runner.run(["git", "rev-list", "--count", "@{u}..HEAD"])
    unpushed = int(count.strip()) if count and count.strip().isdigit() else None
    toplevel = (runner.run(["git", "rev-parse", "--show-toplevel"]) or "").strip()
    worktrees = [w for w in parse_worktrees(runner.run(["git", "worktree", "list", "--porcelain"]) or "")
                 if os.path.realpath(w) != os.path.realpath(toplevel or cwd)]
    pr: dict | None = None
    bodies: dict[int, str] = {}
    if shutil.which("gh"):
        data = runner.json(["gh", "pr", "view", "--json", "number,state,body"])
        if isinstance(data, dict):
            pr = data
            closes, _ = guard.references(str(data.get("body") or ""))
            for number in sorted(set(closes)):
                issue = runner.json(["gh", "issue", "view", str(number), "--json", "body"])
                if isinstance(issue, dict) and isinstance(issue.get("body"), str):
                    bodies[number] = issue["body"]
    return build_warnings(branch, unpushed, pr, bodies, worktrees)


def main() -> int:
    if os.environ.get("PR_STEWARD_GUARD", "").lower() == "off":
        return 0
    try:
        payload = json.load(sys.stdin)
        if payload.get("stop_hook_active"):
            return 0
        cwd = payload.get("cwd")
        if not isinstance(cwd, str) or not os.path.isdir(cwd):
            return 0
        message = build_message(gather(cwd))
        if message:
            print(json.dumps({"systemMessage": message}))
    except Exception:  # noqa: BLE001 - fail open on anything unexpected
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
