#!/usr/bin/env python3
"""Validate the routing-decisions.json eval dataset.

Checks:
- JSON is well-formed
- All entries have required fields
- All expected_route values reference real skills or agents
- Category distribution is reasonable
- No duplicate queries
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVALS_FILE = ROOT / "tooling" / "evals" / "routing-decisions.json"
SKILLS_DIR = ROOT / "skills"
AGENTS_DIR = ROOT / "agents"

REGISTERED_SKILLS = {
    "apple-text",
    "apple-text-audit",
    "apple-text-views",
    "apple-text-textkit-diag",
    "apple-text-recipes",
}

AGENT_NAMES = {
    "textkit-reference",
    "editor-reference",
    "rich-text-reference",
    "platform-reference",
    "textkit-auditor",
}

VALID_ROUTES = REGISTERED_SKILLS | AGENT_NAMES
VALID_TYPES = {"skill", "agent"}
VALID_CATEGORIES = {"single-domain", "multi-domain"}
REQUIRED_FIELDS = {"query", "expected_route", "expected_type", "also_acceptable", "category", "notes"}


def main() -> int:
    if not EVALS_FILE.exists():
        print(f"ERROR: {EVALS_FILE} not found")
        return 1

    with open(EVALS_FILE) as f:
        entries = json.load(f)

    errors: list[str] = []
    queries_seen: set[str] = set()
    categories: dict[str, int] = {}

    for i, entry in enumerate(entries):
        prefix = f"Entry {i}"

        # Required fields
        missing = REQUIRED_FIELDS - set(entry.keys())
        if missing:
            errors.append(f"{prefix}: missing fields: {missing}")
            continue

        # Valid route
        route = entry["expected_route"]
        if route not in VALID_ROUTES:
            errors.append(f"{prefix}: unknown route '{route}' — must be one of {sorted(VALID_ROUTES)}")

        # Valid type
        etype = entry["expected_type"]
        if etype not in VALID_TYPES:
            errors.append(f"{prefix}: unknown type '{etype}' — must be skill or agent")

        # Route/type consistency
        if etype == "skill" and route not in REGISTERED_SKILLS:
            errors.append(f"{prefix}: type is 'skill' but route '{route}' is an agent")
        if etype == "agent" and route not in AGENT_NAMES:
            errors.append(f"{prefix}: type is 'agent' but route '{route}' is a skill")

        # Also-acceptable routes
        for alt in entry["also_acceptable"]:
            if alt not in VALID_ROUTES:
                errors.append(f"{prefix}: unknown also_acceptable route '{alt}'")

        # Valid category
        cat = entry["category"]
        if cat not in VALID_CATEGORIES:
            errors.append(f"{prefix}: unknown category '{cat}'")
        categories[cat] = categories.get(cat, 0) + 1

        # Duplicate queries
        query = entry["query"].strip().lower()
        if query in queries_seen:
            errors.append(f"{prefix}: duplicate query")
        queries_seen.add(query)

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        print(f"\n{len(errors)} error(s) in {EVALS_FILE.name}")
        return 1

    # Coverage report
    routes_covered = {e["expected_route"] for e in entries}
    routes_covered |= {alt for e in entries for alt in e["also_acceptable"]}
    uncovered = VALID_ROUTES - routes_covered
    if uncovered:
        print(f"  WARNING: routes not covered by any eval: {sorted(uncovered)}")

    print(f"Validated {len(entries)} routing eval entries. Categories: {categories}. 0 error(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
