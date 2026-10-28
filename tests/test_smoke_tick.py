import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_support as ss  # noqa: E402

BODY = "## Checklist\n\n- [ ] first\n- [ ] second\n"


class TickSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = ss.Fixture()
        self.addCleanup(self.fx.cleanup)

    def tick(self, item: str):
        return self.fx.run([sys.executable, str(ss.SCRIPTS / "tick.py"), "7", item, "--host", "gh"])

    def test_ticks_and_verifies_by_read_back(self) -> None:
        self.fx.set_issue(7, BODY)
        result = self.tick("2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ticked and verified", result.stdout)
        self.assertEqual(self.fx.load_state()["issues"]["7"]["body"], "## Checklist\n\n- [ ] first\n- [x] second\n")
        views = [c for c in self.fx.calls() if c["argv"][:2] == ["issue", "view"]]
        self.assertEqual(len(views), 2, "fetch before and read-back after")

    def test_ticks_by_text(self) -> None:
        self.fx.set_issue(7, BODY)
        self.assertEqual(self.tick("first").returncode, 0)
        self.assertIn("- [x] first", self.fx.load_state()["issues"]["7"]["body"])

    def test_refuses_empty_body(self) -> None:
        self.fx.set_issue(7, "")
        result = self.tick("1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("empty", result.stderr)
        self.assertFalse([c for c in self.fx.calls() if c["argv"][:2] == ["issue", "edit"]])

    def test_refuses_missing_item(self) -> None:
        self.fx.set_issue(7, BODY)
        result = self.tick("9")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not found", result.stderr)
        self.assertEqual(self.fx.load_state()["issues"]["7"]["body"], BODY)


if __name__ == "__main__":
    unittest.main()
