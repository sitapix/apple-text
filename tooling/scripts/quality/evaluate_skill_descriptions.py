#!/usr/bin/env python3

import argparse
import json
import re
import shlex
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DESCRIPTION_LIMIT = 1024
IMPERATIVE_PREFIXES = ("Use when", "Use this skill when")
VALID_SPLITS = {"train", "validation"}
INTENT_WORDS = (
    "use when",
    "building",
    "choosing",
    "comparing",
    "customizing",
    "debugging",
    "deciding",
    "embedding",
    "evaluating",
    "handling",
    "implementing",
    "integrating",
    "migrating",
    "porting",
    "searching",
    "using",
    "working with",
    "wrapping",
    "writing",
)


class EvaluationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise EvaluationError(message)


def normalize_front_matter_scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


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

        if value in {"|", ">"} or value == "":
            current_key = key
            block_lines = []
        else:
            data[key] = normalize_front_matter_scalar(value)

    if current_key is not None:
        data[current_key] = "\n".join(block_lines).strip()

    return data


def load_skill_descriptions(root: Path) -> dict[str, dict[str, str]]:
    skills: dict[str, dict[str, str]] = {}
    for path in sorted((root / "skills").glob("*/SKILL.md")):
        metadata = parse_front_matter(path)
        name = metadata.get("name")
        description = " ".join(metadata.get("description", "").split())
        if not name:
            fail(f"{path} is missing name")
        skills[name] = {
            "description": description,
            "path": str(path),
        }
    return skills


def lint_description(name: str, description: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    normalized = " ".join(description.split())
    lowered = normalized.lower()

    if not normalized:
        issues.append({"level": "error", "message": "description is empty"})
        return issues

    if len(normalized) > DESCRIPTION_LIMIT:
        issues.append(
            {
                "level": "error",
                "message": f"description exceeds {DESCRIPTION_LIMIT} characters",
            }
        )

    if not normalized.startswith(IMPERATIVE_PREFIXES):
        issues.append(
            {
                "level": "error",
                "message": "description should start with 'Use when' or 'Use this skill when'",
            }
        )

    if not any(token in lowered for token in INTENT_WORDS):
        issues.append(
            {
                "level": "warning",
                "message": "description may be too label-like; add clearer user-intent language",
            }
        )

    if len(normalized) < 80:
        issues.append(
            {
                "level": "warning",
                "message": "description is short; consider adding more trigger context or boundary guidance",
            }
        )

    if " or " not in lowered and " even if " not in lowered and " not " not in lowered:
        issues.append(
            {
                "level": "warning",
                "message": "description may be too narrow; consider adding adjacent cases or boundary guidance",
            }
        )

    if lowered.count("reference") > 0 and "need" not in lowered and "already" not in lowered:
        issues.append(
            {
                "level": "warning",
                "message": "reference-style description should still explain the user intent that triggers it",
            }
        )

    return issues


def lint_skills(root: Path) -> dict[str, object]:
    skills = load_skill_descriptions(root)
    results: list[dict[str, object]] = []

    for name, record in sorted(skills.items()):
        issues = lint_description(name, record["description"])
        if not issues:
            continue
        results.append(
            {
                "skill": name,
                "path": record["path"],
                "description": record["description"],
                "issues": issues,
            }
        )

    error_count = sum(1 for result in results for issue in result["issues"] if issue["level"] == "error")
    warning_count = sum(1 for result in results for issue in result["issues"] if issue["level"] == "warning")
    return {
        "skills_checked": len(skills),
        "error_count": error_count,
        "warning_count": warning_count,
        "results": results,
    }


def print_lint_report(report: dict[str, object]) -> None:
    print(
        f"Checked {report['skills_checked']} skill descriptions. "
        f"{report['error_count']} error(s), {report['warning_count']} warning(s)."
    )
    for result in report["results"]:
        print(f"- {result['skill']} ({result['path']})")
        for issue in result["issues"]:
            print(f"  [{issue['level']}] {issue['message']}")


def load_dataset(path: Path, skills: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")

    if not isinstance(payload, list) or not payload:
        fail(f"{path} must contain a non-empty JSON array")

    entries: list[dict[str, object]] = []
    for index, row in enumerate(payload):
        if not isinstance(row, dict):
            fail(f"{path} entry {index} must be an object")

        skill = row.get("skill")
        query = row.get("query")
        should_trigger = row.get("should_trigger")
        split = row.get("split")

        if not isinstance(skill, str) or skill not in skills:
            fail(f"{path} entry {index} has unknown skill: {skill}")
        if not isinstance(query, str) or not query.strip():
            fail(f"{path} entry {index} must define a non-empty query")
        if not isinstance(should_trigger, bool):
            fail(f"{path} entry {index} must define boolean should_trigger")
        if not isinstance(split, str) or split not in VALID_SPLITS:
            fail(f"{path} entry {index} must use split train or validation")

        entries.append(
            {
                "skill": skill,
                "query": query,
                "should_trigger": should_trigger,
                "split": split,
            }
        )

    return entries


def build_command(command_template: str, query: str, skill: str) -> str:
    return command_template.format(query=shlex.quote(query), skill=shlex.quote(skill))


def iter_tool_uses(payload: object):
    if isinstance(payload, dict):
        if payload.get("type") == "tool_use":
            yield payload
        for value in payload.values():
            yield from iter_tool_uses(value)
    elif isinstance(payload, list):
        for value in payload:
            yield from iter_tool_uses(value)


def detect_trigger(output: str, skill: str, detector: str, pattern: str | None) -> bool:
    if detector == "claude-code-json":
        payload = json.loads(output)
        for tool_use in iter_tool_uses(payload):
            if tool_use.get("name") != "Skill":
                continue
            input_data = tool_use.get("input", {})
            if isinstance(input_data, dict) and input_data.get("skill") == skill:
                return True
        return False

    if pattern is None:
        fail(f"--pattern is required for detector {detector}")

    if detector == "substring":
        return pattern.replace("{skill}", skill) in output

    if detector == "regex":
        compiled = pattern.replace("{skill}", re.escape(skill))
        return re.search(compiled, output, flags=re.MULTILINE) is not None

    fail(f"Unsupported detector: {detector}")


def evaluate_dataset(
    dataset: list[dict[str, object]],
    command_template: str,
    detector: str,
    pattern: str | None,
    runs: int,
    threshold: float,
) -> dict[str, object]:
    per_query: list[dict[str, object]] = []
    split_totals: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "total": 0})
    skill_totals: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "total": 0})

    for entry in dataset:
        triggers = 0
        outputs: list[str] = []
        for _ in range(runs):
            command = build_command(command_template, entry["query"], entry["skill"])
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                details = (result.stderr or result.stdout).strip()
                fail(f"Runner command failed for skill {entry['skill']}: {details}")

            output = result.stdout.strip()
            outputs.append(output)
            if detect_trigger(output, entry["skill"], detector, pattern):
                triggers += 1

        trigger_rate = triggers / runs
        passed = trigger_rate >= threshold if entry["should_trigger"] else trigger_rate < threshold

        per_query.append(
            {
                **entry,
                "runs": runs,
                "triggers": triggers,
                "trigger_rate": trigger_rate,
                "passed": passed,
            }
        )

        split = entry["split"]
        skill = entry["skill"]
        split_totals[split]["total"] += 1
        skill_totals[skill]["total"] += 1
        if passed:
            split_totals[split]["passed"] += 1
            skill_totals[skill]["passed"] += 1

    return {
        "runs": runs,
        "threshold": threshold,
        "queries": per_query,
        "splits": {
            split: {
                "passed": totals["passed"],
                "total": totals["total"],
                "pass_rate": (totals["passed"] / totals["total"]) if totals["total"] else 0.0,
            }
            for split, totals in sorted(split_totals.items())
        },
        "skills": {
            skill: {
                "passed": totals["passed"],
                "total": totals["total"],
                "pass_rate": (totals["passed"] / totals["total"]) if totals["total"] else 0.0,
            }
            for skill, totals in sorted(skill_totals.items())
        },
    }


