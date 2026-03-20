import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class DevcontainerTests(unittest.TestCase):
    def test_devcontainer_exposes_repo_local_caches_and_core_languages(self) -> None:
        config = json.loads((ROOT / ".devcontainer" / "devcontainer.json").read_text(encoding="utf-8"))

        self.assertEqual(config["features"]["ghcr.io/devcontainers/features/node:1"]["version"], "22")
        self.assertEqual(config["features"]["ghcr.io/devcontainers/features/python:1"]["version"], "3.12")
        self.assertEqual(config["remoteEnv"]["UV_CACHE_DIR"], "${containerWorkspaceFolder}/.uv-cache")
        self.assertEqual(config["remoteEnv"]["npm_config_cache"], "${containerWorkspaceFolder}/.npm-cache")

    def test_devcontainer_vscode_customizations_cover_docs_and_workflows(self) -> None:
        config = json.loads((ROOT / ".devcontainer" / "devcontainer.json").read_text(encoding="utf-8"))
        vscode = config["customizations"]["vscode"]

        self.assertIn("astro-build.astro-vscode", vscode["extensions"])
        self.assertIn("redhat.vscode-yaml", vscode["extensions"])
        self.assertIn("GitHub.vscode-github-actions", vscode["extensions"])
        self.assertTrue(vscode["settings"]["python.testing.unittestEnabled"])

    def test_post_create_bootstraps_generated_outputs_and_cli_tools(self) -> None:
        script = (ROOT / ".devcontainer" / "post-create.sh").read_text(encoding="utf-8")

        self.assertIn("fd-find", script)
        self.assertIn("jq", script)
        self.assertIn("ripgrep", script)
        self.assertIn("npm run setup:all", script)
        self.assertIn("npm run mcp:build", script)
        self.assertIn("validate_plugin.py", script)


if __name__ == "__main__":
    unittest.main()
