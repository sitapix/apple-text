import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INSTALL_HOOKS_SCRIPT = ROOT / "scripts" / "install_git_hooks.py"
PRE_COMMIT_HOOK = ROOT / ".githooks" / "pre-commit"


class InstallGitHooksTests(unittest.TestCase):
    def test_install_sets_core_hooks_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            repo.mkdir()

            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)

            scripts_dir = repo / "scripts"
            hooks_dir = repo / ".githooks"
            scripts_dir.mkdir()
            hooks_dir.mkdir()

            shutil.copy2(INSTALL_HOOKS_SCRIPT, scripts_dir / "install_git_hooks.py")
            shutil.copy2(PRE_COMMIT_HOOK, hooks_dir / "pre-commit")

            result = subprocess.run(
                [sys.executable, str(scripts_dir / "install_git_hooks.py")],
                cwd=repo,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            hooks_path = subprocess.run(
                ["git", "config", "--get", "core.hooksPath"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            self.assertEqual(Path(hooks_path).resolve(), hooks_dir.resolve())
            self.assertTrue((hooks_dir / "pre-commit").stat().st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()
