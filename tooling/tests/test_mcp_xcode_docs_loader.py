import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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
    write(additional / "Foundation-AttributedString-Updates.md", "# AttributedString\n\nApple guide text.\n")
    write(diagnostics / "actor-isolated-call.md", "# Diagnostic\n\nCompiler guidance.\n")
    return xcode


def make_fake_repo(root: Path) -> Path:
    repo = root / "repo"
    write(
        repo / "skills" / "catalog.json",
        """
        {
          "skills": [
            {
              "name": "example-skill",
              "kind": "workflow"
            }
          ]
        }
        """,
    )
    write(
        repo / "skills" / "example-skill" / "SKILL.md",
        """
        ---
        name: example-skill
        description: Original description
        license: MIT
        ---

        # Example Skill

        ## Details

        Original body.
        """,
    )
    write(
        repo / "commands" / "ask.md",
        """
        ---
        name: example:ask
        description: Example command
        ---

        Hello $ARGUMENTS
        """,
    )
    write(
        repo / "agents" / "reviewer.md",
        """
        ---
        name: reviewer
        description: Example agent
        tools:
          - read
        ---

        Review content.
        """,
    )
    write(
        repo / "mcp-server" / "skill-annotations.json",
        """
        {
          "example-skill": {
            "category": "entrypoints",
            "tags": ["example"],
            "aliases": ["sample skill"],
            "related": []
          }
        }
        """,
    )
    return repo


class McpXcodeDocsLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        result = subprocess.run(
            ["npm", "--prefix", "mcp-server", "run", "build"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stdout + result.stderr)

    def test_dev_loader_adds_xcode_docs_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            xcode = make_fake_xcode(Path(temp_dir))
            script = """
                import { DevLoader } from "./mcp-server/dist/loader/dev-loader.js";
                import { Logger } from "./mcp-server/dist/config.js";

                const config = {
                  mode: "development",
                  devSourcePath: process.cwd(),
                  xcodePath: process.env.APPLE_TEXT_XCODE_PATH,
                  enableAppleDocs: true,
                  logLevel: "error",
                };

                const loader = new DevLoader(process.cwd(), new Logger(config), config);
                const skills = await loader.loadSkills();
                const appleDocs = [...skills.keys()].filter((name) =>
                  name.startsWith("apple-guide-") || name.startsWith("apple-diag-"),
                );
                console.log(JSON.stringify(appleDocs.sort()));
            """
            result = subprocess.run(
                ["node", "--input-type=module", "-e", script],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "APPLE_TEXT_XCODE_PATH": str(xcode),
                    "APPLE_TEXT_APPLE_DOCS": "true",
                },
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            loaded = json.loads(result.stdout)
            self.assertIn("apple-guide-foundation-attributedstring-updates", loaded)
            self.assertIn("apple-diag-actor-isolated-call", loaded)

    def test_dev_loader_invalidates_cached_skills_after_file_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = make_fake_repo(Path(temp_dir))
            script = """
                import { writeFile } from "fs/promises";
                import { join } from "path";
                import { DevLoader } from "./mcp-server/dist/loader/dev-loader.js";
                import { Logger } from "./mcp-server/dist/config.js";

                const repoPath = process.env.TEST_REPO;
                const config = {
                  mode: "development",
                  devSourcePath: repoPath,
                  enableAppleDocs: false,
                  logLevel: "error",
                };

                const loader = new DevLoader(repoPath, new Logger(config), config);
                const first = await loader.getSkill("example-skill");
                const changes = [];
                loader.onChange((kind) => changes.push(kind));
                loader.startWatching();
                await new Promise((resolve) => setTimeout(resolve, 400));

                await writeFile(
                  join(repoPath, "skills", "example-skill", "SKILL.md"),
                  `---
name: example-skill
description: Updated description
license: MIT
---

# Example Skill

## Details

Updated body.
`,
                  "utf-8",
                );

                const start = Date.now();
                while (!changes.includes("skills")) {
                  if (Date.now() - start > 3000) {
                    throw new Error("Timed out waiting for watcher invalidation");
                  }
                  await new Promise((resolve) => setTimeout(resolve, 50));
                }

                const second = await loader.getSkill("example-skill");
                loader.stopWatching();
                console.log(JSON.stringify({
                  first: first?.description,
                  second: second?.description,
                  changes,
                }));
            """
            result = subprocess.run(
                ["node", "--input-type=module", "-e", script],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env={**os.environ, "TEST_REPO": str(repo)},
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["first"], "Original description")
            self.assertEqual(payload["second"], "Updated description")
            self.assertIn("skills", payload["changes"])

    def test_prod_loader_adds_xcode_docs_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            xcode = make_fake_xcode(Path(temp_dir))
            script = """
                import { ProdLoader } from "./mcp-server/dist/loader/prod-loader.js";
                import { Logger } from "./mcp-server/dist/config.js";

                const config = {
                  mode: "production",
                  xcodePath: process.env.APPLE_TEXT_XCODE_PATH,
                  enableAppleDocs: true,
                  logLevel: "error",
                };

                const loader = new ProdLoader("./mcp-server/bundle.json", new Logger(config), config);
                const skills = await loader.loadSkills();
                const appleDocs = [...skills.keys()].filter((name) =>
                  name.startsWith("apple-guide-") || name.startsWith("apple-diag-"),
                );
                console.log(JSON.stringify(appleDocs.sort()));
            """
            result = subprocess.run(
                ["node", "--input-type=module", "-e", script],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "APPLE_TEXT_XCODE_PATH": str(xcode),
                    "APPLE_TEXT_APPLE_DOCS": "true",
                },
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            loaded = json.loads(result.stdout)
            self.assertIn("apple-guide-foundation-attributedstring-updates", loaded)
            self.assertIn("apple-diag-actor-isolated-call", loaded)


if __name__ == "__main__":
    unittest.main()
