import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_catalog  # noqa: E402


class CatalogTest(unittest.TestCase):
    def test_catalog_is_consistent(self) -> None:
        self.assertEqual(check_catalog.check(), [])

    def test_valid_changelog(self) -> None:
        text = "# Changelog\n\n## [Unreleased]\n\n## [0.3.0] - 2026-10-27\n\n## [0.2.0] - 2026-01-01\n"
        self.assertEqual(check_catalog.check_changelog(text, "0.3.0"), [])

    def test_missing_section(self) -> None:
        errors = check_catalog.check_changelog("## [0.2.0] - 2026-01-01\n", "0.3.0")
        self.assertEqual(len(errors), 1)
        self.assertIn("no section", errors[0])

    def test_missing_date(self) -> None:
        errors = check_catalog.check_changelog("## [0.3.0]\n\n## [0.2.0] - 2026-01-01\n", "0.3.0")
        self.assertEqual(len(errors), 1)
        self.assertIn("no date", errors[0])

    def test_version_lower_than_changelog(self) -> None:
        text = "## [0.10.0] - 2026-03-01\n\n## [0.9.0] - 2026-02-01\n"
        errors = check_catalog.check_changelog(text, "0.9.0")
        self.assertEqual(len(errors), 1)
        self.assertIn("lower than changelog version 0.10.0", errors[0])

    def test_order(self) -> None:
        text = "## [0.2.0] - 2026-01-01\n\n## [0.3.0] - 2026-02-01\n"
        errors = check_catalog.check_changelog(text, "0.3.0")
        self.assertTrue(any("descending" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
