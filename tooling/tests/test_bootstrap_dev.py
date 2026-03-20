import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.dev import bootstrap_dev


class BootstrapDevTests(unittest.TestCase):
    def test_ensure_skills_ref_skips_when_present(self) -> None:
        with patch("scripts.dev.bootstrap_dev.shutil.which", return_value="/tmp/skills-ref"), patch(
            "scripts.dev.bootstrap_dev.run"
        ) as run_mock:
            bootstrap_dev.ensure_skills_ref()
        run_mock.assert_not_called()

    def test_ensure_skills_ref_installs_with_uv_when_missing(self) -> None:
        def which(name: str) -> str | None:
            return {
                "skills-ref": None,
                "uv": "/tmp/uv",
            }.get(name)

        with patch("scripts.dev.bootstrap_dev.shutil.which", side_effect=which), patch(
            "scripts.dev.bootstrap_dev.run"
        ) as run_mock:
            bootstrap_dev.ensure_skills_ref()

        run_mock.assert_called_once_with(
            ["/tmp/uv", "tool", "install", "--from", bootstrap_dev.SKILLS_REF_SOURCE, "skills-ref"],
            cwd=bootstrap_dev.ROOT,
        )

    def test_ensure_node_deps_skips_existing_node_modules(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "node_modules").mkdir()
            mcp_root = root / "mcp-server"
            (mcp_root / "node_modules").mkdir(parents=True)

            with patch.object(bootstrap_dev, "ROOT", root), patch.object(
                bootstrap_dev, "MCP_ROOT", mcp_root
            ), patch("scripts.dev.bootstrap_dev.run") as run_mock:
                bootstrap_dev.ensure_node_deps(force=False)

        run_mock.assert_not_called()

    def test_ensure_node_deps_prefers_npm_ci_with_lockfile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package-lock.json").write_text("{}", encoding="utf-8")
            mcp_root = root / "mcp-server"
            mcp_root.mkdir()

            with patch.object(bootstrap_dev, "ROOT", root), patch.object(
                bootstrap_dev, "MCP_ROOT", mcp_root
            ), patch(
                "scripts.dev.bootstrap_dev.shutil.which", return_value="/tmp/npm"
            ), patch("scripts.dev.bootstrap_dev.run") as run_mock:
                bootstrap_dev.ensure_node_deps(force=False)

        self.assertEqual(
            run_mock.call_args_list,
            [
                unittest.mock.call(["/tmp/npm", "ci"], cwd=root),
                unittest.mock.call(["/tmp/npm", "install"], cwd=mcp_root),
            ],
        )


if __name__ == "__main__":
    unittest.main()
