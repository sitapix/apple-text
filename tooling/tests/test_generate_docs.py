import tempfile
import unittest
from pathlib import Path

from scripts.docs import generate_docs


class GenerateDocsTests(unittest.TestCase):
    def test_parse_front_matter_supports_folded_scalars(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill = Path(temp_dir) / "SKILL.md"
            skill.write_text(
                """---
name: example-skill
description: >
  Use when the user needs exact API details
  or migration guidance for a text stack.
license: MIT
---

# Example
""",
                encoding="utf-8",
            )

            metadata = generate_docs.parse_front_matter(skill)
            self.assertEqual(
                metadata["description"],
                "Use when the user needs exact API details\nor migration guidance for a text stack.",
            )

    def test_parse_front_matter_unquotes_scalar_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill = Path(temp_dir) / "SKILL.md"
            skill.write_text(
                """---
name: example-skill
description: "Use when the user needs exact API details: migration and validation."
license: MIT
---

# Example
""",
                encoding="utf-8",
            )

            metadata = generate_docs.parse_front_matter(skill)
            self.assertEqual(
                metadata["description"],
                "Use when the user needs exact API details: migration and validation.",
            )

    def test_render_agents_page_uses_labels_for_non_toc_sections(self) -> None:
        generate_docs._BASE = "/apple-text"
        agents_page = generate_docs.render_agents_page(
            Path("/tmp"),
            [
                {
                    "name": "textkit-auditor",
                    "description": "Focused TextKit review agent.",
                }
            ],
            [
                {
                    "name": "apple-text-audit",
                    "kind": "workflow",
                    "entrypoint_priority": 1,
                }
            ],
        )

        self.assertIn('<p class="docs-section-label">Audit focus</p>', agents_page)
        self.assertIn('<p class="docs-section-label">Default entry point</p>', agents_page)
        self.assertNotIn("## It checks for", agents_page)
        self.assertNotIn("## Start with the skill unless the user asked for the agent", agents_page)

    def test_render_mcp_server_includes_tool_install_sections(self) -> None:
        generate_docs._BASE = "/apple-text"
        page = generate_docs.render_mcp_server(
            {"owner": {"name": "sitapix"}},
            {"name": "apple-text"},
            [{"name": "apple-text"} for _ in range(35)],
            [{"name": "apple-text:ask"}],
            [{"name": "textkit-auditor"}],
        )

        self.assertIn("## Choose The Right Surface", page)
        self.assertIn("| Surface | Best For | Front Door |", page)
        self.assertIn("apple_text_route", page)
        self.assertIn("## Installation by Tool", page)
        self.assertIn("### VS Code + GitHub Copilot", page)
        self.assertIn("### OpenCode", page)
        self.assertIn("npm run mcp:smoke", page)
        self.assertIn('npx -y @sitapix/apple-text-mcp', page)
        self.assertIn("xcrun mcpbridge", page)

    def test_render_xcode_integration_includes_claude_and_codex_setup(self) -> None:
        generate_docs._BASE = "/apple-text"
        page = generate_docs.render_xcode_integration(
            {"name": "apple-text"},
            [{"name": "apple-text"} for _ in range(35)],
            [{"name": "apple-text:ask"}],
            [{"name": "textkit-auditor"}],
        )

        self.assertIn("## Claude Agent Setup", page)
        self.assertIn("## Codex Setup", page)
        self.assertIn("which node", page)
        self.assertIn("/context", page)
        self.assertIn("codex mcp add xcode -- xcrun mcpbridge", page)

    def test_render_skill_page_includes_documentation_scope_and_related(self) -> None:
        generate_docs._BASE = "/apple-text"
        page = generate_docs.render_skill_page(
            {
                "name": "apple-text-views",
                "category": "platform-selection",
                "kind": "decision",
                "description": "Use when choosing the right text view.",
                "full_description": "Use when choosing the right text view.",
                "body": "# Apple Text Views\n\nCore body.\n\n## Related Skills\n\n- old\n",
                "source": "---\nname: apple-text-views\n---\n",
                "related_skills": ["apple-text", "apple-text-representable"],
                "sidecars": [],
            },
            [
                {
                    "name": "apple-text",
                    "description": "Router.",
                },
                {
                    "name": "apple-text-representable",
                    "description": "Wrapper behavior.",
                },
            ],
            "sitapix",
            "apple-text",
        )

        self.assertIn("## Documentation Scope", page)
        self.assertIn("This page documents the `apple-text-views` decision skill.", page)
        self.assertIn("**Family:** View And Stack Decisions", page)
        self.assertIn("## Related", page)
        self.assertNotIn("## Related Skills", page)

    def test_render_skills_overview_groups_by_family(self) -> None:
        generate_docs._BASE = "/apple-text"
        page = generate_docs.render_skills_overview(
            {"name": "apple-text"},
            [
                {
                    "name": "apple-text",
                    "category": "entrypoints",
                    "kind": "router",
                    "entrypoint_priority": 1,
                    "description": "Use when routing a broad Apple text request.",
                },
                {
                    "name": "apple-text-views",
                    "category": "platform-selection",
                    "kind": "decision",
                    "entrypoint_priority": 2,
                    "description": "Use when choosing the right text view.",
                },
            ],
            [{"name": "apple-text:ask"}],
        )

        self.assertIn("## Browse By Skill Family", page)
        self.assertIn("## Front Door Skills", page)
        self.assertIn("## View And Stack Decisions", page)
        self.assertIn("| Skill | Role | When to Use |", page)
        self.assertIn("Problem Routing", page)


if __name__ == "__main__":
    unittest.main()
