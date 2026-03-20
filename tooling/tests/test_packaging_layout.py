import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class PackagingLayoutTests(unittest.TestCase):
    def test_docs_app_is_consolidated_under_docs_directory(self) -> None:
        self.assertTrue((ROOT / "docs" / "astro.config.mjs").is_file())
        self.assertTrue((ROOT / "docs" / "src" / "content" / "docs").is_dir())
        self.assertTrue((ROOT / "docs" / "public").is_dir())
        self.assertFalse((ROOT / "astro.config.mjs").exists())
        self.assertFalse((ROOT / "src").exists())
        self.assertFalse((ROOT / "public").exists())

    def test_catalog_categories_are_known_and_present(self) -> None:
        catalog = load_json(ROOT / "skills" / "catalog.json")
        category_specs = load_json(ROOT / "tooling" / "config" / "skill-categories.json")
        known_categories = {spec["key"] for spec in category_specs}

        self.assertTrue(known_categories)
        for entry in catalog["skills"]:
            self.assertIn("category", entry, msg=f"Missing category for {entry['name']}")
            self.assertIn(entry["category"], known_categories, msg=f"Unknown category for {entry['name']}")

    def test_agents_symlinks_point_to_source_directories(self) -> None:
        skills_link = ROOT / ".agents" / "skills"
        agents_link = ROOT / ".agents" / "agents"

        self.assertTrue(skills_link.is_symlink(), msg=f"{skills_link} should be a symlink")
        self.assertTrue(agents_link.is_symlink(), msg=f"{agents_link} should be a symlink")
        self.assertEqual(skills_link.resolve(), (ROOT / "skills").resolve())
        self.assertEqual(agents_link.resolve(), (ROOT / "agents").resolve())

    def test_plugin_manifest_paths_exist(self) -> None:
        plugin = load_json(ROOT / ".claude-plugin" / "plugin.json")

        self.assertTrue((ROOT / plugin["commands"]).is_dir())
        self.assertTrue((ROOT / plugin["skills"]).is_dir())
        for agent_path in plugin["agents"]:
            self.assertTrue((ROOT / agent_path).is_file(), msg=f"Missing agent manifest target: {agent_path}")

    def test_marketplace_manifest_matches_plugin_surface(self) -> None:
        plugin = load_json(ROOT / ".claude-plugin" / "plugin.json")
        marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")
        self.assertEqual(len(marketplace["plugins"]), 1)

        packaged = marketplace["plugins"][0]
        self.assertEqual(packaged["name"], plugin["name"])
        self.assertEqual(packaged["version"], plugin["version"])
        self.assertEqual(packaged["commands"], plugin["commands"])
        self.assertEqual(packaged["skills"], plugin["skills"])
        self.assertEqual(packaged["agents"], plugin["agents"])

    def test_versions_are_aligned_across_packaging_manifests(self) -> None:
        claude_code = load_json(ROOT / "claude-code.json")
        plugin = load_json(ROOT / ".claude-plugin" / "plugin.json")
        marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")
        mcp_package = load_json(ROOT / "mcp-server" / "package.json")

        self.assertEqual(claude_code["version"], plugin["version"])
        self.assertEqual(plugin["version"], marketplace["metadata"]["version"])
        self.assertEqual(plugin["version"], marketplace["plugins"][0]["version"])
        self.assertEqual(plugin["version"], mcp_package["version"])

    def test_docs_components_do_not_import_theme_private_node_modules_paths(self) -> None:
        header = (ROOT / "docs" / "src" / "components" / "Header.astro").read_text(encoding="utf-8")
        self.assertNotIn("../../../node_modules/", header)


if __name__ == "__main__":
    unittest.main()
