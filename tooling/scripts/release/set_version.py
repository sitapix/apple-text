#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update plugin manifest versions in one place."
    )
    parser.add_argument("version", help="Version number in X.Y.Z format")
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="Plugin root to update (default: repository root).",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if not VERSION_RE.match(args.version):
        raise SystemExit("ERROR: version must use X.Y.Z format")

    root = Path(args.root).resolve()
    targets = [
        root / "claude-code.json",
        root / ".claude-plugin" / "plugin.json",
        root / ".claude-plugin" / "marketplace.json",
    ]
    mcp_package = root / "mcp-server" / "package.json"
    if mcp_package.exists():
        targets.append(mcp_package)

    claude_code = load_json(targets[0])
    plugin = load_json(targets[1])
    marketplace = load_json(targets[2])

    claude_code["version"] = args.version
    plugin["version"] = args.version
    marketplace.setdefault("metadata", {})["version"] = args.version

    plugins = marketplace.get("plugins", [])
    if len(plugins) != 1:
        raise SystemExit("ERROR: marketplace manifest must contain exactly one plugin entry")
    plugins[0]["version"] = args.version

    mcp = load_json(mcp_package) if mcp_package.exists() else None
    if mcp is not None:
        mcp["version"] = args.version

    write_json(targets[0], claude_code)
    write_json(targets[1], plugin)
    write_json(targets[2], marketplace)
    if mcp is not None:
        write_json(mcp_package, mcp)

    for path in targets:
        print(f"Updated {path.relative_to(root).as_posix()} -> {args.version}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
