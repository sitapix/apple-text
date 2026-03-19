#!/usr/bin/env python3

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
AGENTS_DIR = ROOT / "agents"

SKILL_AGENT_DEPENDENCIES = {
    "text-audit": ["textkit-auditor.md"],
}


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def copy_path(source: Path, destination: Path) -> None:
    if destination.exists():
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()

    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install one or more Apple Text skills into a Claude home directory."
    )
    parser.add_argument("skills", nargs="+", help="Skill directory names to install")
    parser.add_argument(
        "--claude-home",
        default="~/.claude",
        help="Claude home directory (default: ~/.claude)",
    )
    parser.add_argument(
        "--without-dependent-agents",
        action="store_true",
        help="Do not install any agents associated with the selected skills",
    )

    args = parser.parse_args()

    claude_home = Path(args.claude_home).expanduser()
    target_skills_dir = claude_home / "skills"
    target_agents_dir = claude_home / "agents"
    target_skills_dir.mkdir(parents=True, exist_ok=True)

    installed_agents: set[str] = set()

    for skill_name in args.skills:
        source_dir = SKILLS_DIR / skill_name
        if not source_dir.is_dir():
            return fail(f"Unknown skill: {skill_name}")

        if not (source_dir / "SKILL.md").exists():
            return fail(f"{skill_name} is missing SKILL.md")

        destination_dir = target_skills_dir / skill_name
        copy_path(source_dir, destination_dir)
        print(f"Installed skill: {skill_name} -> {destination_dir}")

        if args.without_dependent_agents:
            continue

        for agent_file in SKILL_AGENT_DEPENDENCIES.get(skill_name, []):
            source_agent = AGENTS_DIR / agent_file
            if not source_agent.exists():
                return fail(f"Missing dependent agent for {skill_name}: {agent_file}")
            target_agents_dir.mkdir(parents=True, exist_ok=True)
            destination_agent = target_agents_dir / agent_file
            copy_path(source_agent, destination_agent)
            installed_agents.add(agent_file)

    if installed_agents:
        print("Installed dependent agents:")
        for agent_file in sorted(installed_agents):
            print(f"- {agent_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
