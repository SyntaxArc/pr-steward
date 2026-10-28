import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
import guard  # noqa: E402


class MatchTest(unittest.TestCase):
    def test_matches_merge_and_create(self) -> None:
        self.assertEqual(guard.match_commands("gh pr merge 5 --squash")[0].action, "merge")
        self.assertEqual(guard.match_commands("glab mr create -a me")[0].host, "glab")

    def test_chained_and_env_prefix(self) -> None:
        found = guard.match_commands("git push && FOO=1 gh pr merge 7; echo done")
        self.assertEqual([(i.host, i.action) for i in found], [("gh", "merge")])

    def test_read_only_not_matched(self) -> None:
        for cmd in ("gh pr view 5", "gh pr list", "glab mr view 2", "gh issue create", "echo gh pr merge"):
            self.assertEqual(guard.match_commands(cmd), [], cmd)

    def test_rtk_forms_match_like_plain(self) -> None:
        for cmd in ("rtk gh pr merge 5", "rtk proxy gh pr merge 5", "FOO=1 rtk gh pr merge 5",
                    "cd x && rtk gh pr merge 5", "rtk proxy FOO=1 gh pr merge 5", "a | rtk proxy gh pr merge 5",
                    "false || rtk gh pr merge 5", "echo 'a && b'; rtk gh pr merge 5"):
            found = guard.match_commands(cmd)
            self.assertEqual([(i.host, i.action, i.args) for i in found], [("gh", "merge", ["5"])], cmd)

    def test_rtk_create_and_glab(self) -> None:
        self.assertEqual(guard.match_commands("rtk gh pr create -a me")[0].action, "create")
        self.assertEqual(guard.match_commands("rtk proxy glab mr merge 3")[0].host, "glab")

    def test_rtk_negatives(self) -> None:
        for cmd in ("rtk gh pr view 5", "rtk proxy gh pr list", "rtk git status", "rtk",
                    "rtk proxy", "echo gh pr merge", "rtk echo gh pr merge 5", "echo 'rtk gh pr merge 5'",
                    "echo 'x' && echo \"a; gh pr merge 5\""):
            self.assertEqual(guard.match_commands(cmd), [], cmd)

    def test_unparsable_is_empty(self) -> None:
        self.assertEqual(guard.match_commands("gh pr merge 'unterminated"), [])

    def test_target_and_flags(self) -> None:
        args = ["-R", "o/r", "--squash", "42"]
        self.assertEqual(guard.positional_target(args), "42")
        self.assertIsNone(guard.positional_target(["--squash"]))
        self.assertEqual(guard.flag_value(["--body=hi"], "--body", "-b"), "hi")
        self.assertEqual(guard.flag_value(["-a", "me"], "--assignee", "-a"), "me")


class MergeDecisionTest(unittest.TestCase):
    def test_clean_pr_passes(self) -> None:
        view = {"rollup": [{"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"},
                           {"name": "s", "status": "COMPLETED", "conclusion": "SKIPPED"}],
                "merge_state": "CLEAN", "mergeable": "MERGEABLE", "body": "Part of #3"}
        self.assertEqual(guard.decide_merge(view, {3: "- [ ] todo"}), [])

    def test_red_pending_checks(self) -> None:
        rollup = [{"name": "lint", "status": "COMPLETED", "conclusion": "FAILURE"},
                  {"name": "test", "status": "IN_PROGRESS", "conclusion": ""},
                  {"context": "ext", "state": "PENDING"}]
        reasons = guard.check_problems(rollup)
        self.assertEqual(len(reasons), 2)
        self.assertIn("lint", reasons[0])
        self.assertIn("test", reasons[1])

    def test_mergeability(self) -> None:
        self.assertEqual(len(guard.mergeability_problems("DIRTY", "CONFLICTING")), 1)
        self.assertEqual(len(guard.mergeability_problems("BEHIND", "MERGEABLE")), 1)
        self.assertEqual(guard.mergeability_problems("CLEAN", "MERGEABLE"), [])

    def test_closes_with_unticked_blocks(self) -> None:
        view = {"rollup": [], "merge_state": "CLEAN", "mergeable": "MERGEABLE", "body": "Closes #9"}
        reasons = guard.decide_merge(view, {9: "- [x] a\n- [ ] b\n* [ ] c"})
        self.assertEqual(len(reasons), 1)
        self.assertIn("2 unticked", reasons[0])

    def test_closes_all_ticked_passes(self) -> None:
        self.assertEqual(guard.checklist_problems([9], {9: "- [x] a"}), [])

    def test_references(self) -> None:
        self.assertEqual(guard.references("Closes #1\nfixes org/repo#2\nPart of #3"), ([1, 2], [3]))
        self.assertEqual(guard.references(""), ([], []))


