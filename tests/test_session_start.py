import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "hooks" / "session-start.sh"


def run(cwd: Path) -> str:
    return subprocess.run(["bash", str(SCRIPT)], cwd=cwd, capture_output=True, text=True, check=True).stdout


class SessionStartTest(unittest.TestCase):
    def test_lists_every_skill_directory(self) -> None:
        out = run(ROOT)
        for skill in (ROOT / "skills").glob("*/SKILL.md"):
            self.assertIn(skill.parent.name, out)

    def test_mentions_raw_commands_rule(self) -> None:
        self.assertIn("do not run raw gh pr create", run(ROOT))

    def test_silent_outside_a_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run(Path(tmp)), "")


if __name__ == "__main__":
    unittest.main()
