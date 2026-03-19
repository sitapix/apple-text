#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = ROOT / ".githooks"


def main() -> int:
    if not HOOKS_DIR.exists():
        print(f"Missing hooks directory: {HOOKS_DIR}", file=sys.stderr)
        return 1

    try:
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        print("This directory is not inside a Git repository.", file=sys.stderr)
        return 1

    pre_commit = HOOKS_DIR / "pre-commit"
    pre_commit.chmod(0o755)

    subprocess.run(
        ["git", "config", "core.hooksPath", str(HOOKS_DIR)],
        cwd=ROOT,
        check=True,
    )

    print(f"Installed Git hooks from {HOOKS_DIR}")
    print("The pre-commit hook will regenerate docs, restage them, and run validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
