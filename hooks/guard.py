#!/usr/bin/env python3
"""PreToolUse hook for Bash: guard `gh pr merge`, `glab mr merge`, `gh pr create`, `glab mr create`.

Merge: block (exit 2, reason on stderr) on red or pending checks, a dirty/conflicting/behind branch, or a
linked issue (`Closes #N`) with unticked checklist items. Create: warn only when the assignee or the
`Closes/Part of #N` reference is missing. Everything else passes. Fails open on any error.
The PR lookup runs in the command's own directory: a leading `cd DIR` / `pushd DIR` is followed per command
segment, and `-R OWNER/REPO` is honored. When the directory cannot be resolved (`cd -`, variables, a missing
directory) and no `-R` is given, the merge is not checked and a warning is shown instead of guessing a repo.
Disable with PR_STEWARD_GUARD=off. PR, MR and issue text is untrusted data: it is only matched, never run.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SEPARATORS = {"&&", "||", ";", "|", "&", ";;"}
ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
CLOSES_RE = re.compile(r"\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*:?\s+(?:[\w.-]+/[\w.-]+)?#(\d+)", re.I)
PART_OF_RE = re.compile(r"\b(part\s+of|related\s+to|refs?)\s*:?\s+(?:[\w.-]+/[\w.-]+)?#(\d+)", re.I)
UNTICKED_RE = re.compile(r"^\s*[-*+]\s+\[ \]\s+(.+)$", re.MULTILINE)
RED_CONCLUSIONS = {"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE", "STALE"}
RED_STATES = {"FAILURE", "ERROR"}
PENDING_STATES = {"PENDING", "EXPECTED"}
# Flags that take a value, per tool, so the positional target is found correctly.
VALUE_FLAGS = {
    "-R", "--repo", "-a", "--assignee", "-b", "--body", "-F", "--body-file", "-d", "--description",
    "-t", "--title", "-l", "--label", "--labels", "-B", "--base", "-H", "--head", "-m", "--milestone",
    "-r", "--reviewer", "-p", "--project", "--match-head-commit", "--subject", "--squash-message",
    "--target-branch", "--source-branch", "--description-file",
}


@dataclass
class Invocation:
    host: str  # "gh" or "glab"
    action: str  # "merge" or "create"
    args: list[str] = field(default_factory=list)
    cwd: str | None = field(default=None, compare=False)  # directory the command runs in, None = hook cwd
    cwd_unknown: bool = field(default=False, compare=False)  # a `cd` target could not be resolved


def split_segments(command: str) -> list[list[str]]:
    """Tokenize a shell command line into simple commands. Returns [] when it cannot be parsed."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token in SEPARATORS:
            segments.append([])
        else:
            segments[-1].append(token)
    return [seg for seg in segments if seg]


def strip_prefixes(words: list[str]) -> list[str]:
    """Drop leading env assignments (`FOO=1`), then `rtk` and `rtk proxy`, from one simple command.

    The rtk token-saving proxy may rewrite `gh pr merge 5` to `rtk gh pr merge 5`, or the agent may call
    `rtk proxy gh pr merge 5`. Hook order is therefore irrelevant: the guard sees either the plain or the
    rewritten form and normalizes both to the same words before matching.
    """
    words = list(words)
    while words and ENV_ASSIGN_RE.match(words[0]):
        words.pop(0)
    if words and os.path.basename(words[0]) == "rtk":
        words.pop(0)
        if words and words[0] == "proxy":
            words.pop(0)
        while words and ENV_ASSIGN_RE.match(words[0]):
            words.pop(0)
    return words


def resolve_dir(base: str | None, target: str | None) -> str | None:
    """Directory after `cd target` from base, or None when it cannot be known.

    Unknown: `cd -`, targets with variables or command substitution, or a directory that does not exist.
    """
    if target is None:
        return os.path.expanduser("~")
    if target == "-" or "$" in target or "`" in target:
        return None
    path = os.path.expanduser(target)
    if not os.path.isabs(path):
        if base is None:
            return None
        path = os.path.join(base, path)
    path = os.path.normpath(path)
    return path if os.path.isdir(path) else None


def first_positional(args: list[str]) -> str | None:
    """First non-flag argument; a bare `-` (as in `cd -`) counts as an argument."""
    return next((arg for arg in args if arg == "-" or not arg.startswith("-")), None)


