import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tooling" / "scripts" / "mcp" / "generate_mcp_bundle.py"
DEFAULT_BUNDLE = ROOT / "mcp-server" / "bundle.json"
ANNOTATIONS = ROOT / "mcp-server" / "skill-annotations.json"
OVERRIDES = ROOT / "mcp-server" / "skill-annotations.overrides.json"


class GenerateMcpBundleTests(unittest.TestCase):
    def test_check_passes_for_repo_bundle(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_can_generate_bundle_to_temp_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "bundle.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            bundle = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(bundle["version"], json.loads((ROOT / "mcp-server" / "package.json").read_text())["version"])
            self.assertIn("skills", bundle)
            self.assertIn("apple-text", bundle["skills"])
            self.assertIn("catalog", bundle)
            self.assertIn("searchIndex", bundle)
            self.assertEqual(bundle["searchIndex"]["version"], "apple-text-search-v1")
            self.assertEqual(bundle["searchIndex"]["docCount"], len(bundle["skills"]))
            self.assertIn("category", bundle["skills"]["apple-text"])
            self.assertIn("tags", bundle["skills"]["apple-text"])

    def test_default_bundle_exists(self) -> None:
        self.assertTrue(DEFAULT_BUNDLE.is_file())

    def test_annotations_cover_current_skills(self) -> None:
        annotations = json.loads(ANNOTATIONS.read_text(encoding="utf-8"))
        catalog = json.loads((ROOT / "skills" / "catalog.json").read_text(encoding="utf-8"))
        skill_names = {entry["name"] for entry in catalog["skills"]}
        self.assertEqual(set(annotations.keys()), skill_names)

    def test_annotations_overrides_only_reference_known_skills(self) -> None:
        overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
        catalog = json.loads((ROOT / "skills" / "catalog.json").read_text(encoding="utf-8"))
        skill_names = {entry["name"] for entry in catalog["skills"]}
        self.assertTrue(set(overrides.keys()).issubset(skill_names))


if __name__ == "__main__":
    unittest.main()
