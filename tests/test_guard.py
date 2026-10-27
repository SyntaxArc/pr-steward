import sys
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
