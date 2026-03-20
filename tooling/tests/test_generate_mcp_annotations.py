import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tooling" / "scripts" / "mcp" / "generate_mcp_annotations.py"
OUTPUT = ROOT / "mcp-server" / "skill-annotations.json"


class GenerateMcpAnnotationsTests(unittest.TestCase):
    def test_check_passes_for_repo_annotations(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_can_generate_annotations_to_temp_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "skill-annotations.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            annotations = json.loads(output.read_text(encoding="utf-8"))
            self.assertIn("apple-text", annotations)
            self.assertIn("category", annotations["apple-text"])
            self.assertIn("tags", annotations["apple-text"])
            self.assertIn("aliases", annotations["apple-text"])
            self.assertIn("related", annotations["apple-text"])

    def test_default_annotations_file_exists(self) -> None:
        self.assertTrue(OUTPUT.is_file())


if __name__ == "__main__":
    unittest.main()
