#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class ValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def resolve_skills_ref() -> str:
    executable = shutil.which("skills-ref")
    if executable:
        return executable

    fail("skills-ref is required but was not found on PATH")


def discover_skill_dirs(root: Path) -> list[Path]:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        fail(f"{skills_dir} does not exist")

    skill_dirs = sorted(path for path in skills_dir.iterdir() if path.is_dir())
    if not skill_dirs:
        fail(f"No skill directories found under {skills_dir}")

    return skill_dirs


def run_skills_ref_validate(executable: str, skill_dir: Path, root: Path) -> None:
    result = subprocess.run(
        [executable, "validate", str(skill_dir)],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return

    details = (result.stderr or result.stdout).strip()
    if not details:
        details = f"skills-ref validate exited with status {result.returncode}"
    fail(f"skills-ref validation failed for {skill_dir.relative_to(root)}:\n{details}")


def validate(root: Path) -> str:
    executable = resolve_skills_ref()
    skill_dirs = discover_skill_dirs(root)

    for skill_dir in skill_dirs:
        run_skills_ref_validate(executable, skill_dir, root)

    return f"Validated {len(skill_dirs)} skills with skills-ref."


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate this skill collection with skills-ref.")
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="Plugin root to validate (default: repository root)",
    )
    args = parser.parse_args()

    try:
        message = validate(Path(args.root).resolve())
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
