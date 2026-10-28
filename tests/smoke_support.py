"""Fixture helper for the offline smoke tests: temp git repo, local bare remote, fake `gh` on PATH.

No network and no real `gh`. The fake `gh` answers from a JSON state file (`state.json`) in the fixture
directory and appends every call to `calls.jsonl`. Anything it does not know exits 3 with a clear message.
Note: plain `gh pr checks N` exits 0 even when checks are red (real gh exits 1); the machine-readable
`--json bucket` form carries the result. This keeps land.sh from sleeping in its registration retry loop.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
HOOKS = ROOT / "hooks"

FAKE_GH = r'''#!__PYTHON__
import json, os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
STATE = HERE / "state.json"


def fail(msg, code=3):
    print("fake gh: " + msg, file=sys.stderr)
    sys.exit(code)


def load():
    return json.loads(STATE.read_text())


def save(state):
    STATE.write_text(json.dumps(state))


argv = sys.argv[1:]
repo, args, jq = None, [], None
i = 0
while i < len(argv):
    if argv[i] in ("-R", "--repo") and i + 1 < len(argv):
        repo = argv[i + 1]
        i += 2
    elif argv[i] in ("-q", "--jq") and i + 1 < len(argv):
        jq = argv[i + 1]
        i += 2
    else:
        args.append(argv[i])
        i += 1
with open(HERE / "calls.jsonl", "a") as log:
    log.write(json.dumps({"argv": argv, "cwd": os.getcwd(), "repo": repo}) + "\n")
state = load()


def opt(name):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else None


def pr_for(n):
    pr = state["prs"].get(str(n))
    if pr is None:
        fail("unknown PR %s" % n, 1)
    return pr


def render(obj, fields):
    if jq is None:
        print(json.dumps({k: obj[k] for k in fields if k in obj}))
    elif jq in (".body", ".state", ".mergeStateStatus"):
        print(obj[jq[1:]])
    elif "join" in jq:
        print("\t".join([obj["state"], obj["headRefName"], obj["baseRefName"], str(obj["isCrossRepository"]).lower()]))
    else:
        fail("unsupported --jq %r" % jq)


if args[:2] == ["pr", "view"] and len(args) >= 3:
    pr = pr_for(args[2])
    view = dict(pr)
    view["statusCheckRollup"] = pr.get("checks", [])
    render(view, (opt("--json") or "").split(","))
elif args[:2] == ["pr", "checks"] and len(args) >= 3:
    pr = pr_for(args[2])
    if "--json" in args:
        if jq == ".[].bucket":
            print("\n".join(c.get("bucket", "pass") for c in pr.get("checks", [])))
        else:
            print(json.dumps(pr.get("checks", [])))
    else:
        print("\n".join("%s\t%s" % (c["name"], c.get("bucket", "pass")) for c in pr.get("checks", [])))
elif args[:2] == ["pr", "merge"] and len(args) >= 3:
    pr = pr_for(args[2])
    if pr["state"] != "OPEN":
        fail("PR is not open", 1)
    state.setdefault("merges", []).append({"pr": int(args[2]), "args": args[3:]})
    if state.get("really_merge", True):
        env = dict(os.environ, GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@e", GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@e")
        with tempfile.TemporaryDirectory() as tmp:
            def git(*a):
                subprocess.run(["git", *a], cwd=tmp + "/c", env=env, check=True, capture_output=True)
            subprocess.run(["git", "clone", "-q", state["bare"], tmp + "/c"], env=env, check=True, capture_output=True)
            git("checkout", "-q", pr["baseRefName"])
            git("merge", "-q", "--no-ff", "-m", "Merge PR %s" % args[2], "origin/" + pr["headRefName"])
            git("push", "-q", "origin", pr["baseRefName"])
    pr["state"] = "MERGED"
    save(state)
elif args[:2] == ["pr", "edit"] and len(args) >= 3:
    pr_for(args[2])
elif args[:2] == ["issue", "view"] and len(args) >= 3:
    issue = state["issues"].get(args[2]) or fail("unknown issue %s" % args[2], 1)
    render(issue, ["body"])
elif args[:2] == ["issue", "edit"] and len(args) >= 3:
    issue = state["issues"].get(args[2]) or fail("unknown issue %s" % args[2], 1)
    path = opt("--body-file") or fail("issue edit needs --body-file")
    issue["body"] = Path(path).read_text()
    save(state)
elif args[:1] == ["api"]:
    print("[]")
else:
    fail("unexpected call: gh " + " ".join(argv))
'''


def require_tools() -> None:
    """Skip the calling test when git or python3 is missing."""
    for tool in ("git", "python3"):
        if shutil.which(tool) is None:
            raise unittest.SkipTest(f"{tool} not found on PATH")


class Fixture:
    """Temp git repo + bare remote + fake gh. Use as a context manager or call cleanup()."""

    def __init__(self) -> None:
        require_tools()
        self.tmp = Path(tempfile.mkdtemp(prefix="prsteward-smoke-")).resolve()
        # "github.com" in the path lets land.sh's host check accept the local bare remote.
        self.bare = self.tmp / "github.com" / "test" / "repo.git"
        self.repo = self.tmp / "repo"
        self.bin = self.tmp / "bin"
        self.state_path = self.tmp / "state.json"
        self.env = {
            **os.environ,
            "PATH": f"{self.bin}{os.pathsep}{os.environ.get('PATH', '')}",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
            "GIT_TERMINAL_PROMPT": "0",
        }
        self.env.pop("PR_STEWARD_GUARD", None)
        self.state: dict = {"bare": str(self.bare), "prs": {}, "issues": {}, "really_merge": True}
        self.bin.mkdir()
        gh = self.bin / "gh"
        gh.write_text(FAKE_GH.replace("__PYTHON__", sys.executable))
        gh.chmod(0o755)
        self.bare.mkdir(parents=True)
        self.git("init", "-q", "--bare", "-b", "main", cwd=self.bare)
        self.git("init", "-q", "-b", "main", str(self.repo), cwd=self.tmp)
        self.git("remote", "add", "origin", str(self.bare))
        self.write("README.md", "readme\n")
        self.write("src.txt", "line one\nline two\n")
        self.write("CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- base\n\n## [0.1.0]\n")
        self.commit("initial")
        self.git("push", "-q", "origin", "main")
        self.save_state()

    def cleanup(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def __enter__(self) -> "Fixture":
        return self

    def __exit__(self, *exc: object) -> None:
        self.cleanup()

    def run(self, cmd: list[str], cwd: Path | str | None = None, stdin: str | None = None, timeout: int = 60):
        return subprocess.run(cmd, cwd=cwd or self.repo, env=self.env, input=stdin, capture_output=True, text=True,
                              timeout=timeout, check=False)

    def git(self, *args: str, cwd: Path | str | None = None) -> str:
        result = self.run(["git", *args], cwd=cwd)
        if result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
        return result.stdout

    def write(self, name: str, text: str) -> None:
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def make_branch(self, name: str, files: dict[str, str], base: str = "main") -> None:
        """Branch off base with one commit, push it, return to main."""
        self.git("checkout", "-q", "-b", name, base)
        for path, text in files.items():
            self.write(path, text)
        self.commit(f"work on {name}")
        self.git("push", "-q", "origin", name)
        self.git("checkout", "-q", "main")

    def advance_main(self, files: dict[str, str]) -> None:
        self.git("checkout", "-q", "main")
        for path, text in files.items():
            self.write(path, text)
        self.commit("advance main")
        self.git("push", "-q", "origin", "main")

    def set_pr(self, number: int, head: str, *, checks: list[dict] | None = None, merge_state: str = "CLEAN",
               mergeable: str = "MERGEABLE", body: str = "", state: str = "OPEN") -> None:
        self.state["prs"][str(number)] = {
            "state": state, "headRefName": head, "baseRefName": "main", "isCrossRepository": False,
            "mergeStateStatus": merge_state, "mergeable": mergeable, "body": body,
            "checks": checks if checks is not None else [green()],
        }
        self.save_state()

    def set_issue(self, number: int, body: str) -> None:
        self.state["issues"][str(number)] = {"body": body}
        self.save_state()

    def save_state(self) -> None:
        self.state_path.write_text(json.dumps(self.state))

    def load_state(self) -> dict:
        return json.loads(self.state_path.read_text())

    def calls(self) -> list[dict]:
        path = self.tmp / "calls.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines() if line]

    def remote_show(self, ref: str, path: str) -> str:
        return self.git("show", f"{ref}:{path}", cwd=self.bare)


def green(name: str = "ci") -> dict:
    return {"name": name, "status": "COMPLETED", "conclusion": "SUCCESS", "bucket": "pass"}


def red(name: str = "ci") -> dict:
    return {"name": name, "status": "COMPLETED", "conclusion": "FAILURE", "bucket": "fail"}
