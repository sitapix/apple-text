#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from generate_mcp_annotations import build_annotations


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = ROOT / "mcp-server" / "bundle.json"
MCP_PACKAGE = ROOT / "mcp-server" / "package.json"
SKILL_CATALOG = ROOT / "skills" / "catalog.json"

KIND_LABELS = {
    "router": "Routers",
    "workflow": "Workflows",
    "diag": "Diagnostics",
    "decision": "Decisions",
    "ref": "References",
}
KIND_ORDER = ("router", "workflow", "diag", "decision", "ref")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "use",
    "when",
    "with",
}


class BundleError(RuntimeError):
    pass


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_front_matter_scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_front_matter(text: str, source: Path) -> Dict[str, Any]:
    if not text.startswith("---\n"):
        raise BundleError(f"{source} is missing opening front matter delimiter")

    try:
        _, front_matter, _ = text.split("---\n", 2)
    except ValueError as exc:
        raise BundleError(f"{source} is missing closing front matter delimiter") from exc

    data: Dict[str, Any] = {}
    current_key: Optional[str] = None
    block_lines: List[str] = []
    list_key: Optional[str] = None
    list_values: List[str] = []

    def flush_block() -> None:
        nonlocal current_key, block_lines
        if current_key is not None:
            data[current_key] = "\n".join(block_lines).strip()
            current_key = None
            block_lines = []

    def flush_list() -> None:
        nonlocal list_key, list_values
        if list_key is not None:
            data[list_key] = list_values[:]
            list_key = None
            list_values = []

    for raw_line in front_matter.splitlines():
        if current_key is not None:
            if raw_line.startswith("  ") or raw_line == "":
                block_lines.append(raw_line[2:] if raw_line.startswith("  ") else "")
                continue
            flush_block()

        if list_key is not None:
            stripped = raw_line.strip()
            if stripped.startswith("- "):
                list_values.append(stripped[2:].strip())
                continue
            flush_list()

        if not raw_line.strip():
            continue

        if ":" not in raw_line:
            raise BundleError(f"{source} has malformed front matter line: {raw_line}")

        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value in {"|", ">", ""}:
            if value == "":
                list_key = key
                list_values = []
            else:
                current_key = key
                block_lines = []
        else:
            data[key] = normalize_front_matter_scalar(value)

    flush_block()
    flush_list()
    return data


def split_document(path: Path) -> Tuple[Dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    metadata = parse_front_matter(text, path)
    _, _, body = text.split("---\n", 2)
    return metadata, body.strip()


def normalize_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, str):
        return [value]
    return []


def parse_sections(content: str) -> List[Dict[str, Any]]:
    lines = content.split("\n")
    sections: List[Dict[str, Any]] = []
    current_heading: Optional[str] = None
    current_level = 0
    current_start = 0

    for index, line in enumerate(lines):
        match = None
        if line.startswith("#"):
            import re

            match = re.match(r"^(#{1,6})\s+(.+)$", line)

        if match and len(match.group(1)) <= 2:
            if current_heading is not None or (index > 0 and not sections):
                heading = current_heading or "_preamble"
                section_content = "\n".join(lines[current_start:index])
                sections.append(
                    {
                        "heading": heading,
                        "level": current_level if current_heading else 0,
                        "startLine": current_start,
                        "endLine": index - 1,
                        "charCount": len(section_content),
                    }
                )

            current_heading = match.group(2).strip()
            current_level = len(match.group(1))
            current_start = index
        elif index == 0 and not line.startswith("# "):
            current_heading = None
            current_start = 0

    final_heading = current_heading if current_heading is not None else ("_preamble" if not sections else None)
    if final_heading is not None:
        section_content = "\n".join(lines[current_start:])
        sections.append(
            {
                "heading": final_heading,
                "level": current_level if current_heading else 0,
                "startLine": current_start,
                "endLine": len(lines) - 1,
                "charCount": len(section_content),
            }
        )

    return sections


def load_catalog_entries() -> Dict[str, Dict[str, Any]]:
    catalog = load_json(SKILL_CATALOG)
    return {entry["name"]: entry for entry in catalog.get("skills", [])}


def walk_skill_dirs(root: Path) -> Iterable[Path]:
    for skill_file in sorted(root.glob("**/SKILL.md")):
        yield skill_file.parent


def infer_skill_kind(name: str) -> str:
    if name == "apple-text":
        return "router"
    if name.endswith("-diag"):
        return "diag"
    if name.endswith("-ref"):
        return "ref"
    if (
        "selection" in name
        or "appkit-vs-uikit" in name
        or name.endswith("-views")
        or name.endswith("-parsing")
        or name.endswith("-swiftui-bridging")
    ):
        return "decision"
    return "workflow"


def load_skills() -> Dict[str, Dict[str, Any]]:
    catalog_entries = load_catalog_entries()
    annotations = build_annotations()
    skills: Dict[str, Dict[str, Any]] = {}

    for skill_dir in walk_skill_dirs(ROOT / "skills"):
        metadata, body = split_document(skill_dir / "SKILL.md")
        name = metadata.get("name") or skill_dir.name
        catalog_entry = catalog_entries.get(name, {})
        annotation = annotations.get(name, {})
        skills[name] = {
            "name": name,
            "description": metadata.get("description", ""),
            "content": body,
            "kind": catalog_entry.get("kind") or infer_skill_kind(name),
            "category": annotation.get("category"),
            "tags": annotation.get("tags", []),
            "aliases": annotation.get("aliases", []),
            "relatedSkills": annotation.get("related", []),
            "entrypointPriority": catalog_entry.get("entrypoint_priority"),
            "agent": catalog_entry.get("agent"),
            "sections": parse_sections(body),
        }

    return dict(sorted(skills.items()))


