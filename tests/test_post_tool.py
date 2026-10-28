import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "hooks"
sys.path.insert(0, str(HOOKS))
import post_tool  # noqa: E402


class NormalizeTest(unittest.TestCase):
    def test_gh(self) -> None:
        view = post_tool.normalize("gh", {"number": 7, "state": "OPEN", "labels": [{"name": "bug"}],
                                          "assignees": [{"login": "me"}], "reviewRequests": [{"login": "bob"}]})
        self.assertEqual(view, {"number": 7, "state": "open", "labels": ["bug"], "assignees": ["me"],
                                "reviewers": ["bob"]})

    def test_glab(self) -> None:
        view = post_tool.normalize("glab", {"iid": 3, "state": "merged", "labels": ["x"],
                                            "assignees": [{"username": "me"}], "reviewers": []})
        self.assertEqual((view["number"], view["state"], view["assignees"], view["reviewers"]),
                         (3, "merged", ["me"], []))


class SummaryTest(unittest.TestCase):
    def test_complete(self) -> None:
        line = post_tool.build_summary("create", {"number": 7, "state": "open", "labels": ["bug"],
                                                  "assignees": ["me"], "reviewers": ["bob"]})
        self.assertIn("#7", line)
        self.assertIn("labels: bug", line)
        self.assertNotIn("missing", line)
        self.assertNotIn("\n", line)

    def test_flags_missing(self) -> None:
        line = post_tool.build_summary("merge", {"number": 8, "state": "merged", "labels": [],
                                                 "assignees": [], "reviewers": []})
        self.assertIn("missing: no assignee, no labels", line)


class MainTest(unittest.TestCase):
    def run_hook(self, payload: object, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(HOOKS / "post_tool.py")], input=json.dumps(payload),
                              capture_output=True, text=True, env={**os.environ, **env}, timeout=30)

    def test_unmatched_is_silent(self) -> None:
        done = self.run_hook({"tool_input": {"command": "ls"}, "cwd": "/tmp"})
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_garbage_fails_open(self) -> None:
        done = subprocess.run([sys.executable, str(HOOKS / "post_tool.py")], input="not json",
                              capture_output=True, text=True, timeout=30)
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_guard_off(self) -> None:
        done = self.run_hook({"tool_input": {"command": "gh pr create"}, "cwd": "/tmp"}, PR_STEWARD_GUARD="off")
        self.assertEqual((done.returncode, done.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
