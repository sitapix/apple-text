import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSTALL_SCRIPT = ROOT / "tooling" / "scripts" / "dev" / "install_skill.py"


class InstallSkillTests(unittest.TestCase):
    def test_text_audit_installs_dependent_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            agents_root = Path(temp_dir) / ".agents"
            result = subprocess.run(
                [sys.executable, str(INSTALL_SCRIPT), "apple-text-audit", "--agents-root", str(agents_root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue((agents_root / "skills" / "apple-text-audit" / "SKILL.md").exists())
            self.assertTrue((agents_root / "agents" / "textkit-auditor.md").exists())

    def test_claude_home_alias_installs_into_agent_root_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            agents_root = Path(temp_dir) / ".codex"
            result = subprocess.run(
                [sys.executable, str(INSTALL_SCRIPT), "apple-text-audit", "--claude-home", str(agents_root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue((agents_root / "skills" / "apple-text-audit" / "SKILL.md").exists())
            self.assertTrue((agents_root / "agents" / "textkit-auditor.md").exists())


if __name__ == "__main__":
    unittest.main()
