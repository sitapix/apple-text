#!/usr/bin/env python3

import argparse
import json
import re
import sys
from pathlib import Path

from generate_docs import KIND_ORDER, discover_sidecars, stale_docs


ROOT = Path(__file__).resolve().parent.parent
MAX_SKILL_BODY_LINES = 450
LONG_SKILL_BODY_LINES = 300
EARLY_SUMMARY_WINDOW = 40
SIDECAR_REQUIRED_LINES = 400
PROMINENT_ENTRYPOINT_PRIORITY = 2
PACKAGE_EXCLUSIONS = ("node_modules/", ".astro/", "dist/")
LEGACY_DOCS_PATHS = (
    Path("docs/.vitepress"),
    Path("docs/example-conversations.md"),
    Path("docs/guide"),
    Path("docs/index.md"),
    Path("src/content/docs/guide/skill-catalog.md"),
)
REQUIRED_SKILL_SECTIONS = (
    "## When to Use",
    ("## Quick Decision", "## Decision Tree"),
    "## Core Guidance",
    "## Related Skills",
)


class ValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def parse_front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path} is missing opening front matter delimiter")

    try:
        _, front_matter, _ = text.split("---\n", 2)
    except ValueError:
        fail(f"{path} is missing closing front matter delimiter")

    data: dict[str, str] = {}
    current_key: str | None = None
    block_lines: list[str] = []

    for raw_line in front_matter.splitlines():
        if current_key is not None:
            if raw_line.startswith("  ") or raw_line == "":
                block_lines.append(raw_line[2:] if raw_line.startswith("  ") else "")
                continue
            data[current_key] = "\n".join(block_lines).strip()
            current_key = None
            block_lines = []

        if not raw_line.strip():
            continue

        if ":" not in raw_line:
            fail(f"{path} has malformed front matter line: {raw_line}")

        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value in {"|", ""}:
            current_key = key
            block_lines = []
        else:
            data[key] = value

    if current_key is not None:
        data[current_key] = "\n".join(block_lines).strip()

    return data


def split_front_matter(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path} is missing opening front matter delimiter")

    try:
        _, front_matter, body = text.split("---\n", 2)
    except ValueError:
        fail(f"{path} is missing closing front matter delimiter")

    return front_matter, body


def docs_root_for(path: Path) -> Path | None:
    for candidate in [path.parent, *path.parents]:
        if (
            candidate.name == "docs"
            and candidate.parent.name == "content"
            and candidate.parent.parent.name == "src"
        ):
            return candidate.resolve()
    return None