def load_commands() -> Dict[str, Dict[str, Any]]:
    commands: Dict[str, Dict[str, Any]] = {}
    for path in sorted((ROOT / "commands").glob("*.md")):
        metadata, body = split_document(path)
        name = metadata.get("name") or path.stem
        commands[name] = {
            "name": name,
            "description": metadata.get("description", ""),
            "content": body,
            "argumentHints": normalize_string_list(metadata.get("argument-hint")),
        }
    return commands


def load_agents() -> Dict[str, Dict[str, Any]]:
    agents: Dict[str, Dict[str, Any]] = {}
    for path in sorted((ROOT / "agents").glob("*.md")):
        metadata, body = split_document(path)
        name = metadata.get("name") or path.stem
        agents[name] = {
            "name": name,
            "description": metadata.get("description", ""),
            "model": metadata.get("model"),
            "tools": normalize_string_list(metadata.get("tools")),
            "content": body,
        }
    return agents


def build_catalog(skills: Dict[str, Dict[str, Any]], agents: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    groups: Dict[str, Dict[str, Any]] = {}
    featured: List[Dict[str, Any]] = []

    for kind in KIND_ORDER:
        groups[kind] = {"label": KIND_LABELS[kind], "skills": []}

    for skill in skills.values():
        entry = {
            "name": skill["name"],
            "description": skill["description"],
            "aliases": skill["aliases"],
            "entrypointPriority": skill.get("entrypointPriority"),
        }
        groups[skill["kind"]]["skills"].append(entry)
        if skill.get("entrypointPriority") is not None:
            featured.append(entry)

    for kind in KIND_ORDER:
        groups[kind]["skills"].sort(key=lambda item: item["name"])

    filtered_groups = {
        kind: group
        for kind, group in groups.items()
        if group["skills"]
    }

    featured.sort(
        key=lambda item: (
            item.get("entrypointPriority", 10_000),
            item["name"],
        )
    )

    agent_list = sorted(
        (
            {"name": agent["name"], "description": agent["description"]}
            for agent in agents.values()
        ),
        key=lambda item: item["name"],
    )

    return {
        "groups": filtered_groups,
        "featured": featured,
        "agents": agent_list,
        "totalSkills": len(skills),
        "totalAgents": len(agents),
    }


def tokenize(text: str) -> List[str]:
    import re

    normalized = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return [
        term
        for term in re.split(r"[^a-z0-9@]+", normalized.lower())
        if len(term) > 1 and term not in STOPWORDS
    ]


def build_search_index(skills: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    documents: List[Dict[str, Any]] = []
    section_terms: Dict[str, Dict[str, List[str]]] = {}

    for skill in skills.values():
        documents.append(
            {
                "name": skill["name"],
                "title": skill["name"].replace("-", " "),
                "description": skill["description"],
                "category": skill.get("category") or "",
                "tags": " ".join(skill.get("tags", [])),
                "aliases": " ".join(skill["aliases"]),
                "headings": " ".join(section["heading"] for section in skill["sections"]),
                "body": skill["content"],
                "kind": skill["kind"],
            }
        )

        lines = skill["content"].split("\n")
        per_section: Dict[str, List[str]] = {}
        for section in skill["sections"]:
            body = " ".join(lines[section["startLine"] : section["endLine"] + 1])
            tokens = sorted(set(tokenize(f"{section['heading']} {body}")))
            per_section[section["heading"]] = tokens
        section_terms[skill["name"]] = per_section

    return {
        "version": "apple-text-search-v1",
        "documents": documents,
        "sectionTerms": section_terms,
        "docCount": len(documents),
    }


def build_bundle(previous_generated_at: Optional[str]) -> Dict[str, Any]:
    mcp_package = load_json(MCP_PACKAGE)
    skills = load_skills()
    commands = load_commands()
    agents = load_agents()

    return {
        "version": mcp_package["version"],
        "generatedAt": previous_generated_at or now_iso(),
        "skills": skills,
        "commands": commands,
        "agents": agents,
        "catalog": build_catalog(skills, agents),
        "searchIndex": build_search_index(skills),
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_for_compare(bundle: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(bundle)
    normalized.pop("generatedAt", None)
    return normalized


def read_existing_bundle(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    return load_json(path)


def write_bundle(path: Path) -> None:
    existing = read_existing_bundle(path)
    bundle = build_bundle(existing.get("generatedAt") if existing else None)

    if existing and normalize_for_compare(existing) == normalize_for_compare(bundle):
        return

    bundle["generatedAt"] = now_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def check_bundle(path: Path) -> int:
    existing = read_existing_bundle(path)
    if existing is None:
        raise BundleError(f"Missing generated MCP bundle: {path}")

    bundle = build_bundle(existing.get("generatedAt"))
    if normalize_for_compare(existing) != normalize_for_compare(bundle):
        raise BundleError(
            f"{path.relative_to(ROOT)} is out of date. Run `python3 tooling/scripts/mcp/generate_mcp_bundle.py`."
        )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or validate the committed Apple Text MCP bundle.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output path for the bundle JSON")
    parser.add_argument("--check", action="store_true", help="Fail if the bundle JSON is out of date")
    args = parser.parse_args()

    output = Path(args.output).resolve()
    try:
        if args.check:
            return check_bundle(output)
        write_bundle(output)
    except BundleError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"Wrote {display_path(output)}")
    return 0


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
