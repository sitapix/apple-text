#!/usr/bin/env python3

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOC_EXTENSIONS = {".md", ".mdx"}

MARKDOWN_LINK_RE = re.compile(r"!?[^\S\r\n]*\[[^\]]*\]\(([^)]+)\)")
HREF_RE = re.compile(r'''href\s*=\s*["']([^"']+)["']''')


@dataclass(frozen=True)
class LinkRef:
    source: Path
    line: int
    target: str


def plugin_base(root: Path) -> str:
    plugin_manifest = root / ".claude-plugin" / "plugin.json"
    import json

    data = json.loads(plugin_manifest.read_text(encoding="utf-8"))
    return f"/{data['name']}"


def docs_root(root: Path) -> Path:
    return root / "docs" / "src" / "content" / "docs"


def docs_files(root: Path) -> list[Path]:
    base = docs_root(root)
    return sorted(path for path in base.rglob("*") if path.suffix in DOC_EXTENSIONS)


def files_to_scan(root: Path) -> list[Path]:
    paths = [
        root / "README.md",
        root / ".github" / "CONTRIBUTING.md",
        root / "mcp-server" / "README.md",
        *docs_files(root),
    ]
    return [path for path in paths if path.is_file()]


def build_site_routes(root: Path) -> set[str]:
    base = plugin_base(root)
    site_root = docs_root(root)
    routes: set[str] = set()

    for path in docs_files(root):
        rel = path.relative_to(site_root)
        if rel.name.startswith("404."):
            continue

        if rel.stem == "index":
            parent = rel.parent.as_posix()
            route = f"{base}/{parent}/" if parent != "." else f"{base}/"
        else:
            route = f"{base}/{rel.with_suffix('').as_posix()}/"

        route = normalize_route(route)
        routes.add(route)

    return routes


def normalize_route(route: str) -> str:
    route = route.split("#", 1)[0].split("?", 1)[0].strip()
    if not route:
        return route
    if not route.startswith("/"):
        route = "/" + route
    if route != "/" and not route.endswith("/"):
        route += "/"
    return route


def extract_links(path: Path) -> list[LinkRef]:
    refs: list[LinkRef] = []
    in_fence = False
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        segments = re.split(r"(`[^`]*`)", line)
        for segment in segments:
            if segment.startswith("`") and segment.endswith("`"):
                continue
            for match in MARKDOWN_LINK_RE.finditer(segment):
                refs.append(LinkRef(path, line_number, match.group(1).strip()))
            for match in HREF_RE.finditer(segment):
                refs.append(LinkRef(path, line_number, match.group(1).strip()))
    return refs


def should_skip(target: str) -> bool:
    return (
        not target
        or target.startswith("#")
        or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target) is not None
        or target.startswith("mailto:")
        or target.startswith("data:")
    )


def resolve_relative_file(source: Path, target: str) -> Path:
    clean = target.split("#", 1)[0].split("?", 1)[0]
    return (source.parent / clean).resolve()


def validate_link(ref: LinkRef, *, base: str, routes: set[str], root: Path) -> str | None:
    target = ref.target
    if should_skip(target):
        return None

    if target.startswith("/"):
        route = normalize_route(target)
        if route.startswith(base + "/") or route == f"{base}/":
            if route not in routes:
                return f"Broken site route: {target}"
            return None

        repo_path = (root / target.lstrip("/")).resolve()
        if not repo_path.exists():
            return f"Missing absolute repo path: {target}"
        return None

    candidate = resolve_relative_file(ref.source, target)
    if candidate.exists():
        return None

    site_root = docs_root(root)
    if ref.source.is_relative_to(site_root):
        rel_source = ref.source.relative_to(site_root)
        source_route = (
            f"{base}/{rel_source.parent.as_posix()}/"
            if rel_source.stem == "index"
            else f"{base}/{rel_source.with_suffix('').as_posix()}/"
        )
        resolved_route = normalize_route(source_route + "../" + target)
        normalized = []
        for part in resolved_route.split("/"):
            if part in {"", "."}:
                continue
            if part == "..":
                if normalized:
                    normalized.pop()
                continue
            normalized.append(part)
        rebased = "/" + "/".join(normalized) + "/"
        if rebased in routes:
            return None

    return f"Broken link target: {target}"


def collect_errors(root: Path) -> list[str]:
    base = plugin_base(root)
    routes = build_site_routes(root)
    errors: list[str] = []

    for path in files_to_scan(root):
        for ref in extract_links(path):
            error = validate_link(ref, base=base, routes=routes, root=root)
            if error:
                rel = ref.source.relative_to(root).as_posix()
                errors.append(f"{rel}:{ref.line}: {error}")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate internal documentation links.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root to validate.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    errors = collect_errors(root)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Found {len(errors)} broken internal documentation link(s).", file=sys.stderr)
        return 1

    print("Documentation links are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
