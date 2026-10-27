import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_catalog  # noqa: E402


class CatalogTest(unittest.TestCase):
    def test_catalog_is_consistent(self) -> None:
        self.assertEqual(check_catalog.check(), [])


if __name__ == "__main__":
    unittest.main()
