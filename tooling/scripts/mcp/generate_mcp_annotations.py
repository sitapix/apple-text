#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = ROOT / "skills" / "catalog.json"
CATEGORY_SPECS_PATH = ROOT / "tooling" / "config" / "skill-categories.json"
OUTPUT_PATH = ROOT / "mcp-server" / "skill-annotations.json"
OVERRIDES_PATH = ROOT / "mcp-server" / "skill-annotations.overrides.json"
VALID_CATEGORIES = {
    spec["key"] for spec in json.loads(CATEGORY_SPECS_PATH.read_text(encoding="utf-8"))
}

BASE_TAGS = {
    "entrypoints": ["routing", "entrypoint", "apple-text"],
    "swiftui-bridging": ["swiftui", "bridging", "text-editor"],
    "platform-selection": ["decision", "platform-choice", "architecture"],
    "textkit-runtime": ["textkit", "layout", "runtime"],
    "editor-features": ["editor", "interaction", "editing"],
    "rich-text-modeling": ["rich-text", "attributes", "formatting"],
    "text-model": ["text-processing", "model", "foundation"],
}


class AnnotationError(RuntimeError):
    pass


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_annotations() -> Dict[str, Dict[str, Any]]:
    catalog = load_json(CATALOG_PATH)
    overrides = load_json(OVERRIDES_PATH) if OVERRIDES_PATH.exists() else {}
    annotations: Dict[str, Dict[str, Any]] = {}

    skills = catalog.get("skills", [])
    skill_names = {entry["name"] for entry in skills}
    orphaned = sorted(set(overrides.keys()) - skill_names)
    if orphaned:
        raise AnnotationError(
            "Orphaned MCP annotation overrides for removed skills: " + ", ".join(orphaned)
        )

    for entry in skills:
        name = entry["name"]
        category = entry.get("category") or infer_category(name, entry.get("kind", "workflow"))
        if category not in VALID_CATEGORIES:
            raise AnnotationError(f"Unknown category {category!r} for skill {name}")
        generated = {
            "category": category,
            "tags": infer_tags(name, category),
            "aliases": entry.get("aliases", []),
            "related": entry.get("related_skills", []),
        }
        override = overrides.get(name, {})
        annotations[name] = {
            **generated,
            **override,
        }

    return dict(sorted(annotations.items()))


def infer_category(name: str, kind: str) -> str:
    if name in {"apple-text", "apple-text-audit", "apple-text-apple-docs"}:
        return "entrypoints"

    if kind == "router":
        return "entrypoints"

    if any(token in name for token in ("swiftui", "representable", "texteditor-26")):
        return "swiftui-bridging"

    if kind == "decision" or any(token in name for token in ("views", "appkit-vs-uikit", "selection")):
        return "platform-selection"

    if kind == "diag" or any(token in name for token in ("textkit", "fallback", "layout", "viewport")):
        return "textkit-runtime"

    if any(
        token in name
        for token in (
            "writing-tools",
            "input",
            "undo",
            "find-replace",
            "pasteboard",
            "interaction",
            "accessibility",
            "dynamic-type",
            "spell-autocorrect",
            "drag-drop",
        )
    ):
        return "editor-features"

    if any(
        token in name
        for token in (
            "attributed-string",
            "formatting",
            "colors",
            "markdown",
            "attachments",
        )
    ):
        return "rich-text-modeling"

    return "text-model"


def infer_tags(name: str, category: str | None = None) -> List[str]:
    category = category or infer_category(name, infer_kind_from_name(name))
    tokens = [token for token in name.removeprefix("apple-text-").split("-") if token not in {"ref", "diag"}]
    tags: List[str] = []
    for tag in BASE_TAGS.get(category, []):
        if tag not in tags:
            tags.append(tag)
    for token in tokens:
        if token and token not in tags:
            tags.append(token)
    if name == "apple-text" and "apple-text" not in tags:
        tags.append("apple-text")
    return tags


def infer_kind_from_name(name: str) -> str:
    if name == "apple-text":
        return "router"
    if name.endswith("-diag"):
        return "diag"
    if name.endswith("-ref"):
        return "ref"
    if any(token in name for token in ("views", "selection", "appkit-vs-uikit", "swiftui-bridging")):
        return "decision"
    return "workflow"


def normalize_for_compare(payload: Dict[str, Any]) -> Dict[str, Any]:
    return payload


def write_annotations(path: Path) -> None:
    generated = build_annotations()
    existing = load_json(path) if path.exists() else None
    if existing == normalize_for_compare(generated):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(generated, indent=2) + "\n", encoding="utf-8")


def check_annotations(path: Path) -> int:
    if not path.exists():
        raise AnnotationError(f"Missing generated MCP annotations file: {path}")
    existing = load_json(path)
    generated = build_annotations()
    if existing != normalize_for_compare(generated):
        raise AnnotationError(
            f"{path.relative_to(ROOT)} is out of date. Run `python3 tooling/scripts/mcp/generate_mcp_annotations.py`."
        )
    return 0


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or validate Apple Text MCP skill annotations.")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output path for generated annotations")
    parser.add_argument("--check", action="store_true", help="Fail if the generated annotations are stale")
    args = parser.parse_args()

    output = Path(args.output).resolve()
    try:
        if args.check:
            return check_annotations(output)
        write_annotations(output)
    except AnnotationError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"Wrote {display_path(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