def print_eval_report(report: dict[str, object]) -> None:
    print(f"Runs per query: {report['runs']}, threshold: {report['threshold']}")
    print("Split summary:")
    for split, summary in report["splits"].items():
        print(f"- {split}: {summary['passed']}/{summary['total']} passed ({summary['pass_rate']:.2%})")
    print("Skill summary:")
    for skill, summary in report["skills"].items():
        print(f"- {skill}: {summary['passed']}/{summary['total']} passed ({summary['pass_rate']:.2%})")
    print("Per-query results:")
    for row in report["queries"]:
        print(
            f"- [{row['split']}] {row['skill']} should_trigger={row['should_trigger']} "
            f"rate={row['trigger_rate']:.2%} passed={row['passed']} :: {row['query']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint and evaluate skill descriptions.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root (default: current repo)")
    parser.add_argument("--dataset", help="Path to a JSON description-trigger dataset")
    parser.add_argument("--runner", help="Shell command template for executing a query; supports {query} and {skill}")
    parser.add_argument(
        "--detector",
        default="claude-code-json",
        choices=("claude-code-json", "substring", "regex"),
        help="How to detect whether the target skill triggered",
    )
    parser.add_argument("--pattern", help="Pattern used by substring/regex detectors; supports {skill}")
    parser.add_argument("--runs", type=int, default=3, help="How many runs to execute per query")
    parser.add_argument("--threshold", type=float, default=0.5, help="Minimum trigger-rate threshold for a pass")
    parser.add_argument("--json", action="store_true", help="Print reports as JSON")
    parser.add_argument(
        "--skip-lint",
        action="store_true",
        help="Skip static linting and only validate/evaluate the dataset",
    )
    args = parser.parse_args()

    try:
        root = Path(args.root).resolve()
        lint_report = None
        if not args.skip_lint:
            lint_report = lint_skills(root)
            if args.json:
                print(json.dumps({"lint": lint_report}, indent=2))
            else:
                print_lint_report(lint_report)
            if lint_report["error_count"]:
                return 1

        if not args.dataset:
            return 0

        skills = load_skill_descriptions(root)
        dataset = load_dataset(Path(args.dataset), skills)

        if not args.runner:
            if args.json:
                print(json.dumps({"dataset_entries": len(dataset)}, indent=2))
            else:
                print(f"Validated dataset with {len(dataset)} entries: {args.dataset}")
            return 0

        eval_report = evaluate_dataset(
            dataset=dataset,
            command_template=args.runner,
            detector=args.detector,
            pattern=args.pattern,
            runs=args.runs,
            threshold=args.threshold,
        )
        if args.json:
            print(json.dumps({"eval": eval_report}, indent=2))
        else:
            print_eval_report(eval_report)

        if any(not row["passed"] for row in eval_report["queries"]):
            return 1
        return 0
    except EvaluationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: could not parse runner output as JSON: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
