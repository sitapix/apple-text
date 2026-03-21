import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MCP_ROOT = ROOT / "mcp-server"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class McpServerLayoutTests(unittest.TestCase):
    def test_package_exists_with_expected_entry_points(self) -> None:
        package = load_json(MCP_ROOT / "package.json")

        self.assertEqual(package["name"], "@sitapix/apple-text-mcp")
        self.assertEqual(package["bin"]["apple-text-mcp"], "dist/index.js")
        self.assertIn("build:bundle", package["scripts"])

    def test_core_source_files_exist(self) -> None:
        expected_files = [
            MCP_ROOT / "README.md",
            MCP_ROOT / "LICENSE",
            MCP_ROOT / "skill-annotations.json",
            MCP_ROOT / "skill-annotations.overrides.json",
            MCP_ROOT / "scripts" / "smoke.mjs",
            MCP_ROOT / "scripts" / "validate-pack.mjs",
            MCP_ROOT / "tsconfig.json",
            MCP_ROOT / "src" / "index.ts",
            MCP_ROOT / "src" / "loader" / "dev-loader.ts",
            MCP_ROOT / "src" / "loader" / "prod-loader.ts",
            MCP_ROOT / "src" / "loader" / "xcode-docs.ts",
            MCP_ROOT / "src" / "resources" / "handler.ts",
            MCP_ROOT / "src" / "prompts" / "handler.ts",
            MCP_ROOT / "src" / "tools" / "handler.ts",
            MCP_ROOT / "src" / "scripts" / "bundle.ts",
        ]

        for path in expected_files:
            self.assertTrue(path.is_file(), msg=f"Missing MCP server file: {path}")

    def test_root_package_exposes_mcp_scripts(self) -> None:
        package = load_json(ROOT / "package.json")

        self.assertEqual(package["scripts"]["mcp:build"], "npm --prefix mcp-server run build")
        self.assertEqual(package["scripts"]["mcp:bundle"], "npm --prefix mcp-server run build:bundle")
        self.assertEqual(package["scripts"]["mcp:pack:check"], "npm --prefix mcp-server run pack:check")
        self.assertEqual(package["scripts"]["mcp:smoke"], "npm --prefix mcp-server run smoke")
        self.assertEqual(package["scripts"]["mcp:smoke:dev"], "npm --prefix mcp-server run smoke:dev")
        self.assertEqual(package["scripts"]["mcp:start"], "npm --prefix mcp-server run start:dev")


if __name__ == "__main__":
    unittest.main()
