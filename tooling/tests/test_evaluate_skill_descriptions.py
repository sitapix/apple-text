import json
import tempfile
import unittest
from pathlib import Path

from scripts.quality import evaluate_skill_descriptions as desc_eval


def write(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


class EvaluateSkillDescriptionsTests(unittest.TestCase):
    def make_repo(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        write(
            root / "skills" / "example-skill" / "SKILL.md",
            """---
name: example-skill
description: Use when the user needs exact example-skill API details or migration guidance.
license: MIT
---

# Example
""",
        )
        return root

    def test_lint_flags_label_style_descriptions(self) -> None:
        root = self.make_repo()
        write(
            root / "skills" / "label-skill" / "SKILL.md",
            """---
name: label-skill
description: TextKit complete reference
license: MIT
---

# Label
""",
        )

        report = desc_eval.lint_skills(root)
        self.assertEqual(report["error_count"], 1)
        result = next(item for item in report["results"] if item["skill"] == "label-skill")
        messages = [issue["message"] for issue in result["issues"]]
        self.assertTrue(any("should start with 'Use when'" in message for message in messages))

    def test_parse_front_matter_unquotes_scalar_values(self) -> None:
        root = self.make_repo()
        write(
            root / "skills" / "quoted-skill" / "SKILL.md",
            """---
name: quoted-skill
description: "Use when the user needs exact API details: migration and validation."
license: MIT
---

# Quoted
""",
        )

        skills = desc_eval.load_skill_descriptions(root)
        self.assertEqual(
            skills["quoted-skill"]["description"],
            "Use when the user needs exact API details: migration and validation.",
        )

    def test_load_dataset_rejects_unknown_split(self) -> None:
        root = self.make_repo()
        dataset_path = root / "evals.json"
        dataset_path.write_text(
            json.dumps(
                [
                    {
                        "skill": "example-skill",
                        "query": "help",
                        "should_trigger": True,
                        "split": "dev",
                    }
                ]
            ),
            encoding="utf-8",
        )

        with self.assertRaises(desc_eval.EvaluationError):
            desc_eval.load_dataset(dataset_path, desc_eval.load_skill_descriptions(root))

    def test_evaluate_dataset_with_fake_claude_json_runner(self) -> None:
        root = self.make_repo()
        runner = root / "fake_runner.py"
        write(
            runner,
            """#!/usr/bin/env python3
import json
import sys

query = sys.argv[1]
skill = sys.argv[2]
if "trigger" in query:
    payload = {"messages": [{"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": skill}}]}]}
else:
    payload = {"messages": [{"content": [{"type": "text", "text": "no skill"}]}]}
print(json.dumps(payload))
""",
        )
        runner.chmod(0o755)

        dataset = [
            {"skill": "example-skill", "query": "please trigger this", "should_trigger": True, "split": "train"},
            {"skill": "example-skill", "query": "do not use anything", "should_trigger": False, "split": "validation"},
        ]

        report = desc_eval.evaluate_dataset(
            dataset=dataset,
            command_template=f"python3 {runner} {{query}} {{skill}}",
            detector="claude-code-json",
            pattern=None,
            runs=1,
            threshold=0.5,
        )

        self.assertEqual(report["splits"]["train"]["pass_rate"], 1.0)
        self.assertEqual(report["splits"]["validation"]["pass_rate"], 1.0)
        self.assertTrue(all(row["passed"] for row in report["queries"]))


if __name__ == "__main__":
    unittest.main()
