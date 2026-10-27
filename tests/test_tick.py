import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import tick  # noqa: E402

BODY = "## Checklist\n\n- [ ] first\n- [ ] second\n- [x] third\n"


class TickTest(unittest.TestCase):
    def test_normal_tick_by_text(self) -> None:
        self.assertEqual(tick.tick(BODY, "second"), "## Checklist\n\n- [ ] first\n- [x] second\n- [x] third\n")

    def test_tick_by_number(self) -> None:
        self.assertEqual(tick.tick(BODY, 1), BODY.replace("- [ ] first", "- [x] first"))
        self.assertEqual(tick.tick(BODY, "2"), BODY.replace("- [ ] second", "- [x] second"))

    def test_number_out_of_range(self) -> None:
        with self.assertRaises(tick.TickError):
            tick.tick(BODY, 4)

    def test_crlf_preserved(self) -> None:
        body = BODY.replace("\n", "\r\n")
        self.assertEqual(tick.tick(body, "first"), body.replace("- [ ] first", "- [x] first"))

    def test_fenced_code_ignored(self) -> None:
        body = "```\n- [ ] fake\n```\n- [ ] real\n"
        self.assertEqual(tick.tick(body, 1), "```\n- [ ] fake\n```\n- [x] real\n")
        with self.assertRaises(tick.TickError):
            tick.tick(body, "fake")
        with self.assertRaises(tick.TickError):
            tick.tick(body, 2)

    def test_nested_list(self) -> None:
        body = "- [ ] parent\n  - [ ] child\n    - [ ] grandchild\n"
        self.assertEqual(tick.tick(body, 2), "- [ ] parent\n  - [x] child\n    - [ ] grandchild\n")
        self.assertEqual(tick.tick(body, "grandchild"), "- [ ] parent\n  - [ ] child\n    - [x] grandchild\n")

    def test_duplicate_text_ticks_first_unticked(self) -> None:
        body = "- [x] same\n- [ ] same\n- [ ] same\n"
        self.assertEqual(tick.tick(body, "same"), "- [x] same\n- [x] same\n- [ ] same\n")

    def test_empty_body_refused(self) -> None:
        for body in ("", "  \n\t\n"):
            with self.assertRaises(tick.TickError):
                tick.tick(body, 1)

    def test_missing_item_refused(self) -> None:
        with self.assertRaises(tick.TickError):
            tick.tick(BODY, "nope")

    def test_already_ticked_idempotent(self) -> None:
        self.assertEqual(tick.tick(BODY, "third"), BODY)
        self.assertEqual(tick.tick(BODY, 3), BODY)
        once = tick.tick(BODY, "first")
        self.assertEqual(tick.tick(once, "first"), once)

    def test_item_count_unchanged(self) -> None:
        self.assertEqual(len(tick.find_items(tick.tick(BODY, "first"))), len(tick.find_items(BODY)))


if __name__ == "__main__":
    unittest.main()
