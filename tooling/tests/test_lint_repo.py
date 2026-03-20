import tempfile
import unittest
from pathlib import Path

from scripts.quality import lint_repo


class LintRepoTests(unittest.TestCase):
    def test_invalid_json_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "broken.json"
            target.write_text('{"a": }\n', encoding="utf-8")

            issues = lint_repo.lint_repo(root)

        self.assertTrue(any("invalid JSON" in issue for issue in issues))

    def test_trailing_whitespace_is_ignored_for_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "README.md"
            target.write_text("line with two spaces  \n", encoding="utf-8")

            issues = lint_repo.lint_repo(root)

        self.assertEqual(issues, [])

    def test_trailing_whitespace_is_reported_for_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "tool.py"
            target.write_text("print('hi')  \n", encoding="utf-8")

            issues = lint_repo.lint_repo(root)

        self.assertTrue(any("trailing whitespace" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