class CreateDecisionTest(unittest.TestCase):
    def test_warns_missing_both(self) -> None:
        self.assertEqual(len(guard.decide_create(["--title", "x"], "no ref")), 2)

    def test_ok(self) -> None:
        self.assertEqual(guard.decide_create(["--assignee", "@me"], "Part of #4"), [])

    def test_unknown_body_skips_reference_warning(self) -> None:
        self.assertEqual(guard.decide_create(["-a", "me"], None), [])

    def test_web_never_warns(self) -> None:
        self.assertEqual(guard.decide_create(["--web"], ""), [])


class WorkingDirectoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = os.path.realpath(self._tmp.name)
        os.mkdir(os.path.join(self.base, "sub"))

    def test_cd_absolute_sets_cwd(self) -> None:
        inv = guard.match_commands(f"cd {self.base} && gh pr merge 5", "/elsewhere")[0]
        self.assertEqual((inv.cwd, inv.cwd_unknown), (self.base, False))

    def test_cd_relative_uses_base(self) -> None:
        inv = guard.match_commands("cd sub && gh pr merge 5", self.base)[0]
        self.assertEqual(inv.cwd, os.path.join(self.base, "sub"))

    def test_cd_with_rtk_and_semicolon(self) -> None:
        inv = guard.match_commands("cd sub; rtk gh pr merge 5", self.base)[0]
        self.assertEqual(inv.cwd, os.path.join(self.base, "sub"))

    def test_no_cd_keeps_base(self) -> None:
        inv = guard.match_commands("gh pr merge 5", self.base)[0]
        self.assertEqual((inv.cwd, inv.cwd_unknown), (self.base, False))

    def test_unknown_targets(self) -> None:
        for cmd in ("cd /does/not/exist && gh pr merge 5", "cd - && gh pr merge 5", "cd $X && gh pr merge 5",
                    "popd && gh pr merge 5"):
            inv = guard.match_commands(cmd, self.base)[0]
            self.assertEqual((inv.cwd, inv.cwd_unknown), (None, True), cmd)

    def test_absolute_cd_recovers_after_unknown(self) -> None:
        inv = guard.match_commands(f"cd - && cd {self.base} && gh pr merge 5", self.base)[0]
        self.assertEqual((inv.cwd, inv.cwd_unknown), (self.base, False))

    def test_unknown_cwd_without_repo_flag_warns_and_skips_lookup(self) -> None:
        with mock.patch.object(guard, "fetch_view") as fetch:
            blocks, warns = guard.evaluate("cd /does/not/exist && gh pr merge 5", self.base)
        fetch.assert_not_called()
        self.assertEqual(blocks, [])
        self.assertTrue(any("not checked" in w for w in warns))

    def test_unknown_cwd_with_repo_flag_still_checks(self) -> None:
        view = {"rollup": [{"name": "lint", "conclusion": "FAILURE"}], "merge_state": "", "mergeable": "", "body": ""}
        with mock.patch.object(guard, "fetch_view", return_value=view) as fetch:
            blocks, _ = guard.evaluate("cd /does/not/exist && gh pr merge 5 -R o/r", self.base)
        fetch.assert_called_once()
        self.assertEqual(blocks, ["checks failed: lint"])

    def test_lookup_runs_in_the_resolved_directory(self) -> None:
        seen: list[str | None] = []

        def fake_run(cmd, **kwargs):  # noqa: ANN001
            seen.append(kwargs.get("cwd"))
            return subprocess.CompletedProcess(cmd, 0, stdout="{}", stderr="")

        with mock.patch.object(guard.subprocess, "run", fake_run):
            guard.evaluate("cd sub && gh pr merge 5", self.base)
        self.assertTrue(seen)
        self.assertTrue(all(c == os.path.join(self.base, "sub") for c in seen))


if __name__ == "__main__":
    unittest.main()
