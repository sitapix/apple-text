import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VALIDATE_SCRIPT = ROOT / "scripts" / "validate_plugin.py"
GENERATE_DOCS_SCRIPT = ROOT / "scripts" / "generate_docs.py"


def write(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")


def make_fixture_repo(root: Path) -> None:
    (root / "agents").mkdir(parents=True, exist_ok=True)
    write(
        root / "README.md",
        """
        # Fixture Plugin

        - 1 focused text skills under `skills/`
        - `/skill apple-text`
        """,
    )
    write(
        root / "AGENTS.md",
        """
        # Fixture
        """,
    )
    write(
        root / ".npmignore",
        """
        node_modules/
        .astro/
        dist/
        """,
    )
    write(
        root / "config" / "skill-kinds.json",
        """
        [
          {
            "key": "router",
            "sidebar_label": "Router",
            "title": "Router Skills",
            "description": "Broad intake and redirection when the problem is clearly Apple text but still mixed.",
            "badge_variant": "note"
          },
          {
            "key": "workflow",
            "sidebar_label": "Workflow",
            "title": "Workflow Skills",
            "description": "Guided scans or integration flows where the steps matter as much as the end state.",
            "badge_variant": "tip"
          },
          {
            "key": "diag",
            "sidebar_label": "Diagnostic",
            "title": "Diagnostic Skills",
            "description": "Symptom-first debugging for broken behavior, regressions, and failure analysis.",
            "badge_variant": "caution"
          },
          {
            "key": "decision",
            "sidebar_label": "Decision",
            "title": "Decision Skills",
            "description": "Tradeoff questions where the main task is choosing the right approach.",
            "badge_variant": "default"
          },
          {
            "key": "ref",
            "sidebar_label": "Reference",
            "title": "Reference Skills",
            "description": "Direct API and behavior reference for users who already know the stack.",
            "badge_variant": "note"
          }
        ]
        """,
    )
    write(
        root / "claude-code.json",
        """
        {
          "name": "fixture-plugin",
          "version": "1.0.0",
          "description": "Fixture plugin",
          "author": "Fixture",
          "license": "MIT",
          "skills": [
            {
              "name": "apple-text",
              "description": "Fixture skill"
            }
          ]
        }
        """,
    )
    write(
        root / ".claude-plugin" / "plugin.json",
        """
        {
          "name": "fixture-plugin",
          "version": "1.0.0",
          "description": "Fixture plugin",
          "author": { "name": "Fixture" },
          "license": "MIT",
          "commands": "./commands/",
          "agents": "./agents/",
          "hooks": "./hooks/hooks.json",
          "skills": "./skills/",
          "keywords": ["fixture"]
        }
        """,
    )
    write(
        root / ".claude-plugin" / "marketplace.json",
        """
        {
          "name": "fixture-marketplace",
          "owner": { "name": "Fixture" },
          "metadata": {
            "description": "Fixture plugin",
            "version": "1.0.0"
          },
          "plugins": [
            {
              "name": "fixture-plugin",
              "source": "./",
              "description": "Fixture plugin",
              "version": "1.0.0",
              "author": { "name": "Fixture" },
              "license": "MIT",
              "keywords": ["fixture"],
              "commands": "./commands/",
              "agents": "./agents/",
              "hooks": "./hooks/hooks.json",
              "skills": "./skills/"
            }
          ]
        }
        """,
    )
    write(
        root / "commands" / "ask.md",
        """
        ---
        description: Fixture command
        ---

        # Ask

        Route broad requests to `/skill apple-text`.
        """,
    )
    write(
        root / "hooks" / "hooks.json",
        """
        {
          "hooks": {}
        }
        """,
    )
    write(
        root / "src" / "content" / "docs" / "docs" / "index.md",
        """
        ---
        title: Fixture Plugin
        ---

        # Docs

        - `/skill apple-text`
        """,
    )
    write(
        root / "src" / "content" / "docs" / "docs" / "guide" / "entry-points.md",
        """
        ---
        title: Entry Points
        ---

        # Entry Points

        - `apple-text`
        """,
    )
    write(
        root / "src" / "content" / "docs" / "docs" / "skills" / "index.mdx",
        """
        ---
        title: Skills
        ---

        # Skills

        Fixture currently ships 1 skills.

        - `apple-text`
        """,
    )
    write(
        root / "src" / "content" / "docs" / "docs" / "guide" / "overview.md",
        """
        ---
        title: Guide
        ---

        # Guide
        """,
    )
    write(
        root / "src" / "content" / "docs" / "docs" / "guide" / "problem-routing.md",
        """
        ---
        title: Problem Routing
        ---

        # Problem Routing
        """,
    )
    write(
        root / "src" / "content" / "docs" / "docs" / "guide" / "commands-and-agents.md",
        """
        ---
        title: Commands And Agents
        ---

        # Commands And Agents
        """,
    )
    write(
        root / "src" / "content" / "docs" / "docs" / "guide" / "install.md",
        """
        ---
        title: Install
        ---

        # Install
        """,
    )
    write(
        root / "src" / "content" / "docs" / "docs" / "guide" / "maintenance.md",
        """
        ---
        title: Maintenance
        ---

        # Maintenance
        """,
    )
    write(
        root / "skills" / "catalog.json",
        """
        {
          "skills": [
            {
              "name": "apple-text",
              "kind": "router",
              "entrypoint_priority": 1,
              "aliases": ["fixture"],
              "related_skills": []
            }
          ]
        }
        """,
    )
    write(
        root / "skills" / "apple-text" / "SKILL.md",
        """
        ---
        name: apple-text
        description: Fixture skill
        license: MIT
        ---

        # Fixture Skill

        Use this skill when the request needs broad routing.

        ## When to Use

        Use it for broad Apple text questions.

        ## Quick Decision

        Broad request -> stay here.

        ## Core Guidance

        Route broad requests before diving into implementation detail.

        ## Related Skills

        No related skills in this fixture.
        """,
    )
    result = subprocess.run(
        [sys.executable, str(GENERATE_DOCS_SCRIPT), "--root", str(root)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)


def run_validator(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--root", str(root)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


class ValidatePluginTests(unittest.TestCase):
    def make_repo(self) -> Path:
        temp_dir = tempfile.mkdtemp()
        root = Path(temp_dir)
        make_fixture_repo(root)
        self.addCleanup(lambda: shutil.rmtree(root, ignore_errors=True))
        return root

    def test_current_repo_validates(self) -> None:
        result = run_validator(ROOT)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

    def test_missing_front_matter_fails(self) -> None:
        root = self.make_repo()
        (root / "skills" / "apple-text" / "SKILL.md").write_text("# Broken\n", encoding="utf-8")
        result = run_validator(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("front matter", result.stderr)

    def test_catalog_drift_fails(self) -> None:
        root = self.make_repo()
        (root / "skills" / "catalog.json").write_text(
            textwrap.dedent(
                """
                {
                  "skills": []
                }
                """
            ).lstrip(),
            encoding="utf-8",
        )
        result = run_validator(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("non-empty 'skills' array", result.stderr)

    def test_bad_skill_reference_fails(self) -> None:
        root = self.make_repo()
        skill = root / "skills" / "apple-text" / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "\nUse `/skill missing-skill`.\n", encoding="utf-8")
        result = run_validator(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("/skill missing-skill", result.stderr)

    def test_missing_agent_target_fails(self) -> None:
        root = self.make_repo()
        skill = root / "skills" / "apple-text" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        text = text.replace("license: MIT\n", "license: MIT\nagent: missing-agent\n")
        skill.write_text(text, encoding="utf-8")
        result = run_validator(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing agent", result.stderr)

    def test_stale_generated_docs_fail(self) -> None:
        root = self.make_repo()
        readme = root / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace("1 focused text skills", "999 focused text skills"),
            encoding="utf-8",
        )
        result = run_validator(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Generated docs are stale", result.stderr)

    def test_markdown_link_with_code_label_fails(self) -> None:
        root = self.make_repo()
        skill = root / "skills" / "apple-text" / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8") + "\n[`missing.md`](missing.md)\n",
            encoding="utf-8",
        )
        result = run_validator(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing linked file", result.stderr)

    def test_unlinked_sidecar_fails(self) -> None:
        root = self.make_repo()
        write(root / "skills" / "apple-text" / "reference.md", "# Orphan\n")
        result = run_validator(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must link to sidecar file reference.md", result.stderr)

    def test_catalog_sidecars_field_fails(self) -> None:
        root = self.make_repo()
        catalog_path = root / "skills" / "catalog.json"
        catalog_path.write_text(
            textwrap.dedent(
                """
                {
                  "skills": [
                    {
                      "name": "apple-text",
                      "kind": "router",
                      "entrypoint_priority": 1,
                      "aliases": ["fixture"],
                      "related_skills": [],
                      "sidecars": ["reference.md"]
                    }
                  ]
                }
                """
            ).lstrip(),
            encoding="utf-8",
        )
        result = run_validator(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not define sidecars", result.stderr)

    def test_long_skill_without_summary_or_sidecar_fails(self) -> None:
        root = self.make_repo()
        skill_path = root / "skills" / "apple-text" / "SKILL.md"
        delayed_summary = "\n".join(f"Delay {index}" for index in range(1, 60))
        long_body = "\n".join(f"Line {index}" for index in range(1, 320))
        text = skill_path.read_text(encoding="utf-8")
        text = text.replace(
            "Use it for broad Apple text questions.\n\n## Quick Decision",
            f"Use it for broad Apple text questions.\n\n{delayed_summary}\n\n## Quick Decision",
        )
        text = text.replace(
            "Route broad requests before diving into implementation detail.",
            long_body,
        )
        skill_path.write_text(text, encoding="utf-8")
        result = run_validator(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("early summary section or linked sidecar", result.stderr)


if __name__ == "__main__":
    unittest.main()
