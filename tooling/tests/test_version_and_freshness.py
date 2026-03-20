import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SET_VERSION_SCRIPT = ROOT / "tooling" / "scripts" / "release" / "set_version.py"
SKILL_FRESHNESS_SCRIPT = ROOT / "tooling" / "scripts" / "quality" / "skill_freshness.py"


def write(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")


class SetVersionTests(unittest.TestCase):
    def test_updates_all_manifest_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(
                root / "claude-code.json",
                """
                {"name":"apple-text","version":"1.0.0"}
                """,
            )
            write(
                root / ".claude-plugin" / "plugin.json",
                """
                {"name":"apple-text","version":"1.0.0"}
                """,
            )
            write(
                root / ".claude-plugin" / "marketplace.json",
                """
                {
                  "metadata": {"version": "1.0.0"},
                  "plugins": [{"name": "apple-text", "version": "1.0.0"}]
                }
                """,
            )
            write(
                root / "mcp-server" / "package.json",
                """
                {"name":"apple-text-mcp","version":"1.0.0"}
                """,
            )

            result = subprocess.run(
                [sys.executable, str(SET_VERSION_SCRIPT), "2.3.4", "--root", str(root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertEqual(json.loads((root / "claude-code.json").read_text())["version"], "2.3.4")
            self.assertEqual(json.loads((root / ".claude-plugin" / "plugin.json").read_text())["version"], "2.3.4")
            marketplace = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
            self.assertEqual(marketplace["metadata"]["version"], "2.3.4")
            self.assertEqual(marketplace["plugins"][0]["version"], "2.3.4")
            self.assertEqual(json.loads((root / "mcp-server" / "package.json").read_text())["version"], "2.3.4")


class SkillFreshnessTests(unittest.TestCase):
    def test_uses_filesystem_mtime_when_git_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_file = root / "skills" / "apple-text" / "SKILL.md"
            write(
                skill_file,
                """
                ---
                name: apple-text
                description: Fixture
                license: MIT
                ---
                """,
            )
            stale_timestamp = 946684800  # 2000-01-01 UTC
            os.utime(skill_file, (stale_timestamp, stale_timestamp))

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_FRESHNESS_SCRIPT),
                    "--root",
                    str(root),
                    "--months",
                    "6",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("STALE", result.stdout)
            self.assertIn("apple-text", result.stdout)
            self.assertIn("mtime", result.stdout)


if __name__ == "__main__":
    unittest.main()
