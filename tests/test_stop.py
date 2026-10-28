import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "hooks"
sys.path.insert(0, str(HOOKS))
import stop  # noqa: E402


def git(cwd: str, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd, check=True,
                   capture_output=True)


class WarningsTest(unittest.TestCase):
    def test_main_branch_silent(self) -> None:
        self.assertEqual(stop.build_warnings("main", None, None, {}, ["/tmp/wt"]), [])
        self.assertEqual(stop.build_warnings("release/1.x", 3, None, {}, []), [])

    def test_clean_feature_branch_silent(self) -> None:
        self.assertEqual(stop.build_warnings("feat/x", 0, None, {}, ["/home/me/repo"]), [])
        self.assertEqual(stop.build_message([]), "")

    def test_unpushed(self) -> None:
        self.assertIn("2 unpushed", stop.build_warnings("feat/x", 2, None, {}, [])[0])
        self.assertIn("no upstream", stop.build_warnings("feat/x", None, None, {}, [])[0])

    def test_open_pr_unticked_issue(self) -> None:
        pr = {"number": 9, "state": "OPEN", "body": "Closes #4"}
        warns = stop.build_warnings("feat/x", 0, pr, {4: "- [x] a\n- [ ] b"}, [])
        self.assertEqual(len(warns), 1)
        self.assertIn("issue #4", warns[0])
        self.assertEqual(stop.build_warnings("feat/x", 0, {**pr, "state": "MERGED"}, {4: "- [ ] b"}, []), [])
        self.assertEqual(stop.build_warnings("feat/x", 0, {**pr, "body": "Part of #4"}, {4: "- [ ] b"}, []), [])

    def test_scratch_worktrees(self) -> None:
        warns = stop.build_warnings("feat/x", 0, None, {}, ["/tmp/a", "/home/me/r", "/x/scratchpad/wt"])
        self.assertEqual(len(warns), 1)
        self.assertIn("/tmp/a", warns[0])
        self.assertNotIn("/home/me/r", warns[0])

    def test_parse_worktrees(self) -> None:
        self.assertEqual(stop.parse_worktrees("worktree /a\nHEAD x\n\nworktree /b\nbranch y\n"), ["/a", "/b"])


class GitTest(unittest.TestCase):
    def test_gather_in_temp_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = os.path.join(tmp, "repo")
            os.mkdir(repo)
            git(repo, "init", "-q", "-b", "master")
            git(repo, "commit", "-q", "--allow-empty", "-m", "init")
            self.assertEqual(stop.gather(repo), [])
            git(repo, "checkout", "-q", "-b", "feat/x")
            warns = stop.gather(repo)
            self.assertTrue(any("no upstream" in w for w in warns), warns)

    def test_non_git_dir_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(stop.gather(tmp), [])


class MainTest(unittest.TestCase):
    def run_hook(self, payload: object, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(HOOKS / "stop.py")], input=json.dumps(payload),
                              capture_output=True, text=True, env={**os.environ, **env}, timeout=30)

    def test_stop_hook_active_exits_silently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = os.path.join(tmp, "repo")
            os.mkdir(repo)
            git(repo, "init", "-q", "-b", "feat/x")
            git(repo, "commit", "-q", "--allow-empty", "-m", "init")
            done = self.run_hook({"cwd": repo, "stop_hook_active": True})
            self.assertEqual((done.returncode, done.stdout), (0, ""))
            done = self.run_hook({"cwd": repo})
            self.assertEqual(done.returncode, 0)
            self.assertIn("systemMessage", json.loads(done.stdout))

    def test_guard_off_and_garbage(self) -> None:
        done = self.run_hook({"cwd": "/tmp"}, PR_STEWARD_GUARD="off")
        self.assertEqual((done.returncode, done.stdout), (0, ""))
        done = subprocess.run([sys.executable, str(HOOKS / "stop.py")], input="nope", capture_output=True,
                              text=True, timeout=30)
        self.assertEqual((done.returncode, done.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
