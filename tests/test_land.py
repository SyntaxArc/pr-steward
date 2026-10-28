import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import union_resolve  # noqa: E402


def conflict(ours: str, theirs: str) -> str:
    return f"<<<<<<< HEAD\n{ours}=======\n{theirs}>>>>>>> pr\n"


class UnionResolveTest(unittest.TestCase):
    def test_changelog_bullets_from_both_sides(self) -> None:
        text = "## [Unreleased]\n\n### Added\n\n" + conflict("- ours\n", "- theirs\n") + "\n## [0.1.0]\n"
        self.assertEqual(
            union_resolve.resolve_text(text),
            "## [Unreleased]\n\n### Added\n\n- ours\n- theirs\n\n## [0.1.0]\n",
        )

    def test_table_rows_from_both_sides(self) -> None:
        text = "| a | b |\n| - | - |\n" + conflict("| one | 1 |\n", "| two | 2 |\n")
        self.assertEqual(union_resolve.resolve_text(text), "| a | b |\n| - | - |\n| one | 1 |\n| two | 2 |\n")

    def test_multiple_blocks_and_empty_side(self) -> None:
        text = conflict("- a\n", "") + "mid\n" + conflict("", "- b\n")
        self.assertEqual(union_resolve.resolve_text(text), "- a\nmid\n- b\n")

    def test_diff3_base_section_is_dropped(self) -> None:
        text = "<<<<<<< HEAD\n- ours\n||||||| base\n- old\n=======\n- theirs\n>>>>>>> pr\n"
        self.assertEqual(union_resolve.resolve_text(text), "- ours\n- theirs\n")

    def test_prose_conflict_raises(self) -> None:
        with self.assertRaises(union_resolve.ConflictError):
            union_resolve.resolve_text(conflict("- ours\n", "Some rewritten paragraph.\n"))

    def test_heading_conflict_raises(self) -> None:
        with self.assertRaises(union_resolve.ConflictError):
            union_resolve.resolve_text(conflict("## [Unreleased]\n", "## [0.2.0]\n"))

    def test_unterminated_block_raises(self) -> None:
        with self.assertRaises(union_resolve.ConflictError):
            union_resolve.resolve_text("<<<<<<< HEAD\n- a\n=======\n- b\n")

    def test_text_without_conflicts_is_unchanged(self) -> None:
        self.assertEqual(union_resolve.resolve_text("- a\n\nprose\n"), "- a\n\nprose\n")

    def test_cli_rewrites_file_and_refuses_bad_one(self) -> None:
        script = Path(union_resolve.__file__)
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "CHANGELOG.md"
            bad = Path(tmp) / "README.md"
            good.write_text(conflict("- a\n", "- b\n"))
            bad_text = conflict("prose a\n", "prose b\n")
            bad.write_text(bad_text)
            ok = subprocess.run([sys.executable, str(script), str(good)], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0)
            self.assertEqual(good.read_text(), "- a\n- b\n")
            fail = subprocess.run([sys.executable, str(script), str(bad)], capture_output=True, text=True)
            self.assertEqual(fail.returncode, 2)
            self.assertEqual(bad.read_text(), bad_text)


if __name__ == "__main__":
    unittest.main()
