import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tooling" / "scripts" / "docs" / "xcode_docs.py"


def write(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")


def make_fake_xcode(root: Path) -> Path:
    xcode = root / "Xcode.app"
    additional = (
        xcode
        / "Contents/PlugIns/IDEIntelligenceChat.framework/Versions/A/Resources/AdditionalDocumentation"
    )
    diagnostics = (
        xcode
        / "Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/share/doc/swift/diagnostics"
    )
    write(additional / "Foundation-AttributedString-Updates.md", "# AttributedString\n")
    write(additional / "SwiftUI-Styled-Text-Editing.md", "# Styled Text\n")
    write(additional / "SwiftUI-New-Toolbar-Features.md", "# Toolbar\n")
    write(diagnostics / "actor-isolated-call.md", "# Diagnostic\n")
    return xcode


class XcodeDocsTests(unittest.TestCase):
    def test_detect_reports_fake_xcode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            xcode = make_fake_xcode(Path(temp_dir))
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "detect", "--xcode-path", str(xcode)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("AdditionalDocumentation", result.stdout)
            self.assertIn("Swift diagnostics", result.stdout)

    def test_sync_writes_curated_docs_and_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            xcode = make_fake_xcode(temp_root)
            repo_root = temp_root / "repo"
            (repo_root / "skills" / "apple-text-apple-docs").mkdir(parents=True, exist_ok=True)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "sync",
                    "--xcode-path",
                    str(xcode),
                    "--root",
                    str(repo_root),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            target_dir = repo_root / "skills" / "apple-text-apple-docs"
            self.assertTrue((target_dir / "xcode-attributedstring-updates.md").exists())
            self.assertTrue((target_dir / "xcode-styled-text-editing.md").exists())
            self.assertTrue((target_dir / "xcode-toolbar-features.md").exists())
            index = (target_dir / "xcode-docs-index.md").read_text(encoding="utf-8")
            self.assertIn("actor-isolated-call.md", index)
            self.assertIn("Xcode MCP resources", index)

    def test_read_diagnostic_prints_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            xcode = make_fake_xcode(Path(temp_dir))
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "read",
                    "--xcode-path",
                    str(xcode),
                    "--diagnostic",
                    "actor-isolated-call",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("# Diagnostic", result.stdout)

    def test_session_context_reports_detected_xcode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            xcode = make_fake_xcode(Path(temp_dir))
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "session-context",
                    "--xcode-path",
                    str(xcode),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("disabled via APPLE_TEXT_APPLE_DOCS=false", result.stdout)

    def test_session_context_reports_detected_xcode_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            xcode = make_fake_xcode(Path(temp_dir))
            env = dict(**os.environ, APPLE_TEXT_APPLE_DOCS="true")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "session-context",
                    "--xcode-path",
                    str(xcode),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("Xcode detected with 3 guides and 1 Swift diagnostics", result.stdout)
            self.assertIn("apple-text-apple-docs", result.stdout)

    def test_session_context_honors_disable_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            xcode = make_fake_xcode(Path(temp_dir))
            env = dict(**os.environ, APPLE_TEXT_APPLE_DOCS="false")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "session-context",
                    "--xcode-path",
                    str(xcode),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("disabled via APPLE_TEXT_APPLE_DOCS=false", result.stdout)


if __name__ == "__main__":
    unittest.main()
