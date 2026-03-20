import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class CiWorkflowTests(unittest.TestCase):
    def test_validate_workflow_runs_full_check(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        self.assertIn("run: npm run check", workflow)
        self.assertNotIn("run: npm run preflight", workflow)

    def test_deploy_docs_workflow_uploads_docs_dist(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "deploy-docs.yml").read_text(encoding="utf-8")
        self.assertIn("path: docs/dist", workflow)
        self.assertNotIn("path: dist", workflow)

    def test_pre_push_hook_runs_full_check(self) -> None:
        hook = (ROOT / ".githooks" / "pre-push").read_text(encoding="utf-8")
        self.assertIn("npm run check", hook)
        self.assertNotIn("npm run preflight", hook)


if __name__ == "__main__":
    unittest.main()
