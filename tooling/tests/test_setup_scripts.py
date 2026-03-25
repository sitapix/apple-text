import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class SetupScriptsTests(unittest.TestCase):
    def test_shell_scripts_exist(self) -> None:
        self.assertTrue((ROOT / "scripts" / "regenerate.sh").is_file())
        self.assertTrue((ROOT / "scripts" / "quality-check.sh").is_file())
        self.assertTrue((ROOT / "scripts" / "validate-skills.sh").is_file())
        self.assertTrue((ROOT / "scripts" / "build-agents.mjs").is_file())

    def test_root_package_exposes_core_scripts(self) -> None:
        package_json = (ROOT / "package.json").read_text(encoding="utf-8")
        self.assertIn('"setup":', package_json)
        self.assertIn('"setup:all":', package_json)
        self.assertIn('"build":', package_json)
        self.assertIn('"check":', package_json)
        self.assertIn('"test":', package_json)
        self.assertIn('"release":', package_json)


if __name__ == "__main__":
    unittest.main()
