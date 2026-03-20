import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SCRIPT = ROOT / "tooling" / "scripts" / "quality" / "validate_plugin.py"


def write(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")


def make_fixture_repo(root: Path) -> None:
    write(
        root / "skills" / "apple-text" / "SKILL.md",
        """
        ---
        name: apple-text
        description: Fixture skill
        ---

        # Fixture
        """,
    )


def make_fake_skills_ref(root: Path) -> tuple[Path, Path]:
    bin_dir = root / "bin"
    log_path = root / "skills-ref.log"
    script = bin_dir / "skills-ref"
    write(
        script,
        f"""
        #!/usr/bin/env python3
        import os
        import sys
        from pathlib import Path

        log_path = Path(os.environ.get("SKILLS_REF_LOG_PATH", "skills-ref.log"))
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(" ".join(sys.argv[1:]) + "\\n")

        if sys.argv[1:2] != ["validate"] or len(sys.argv) != 3:
            print(f"unexpected args: {{sys.argv[1:]}}", file=sys.stderr)
            raise SystemExit(2)

        fail_match = os.environ.get("SKILLS_REF_FAIL_MATCH")
        if fail_match and fail_match in sys.argv[2]:
            print(os.environ.get("SKILLS_REF_FAIL_MESSAGE", "fake skills-ref failure"), file=sys.stderr)
            raise SystemExit(1)

        raise SystemExit(int(os.environ.get("SKILLS_REF_EXIT_CODE", "0")))
        """,
    )
    script.chmod(0o755)
    return bin_dir, log_path


def run_validator(root: Path, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--root", str(root)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


class ValidatePluginTests(unittest.TestCase):
    def make_repo(self) -> Path:
        temp_dir = tempfile.mkdtemp()
        root = Path(temp_dir)
        make_fixture_repo(root)
        self.addCleanup(lambda: shutil.rmtree(root, ignore_errors=True))
        return root

    def make_env_with_skills_ref(self, root: Path, **extra: str) -> tuple[dict[str, str], Path]:
        bin_dir, log_path = make_fake_skills_ref(root)
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["SKILLS_REF_LOG_PATH"] = str(log_path)
        env.update(extra)
        return env, log_path

    def test_requires_skills_ref_on_path(self) -> None:
        root = self.make_repo()
        env = os.environ.copy()
        env["PATH"] = ""
        result = run_validator(root, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("skills-ref is required", result.stderr)

    def test_current_repo_validates_when_skills_ref_succeeds(self) -> None:
        env, _ = self.make_env_with_skills_ref(ROOT)
        result = run_validator(ROOT, env=env)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Validated", result.stdout)
        self.assertIn("skills-ref", result.stdout)

    def test_runs_skills_ref_for_each_skill_directory(self) -> None:
        root = self.make_repo()
        write(
            root / "skills" / "apple-text-bidi" / "SKILL.md",
            """
            ---
            name: apple-text-bidi
            description: Fixture bidi skill
            ---

            # Fixture
            """,
        )
        env, log_path = self.make_env_with_skills_ref(root)
        result = run_validator(root, env=env)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

        lines = log_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(any("skills/apple-text" in line for line in lines))
        self.assertTrue(any("skills/apple-text-bidi" in line for line in lines))

    def test_propagates_skills_ref_failures(self) -> None:
        root = self.make_repo()
        env, _ = self.make_env_with_skills_ref(
            root,
            SKILLS_REF_FAIL_MATCH="skills/apple-text",
            SKILLS_REF_FAIL_MESSAGE="name field is invalid",
        )
        result = run_validator(root, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("skills-ref validation failed", result.stderr)
        self.assertIn("name field is invalid", result.stderr)


if __name__ == "__main__":
    unittest.main()