def resolve_docs_route_candidate(path: Path, target: str) -> Path | None:
    docs_dir = docs_root_for(path)
    if docs_dir is None:
        return None
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return None

    if target.startswith("/"):
        base = (docs_dir / target.lstrip("/")).resolve()
    else:
        base = (path.parent / target).resolve()
    candidates = [
        base,
        base.with_suffix(".md"),
        base.with_suffix(".mdx"),
        base / "index.md",
        base / "index.mdx",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def validate_markdown_links(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    inline_code_spans = [match.span() for match in re.finditer(r"`[^`\n]+`", text)]
    unresolved: list[str] = []

    for match in pattern.finditer(text):
        if any(start <= match.start() and match.end() <= end for start, end in inline_code_spans):
            continue

        target = match.group(1)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if target.startswith("/Users/"):
            unresolved.append(f"{path}: absolute local path link is not portable: {target}")
            continue
        if target.startswith("/"):
            if resolve_docs_route_candidate(path, target) is None and target != "/":
                unresolved.append(f"{path}: missing linked file {target}")
            continue
        if target.startswith("/skill "):
            continue

        link_target = (path.parent / target).resolve()
        if not link_target.exists() and resolve_docs_route_candidate(path, target) is None:
            unresolved.append(f"{path}: missing linked file {target}")

    return unresolved


def validate_docs_route_links(path: Path) -> list[str]:
    docs_dir = docs_root_for(path)
    if docs_dir is None:
        return []

    text = path.read_text(encoding="utf-8")
    offenders: list[str] = []
    patterns = [
        re.compile(r"\[[^\]]+\]\(([^)]+)\)"),
        re.compile(r'href=["\']([^"\']+)["\']'),
    ]

    for pattern in patterns:
        for match in pattern.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#", "/")):
                continue
            if not target.endswith((".md", ".mdx")):
                continue

            resolved = (path.parent / target).resolve()
            if docs_dir in resolved.parents:
                offenders.append(
                    f"{path}: doc links must use route paths, not source filenames: {target}"
                )

    return offenders


def require_section_order(path: Path, body: str) -> int:
    lines = body.rstrip("\n").splitlines()
    heading_positions: dict[str, int] = {}
    for index, line in enumerate(lines):
        if line.startswith("## "):
            heading_positions.setdefault(line.strip(), index)

    order_positions: list[int] = []
    quick_index = -1
    for required in REQUIRED_SKILL_SECTIONS:
        if isinstance(required, tuple):
            found = [heading_positions.get(option) for option in required if option in heading_positions]
            found = [value for value in found if value is not None]
            if not found:
                fail(f"{path} is missing either '## Quick Decision' or '## Decision Tree'")
            quick_index = min(found)
            order_positions.append(quick_index)
            continue

        if required not in heading_positions:
            fail(f"{path} is missing required section: {required}")
        order_positions.append(heading_positions[required])

    if order_positions != sorted(order_positions):
        fail(
            f"{path} must keep its top-level sections in order: "
            "When to Use → Quick Decision/Decision Tree → Core Guidance → Related Skills"
        )

    return quick_index


def has_scope_sentence(body: str) -> bool:
    lines = body.splitlines()
    first_h2 = next((index for index, line in enumerate(lines) if line.startswith("## ")), len(lines))
    scope_lines = []
    for raw_line in lines[:first_h2]:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        scope_lines.append(line)
    return any(line.endswith((".", ":", "?")) or len(line.split()) >= 6 for line in scope_lines)


def load_catalog(root: Path) -> tuple[dict[str, dict], list[dict]]:
    catalog_path = root / "skills" / "catalog.json"
    data = load_json(catalog_path)
    entries = data.get("skills")
    if not isinstance(entries, list) or not entries:
        fail(f"{catalog_path} must define a non-empty 'skills' array")

    catalog: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            fail(f"{catalog_path} contains a non-object skill entry")

        for key in ("name", "kind", "entrypoint_priority", "aliases", "related_skills"):
            if key not in entry:
                fail(f"{catalog_path} entry is missing required field: {key}")

        name = entry["name"]
        if not isinstance(name, str) or not name:
            fail(f"{catalog_path} has an invalid skill name entry")
        if name in catalog:
            fail(f"{catalog_path} contains duplicate skill name: {name}")

        if entry["kind"] not in KIND_ORDER:
            fail(f"{catalog_path} entry '{name}' has unsupported kind: {entry['kind']}")

        if not isinstance(entry["entrypoint_priority"], int) or entry["entrypoint_priority"] < 1:
            fail(f"{catalog_path} entry '{name}' must use a positive integer entrypoint_priority")

        for list_key in ("aliases", "related_skills"):
            value = entry.get(list_key, [])
            if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
                fail(f"{catalog_path} entry '{name}' has invalid list field: {list_key}")

        if "sidecars" in entry:
            fail(f"{catalog_path} entry '{name}' must not define sidecars; they are auto-discovered")

        if "agent" in entry and (not isinstance(entry["agent"], str) or not entry["agent"]):
            fail(f"{catalog_path} entry '{name}' has invalid agent value")

        catalog[name] = entry

    return catalog, entries


def validate_named_entrypoints(root: Path, prominent_skills: list[str], skill_count: int) -> None:
    readme = (root / "README.md").read_text(encoding="utf-8")
    skills_overview_doc = (root / "src" / "content" / "docs" / "skills" / "index.mdx").read_text(encoding="utf-8")

    readme_count = re.search(r"(\d+)\s+focused text skills", readme)
    if not readme_count or int(readme_count.group(1)) != skill_count:
        fail("README.md skill count does not match skills/catalog.json")

    doc_count = re.search(r"ships\s+(\d+)\s+skills", skills_overview_doc)
    if not doc_count or int(doc_count.group(1)) != skill_count:
        fail("src/content/docs/skills/index.mdx skill count does not match skills/catalog.json")

    for relative_path in (
        Path("README.md"),
        Path("src/content/docs/index.mdx"),
        Path("src/content/docs/skills/index.mdx"),
        Path("src/content/docs/guide/entry-points.md"),
        Path("commands/ask.md"),
    ):
        text = (root / relative_path).read_text(encoding="utf-8")
        for skill_name in prominent_skills:
            if skill_name not in text:
                fail(f"{relative_path} is missing prominent entry point: {skill_name}")


def validate_npmignore(root: Path) -> None:
    npmignore_path = root / ".npmignore"
    if not npmignore_path.exists():
        fail(".npmignore is required to keep package output small")

    contents = npmignore_path.read_text(encoding="utf-8")
    for pattern in PACKAGE_EXCLUSIONS:
        if pattern not in contents:
            fail(f".npmignore must exclude {pattern}")


def validate(root: Path) -> str:
    skills_dir = root / "skills"
    agents_dir = root / "agents"
    commands_dir = root / "commands"
    docs_dir = root / "src" / "content" / "docs"

    skill_files = sorted(skills_dir.glob("*/SKILL.md"))
    if not skill_files:
        fail("No skills found under skills/")

    catalog, catalog_entries = load_catalog(root)
    skill_names: set[str] = set()

    for skill_file in skill_files:
        metadata = parse_front_matter(skill_file)
        for key in ("name", "description", "license"):
            if not metadata.get(key):
                fail(f"{skill_file} is missing required front matter field: {key}")

        _, body = split_front_matter(skill_file)
        body_lines = body.rstrip("\n").splitlines()
        if len(body_lines) > MAX_SKILL_BODY_LINES:
            fail(
                f"{skill_file} body is {len(body_lines)} lines; keep SKILL.md under "
                f"{MAX_SKILL_BODY_LINES} lines and move detail into supporting files"
            )

        if not has_scope_sentence(body):
            fail(f"{skill_file} must include a short scope sentence before its first '##' section")

        quick_index = require_section_order(skill_file, body)

        skill_name = metadata["name"]
        expected_dir = skill_file.parent.name
        if skill_name != expected_dir:
            fail(f"{skill_file} name '{skill_name}' does not match directory '{expected_dir}'")

        if skill_name in skill_names:
            fail(f"Duplicate skill name found: {skill_name}")
        skill_names.add(skill_name)

        if skill_name not in catalog:
            fail(f"{skill_file} is missing from skills/catalog.json")

        catalog_entry = catalog[skill_name]
        sidecars = discover_sidecars(skill_file.parent)

        skill_text = skill_file.read_text(encoding="utf-8")
        for sidecar_name in sidecars:
            if f"]({sidecar_name})" not in skill_text:
                fail(f"{skill_file} must link to sidecar file {sidecar_name}")

        if len(body_lines) > SIDECAR_REQUIRED_LINES and not sidecars:
            fail(
                f"{skill_file} body is {len(body_lines)} lines; skills over "
                f"{SIDECAR_REQUIRED_LINES} lines must move detail into linked sidecar markdown files"
            )

        if len(body_lines) > LONG_SKILL_BODY_LINES and quick_index >= EARLY_SUMMARY_WINDOW and not sidecars:
            fail(
                f"{skill_file} is long enough to require an early summary section or linked sidecar markdown files"
            )

        metadata_agent = metadata.get("agent")
        catalog_agent = catalog_entry.get("agent")
        if metadata_agent and not (agents_dir / f"{metadata_agent}.md").exists():
            fail(f"{skill_file} references missing agent: {metadata_agent}")
        if catalog_agent and metadata_agent != catalog_agent:
            fail(f"{skill_file} agent metadata must match skills/catalog.json")

        for related_skill in catalog_entry["related_skills"]:
            if related_skill == skill_name:
                fail(f"skills/catalog.json entry '{skill_name}' cannot relate to itself")

    catalog_names = set(catalog)
    if catalog_names != skill_names:
        missing = sorted(skill_names - catalog_names)
        extra = sorted(catalog_names - skill_names)
        if missing:
            fail(f"skills/catalog.json is missing skills: {', '.join(missing)}")
        if extra:
            fail(f"skills/catalog.json references unknown skills: {', '.join(extra)}")

    for entry in catalog_entries:
        for related_skill in entry["related_skills"]:
            if related_skill not in skill_names:
                fail(f"skills/catalog.json entry '{entry['name']}' references unknown related skill: {related_skill}")
        agent_name = entry.get("agent")
        if agent_name and not (agents_dir / f"{agent_name}.md").exists():
            fail(f"skills/catalog.json entry '{entry['name']}' references missing agent: {agent_name}")

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name == "catalog.json":
            continue
        if not (skill_dir / "SKILL.md").exists():
            fail(f"{skill_dir} is missing SKILL.md")

    agent_names: set[str] = set()
    for agent_file in sorted(agents_dir.glob("*.md")):
        metadata = parse_front_matter(agent_file)
        for key in ("name", "description"):
            if not metadata.get(key):
                fail(f"{agent_file} is missing required front matter field: {key}")
        agent_names.add(metadata["name"])

    for command_file in sorted(commands_dir.glob("*.md")):
        metadata = parse_front_matter(command_file)
        if not metadata.get("description"):
            fail(f"{command_file} is missing required front matter field: description")

    unresolved: list[str] = []
    ref_pattern = re.compile(r"/skill\s+([A-Za-z0-9._-]+)")
    markdown_files = [root / "README.md"]
    markdown_files.extend(sorted(skills_dir.rglob("*.md")))
    markdown_files.extend(sorted(commands_dir.glob("*.md")))
    markdown_files.extend(sorted(docs_dir.rglob("*.md")))
    markdown_files.extend(sorted(docs_dir.rglob("*.mdx")))
    markdown_files.extend(sorted(agents_dir.glob("*.md")))

    for markdown_file in markdown_files:
        text = markdown_file.read_text(encoding="utf-8")
        for match in ref_pattern.findall(text):
            if match not in skill_names:
                unresolved.append(f"{markdown_file}: /skill {match}")
        unresolved.extend(validate_markdown_links(markdown_file))
        unresolved.extend(validate_docs_route_links(markdown_file))

    if unresolved:
        fail("Validation errors:\n" + "\n".join(unresolved))

    for legacy_path in LEGACY_DOCS_PATHS:
        if (root / legacy_path).exists():
            fail(f"Legacy VitePress docs path should not exist: {legacy_path}")

    validate_npmignore(root)

    stale_generated_docs = stale_docs(root)
    if stale_generated_docs:
        stale_paths = ", ".join(path.relative_to(root).as_posix() for path in stale_generated_docs)
        fail(f"Generated docs are stale: {stale_paths}. Run python3 scripts/generate_docs.py")

    prominent_skills = sorted(
        entry["name"]
        for entry in catalog_entries
        if entry["entrypoint_priority"] <= PROMINENT_ENTRYPOINT_PRIORITY
    )
    validate_named_entrypoints(root, prominent_skills, len(skill_files))

    claude_code = load_json(root / "claude-code.json")
    plugin = load_json(root / ".claude-plugin" / "plugin.json")
    marketplace = load_json(root / ".claude-plugin" / "marketplace.json")

    plugin_version = plugin.get("version")
    marketplace_version = marketplace.get("metadata", {}).get("version")
    marketplace_plugins = marketplace.get("plugins", [])
    if len(marketplace_plugins) != 1:
        fail("Marketplace manifest must contain exactly one plugin entry")

    market_plugin = marketplace_plugins[0]

    if claude_code.get("version") != plugin_version:
        fail("claude-code.json version does not match .claude-plugin/plugin.json")
    if plugin.get("name") != claude_code.get("name"):
        fail("claude-code.json name does not match .claude-plugin/plugin.json")
    if marketplace_version != plugin_version:
        fail(".claude-plugin/marketplace.json metadata version does not match plugin.json")
    if market_plugin.get("name") != plugin.get("name"):
        fail("Marketplace plugin name does not match plugin.json name")
    if market_plugin.get("version") != plugin_version:
        fail("Marketplace plugin version does not match plugin.json version")
    if plugin.get("license") != claude_code.get("license"):
        fail("claude-code.json license does not match .claude-plugin/plugin.json")
    if market_plugin.get("license") != plugin.get("license"):
        fail("Marketplace plugin license does not match plugin.json license")

    plugin_author = plugin.get("author", {})
    market_author = market_plugin.get("author", {})
    if market_author.get("name") != plugin_author.get("name"):
        fail("Marketplace plugin author does not match plugin.json author")

    if plugin.get("skills") != "./skills/" or market_plugin.get("skills") != "./skills/":
        fail("Plugin manifests must point skills to ./skills/")
    if plugin.get("agents") != "./agents/" or market_plugin.get("agents") != "./agents/":
        fail("Plugin manifests must point agents to ./agents/")
    if plugin.get("hooks") != "./hooks/hooks.json" or market_plugin.get("hooks") != "./hooks/hooks.json":
        fail("Plugin manifests must point hooks to ./hooks/hooks.json")
    if plugin.get("commands") != "./commands/" or market_plugin.get("commands") != "./commands/":
        fail("Plugin manifests must point commands to ./commands/")
    if market_plugin.get("source") != "./":
        fail("Marketplace plugin source must be ./")
    if market_plugin.get("keywords") != plugin.get("keywords"):
        fail("Marketplace plugin keywords must match plugin.json keywords")

    return (
        f"Validated {len(skill_files)} skills, {len(list(commands_dir.glob('*.md')))} commands, "
        f"{len(agent_names)} agents, routing catalog, package rules, and plugin manifests."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Apple Text plugin integrity.")
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