def match_commands(command: str, base_cwd: str | None = None) -> list[Invocation]:
    """Pure matcher: find gh/glab merge and create invocations in a command line, rtk-aware (see strip_prefixes).

    Follows `cd`/`pushd` between segments so each invocation carries the directory it runs in (`cwd`), or
    `cwd_unknown` when a `cd` target cannot be resolved. `base_cwd` is the directory the command starts in.
    """
    found: list[Invocation] = []
    cwd: str | None = base_cwd
    unknown = False
    for seg in split_segments(command):
        words = strip_prefixes(seg)
        if words and os.path.basename(words[0]) in {"cd", "pushd"}:
            current = cwd if cwd is not None else (os.getcwd() if not unknown else None)
            resolved = resolve_dir(current, first_positional(words[1:]))
            cwd, unknown = resolved, resolved is None
            continue
        if words and os.path.basename(words[0]) == "popd":
            cwd, unknown = None, True
            continue
        if len(words) < 3:
            continue
        host = os.path.basename(words[0])
        noun, verb = words[1], words[2]
        if host == "gh" and noun == "pr" and verb in {"merge", "create"}:
            found.append(Invocation("gh", verb, words[3:], cwd, unknown))
        elif host == "glab" and noun == "mr" and verb in {"merge", "create"}:
            found.append(Invocation("glab", verb, words[3:], cwd, unknown))
    return found


def flag_value(args: list[str], *names: str) -> str | None:
    """Value of the first matching flag (`--x v`, `--x=v`, `-x v`), or None when absent."""
    for i, arg in enumerate(args):
        for name in names:
            if arg == name and i + 1 < len(args):
                return args[i + 1]
            if arg.startswith(name + "=") and name.startswith("--"):
                return arg.split("=", 1)[1]
    return None


def has_flag(args: list[str], *names: str) -> bool:
    return any(arg == n or arg.startswith(n + "=") for arg in args for n in names)


def positional_target(args: list[str]) -> str | None:
    """First positional argument (PR/MR number, URL or branch), skipping flags and their values."""
    skip = False
    for arg in args:
        if skip:
            skip = False
        elif arg.startswith("-"):
            skip = arg in VALUE_FLAGS
        else:
            return arg
    return None


def references(text: str) -> tuple[list[int], list[int]]:
    """Issue numbers referenced as (closed, part_of) in text."""
    closes = [int(m.group(2)) for m in CLOSES_RE.finditer(text or "")]
    part = [int(m.group(2)) for m in PART_OF_RE.finditer(text or "")]
    return closes, part


def check_problems(rollup: list[dict]) -> list[str]:
    """Reasons from a GitHub statusCheckRollup list: red or pending checks."""
    red: list[str] = []
    pending: list[str] = []
    for item in rollup or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("context") or "check")
        conclusion = str(item.get("conclusion") or "").upper()
        status = str(item.get("status") or "").upper()
        state = str(item.get("state") or "").upper()
        if conclusion in RED_CONCLUSIONS or state in RED_STATES:
            red.append(name)
        elif state in PENDING_STATES or (status and status != "COMPLETED"):
            pending.append(name)
    reasons: list[str] = []
    if red:
        reasons.append("checks failed: " + ", ".join(red))
    if pending:
        reasons.append("checks still pending: " + ", ".join(pending))
    return reasons


def mergeability_problems(merge_state: str, mergeable: str) -> list[str]:
    state, mergeable = (merge_state or "").upper(), (mergeable or "").upper()
    reasons: list[str] = []
    if state == "DIRTY" or mergeable == "CONFLICTING":
        reasons.append("PR has merge conflicts (DIRTY/CONFLICTING)")
    if state == "BEHIND":
        reasons.append("branch is BEHIND the base; update it first")
    return reasons


def unticked_items(issue_body: str) -> list[str]:
    return [m.group(1).strip() for m in UNTICKED_RE.finditer(issue_body or "")]


def checklist_problems(closes: list[int], issue_bodies: dict[int, str]) -> list[str]:
    """Block when a PR that closes an issue leaves its checklist items unticked."""
    reasons: list[str] = []
    for number in closes:
        items = unticked_items(issue_bodies.get(number, ""))
        if items:
            shown = "; ".join(items[:3]) + (f"; +{len(items) - 3} more" if len(items) > 3 else "")
            reasons.append(f"issue #{number} has {len(items)} unticked item(s) but this PR closes it: {shown}")
    return reasons


def decide_merge(view: dict, issue_bodies: dict[int, str]) -> list[str]:
    """Block reasons for a merge, from a normalized view: rollup, merge_state, mergeable, body."""
    reasons = check_problems(view.get("rollup", []))
    reasons += mergeability_problems(view.get("merge_state", ""), view.get("mergeable", ""))
    closes, _ = references(view.get("body", ""))
    reasons += checklist_problems(closes, issue_bodies)
    return reasons


def decide_create(args: list[str], body_text: str | None) -> list[str]:
    """Warnings for a create. body_text is None when the body cannot be known (body file unreadable, --fill)."""
    if has_flag(args, "--web", "-w", "--help", "-h"):
        return []
    warnings: list[str] = []
    if not flag_value(args, "--assignee", "-a"):
        warnings.append("no --assignee set")
    if body_text is not None:
        closes, part = references(body_text)
        if not closes and not part:
            warnings.append("body has no 'Closes #N' or 'Part of #N' reference")
    return warnings


