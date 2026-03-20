import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts.docs import validate_doc_links


def write(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")


class ValidateDocLinksTests(unittest.TestCase):
    def test_accepts_valid_site_and_relative_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(
                root / ".claude-plugin" / "plugin.json",
                """
                {"name": "apple-text"}
                """,
            )
            write(
                root / "README.md",
                """
                See the [guide](/apple-text/guide/) and [local](./mcp-server/README.md).
                """,
            )
            write(root / ".github" / "CONTRIBUTING.md", "No links.\n")
            write(root / "mcp-server" / "README.md", "No links.\n")
            write(root / "docs" / "src" / "content" / "docs" / "index.mdx", '<LinkCard href="/apple-text/guide/" />\n')
            write(root / "docs" / "src" / "content" / "docs" / "guide" / "index.mdx", "Guide home.\n")

            self.assertEqual(validate_doc_links.collect_errors(root), [])

    def test_reports_broken_mdx_href_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(
                root / ".claude-plugin" / "plugin.json",
                """
                {"name": "apple-text"}
                """,
            )
            write(root / "README.md", "Home.\n")
            write(root / ".github" / "CONTRIBUTING.md", "No links.\n")
            write(root / "mcp-server" / "README.md", "No links.\n")
            write(
                root / "docs" / "src" / "content" / "docs" / "index.mdx",
                """
                <LinkCard href="/apple-text/guide/missing/" />
                """,
            )
            write(root / "docs" / "src" / "content" / "docs" / "guide" / "index.mdx", "Guide home.\n")

            errors = validate_doc_links.collect_errors(root)
            self.assertEqual(len(errors), 1)
            self.assertIn("Broken site route", errors[0])

    def test_reports_broken_relative_markdown_link(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(
                root / ".claude-plugin" / "plugin.json",
                """
                {"name": "apple-text"}
                """,
            )
            write(root / "README.md", "Home.\n")
            write(root / ".github" / "CONTRIBUTING.md", "No links.\n")
            write(root / "mcp-server" / "README.md", "No links.\n")
            write(
                root / "docs" / "src" / "content" / "docs" / "guide" / "index.mdx",
                """
                Broken [link](./missing.md)
                """,
            )

            errors = validate_doc_links.collect_errors(root)
            self.assertEqual(len(errors), 1)
            self.assertIn("Broken link target", errors[0])


if __name__ == "__main__":
    unittest.main()
