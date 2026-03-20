import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class SetupScriptsTests(unittest.TestCase):
    def test_shell_wrappers_exist(self) -> None:
        self.assertTrue((ROOT / "tooling" / "scripts" / "workflows" / "setup_all.sh").is_file())
        self.assertTrue((ROOT / "tooling" / "scripts" / "workflows" / "build_all.sh").is_file())

    def test_root_package_exposes_setup_and_build_wrappers(self) -> None:
        package_json = (ROOT / "package.json").read_text(encoding="utf-8")
        self.assertIn('"setup:all": "bash tooling/scripts/workflows/setup_all.sh"', package_json)
        self.assertIn('"build:all": "bash tooling/scripts/workflows/build_all.sh"', package_json)
        self.assertIn('"lint": "npm run lint:repo && npm run descriptions:lint"', package_json)
        self.assertIn('"lint:repo": "python3 tooling/scripts/quality/lint_repo.py"', package_json)


if __name__ == "__main__":
    unittest.main()