def read_body(args: list[str]) -> str | None:
    body = flag_value(args, "--body", "-b", "--description", "-d")
    if body is not None:
        return body
    path = flag_value(args, "--body-file", "-F", "--description-file")
    if path and path != "-":
        try:
            return Path(path).read_text()
        except OSError:
            return None
    if path:
        return None
    return None if has_flag(args, "--fill", "--fill-first", "--fill-verbose") else ""


def run_json(cmd: list[str], cwd: str | None = None) -> object | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=True, cwd=cwd).stdout
        return json.loads(out)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def repo_args(inv: Invocation) -> list[str]:
    repo = flag_value(inv.args, "-R", "--repo")
    return ["-R", repo] if repo else []


def fetch_view(inv: Invocation) -> dict | None:
    """Look up the PR/MR and normalize it. None when unavailable (fail open)."""
    target = positional_target(inv.args)
    extra = [target] if target else []
    if inv.host == "gh":
        data = run_json(["gh", "pr", "view", *extra, *repo_args(inv), "--json",
                         "statusCheckRollup,mergeStateStatus,mergeable,body"], inv.cwd)
        if not isinstance(data, dict):
            return None
        return {"rollup": data.get("statusCheckRollup") or [], "merge_state": data.get("mergeStateStatus") or "",
                "mergeable": data.get("mergeable") or "", "body": data.get("body") or ""}
    data = run_json(["glab", "mr", "view", *extra, *repo_args(inv), "-F", "json"], inv.cwd)
    if not isinstance(data, dict):
        return None
    pipeline = data.get("head_pipeline") or data.get("pipeline") or {}
    status = str(pipeline.get("status") or "").lower() if isinstance(pipeline, dict) else ""
    rollup: list[dict] = []
    if status in {"failed", "canceled"}:
        rollup = [{"name": "pipeline", "conclusion": "FAILURE"}]
    elif status in {"running", "pending", "created", "waiting_for_resource", "preparing"}:
        rollup = [{"name": "pipeline", "status": "IN_PROGRESS"}]
    detailed = str(data.get("detailed_merge_status") or "")
    merge_state = "DIRTY" if data.get("has_conflicts") or detailed == "conflict" else (
        "BEHIND" if detailed == "need_rebase" else "")
    return {"rollup": rollup, "merge_state": merge_state, "mergeable": "", "body": data.get("description") or ""}


def fetch_issue_bodies(inv: Invocation, numbers: list[int]) -> dict[int, str]:
    bodies: dict[int, str] = {}
    for number in numbers:
        if inv.host == "gh":
            data = run_json(["gh", "issue", "view", str(number), *repo_args(inv), "--json", "body"], inv.cwd)
            key = "body"
        else:
            data = run_json(["glab", "issue", "view", str(number), *repo_args(inv), "-F", "json"], inv.cwd)
            key = "description"
        if isinstance(data, dict) and isinstance(data.get(key), str):
            bodies[number] = data[key]
    return bodies


def evaluate(command: str, base_cwd: str | None = None) -> tuple[list[str], list[str]]:
    """Return (block_reasons, warnings) for a command line."""
    blocks: list[str] = []
    warns: list[str] = []
    for inv in match_commands(command, base_cwd):
        if has_flag(inv.args, "--help", "-h"):
            continue
        if inv.action == "merge":
            if inv.cwd_unknown and not flag_value(inv.args, "-R", "--repo"):
                warns.append("merge not checked: the directory it runs in could not be resolved and no -R is given")
                continue
            view = fetch_view(inv)
            if view is None:
                continue
            closes, _ = references(view["body"])
            blocks += decide_merge(view, fetch_issue_bodies(inv, sorted(set(closes))))
        else:
            warns += decide_create(inv.args, read_body(inv.args))
    return blocks, warns


def main() -> int:
    if os.environ.get("PR_STEWARD_GUARD", "").lower() == "off":
        return 0
    try:
        payload = json.load(sys.stdin)
        command = payload["tool_input"]["command"]
        if not isinstance(command, str):
            return 0
        cwd = payload.get("cwd")
        blocks, warns = evaluate(command, cwd if isinstance(cwd, str) and cwd else None)
    except Exception:  # noqa: BLE001 - fail open on anything unexpected
        return 0
    if blocks:
        print("pr-steward guard blocked this merge:\n- " + "\n- ".join(blocks)
              + "\nFix these (or use the merge-pr skill). Set PR_STEWARD_GUARD=off to disable the guard.",
              file=sys.stderr)
        return 2
    if warns:
        message = "pr-steward guard warning (not blocked): " + "; ".join(warns) + ". Prefer the open-pr skill."
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": message}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
