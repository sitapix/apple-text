import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class PublishMcpWorkflowTests(unittest.TestCase):
    def test_publish_workflow_exists(self) -> None:
        self.assertTrue((ROOT / ".github" / "workflows" / "publish-mcp.yml").is_file())

    def test_root_package_exposes_publish_scripts(self) -> None:
        package_json = (ROOT / "package.json").read_text(encoding="utf-8")
        self.assertIn('"mcp:pack:check": "npm --prefix mcp-server run pack:check"', package_json)
        self.assertIn('"mcp:pack:dry-run": "npm --prefix mcp-server run pack:dry-run"', package_json)
        self.assertIn('"mcp:publish:dry-run": "npm --prefix mcp-server run publish:dry-run"', package_json)

    def test_mcp_package_has_publish_config(self) -> None:
        package_json = (ROOT / "mcp-server" / "package.json").read_text(encoding="utf-8")
        self.assertIn('"bin"', package_json)
        self.assertIn('"apple-text-mcp": "dist/index.js"', package_json)
        self.assertIn('"pack:check"', package_json)
        self.assertIn('"pack:dry-run"', package_json)
        self.assertIn("npm pack --dry-run", package_json)
        self.assertIn('"publish:dry-run"', package_json)
        self.assertIn("npm publish --dry-run", package_json)
        self.assertIn('"smoke:dev"', package_json)
        self.assertIn('"publishConfig"', package_json)


if __name__ == "__main__":
    unittest.main()
