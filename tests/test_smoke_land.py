import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_support as ss  # noqa: E402

CHANGELOG = "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- base\n- {}\n\n## [0.1.0]\n"


class LandSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = ss.Fixture()
        self.addCleanup(self.fx.cleanup)

    def land(self, *prs: str):
        return self.fx.run(["bash", str(ss.SCRIPTS / "land.sh"), *prs])

    def merges(self) -> list:
        return self.fx.load_state().get("merges", [])

    def test_rebases_onto_advanced_main_and_merges(self) -> None:
        self.fx.make_branch("feat", {"feature.txt": "feature\n"})
        self.fx.advance_main({"other.txt": "other\n"})
        advanced = self.fx.git("rev-parse", "main")
        self.fx.set_pr(11, "feat")
        result = self.land("11")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PR 11: MERGED", result.stdout)
        self.assertEqual(self.fx.load_state()["prs"]["11"]["state"], "MERGED")
        self.assertEqual(self.fx.remote_show("main", "feature.txt"), "feature\n")
        self.assertEqual(self.fx.remote_show("main", "other.txt"), "other\n")
        # The feature commit was rebased: its parent is the advanced main tip.
        self.assertEqual(self.fx.git("rev-parse", "main^2^", cwd=self.fx.bare), advanced)
        self.assertNotEqual(self.fx.run(["git", "ls-remote", "--exit-code", "--heads", "origin", "feat"]).returncode, 0,
                            "head branch should be deleted")

    def test_union_resolves_append_only_changelog_conflict(self) -> None:
        self.fx.make_branch("feat", {"CHANGELOG.md": CHANGELOG.format("from feat")})
        self.fx.advance_main({"CHANGELOG.md": CHANGELOG.format("from main")})
        self.fx.set_pr(12, "feat")
        result = self.land("12")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = self.fx.remote_show("main", "CHANGELOG.md")
        self.assertIn("- from feat", log)
        self.assertIn("- from main", log)
        self.assertNotIn("<<<<<<<", log)

    def test_stops_on_real_source_conflict(self) -> None:
        self.fx.make_branch("feat", {"src.txt": "line one\nfeat change\n"})
        self.fx.advance_main({"src.txt": "line one\nmain change\n"})
        self.fx.set_pr(13, "feat")
        result = self.land("13")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("src.txt", result.stderr)
        self.assertEqual(self.merges(), [])
        self.assertEqual(self.fx.load_state()["prs"]["13"]["state"], "OPEN")

    def test_stops_on_red_checks(self) -> None:
        self.fx.make_branch("feat", {"feature.txt": "feature\n"})
        self.fx.set_pr(14, "feat", checks=[ss.red()])
        result = self.land("14")
        self.assertEqual(result.returncode, 5, result.stdout + result.stderr)
        self.assertIn("a check failed", result.stderr)
        self.assertEqual(self.merges(), [])

    def test_refuses_pr_that_is_not_open(self) -> None:
        self.fx.make_branch("feat", {"feature.txt": "feature\n"})
        self.fx.set_pr(15, "feat", state="MERGED")
        result = self.land("15")
        self.assertEqual(result.returncode, 3)
        self.assertEqual(self.merges(), [])


if __name__ == "__main__":
    unittest.main()
