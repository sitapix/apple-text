import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INSTALL_SCRIPT = ROOT / "scripts" / "install_skill.py"


class InstallSkillTests(unittest.TestCase):
    def test_text_audit_installs_dependent_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            claude_home = Path(temp_dir) / ".claude"
            result = subprocess.run(
                [sys.executable, str(INSTALL_SCRIPT), "text-audit", "--claude-home", str(claude_home)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue((claude_home / "skills" / "text-audit" / "SKILL.md").exists())
            self.assertTrue((claude_home / "agents" / "textkit-auditor.md").exists())


if __name__ == "__main__":
    unittest.main()
