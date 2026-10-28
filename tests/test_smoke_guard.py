import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_support as ss  # noqa: E402


class GuardSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = ss.Fixture()
        self.addCleanup(self.fx.cleanup)

    def hook(self, command: str, cwd: Path | str | None = None):
        payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd or self.fx.repo)}
        return self.fx.run([sys.executable, str(ss.HOOKS / "guard.py")], stdin=json.dumps(payload))

    def test_clean_pr_allowed(self) -> None:
        self.fx.set_pr(5, "feat")
        result = self.hook("gh pr merge 5 --merge")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.fx.calls(), "guard should have asked gh")

    def test_red_checks_block(self) -> None:
        self.fx.set_pr(5, "feat", checks=[ss.red("build")])
        result = self.hook("gh pr merge 5")
        self.assertEqual(result.returncode, 2)
        self.assertIn("checks failed: build", result.stderr)

    def test_closes_issue_with_unticked_items_blocks(self) -> None:
        self.fx.set_pr(5, "feat", body="Closes #9")
        self.fx.set_issue(9, "- [x] done\n- [ ] todo\n")
        result = self.hook("gh pr merge 5")
        self.assertEqual(result.returncode, 2)
        self.assertIn("issue #9 has 1 unticked", result.stderr)

    def test_part_of_issue_allowed(self) -> None:
        self.fx.set_pr(5, "feat", body="Part of #9")
        self.fx.set_issue(9, "- [ ] todo\n")
        self.assertEqual(self.hook("gh pr merge 5").returncode, 0)

    def test_cd_resolves_directory(self) -> None:
        self.fx.set_pr(5, "feat")
        other = self.fx.tmp / "other"
        other.mkdir()
        result = self.hook(f"cd {other} && gh pr merge 5", cwd=self.fx.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        cwds = {os.path.realpath(c["cwd"]) for c in self.fx.calls()}
        self.assertEqual(cwds, {os.path.realpath(other)})

    def test_repo_flag_honored(self) -> None:
        self.fx.set_pr(5, "feat")
        result = self.hook("cd /nonexistent/dir && gh pr merge 5 -R owner/repo")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.fx.calls()
        self.assertTrue(calls)
        self.assertTrue(all(c["repo"] == "owner/repo" for c in calls))

    def test_unknown_cwd_warns_and_allows(self) -> None:
        self.fx.set_pr(5, "feat", checks=[ss.red()])
        result = self.hook("cd /nonexistent/dir && gh pr merge 5")
        self.assertEqual(result.returncode, 0)
        self.assertIn("merge not checked", result.stdout)
        self.assertEqual(self.fx.calls(), [])

    def test_guard_off_allows(self) -> None:
        self.fx.set_pr(5, "feat", checks=[ss.red()])
        self.fx.env["PR_STEWARD_GUARD"] = "off"
        self.assertEqual(self.hook("gh pr merge 5").returncode, 0)


if __name__ == "__main__":
    unittest.main()
