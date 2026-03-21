#!/usr/bin/env python3

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[3]
KIND_SPECS_PATH = ROOT / "tooling" / "config" / "skill-kinds.json"
CATEGORY_SPECS_PATH = ROOT / "tooling" / "config" / "skill-categories.json"
PROMINENT_ENTRYPOINT_PRIORITY = 2
KIND_SPECS = json.loads(KIND_SPECS_PATH.read_text(encoding="utf-8"))
CATEGORY_SPECS = json.loads(CATEGORY_SPECS_PATH.read_text(encoding="utf-8"))
KIND_ORDER = tuple(spec["key"] for spec in KIND_SPECS)
KIND_TITLES = {spec["key"]: spec["title"] for spec in KIND_SPECS}
KIND_DESCRIPTIONS = {spec["key"]: spec["description"] for spec in KIND_SPECS}
KIND_BADGE_VARIANTS = {spec["key"]: spec["badge_variant"] for spec in KIND_SPECS}
CATEGORY_ORDER = tuple(spec["key"] for spec in CATEGORY_SPECS)
CATEGORY_TITLES = {spec["key"]: spec["title"] for spec in CATEGORY_SPECS}
CATEGORY_DESCRIPTIONS = {spec["key"]: spec["description"] for spec in CATEGORY_SPECS}
ENTRYPOINT_ROLE_BLURBS = {
    "router": "Best when the request is broad and the right specialist is not obvious yet.",
    "workflow": "Best when the user wants a guided scan or implementation flow.",
    "diag": "Best when something is broken and symptoms are the starting point.",
    "decision": "Best when the main task is choosing the right API, view, or architecture.",
    "ref": "Best when the subsystem is already known and the user needs mechanics or API detail.",
}


def load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def docs_root(root: Path) -> Path:
    return root / "docs" / "src" / "content" / "docs"


def discover_sidecars(skill_dir: Path) -> List[str]:
    return sorted(path.name for path in skill_dir.glob("*.md") if path.name != "SKILL.md")


def normalize_front_matter_scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_front_matter(path: Path) -> Dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise RuntimeError(f"{path} is missing opening front matter delimiter")

    try:
        _, front_matter, _ = text.split("---\n", 2)
    except ValueError as exc:
        raise RuntimeError(f"{path} is missing closing front matter delimiter") from exc

    data: Dict[str, str] = {}
    current_key: Optional[str] = None
    block_lines: List[str] = []

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
            raise RuntimeError(f"{path} has malformed front matter line: {raw_line}")

        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value in {"|", ">", ""}:
            current_key = key
            block_lines = []
        else:
            data[key] = normalize_front_matter_scalar(value)

    if current_key is not None:
        data[current_key] = "\n".join(block_lines).strip()

    return data


def split_document(path: Path) -> Tuple[Dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    metadata = parse_front_matter(path)
    _, _, body = text.split("---\n", 2)
    return metadata, body.strip()


def sentence(text: str) -> str:
    cleaned = " ".join(text.split())
    return cleaned if cleaned.endswith(".") else cleaned + "."


def summarize_description(text: str) -> str:
    first_paragraph = text.strip().split("\n\n", 1)[0]
    return sentence(first_paragraph)


def table_description(text: str) -> str:
    """Shorter description for table cells — text before em dash."""
    if " \u2014 " in text:
        return text.split(" \u2014 ", 1)[0] + "."
    return text


def strip_sidecar_links(body: str) -> str:
    """Convert sidecar file markdown links to inline code references.

    SKILL.md bodies link sidecars as [file.md](file.md). When rendered
    inline in a docs page the target does not exist, so replace with `file.md`.
    """
    return re.sub(r"\[([a-z][a-z0-9-]*\.md)\]\(\1\)", r"`\1`", body)


def mdx_escape_body(body: str) -> str:
    """Escape generic type brackets (e.g. Range<String.Index>) in prose for MDX.

    MDX treats bare <Uppercase...> as JSX tags. This escapes those
    occurrences outside of fenced code blocks and inline code spans.
    """
    lines = body.split("\n")
    result = []
    in_fence = False

    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            result.append(line)
            continue

        if in_fence:
            result.append(line)
            continue

        # Split by inline code spans to avoid escaping inside backticks
        parts = re.split(r"(`[^`]*`)", line)
        escaped = []
        for part in parts:
            if part.startswith("`") and part.endswith("`") and len(part) > 1:
                escaped.append(part)
            else:
                escaped.append(re.sub(r"<(?=[A-Z])", r"&lt;", part))
        result.append("".join(escaped))

    return "\n".join(result)


def body_without_leading_h1(body: str) -> str:
    """Remove leading H1 and trailing related-skills section.

    The H1 duplicates the page title and the trailing related-skills
    section is replaced by auto-generated links from catalog.json.
    """
    lines = body.split("\n")
    if lines and lines[0].startswith("# "):
        lines = lines[1:]

    # Find and remove trailing related-skills section
    cut = None
    for i, line in enumerate(lines):
        if line.strip() in {"## Related Skills", "## Related"}:
            # Only cut if there are no further H2 sections after this one
            has_later_h2 = any(
                ln.startswith("## ") and ln.strip() not in {"## Related Skills", "## Related"}
                for ln in lines[i + 1 :]
            )
            if not has_later_h2:
                cut = i
                break
    if cut is not None:
        lines = lines[:cut]

    return "\n".join(lines).strip()


def skill_page_title(skill: Dict) -> str:
    for line in skill.get("body", "").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return skill["name"]


def render_skill_table(skills: List[Dict], scope: str) -> List[str]:
    """Render skills as a two-column markdown table."""
    lines = [
        "| Skill | When to Use |",
        "|-------|-------------|",
    ]
    for skill in skills:
        link = f"[`{skill['name']}`]({skill_doc_link(skill['name'], scope)})"
        desc = table_description(skill["description"]).replace("|", "\\|")
        lines.append(f"| {link} | {desc} |")
    lines.append("")
    return lines


def display_plugin_name(plugin_name: str) -> str:
    return plugin_name.replace("-", " ").title()


def source_repo_url(plugin: Dict, owner: str) -> str:
    return plugin.get("repository") or plugin.get("homepage") or f"https://github.com/{owner}/{plugin['name']}"


def agent_skills_install_snippet(plugin: Dict, owner: str, command_name: str) -> List[str]:
    repo_url = source_repo_url(plugin, owner)
    return [
        "```bash",
        f"git clone {repo_url}",
        f"cd {plugin['name']}",
        "```",
        "",
        "Use this path when your client can discover skills from a cloned repo or workspace.",
        "",
        f"If that client exposes commands, start with `/{command_name}` for broad Apple text questions.",
        "",
        "If it only loads direct skills, open the matching Apple Text skill or copy one focused skill into your local skills folder.",
        "",
    ]


def selective_skill_install_snippet(skill_name: str) -> List[str]:
    return [
        "```bash",
        "mkdir -p /path/to/your/project/.agents/skills",
        f"cp -R skills/{skill_name} /path/to/your/project/.agents/skills/",
        "```",
        "",
    ]


def render_retro_wordmark_html(title: str) -> str:
    safe_title = html.escape(title)
    return "".join(
        [
            f'<span class="retro-wordmark" aria-label="{safe_title}">',
            f'<span class="sr-only">{safe_title}</span>',
            '<span class="retro-letter retro-fill-1" aria-hidden="true">A</span>',
            '<span class="retro-letter retro-fill-2" aria-hidden="true">p</span>',
            '<span class="retro-letter retro-fill-3" aria-hidden="true">p</span>',
            '<span class="retro-letter retro-fill-4" aria-hidden="true">l</span>',
            '<span class="retro-letter retro-fill-5" aria-hidden="true">e</span>',
            '<span class="retro-space" aria-hidden="true">&nbsp;</span>',
            '<span class="retro-letter retro-fill-1" aria-hidden="true">T</span>',
            '<span class="retro-letter retro-fill-2" aria-hidden="true">e</span>',
            '<span class="retro-letter retro-fill-3" aria-hidden="true">x</span>',
            '<span class="retro-letter retro-fill-4" aria-hidden="true">t</span>',
            '</span>',
        ]
    )


def with_doc_frontmatter(
    title: str,
    body: str,
    description: Optional[str] = None,
    extra_frontmatter: Optional[List[str]] = None,
) -> str:
    lines = [
        "---",
        f"title: {json.dumps(title)}",
    ]
    if description:
        lines.append(f"description: {json.dumps(description)}")
    if extra_frontmatter:
        lines.extend(extra_frontmatter)
    lines.extend(
        [
            "---",
            "",
            body.strip(),
            "",
        ]
    )
    return "\n".join(lines)


def load_skill_entries(root: Path) -> List[Dict]:
    catalog = load_json(root / "skills" / "catalog.json")
    skills = []
    for entry in catalog["skills"]:
        skill_path = root / "skills" / entry["name"] / "SKILL.md"
        metadata, body = split_document(skill_path)
        merged = dict(entry)
        merged["sidecars"] = discover_sidecars(skill_path.parent)
        merged["description"] = summarize_description(metadata["description"])
        merged["full_description"] = sentence(metadata["description"])
        merged["license"] = metadata["license"]
        merged["path"] = skill_path
        merged["body"] = body
        merged["source"] = skill_path.read_text(encoding="utf-8").rstrip()
        skills.append(merged)
    return skills


def load_commands(root: Path, plugin_name: str) -> List[Dict]:
    commands = []
    for path in sorted((root / "commands").glob("*.md")):
        metadata = parse_front_matter(path)
        commands.append(
            {
                "name": f"{plugin_name}:{path.stem}",
                "description": summarize_description(metadata["description"]),
                "path": path,
            }
        )
    return commands


def load_agents(root: Path) -> List[Dict]:
    agents = []
    for path in sorted((root / "agents").glob("*.md")):
        metadata = parse_front_matter(path)
        agents.append(
            {
                "name": metadata["name"],
                "description": summarize_description(metadata["description"]),
                "path": path,
            }
        )
    return agents


def prominent_skills(skills: List[Dict]) -> List[Dict]:
    return sorted(
        [skill for skill in skills if skill["entrypoint_priority"] <= PROMINENT_ENTRYPOINT_PRIORITY],
        key=lambda skill: (skill["entrypoint_priority"], skill["name"]),
    )


def front_door_skills(skills: List[Dict]) -> List[Dict]:
    featured = prominent_skills(skills)
    docs_search_skill = find_skill(skills, "apple-text-apple-docs")
    if docs_search_skill is not None and docs_search_skill not in featured:
        featured = [*featured, docs_search_skill]
    return featured


def grouped_skills(skills: List[Dict]) -> List[Tuple[str, List[Dict]]]:
    groups = []
    for kind in KIND_ORDER:
        members = sorted(
            [skill for skill in skills if skill["kind"] == kind],
            key=lambda skill: (skill["entrypoint_priority"], skill["name"]),
        )
        groups.append((kind, members))
    return groups


def grouped_skills_by_category(skills: List[Dict]) -> List[Tuple[str, List[Dict]]]:
    groups = []
    for category in CATEGORY_ORDER:
        members = sorted(
            [skill for skill in skills if skill.get("category") == category],
            key=lambda skill: (skill["entrypoint_priority"], skill["name"]),
        )
        if members:
            groups.append((category, members))
    return groups


def entrypoint_summary(skill: Dict) -> str:
    return table_description(skill["description"])


def role_anchor(kind: str) -> str:
    return KIND_TITLES[kind].lower().replace(" ", "-")


def family_anchor(category: str) -> str:
    return category


def specialist_entry_skills(skills: List[Dict]) -> List[Dict]:
    return sorted(
        [
            skill
            for skill in skills
            if skill["entrypoint_priority"] == PROMINENT_ENTRYPOINT_PRIORITY + 1
            and skill["kind"] in {"workflow", "diag", "decision"}
        ],
        key=lambda skill: (skill["kind"], skill["name"]),
    )


def top_decision_skills(skills: List[Dict], limit: int = 3) -> List[Dict]:
    decisions = sorted(
        [
            skill
            for skill in skills
            if skill["kind"] == "decision" and skill["entrypoint_priority"] <= PROMINENT_ENTRYPOINT_PRIORITY + 1
        ],
        key=lambda skill: (skill["entrypoint_priority"], skill["name"]),
    )
    return decisions[:limit]


def find_skill(skills: List[Dict], name: str) -> Optional[Dict]:
    for skill in skills:
        if skill["name"] == name:
            return skill
    return None


def top_skill_of_kind(skills: List[Dict], kind: str) -> Optional[Dict]:
    matches = [skill for skill in skills if skill["kind"] == kind]
    if not matches:
        return None
    return sorted(matches, key=lambda skill: (skill["entrypoint_priority"], skill["name"]))[0]


# Set once by generated_docs(); matches the Astro `base` config.
_BASE = ""


def skill_doc_link(skill_name: str, scope: str) -> str:
    if scope not in {"root", "skills", "guide", "skill"}:
        raise ValueError("Unknown scope: " + scope)
    return f"{_BASE}/skills/{skill_name}/"


def docs_page_link(route: str, scope: str) -> str:
    prefixes = {
        "root": "",
        "skills": "",
        "guide": "guide/",
    }
    if scope not in prefixes:
        raise ValueError("Unknown scope: " + scope)
    return f"{_BASE}/{prefixes[scope]}{route.strip('/')}/"


def linked_skill_line(skill: Dict, scope: str) -> str:
    return f"- [`{skill['name']}`]({skill_doc_link(skill['name'], scope)}): {skill['description']}"


def render_skill_list(skills: List[Dict], scope: str) -> List[str]:
    lines = [linked_skill_line(skill, scope) for skill in skills]
    lines.append("")
    return lines


def render_family_skill_table(skills: List[Dict], scope: str) -> List[str]:
    lines = [
        "| Skill | Role | When to Use |",
        "|-------|------|-------------|",
    ]
    for skill in skills:
        link = f"[`{skill['name']}`]({skill_doc_link(skill['name'], scope)})"
        role = KIND_TITLES.get(skill["kind"], skill["kind"]).replace(" Skills", "")
        desc = table_description(skill["description"]).replace("|", "\\|")
        lines.append(f"| {link} | {role} | {desc} |")
    lines.append("")
    return lines


def render_code_component(source_var: str, language: str, title: str) -> str:
    return f'<Code code={{{source_var}}} lang={{{json.dumps(language)}}} title={{{json.dumps(title)}}} />'


def render_linkcard_grid_mdx(
    cards: List[Tuple[str, str] | Tuple[str, str, str]],
    stagger: bool = False,
) -> List[str]:
    opening = "<CardGrid stagger={true}>" if stagger else "<CardGrid>"
    lines = [opening, ""]

    for card in cards:
        title, href = card[0], card[1]
        description = card[2] if len(card) > 2 else None
        props = [
            f"title={{{json.dumps(title)}}}",
            f"href={{{json.dumps(href)}}}",
        ]
        if description is not None:
            props.append(f"description={{{json.dumps(description)}}}")
        lines.append(f"  <LinkCard {' '.join(props)} />")
        lines.append("")

    lines.extend(
        [
            "</CardGrid>",
            "",
        ]
    )
    return lines


def indent_lines(lines: List[str], prefix: str = "    ") -> List[str]:
    return [f"{prefix}{line}" if line else "" for line in lines]


def example_prompts() -> List[str]:
    return [
        '"My UITextView fell back to TextKit 1"',
        '"Which text view should I use?"',
        '"How do I wrap UITextView in SwiftUI?"',
        '"Audit this editor for anti-patterns"',
        '"What changed in Apple\'s latest styled text editing docs?"',
        '"How do I use TextEditor with AttributedString in iOS 26?"',
    ]


def project_status_note() -> List[str]:
    return [
        "> Status: Apple Text is still in an early phase. Some routes, docs, or packaging paths may still be incomplete or wrong. If you hit a bug or something looks off, please open an issue. Feedback is welcome too.",
        "",
    ]


def render_readme(plugin: Dict, marketplace: Dict, skills: List[Dict], commands: List[Dict], agents: List[Dict]) -> str:
    plugin_title = display_plugin_name(plugin["name"])
    owner = marketplace["owner"]["name"]
    command_name = commands[0]["name"] if commands else f"{plugin['name']}:ask"
    docs_search_skill = find_skill(skills, "apple-text-apple-docs")
    family_groups = grouped_skills_by_category(skills)

    lines = [
        f"# {plugin_title}",
        "",
        "Deep text-system expertise for AI coding assistants. Covers TextKit 1 and 2, UITextView, NSTextView, attributed strings, text input, Core Text, Writing Tools, and everything in between.",
        "",
        "## What is Apple Text?",
        "",
        "Apple Text gives AI coding assistants focused guidance on Apple's text rendering and editing stack, including TextKit behavior, text view selection, attributed text, layout, and Writing Tools integration.",
        "",
        f"- **{len(skills)} focused text skills** covering TextKit, views, formatting, storage, input, layout, accessibility, and more",
        f"- **{len(agents)} agent** for autonomous code auditing (fallback triggers, editing lifecycle bugs, deprecated APIs)",
        f"- **{len(commands)} command** for plain-language text questions",
        "",
    ]
    lines.extend(project_status_note())
    lines.extend(
        [
        "## Quick Start",
        "",
        "Apple Text is one collection with three practical entry points:",
        "",
        f"- **Claude Code plugin** for the native `/plugin` and `/{command_name}` flow",
        "- **MCP server** for VS Code, Cursor, Gemini CLI, Claude Desktop, and similar clients",
        "- **Xcode via MCP** for Claude Agent or Codex inside Xcode",
        "",
        "### 1. Add the Marketplace",
        "",
        "```bash",
        f"/plugin marketplace add {owner}/{plugin['name']}",
        "```",
        "",
        "### 2. Install the Plugin",
        "",
        "Use `/plugin` to open the plugin menu, search for `apple-text`, then install it.",
        "",
        "### 3. Verify Installation",
        "",
        "Use `/plugin`, then open `Manage and install`. Apple Text should be listed there.",
        "",
        "### 4. Use Skills",
        "",
        "Skills are suggested automatically in Claude Code based on your question and context. Start with prompts like these:",
        "",
        "```",
        *example_prompts(),
        "```",
        "",
        f"The default starting point for broad questions is `/{command_name}`.",
        "",
        "```",
        f"/{command_name} your question here",
        "```",
        "",
        "## Other Ways to Use Apple Text",
        "",
        "### Xcode Via MCP",
        "",
        f"For Claude Agent or Codex inside Xcode, use the dedicated [Xcode integration guide](https://{owner}.github.io/{plugin['name']}/guide/xcode-integration/).",
        "",
        "Run Apple Text for text-system guidance and `xcrun mcpbridge` alongside it if you also want Xcode actions.",
        "",
        "### Repo Clone For Agent Skills Clients",
        "",
    ]
    )
    lines.extend(agent_skills_install_snippet(plugin, owner, command_name))
    lines.extend(
        [
        "### Standalone MCP Server",
        "",
        "If your coding tool supports Model Context Protocol, use the standalone MCP package in `mcp-server/`.",
        "",
        f"Setup and client configuration examples for Claude Desktop, Cursor, VS Code, and Gemini CLI are in [`mcp-server/README.md`](https://github.com/{owner}/{plugin['name']}/blob/main/mcp-server/README.md).",
        "",
        "### Copy Specific Skills Elsewhere",
        "",
        ]
    )
    lines.extend(selective_skill_install_snippet("apple-text-views"))
    lines.extend(
        [
        "",
        "## Troubleshooting",
        "",
        "- If Apple Text does not appear after install, use `/plugin` and check `Manage and install` first.",
        f"- If `/{command_name}` is unavailable, confirm the plugin is installed from the marketplace flow above.",
        "",
        "## Start Here",
        "",
    ]
    )

    featured = front_door_skills(skills)
    for skill in featured:
        lines.append(f"- **`/skill {skill['name']}`** — {entrypoint_summary(skill)}")
    if docs_search_skill is not None and docs_search_skill not in featured:
        lines.append(f"- **`/skill {docs_search_skill['name']}`** — {entrypoint_summary(docs_search_skill)}")

    lines.extend([
        "",
        "## Skill Families",
        "",
        "Choose the topic family first. The skill role (`router`, `workflow`, `diag`, `decision`, `ref`) is the second pass.",
        "",
    ])
    for category, members in family_groups:
        skill_names = ", ".join(f"`/skill {skill['name']}`" for skill in members)
        lines.append(
            f"- **{CATEGORY_TITLES[category]}** — {CATEGORY_DESCRIPTIONS[category]} Includes {skill_names}."
        )

    lines.extend([
        "",
        "## Documentation",
        "",
        f"Full documentation, skill catalog, MCP setup, and Xcode integration guides are at [{owner}.github.io/{plugin['name']}](https://{owner}.github.io/{plugin['name']}/).",
        "",
        "## Acknowledgments",
        "",
        "Apple Text was inspired by [Axiom](https://github.com/CharlesWiltgen/Axiom) by Charles Wiltgen, especially its packaging and documentation structure.",
        "",
        "## Contributing",
        "",
        f"Contributor setup, validation, and release notes live in [`.github/CONTRIBUTING.md`](https://github.com/{owner}/{plugin['name']}/blob/main/.github/CONTRIBUTING.md).",
        "",
    ])
    return "\n".join(lines)


def render_home(plugin: Dict, marketplace: Dict, skills: List[Dict], commands: List[Dict], agents: List[Dict]) -> str:
    plugin_title = display_plugin_name(plugin["name"])
    owner = marketplace["owner"]["name"]
    marketplace_name = marketplace["name"]
    command_name = commands[0]["name"] if commands else f"{plugin['name']}:ask"
    featured = front_door_skills(skills)
    audit_skill = top_skill_of_kind(skills, "workflow")

    lines = [
        'import { CardGrid, LinkCard } from "@astrojs/starlight/components";',
        "",
        '<div class="docs-intro">',
        "",
        '<p class="docs-eyebrow">Focused Apple text docs</p>',
        "",
        f'<p class="docs-lead">{plugin_title} helps route Apple text questions to the right skill or guide.</p>',
        "",
        "<p>It covers TextKit, UIKit and AppKit text views, attributed text, layout invalidation, editor behavior, and Writing Tools.</p>",
        "",
        '<div class="docs-meta">',
        f'<span class="docs-chip">{len(skills)} skills</span>',
        f'<span class="docs-chip">{len(commands)} command{"s" if len(commands) != 1 else ""}</span>',
        f'<span class="docs-chip">{len(agents)} agent{"s" if len(agents) != 1 else ""}</span>',
        "</div>",
        "",
        "</div>",
        "",
        *project_status_note(),
        "## Start Here",
        "",
        "Choose the shortest path that matches the client you are using. Apple Text is one collection, surfaced through plugin commands, MCP, and Xcode MCP.",
        "",
    ]
    start_cards = [
        ("Ask A Question", docs_page_link("commands", "root"), f"Start with `/{command_name}` for broad Apple text intake."),
        ("Use In Xcode", docs_page_link("guide/xcode-integration", "root"), "Configure Apple Text inside Xcode Claude Agent or Codex via MCP."),
        ("Browse Skills", docs_page_link("skills", "root"), "Browse the catalog when you already know the API family."),
        ("Review Editor Code", docs_page_link("agents", "root"), "Use the audit path when you want findings from real code."),
        ("Install", docs_page_link("setup", "root"), "Add the marketplace in Claude Code, install Apple Text, and verify it in Manage and install."),
        ("Use With MCP", docs_page_link("guide/mcp-server", "root"), "Connect Apple Text to generic MCP clients and start from `apple_text_route`."),
        ("Examples", docs_page_link("example-conversations", "root"), "See example prompts, routing, and answer shapes."),
        ("Guide", docs_page_link("guide", "root"), "Read the routing model for an overview of the entry points."),
    ]
    lines.extend(render_linkcard_grid_mdx(start_cards, stagger=True))
    if audit_skill is not None:
        lines.extend(
            [
                f"> For findings-first review work, start with [`{audit_skill['name']}`]({skill_doc_link(audit_skill['name'], 'root')}) or the [Agents]({docs_page_link('agents', 'root')}) page.",
                "",
            ]
        )
    lines.extend(
        [
            "## Front Doors",
            "",
            "These are the main entry points.",
            "",
        ]
    )

    lines.extend(
        render_linkcard_grid_mdx(
            [(skill["name"], skill_doc_link(skill["name"], "root"), entrypoint_summary(skill)) for skill in featured]
        )
    )
    lines.extend(
        [
            "## Install Fast",
            "",
            "Pick the surface first, then use the matching front door:",
            "",
            f"- **Claude Code plugin** -> install from the marketplace, then start with `/{command_name}`",
            "- **Generic MCP client** -> connect Apple Text MCP, then start with `apple_text_route`",
            "- **Xcode Claude Agent or Codex** -> connect the MCP server inside Xcode, then use the same route-first MCP flow",
            "",
            "Claude Code plugin install is the default path:",
            "",
            "```bash",
            f"/plugin marketplace add {owner}/{plugin['name']}",
            "```",
            "",
            "Use `/plugin` to open the plugin menu, search for `apple-text`, and install it.",
            "",
            "Use `/plugin`, then open `Manage and install`, to verify that Apple Text is installed.",
            "",
            "Clone the repo only when you want to load Apple Text through a local checkout:",
            "",
        ]
    )
    lines.extend(agent_skills_install_snippet(plugin, owner, command_name))
    lines.extend(
        [
            "Marketplace install is also supported:",
            "",
            "```bash",
            f"/plugin marketplace add {owner}/{plugin['name']}",
            f"/plugin install {plugin['name']}@{marketplace_name}",
            "```",
            "",
            "If you only want a subset in another workspace, copy a focused skill instead of the whole collection:",
            "",
        ]
    )
    lines.extend(selective_skill_install_snippet("apple-text-views"))
    lines.extend(
        [
            "## Why This Exists",
            "",
            "Apple text-system work often spans several frameworks and abstractions. These docs keep TextKit, UIKit/AppKit text views, attributed text, layout invalidation, viewport rendering, and Writing Tools easy to find.",
            "",
        ]
    )
    return "\n".join(lines)


def render_setup_page(marketplace: Dict, plugin: Dict, commands: List[Dict], agents: List[Dict]) -> str:
    owner = marketplace["owner"]["name"]
    marketplace_name = marketplace["name"]
    command_name = commands[0]["name"] if commands else f"{plugin['name']}:ask"
    agent_note = agents[0]["name"] if agents else "the bundled specialist agent"

    lines = [
        "Use this page when you are installing Apple Text and choosing the fastest path into the skills.",
        "",
        "## Claude Code Quick Start",
        "",
        "Apple Text is one collection with multiple entry points. This page helps you pick the right installation surface first:",
        "",
        f"- **Claude Code plugin** -> native `/{command_name}` command flow",
        "- **Generic MCP client** -> `apple_text_route` plus `apple_text_read_skill`",
        "- **Xcode Claude Agent or Codex** -> Apple Text MCP inside Xcode, optionally alongside `xcrun mcpbridge`",
        "",
        "### 1. Add the Marketplace",
        "",
        "```bash",
        f"/plugin marketplace add {owner}/{plugin['name']}",
        "```",
        "",
        "### 2. Install the Plugin",
        "",
        "Use `/plugin` to open the plugin menu, search for `apple-text`, then install it.",
        "",
        "### 3. Verify Installation",
        "",
        "Use `/plugin`, then open `Manage and install`. Apple Text should be listed there.",
        "",
        "### 4. Start Using It",
        "",
        f"Use `/{command_name}` for broad Apple text intake, or browse [Skills]({docs_page_link('skills', 'root')}) when the subsystem is already clear.",
        "",
        "Good first prompts:",
        "",
        *[f"- {prompt}" for prompt in example_prompts()],
        "",
        "## Advanced Paths",
        "",
        "### Use The Repo Directly",
        "",
    ]
    lines.extend(agent_skills_install_snippet(plugin, owner, command_name))
    lines.extend(
        [
        "Pick this path when you want the full Apple Text collection available immediately.",
        "",
        "### Use The MCP Server",
        "",
        f"If your tool supports MCP, read [MCP Server]({docs_page_link('guide/mcp-server', 'root')}) for local setup and client configuration snippets. In MCP clients, start with `apple_text_route`, then follow the suggested `apple_text_read_skill` call.",
        "",
        f"For Xcode Claude Agent or Codex, use [Xcode Integration]({docs_page_link('guide/xcode-integration', 'root')}).",
        "",
        "### Copy Selected Skills",
        "",
        ]
    )
    lines.extend(selective_skill_install_snippet("apple-text-views"))
    lines.extend(
        [
        "Pick this path when you already know the subsystem and want a smaller local surface in another workspace.",
        "",
        "## What You Get",
        "",
        f"- **{len(commands)} command{'s' if len(commands) != 1 else ''}**: `/{command_name}` for plain-language questions.",
        f"- **{len(agents)} agent{'s' if len(agents) != 1 else ''}**: `{agent_note}` runs focused TextKit audits.",
        f"- **Skills**: browse the [full catalog]({docs_page_link('skills', 'root')}) or start from [problem routing]({docs_page_link('guide/problem-routing', 'root')}).",
        "",
        "## Troubleshooting",
        "",
        "- If Apple Text does not appear after install, use `/plugin` and check `Manage and install`.",
        f"- If `/{command_name}` is unavailable, confirm the plugin is installed from the marketplace flow above.",
        "",
        "## Read Next",
        "",
        f"- [Skills]({docs_page_link('skills', 'root')})",
        f"- [Commands]({docs_page_link('commands', 'root')})",
        f"- [Agents]({docs_page_link('agents', 'root')})",
        f"- [MCP Server]({docs_page_link('guide/mcp-server', 'root')})",
        f"- [Problem Routing]({docs_page_link('guide/problem-routing', 'root')})",
        "",
        ]
    )
    return "\n".join(lines)


def render_skills_overview(skills: List[Dict], commands: List[Dict]) -> str:
    featured = prominent_skills(skills)
    families = grouped_skills_by_category(skills)
    command_name = commands[0]["name"] if commands else "apple-text:ask"

    lines = [
        'import { CardGrid, LinkCard } from "@astrojs/starlight/components";',
        "",
        f"Apple Text ships {len(skills)} skills. This page is the canonical grouped catalog: choose the topic family first, then use each skill's role label to narrow further.",
        "",
        "## Start Here",
        "",
        f"If the user does not know the catalog yet, start with `/{command_name}`.",
        "",
    ]
    lines.extend(
        render_linkcard_grid_mdx(
            [(skill["name"], skill_doc_link(skill["name"], "skills")) for skill in featured],
            stagger=True,
        )
    )

    lines.extend(
        [
            "## Browse By Skill Family",
            "",
            "These sections group related skills by subsystem so SwiftUI wrappers, TextKit runtime issues, and rich-text modeling stop competing for the same slot.",
            "",
        ]
    )
    lines.extend(
        render_linkcard_grid_mdx(
            [
                (f"{CATEGORY_TITLES[category]} ({len(members)})", f"#{family_anchor(category)}")
                for category, members in families
            ]
        )
    )
    for category, members in families:
        lines.extend(
            [
                f"## {CATEGORY_TITLES[category]}",
                "",
                CATEGORY_DESCRIPTIONS[category],
                "",
            ]
        )
        lines.extend(render_family_skill_table(members, "skills"))

    lines.extend(
        [
            "## Need A Role-Based View?",
            "",
            f"Use [Problem Routing]({docs_page_link('guide/problem-routing', 'skills')}) when the answer shape is clearer than the subsystem and you want to scan routers, workflows, diagnostics, decisions, and references directly.",
            "",
        ]
    )

    lines.extend(
        [
            "## Read Next",
            "",
        ]
    )
    lines.extend(
        render_linkcard_grid_mdx(
            [
                ("Problem Routing", docs_page_link("guide/problem-routing", "skills")),
                ("Entry Points", docs_page_link("guide/entry-points", "skills")),
                ("Example Conversations", docs_page_link("example-conversations", "skills")),
            ]
        )
    )
    return "\n".join(lines)


def render_commands_page(root: Path, commands: List[Dict], skills: List[Dict]) -> str:
    router_skill = top_skill_of_kind(skills, "router")
    workflow_skill = top_skill_of_kind(skills, "workflow")
    diagnostic_skill = top_skill_of_kind(skills, "diag")
    decision_skill = top_skill_of_kind(skills, "decision")

    lines = [
        'import { CardGrid, LinkCard } from "@astrojs/starlight/components";',
        "",
        '<div class="docs-intro">',
        "",
        '<p class="docs-eyebrow">One front door</p>',
        "",
        "<p class=\"docs-lead\">Use the command surface when you know the question belongs to Apple text, but you do not want to pick the skill yourself.</p>",
        "",
        "<p>This page covers the main intake command and the routes it typically suggests.</p>",
        "",
        "</div>",
        "",
    ]

    for command in commands:
        lines.extend(
            [
                f"## `/{command['name']}`",
                "",
                command["description"],
                "",
                '<div class="docs-spec-grid">',
                "",
                '<div class="docs-spec-card">',
                '<p class="docs-section-label">Good prompts</p>',
                "<ul>",
                "<li>broad Apple text questions</li>",
                "<li>first-contact prompts that mention symptoms instead of APIs</li>",
                "<li>mixed requests where routing matters more than memorizing the catalog</li>",
                "</ul>",
                "",
                "</div>",
                "",
                '<div class="docs-spec-card">',
                '<p class="docs-section-label">Skip this when</p>',
                "",
                "<ul>",
                "<li>the user already named the exact subsystem</li>",
                "<li>you are already on a matching skill page</li>",
                "<li>the task is a findings-first scan over real code</li>",
                "</ul>",
                "",
                "</div>",
                "",
                "</div>",
                "",
                "## Typical routes",
                "",
            ]
        )
        route_cards = []
        if router_skill is not None:
            route_cards.append(
                (
                    router_skill["name"],
                    skill_doc_link(router_skill["name"], "root"),
                    "Broad questions route here first.",
                )
            )
        if workflow_skill is not None:
            route_cards.append(
                (
                    workflow_skill["name"],
                    skill_doc_link(workflow_skill["name"], "root"),
                    "Review or integration flows usually land here.",
                )
            )
        if diagnostic_skill is not None:
            route_cards.append(
                (
                    diagnostic_skill["name"],
                    skill_doc_link(diagnostic_skill["name"], "root"),
                    "Broken behavior routes into diagnosis.",
                )
            )
        if decision_skill is not None:
            route_cards.append(
                (
                    decision_skill["name"],
                    skill_doc_link(decision_skill["name"], "root"),
                    "Tradeoff questions route into comparison.",
                )
            )
        lines.extend(render_linkcard_grid_mdx(route_cards))
        lines.extend(
            [
                "## Try prompts like these",
                "",
                '- "Why did my UITextView fall back to TextKit 1?"',
                '- "Review this editor code for TextKit problems."',
                '- "Should this screen use TextEditor or UITextView?"',
                "",
                "## Next move",
                "",
                f"If the prompt is already scoped, start with [Skills]({docs_page_link('skills', 'root')}). If the task is a specialist code scan, use [Agents]({docs_page_link('agents', 'root')}).",
                "",
            ]
        )
    return "\n".join(lines)


def render_agents_page(root: Path, agents: List[Dict], skills: List[Dict]) -> str:
    audit_skill = find_skill(skills, "apple-text-audit")

    lines = [
        'import { CardGrid, LinkCard } from "@astrojs/starlight/components";',
        "",
        '<div class="docs-intro">',
        "",
        '<p class="docs-eyebrow">Code review and audit agents</p>',
        "",
        "<p class=\"docs-lead\">Use an agent when you want findings, file references, and fix directions instead of a general explanation.</p>",
        "",
        f"<p>Apple Text currently ships {len(agents)} agent{'s' if len(agents) != 1 else ''}. Use this page when you want the agent surface directly.</p>",
        "",
        "</div>",
        "",
    ]

    for agent in agents:
        lines.extend(
            [
                f"## `{agent['name']}`",
                "",
                agent["description"],
                "",
                '<div class="docs-spec-grid">',
                "",
                '<div class="docs-spec-card">',
                '<p class="docs-section-label">Best for</p>',
                "<ul>",
                "<li>findings-first reviews of editor code</li>",
                "<li>scanning a codebase for TextKit anti-patterns</li>",
                "<li>focused audits where file references and fix directions matter</li>",
                "</ul>",
                "",
                "</div>",
                "",
                '<div class="docs-spec-card">',
                '<p class="docs-section-label">You get</p>',
                "",
                "<ul>",
                "<li>findings grouped by severity</li>",
                "<li>file references for each issue</li>",
                "<li>one concrete fix direction per finding</li>",
                "</ul>",
                "",
                "</div>",
                "",
                "</div>",
                "",
                '<p class="docs-section-label">Audit focus</p>',
                "",
                "- TextKit 1 fallback triggers",
                "- deprecated glyph and layout APIs",
                "- missing editing lifecycle calls",
                "- unsafe text storage patterns",
                "- Writing Tools compatibility problems",
                "",
            ]
        )
    if audit_skill is not None:
        lines.extend(
            [
                '<p class="docs-section-label">Default entry point</p>',
                "",
            ]
        )
        lines.extend(
            render_linkcard_grid_mdx(
                [
                    (
                        audit_skill["name"],
                        skill_doc_link(audit_skill["name"], "root"),
                        "Natural-language audit entry point for most review requests.",
                    ),
                    (
                        "Skills",
                        docs_page_link("skills", "root"),
                        "Browse the rest of the catalog when the work is not a code scan.",
                    ),
                ]
            )
        )
        lines.extend(
            [
                f"If the user just asked for a review in natural language, start with [`{audit_skill['name']}`]({skill_doc_link(audit_skill['name'], 'root')}). Reach for the agent page when you want a direct tool handoff instead.",
                "",
            ]
        )
    return "\n".join(lines)


def render_guide_index(skills: List[Dict]) -> str:
    skill_names = {skill["name"] for skill in skills}
    choice_names = [skill["name"] for skill in top_decision_skills(skills)]
    if "apple-text" in skill_names:
        broad_line = f"- Question is broad: start from `/apple-text:ask`. If you want the reasoning model first, read [Problem Routing]({docs_page_link('problem-routing', 'guide')})."
    else:
        broad_line = f"- Question is broad: read [Problem Routing]({docs_page_link('problem-routing', 'guide')})."

    debug_targets = [name for name in ("apple-text-textkit-diag", "apple-text-audit") if name in skill_names]
    if len(debug_targets) == 2:
        editor_line = f"- Editor is broken: jump to `/skill {debug_targets[0]}` or `/skill {debug_targets[1]}`."
    elif len(debug_targets) == 1:
        editor_line = f"- Editor is broken: jump to `/skill {debug_targets[0]}`."
    else:
        editor_line = f"- Editor is broken: start from [Problem Routing]({docs_page_link('problem-routing', 'guide')})."

    if len(choice_names) == 1:
        choice_line = f"- You need a choice: use `{choice_names[0]}`."
    elif len(choice_names) == 2:
        choice_line = f"- You need a choice: use `{choice_names[0]}` or `{choice_names[1]}`."
    elif len(choice_names) >= 3:
        choice_line = (
            f"- You need a choice: use `{choice_names[0]}`, `{choice_names[1]}`, "
            f"or `{choice_names[2]}`."
        )
    else:
        choice_line = f"- You need a choice: start from [Problem Routing]({docs_page_link('problem-routing', 'guide')})."

    lines = [
        'import { CardGrid, LinkCard, Steps } from "@astrojs/starlight/components";',
        "",
        "Use the guide when you need the routing model instead of a single command or skill page.",
        "",
        "Start here when you want a simple map from broad Apple text questions to the right specialist page.",
        "",
        "<Steps>",
        "",
        "1. Install Apple Text in Claude Code.",
        "2. Start from `/apple-text:ask` for a broad Apple text question.",
        "3. Open specialist skills only when the problem is clearly scoped.",
        "",
        "</Steps>",
        "",
        "## What Makes This Collection Different",
        "",
        "- It focuses on Apple text-system work.",
        "- It keeps UIKit, AppKit, TextKit, and SwiftUI text concerns visible.",
        "- It favors focused skills and diagnostics over giant catch-all documents.",
        "",
        "## What The Guide Helps You Do",
        "",
        "- Get from install to a good first answer quickly.",
        "- Route broad questions without explaining the whole catalog.",
        "- Understand when to use commands, skills, or the agent surface.",
        "",
        "## Fast Path",
        "",
        broad_line,
        editor_line,
        choice_line,
        "",
        "## Read Next",
        "",
    ]
    lines.extend(
        render_linkcard_grid_mdx(
            [
                ("Quick Start", docs_page_link("quick-start", "guide")),
                ("MCP Server", docs_page_link("mcp-server", "guide")),
                ("Xcode Integration", docs_page_link("xcode-integration", "guide")),
                ("Install", docs_page_link("install", "guide")),
                ("Routing Model", docs_page_link("routing-model", "guide")),
                ("Entry Points", docs_page_link("entry-points", "guide")),
                ("Problem Routing", docs_page_link("problem-routing", "guide")),
                ("Commands And Agents", docs_page_link("commands-and-agents", "guide")),
            ],
            stagger=True,
        )
    )
    return "\n".join(lines)


def render_quick_start(marketplace: Dict, plugin: Dict, skills: List[Dict], commands: List[Dict]) -> str:
    owner = marketplace["owner"]["name"]
    command_name = commands[0]["name"] if commands else f"{plugin['name']}:ask"
    featured = front_door_skills(skills)
    router_skill = top_skill_of_kind(skills, "router")
    workflow_skill = top_skill_of_kind(skills, "workflow")
    diagnostic_skill = top_skill_of_kind(skills, "diag")
    decision_skill = top_skill_of_kind(skills, "decision")

    lines = [
        'import { CardGrid, LinkCard, Steps } from "@astrojs/starlight/components";',
        "",
        '<div class="docs-intro">',
        "",
        '<p class="docs-eyebrow">Fastest path from install to first good answer</p>',
        "",
        "<p class=\"docs-lead\">Add the marketplace, install Apple Text in Claude Code, verify it, then ask one broad Apple text question.</p>",
        "",
        "<p>This page is a short path from installation to a first question.</p>",
        "",
        "</div>",
        "",
        "<Steps>",
        "",
        "1. **Add the marketplace**",
        "",
        "    ```bash",
        f"    /plugin marketplace add {owner}/{plugin['name']}",
        "    ```",
        "",
        "2. **Install the plugin**",
        "",
        "    Use `/plugin` to open the plugin menu, search for `apple-text`, then install it.",
        "",
        "3. **Verify installation**",
        "",
        "    Use `/plugin`, then open `Manage and install`. Apple Text should be listed there.",
        "",
        "4. **Ask one plain-language question**",
        "",
        f"    Start with `/{command_name}`.",
        "",
        "    Good first prompts:",
        "",
        *[f"    - {prompt}" for prompt in example_prompts()[:3]],
        "",
        "</Steps>",
        "",
        "## Advanced paths",
        "",
        "Clone the repo only when you want to load Apple Text through a local checkout:",
        "",
    ]
    lines.extend(agent_skills_install_snippet(plugin, owner, command_name))
    lines.extend(
        [
            "",
            "## Main entry points",
            "",
        ]
    )
    lines.extend(
        render_linkcard_grid_mdx(
            [(skill["name"], skill_doc_link(skill["name"], "guide"), entrypoint_summary(skill)) for skill in featured]
        )
    )
    lines.extend(
        [
            "## Route common prompts",
            "",
        ]
    )
    if router_skill is not None:
        lines.append(
            f'- "I have an Apple text problem but I do not know the subsystem yet." -> start with `/{command_name}`.'
        )
    if workflow_skill is not None:
        lines.append(
            f'- "Review this editor code for risks." -> start with [`{workflow_skill["name"]}`]({skill_doc_link(workflow_skill["name"], "guide")}).'
        )
    if diagnostic_skill is not None:
        lines.append(
            f'- "My layout is stale or TextKit fell back." -> start with [`{diagnostic_skill["name"]}`]({skill_doc_link(diagnostic_skill["name"], "guide")}).'
        )
    if decision_skill is not None:
        lines.append(
            f'- "Should this use TextEditor, UITextView, or NSTextView?" -> start with [`{decision_skill["name"]}`]({skill_doc_link(decision_skill["name"], "guide")}).'
        )
    lines.extend(
        [
            "## What next",
            "",
            f"- Read [Routing Model]({docs_page_link('routing-model', 'guide')}) if the question is still broad.",
            f"- Use [Problem Routing]({docs_page_link('problem-routing', 'guide')}) if you already know the answer shape.",
            f"- Browse [Skills]({docs_page_link('skills', 'root')}) if you want the full catalog.",
            "",
        ]
    )
    return "\n".join(lines)


def render_routing_model(skills: List[Dict], commands: List[Dict]) -> str:
    command_name = commands[0]["name"] if commands else "apple-text:ask"
    skill_names = {skill["name"] for skill in skills}
    routers = [skill for skill in skills if skill["kind"] == "router"]
    workflows = [skill for skill in skills if skill["kind"] == "workflow"]
    diagnostics = [skill for skill in skills if skill["kind"] == "diag"]
    decisions = top_decision_skills(skills)
    references = [skill for skill in skills if skill["kind"] == "ref"]

    lines = [
        "Use this page when you are routing a prompt and want a simple decision model instead of a full catalog scan.",
        "",
        "Apple Text uses progressive disclosure: start broad, then move to the narrowest skill that matches the job.",
        "",
        "## Routing Pattern",
        "",
        f"1. Start with `/{command_name}`.",
        "2. Decide whether the user needs a workflow, a diagnosis, a choice, or a reference.",
        "3. Open the narrowest skill that matches that answer shape.",
        "",
        "Do not memorize every skill name. Ask whether the prompt is broad, broken, comparative, or already scoped to a subsystem.",
        "",
        "## Mental Model",
        "",
    ]

    if routers:
        lines.extend(
            [
                f"- **Broad intake**: start with `/{command_name}`.",
                "Use this when the problem is clearly Apple text work but still mixed or underspecified.",
            ]
        )

    if workflows:
        lines.extend(
            [
                f"- **Guided flow or review**: start with `/skill {workflows[0]['name']}`.",
                "Use this when the user wants an audit, integration walkthrough, or step-by-step implementation path.",
            ]
        )

    if diagnostics:
        lines.extend(
            [
                f"- **Broken behavior**: start with `/skill {diagnostics[0]['name']}`.",
                "Use this when the user starts with stale layout, fallback, crashes, or rendering bugs.",
            ]
        )

    if decisions:
        decision_names = ", ".join(f"`{skill['name']}`" for skill in decisions[:3])
        lines.extend(
            [
                f"- **Tradeoff question**: use {decision_names}.",
                "Use this when the main job is picking the right API, architecture, or view.",
            ]
        )

    if references:
        lines.extend(
            [
                f"- **Known API family**: start with `/skill {references[0]['name']}` or the matching reference skill.",
                "Use this when the user already knows the subsystem and wants mechanics, behavior, or API detail.",
            ]
        )

    lines.extend(
        [
            "",
            "## Prompt Patterns",
            "",
            '- "Why is this editor broken?" -> diagnostic skill',
            '- "Review this code for risks." -> workflow skill',
            '- "Should I use A or B?" -> decision skill',
            '- "How does this Apple text API behave?" -> reference skill',
            "",
            "## Shortcuts",
            "",
        ]
    )
    if "apple-text" in skill_names:
        lines.append("- Broad Apple text question -> [`apple-text`](/skills/apple-text/)")
    if "apple-text-audit" in skill_names:
        lines.append("- Findings-first review -> [`apple-text-audit`](/skills/apple-text-audit/)")
    if "apple-text-textkit-diag" in skill_names:
        lines.append("- Debugging a broken editor -> [`apple-text-textkit-diag`](/skills/apple-text-textkit-diag/)")
    if "apple-text-views" in skill_names:
        lines.append("- Choosing among text stacks -> [`apple-text-views`](/skills/apple-text-views/)")
    lines.extend(
        [
            "",
            "## Read Next",
            "",
            f"- [Quick Start]({docs_page_link('quick-start', 'guide')})",
            f"- [Entry Points]({docs_page_link('entry-points', 'guide')})",
            f"- [Problem Routing]({docs_page_link('problem-routing', 'guide')})",
            "",
        ]
    )
    return "\n".join(lines)


def render_entry_points(skills: List[Dict], commands: List[Dict]) -> str:
    featured = front_door_skills(skills)
    specialists = specialist_entry_skills(skills)
    command = commands[0] if commands else None
    router_skill = top_skill_of_kind(skills, "router")
    router_name = router_skill["name"] if router_skill is not None else "apple-text"

    lines = [
        "These are the main entry points.",
        "",
        "> Start with the smallest entry point that matches the request.",
        "",
    ]

    if command is not None:
        lines.extend(
            [
                f"## `/{command['name']}`",
                "",
                command["description"],
                "",
                "Good for:",
                "",
                "- plain-language prompts",
                "- first-contact questions",
                "- mixed symptoms where the right skill is not obvious yet",
                "",
            ]
        )

    lines.extend(["## Prominent Skills", ""])
    for skill in featured:
        lines.extend(
            [
                f"### [`{skill['name']}`]({skill_doc_link(skill['name'], 'guide')})",
                "",
                skill["description"],
                "",
                "Best first move:",
                "",
                f"- {ENTRYPOINT_ROLE_BLURBS.get(skill['kind'], entrypoint_summary(skill))}",
                "",
            ]
        )

    lines.extend(
        [
            "## Direct Specialist Skills",
            "",
            "These are the next stop once the request is already scoped:",
            "",
        ]
    )
    lines.extend(render_skill_list(specialists, "guide"))
    return "\n".join(lines)


def render_problem_routing(skills: List[Dict]) -> str:
    groups = grouped_skills(skills)
    featured = prominent_skills(skills)

    lines = [
        'import { CardGrid, LinkCard } from "@astrojs/starlight/components";',
        "",
        f"Use this page when you know the answer shape but not the exact skill name. If the subsystem is already clear, use the [Skills]({docs_page_link('skills', 'root')}) page for topic families instead.",
        "",
        "## Start Here",
        "",
    ]
    lines.extend(render_skill_list(featured, "guide"))
    lines.extend(
        render_linkcard_grid_mdx(
            [
                (KIND_TITLES[kind], f"#{role_anchor(kind)}")
                for kind, members in groups
                if members
            ]
        )
    )
    lines.extend(["## Route By Answer Type", ""])

    for kind, members in groups:
        example = members[0]["name"] if members else "apple-text"
        lines.extend(
            [
                f"### {KIND_TITLES[kind]}",
                "",
                KIND_DESCRIPTIONS[kind],
                "",
                f"Example route: `/skill {example}`",
                "",
            ]
        )
        lines.extend(render_skill_list(members, "guide"))

    return "\n".join(lines)


def render_commands_and_agents(root: Path, commands: List[Dict], agents: List[Dict]) -> str:
    lines = [
        f"{len(commands)} command and {len(agents)} agent.",
        "",
        "Use commands for broad questions. Use agents for specialist scans over real code.",
        "",
        "## Commands",
        "",
    ]

    for command in commands:
        lines.extend(
            [
                f"### `{command['name']}`",
                "",
                command["description"],
                "",
            ]
        )

    lines.extend(["## Agents", ""])
    for agent in agents:
        lines.extend(
            [
                f"### `{agent['name']}`",
                "",
                agent["description"],
                "",
            ]
        )

    return "\n".join(lines)


def render_install(marketplace: Dict, plugin: Dict, agents: List[Dict]) -> str:
    owner = marketplace["owner"]["name"]
    command_name = f"{plugin['name']}:ask"

    lines = [
        "This guide covers the default Claude Code install flow.",
        "",
        "## Claude Code Install",
        "",
        "### 1. Add the marketplace",
        "",
        "```bash",
        f"/plugin marketplace add {owner}/{plugin['name']}",
        "```",
        "",
        "### 2. Install the plugin",
        "",
        "Use `/plugin` to open the plugin menu, search for `apple-text`, then install it.",
        "",
        "### 3. Verify installation",
        "",
        "Use `/plugin`, then open `Manage and install`. Apple Text should be listed there.",
        "",
        "### 4. Start using it",
        "",
        f"Use `/{command_name}` for broad Apple text intake.",
        "",
        "",
    ]
    return "\n".join(lines)


def documentation_scope_text(skill: Dict) -> str:
    name = skill["name"]
    kind = skill["kind"]

    if name == "apple-text-apple-docs":
        return (
            "This page documents the `apple-text-apple-docs` router skill. The router maps text-system "
            "questions to Apple-authored Xcode doc files and the checked-in fallback sidecars."
        )

    if kind == "router":
        return (
            f"This page documents the `{name}` router skill. The router maps broad Apple text questions "
            "to narrower specialist skills when the right subsystem is not obvious yet."
        )
    if kind == "workflow":
        return (
            f"This page documents the `{name}` workflow skill. Use it when the job is a guided review, "
            "implementation flow, or integration pass instead of a single API lookup."
        )
    if kind == "diag":
        return (
            f"This page documents the `{name}` diagnostic skill. Use it when broken behavior, regressions, "
            "or symptoms are the starting point."
        )
    if kind == "decision":
        return (
            f"This page documents the `{name}` decision skill. Use it when the main task is choosing the "
            "right Apple text API, view, or architecture."
        )
    return (
        f"This page documents the `{name}` reference skill. Use it when the subsystem is already known "
        "and you need mechanics, behavior, or API detail."
    )


def render_mcp_server(plugin: Dict, skills: List[Dict], commands: List[Dict], agents: List[Dict]) -> str:
    plugin_name = plugin["name"]
    package_name = "apple-text-mcp"
    command_name = commands[0]["name"] if commands else f"{plugin_name}:ask"
    root_path = f"/absolute/path/to/{plugin_name}"
    dist_path = f"{root_path}/mcp-server/dist/index.js"

    lines = [
        'import { CardGrid, LinkCard } from "@astrojs/starlight/components";',
        "",
        f"{display_plugin_name(plugin_name)} includes an MCP (Model Context Protocol) server that brings the same Apple Text collection to any MCP-compatible AI coding tool.",
        "",
        "## Choose The Right Surface",
        "",
        "| Surface | Best For | Front Door |",
        "|---------|----------|------------|",
        f"| Claude Code plugin | Native plugin install, `/plugin`, and command-first flow | `/{command_name}` |",
        "| Generic MCP client | VS Code, Cursor, Claude Desktop, Gemini CLI, OpenCode | `apple_text_route` |",
        "| Xcode via MCP | Claude Agent or Codex inside Xcode | `apple_text_route` plus optional `xcrun mcpbridge` |",
        "",
        "## What You Get",
        "",
        "The MCP server exposes Apple Text as a focused, read-only documentation surface:",
        "",
        f"- {len(skills)} skills as MCP Resources",
        f"- {len(commands)} command{'s' if len(commands) != 1 else ''} as MCP Prompts",
        "- 5 read-only MCP Tools for route-first guidance, catalog lookup, search, skill reads, and agent inspection",
        "",
        "For normal natural-language questions, start with `apple_text_route`, then follow the suggested `apple_text_read_skill` call.",
        "",
        "## Prerequisites",
        "",
        "- Node.js 18+",
        "",
        "For the published package, that is enough:",
        "",
        "```bash",
        f"npx -y {package_name}",
        "```",
        "",
        "If you are contributing or want development mode, build from a local checkout:",
        "",
        "```bash",
        f"git clone https://github.com/sitapix/{plugin_name}",
        f"cd {plugin_name}",
        "npm run setup:all",
        "npm run mcp:bundle",
        "```",
        "",
        "That produces `mcp-server/dist/index.js` and the bundled snapshot it reads in production mode.",
        "",
        "## Installation by Tool",
        "",
        "Each tool needs a config snippet that tells it how to launch the Apple Text MCP server.",
        "",
        "### VS Code + GitHub Copilot",
        "",
        "Add to your VS Code `settings.json`:",
        "",
        "```json",
        "{",
        '  "github.copilot.chat.mcp.servers": {',
        f'    "{plugin_name}": {{',
        '      "command": "npx",',
        f'      "args": ["-y", "{package_name}"]',
        "    }",
        "  }",
        "}",
        "```",
        "",
        "### Claude Desktop",
        "",
        "Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:",
        "",
        "```json",
        "{",
        '  "mcpServers": {',
        f'    "{plugin_name}": {{',
        '      "command": "npx",',
        f'      "args": ["-y", "{package_name}"]',
        "    }",
        "  }",
        "}",
        "```",
        "",
        "### Cursor",
        "",
        "Add to `.cursor/mcp.json` in your workspace:",
        "",
        "```json",
        "{",
        '  "mcpServers": {',
        f'    "{plugin_name}": {{',
        '      "command": "npx",',
        f'      "args": ["-y", "{package_name}"]',
        "    }",
        "  }",
        "}",
        "```",
        "",
        "### Gemini CLI",
        "",
        "Add to `~/.gemini/config.toml`:",
        "",
        "```toml",
        "[[mcp_servers]]",
        f'name = "{plugin_name}"',
        'command = "npx"',
        f'args = ["-y", "{package_name}"]',
        "```",
        "",
        "### OpenCode",
        "",
        "Add to `opencode.jsonc` in your project root, or `~/.config/opencode/opencode.jsonc` for global config:",
        "",
        "```json",
        "{",
        '  "mcp": {',
        f'    "{plugin_name}": {{',
        '      "type": "local",',
        f'      "command": ["npx", "-y", "{package_name}"]',
        "    }",
        "  }",
        "}",
        "```",
        "",
        "## Working Alongside Xcode Tools",
        "",
        "Apple Text is a read-only knowledge server. It does not build, test, or control Xcode projects.",
        "",
        "If you also want Xcode actions, run Apple's separate Xcode MCP bridge alongside Apple Text:",
        "",
        "```bash",
        "codex mcp add xcode -- xcrun mcpbridge",
        "```",
        "",
        "That gives you two complementary servers:",
        "",
        "- `apple-text` for text-system guidance, search, and references",
        "- `xcode` for build, test, and project actions exposed by Xcode",
        "",
        f"If you want the full Xcode-specific setup, use [Xcode Integration]({docs_page_link('xcode-integration', 'guide')}).",
        "",
        "## Configuration",
        "",
        "### Environment Variables",
        "",
        "| Variable | Values | Default | Description |",
        "|----------|--------|---------|-------------|",
        "| `APPLE_TEXT_MCP_MODE` | `development`, `production` | `production` | Runtime mode |",
        "| `APPLE_TEXT_DEV_PATH` | File path | — | Repo root for development mode |",
        "| `APPLE_TEXT_APPLE_DOCS` | `true`, `false` | `false` | Enable Apple-authored markdown docs from the local Xcode install when you want the Xcode-backed overlay |",
        "| `APPLE_TEXT_XCODE_PATH` | File path | `/Applications/Xcode.app` | Override the Xcode.app path used for Apple docs discovery |",
        "| `APPLE_TEXT_MCP_LOG_LEVEL` | `debug`, `info`, `warn`, `error` | `info` | Logging verbosity |",
        "",
        "### Development Mode (Live Skills)",
        "",
        "For Apple Text contributors who want live skill changes without rebundling:",
        "",
        "```bash",
        "APPLE_TEXT_MCP_MODE=development \\",
        f"APPLE_TEXT_DEV_PATH={root_path} \\",
        f"node {dist_path}",
        "```",
        "",
        "Changes to skill files are reflected immediately. When Xcode is installed, this mode can also load Apple-authored markdown docs from the local Xcode bundle without failing if they are absent.",
        "",
        "### Production Mode (Bundled)",
        "",
        "The default after `npm run mcp:bundle` or when launched through the published npm package. The server reads from the bundled snapshot and does not need live repo reads after initialization.",
        "",
        "```bash",
        f"npx -y {package_name}",
        "```",
        "",
        "## Verify It Works",
        "",
        "### Quick Test",
        "",
        "Run the server directly to confirm it launches without errors:",
        "",
        "```bash",
        f"npx -y {package_name}",
        "```",
        "",
        "The server should start and wait for stdin input. Press `Ctrl+C` to stop.",
        "",
        "### Repo Smoke Test",
        "",
        "From the repo root:",
        "",
        "```bash",
        "npm run mcp:smoke",
        "```",
        "",
        "That uses the official MCP SDK client to verify initialization, resources, tools, and prompts.",
        "",
        "### MCP Inspector",
        "",
        "For interactive testing:",
        "",
        "```bash",
        f"npx @modelcontextprotocol/inspector npx -y {package_name}",
        "```",
        "",
        "### In Your Tool",
        "",
        "Once configured, the most reliable MCP workflow is:",
        "",
        "1. Call `apple_text_route` with the user's question.",
        "2. Follow the suggested `apple_text_read_skill` call.",
        "3. Use `apple_text_search_skills` only if routing is ambiguous or you want more options.",
        "",
        "If you want a quick manual test, try asking your AI tool:",
        "",
        "```text",
        '"What Apple text skills do you have?"',
        "```",
        "",
        "It should list Apple Text skills through the MCP resources surface and offer the prompt/tool surface as needed.",
        "",
        "## Troubleshooting",
        "",
        "### Server Won't Start",
        "",
        "Check Node version:",
        "",
        "```bash",
        "node --version",
        "```",
        "",
        "### Skills Not Appearing",
        "",
        "Enable debug logging to see what the server loads:",
        "",
        "```bash",
        f"APPLE_TEXT_MCP_LOG_LEVEL=debug npx -y {package_name} 2>&1 | head -20",
        "```",
        "",
        "### Client Can't Connect",
        "",
        "MCP uses stdin/stdout for communication. Common issues:",
        "",
        f'- Wrong config — make sure your config points to `npx -y {package_name}` or an absolute local `dist/index.js` path',
        "- Other stdout writers — make sure nothing else writes to stdout; logs should go to stderr",
        "",
        "If you want live skills, make sure `APPLE_TEXT_MCP_MODE=development` and `APPLE_TEXT_DEV_PATH` points at the repo root.",
        "If you expect Apple-authored Xcode docs in development mode, make sure Xcode is installed or set `APPLE_TEXT_XCODE_PATH` to the right app bundle.",
        "",
        "## What's Next",
        "",
    ]
    lines.extend(
        render_linkcard_grid_mdx(
            [
                ("Skills", docs_page_link("skills", "root"), "Browse the full Apple Text skill catalog."),
                ("Commands", docs_page_link("commands", "root"), f"See how `/{command_name}` fits into the MCP prompt surface."),
                ("Agents", docs_page_link("agents", "root"), f"See the {len(agents)} bundled specialist agent{'s' if len(agents) != 1 else ''}."),
                ("Xcode Integration", docs_page_link("xcode-integration", "guide"), "Configure Apple Text MCP inside Xcode Claude Agent or Codex."),
            ]
        )
    )
    return "\n".join(lines)


def render_xcode_integration(plugin: Dict, skills: List[Dict], commands: List[Dict], agents: List[Dict]) -> str:
    plugin_name = plugin["name"]
    root_path = f"/absolute/path/to/{plugin_name}"
    dist_path = f"{root_path}/mcp-server/dist/index.js"
    node_path = "/absolute/path/to/node"
    path_env = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

    lines = [
        'import { CardGrid, LinkCard } from "@astrojs/starlight/components";',
        "",
        f"Use {display_plugin_name(plugin_name)} inside Xcode 26.3+ with Claude Agent or Codex via MCP.",
        "",
        "This is the same Apple Text collection you use from the Claude Code plugin or other MCP clients. The difference in Xcode is only the transport: MCP instead of `/plugin` commands.",
        "",
        "Apple Text and Xcode Tools solve different problems:",
        "",
        "- `apple-text` is a read-only knowledge server for Apple text systems",
        "- `xcode` via `xcrun mcpbridge` exposes Xcode actions like build, test, and project access",
        "",
        "Use them together when you want both guidance and Xcode execution.",
        "",
        "## What You Get",
        "",
        "The same Apple Text catalog available to other MCP clients, with the same route-first MCP workflow:",
        "",
        f"- {len(skills)} skills for Apple text systems",
        f"- {len(commands)} command{'s' if len(commands) != 1 else ''} as prompt entry points",
        "- 5 read-only MCP tools including `apple_text_route` as the front door for natural-language questions",
        "",
        "## Prerequisites",
        "",
        "- Xcode 26.3+ with Claude Agent or Codex enabled",
        "- Xcode Tools enabled in Xcode > Settings > Intelligence",
        "- Node.js 18+",
        "- A local Apple Text checkout built with `npm run mcp:bundle`",
        "",
        "Build the server before configuring Xcode:",
        "",
        "```bash",
        f"git clone https://github.com/sitapix/{plugin_name}",
        f"cd {plugin_name}",
        "npm run setup:all",
        "npm run mcp:bundle",
        "```",
        "",
        "If you want Xcode actions in addition to Apple Text guidance, add Apple's Xcode MCP bridge too:",
        "",
        "```bash",
        "codex mcp add xcode -- xcrun mcpbridge",
        "```",
        "",
        "## Claude Agent Setup",
        "",
        "Xcode's Claude Agent uses its own config directory and does not read your normal Claude Desktop config.",
        "",
        "### 1. Create the config directory",
        "",
        "```bash",
        "mkdir -p ~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig",
        "```",
        "",
        "### 2. Find your absolute `node` path",
        "",
        "Xcode does not inherit your shell setup, so use an absolute path:",
        "",
        "```bash",
        "which node",
        "```",
        "",
        "### 3. Create the config file",
        "",
        "Create `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json`:",
        "",
        "```json",
        "{",
        '  "projects": {',
        '    "*": {',
        '      "mcpServers": {',
        f'        "{plugin_name}": {{',
        '          "type": "stdio",',
        f'          "command": "{node_path}",',
        f'          "args": ["{dist_path}"],',
        '          "env": {',
        f'            "PATH": "{path_env}"',
        "          }",
        "        }",
        "      }",
        "    }",
        "  }",
        "}",
        "```",
        "",
        'Replace the `node` path with the result of `which node`. Replace `"*"` with a specific project path if you want narrower scope.',
        "",
        "### 4. Restart Xcode",
        "",
        "Close and reopen Xcode completely for the config to take effect.",
        "",
        "### 5. Verify",
        "",
        "Type `/context` in the Claude Agent panel. You should see Apple Text listed as a connected MCP server.",
        "",
        "For normal questions, start from `apple_text_route` rather than manually browsing the catalog.",
        "",
        "## Codex Setup",
        "",
        "Codex uses `.codex/config.toml` in your project root, or `~/.codex/config.toml` for global config.",
        "",
        "### 1. Add the MCP server",
        "",
        "```toml",
        f"[mcp_servers.{plugin_name}]",
        f'command = "{node_path}"',
        f'args = ["{dist_path}"]',
        f'env = {{ "PATH" = "{path_env}" }}',
        "```",
        "",
        "### 2. Restart Xcode",
        "",
        "Close and reopen Xcode for the config to take effect.",
        "",
        "After setup, use the same MCP flow as other clients: `apple_text_route` first, then `apple_text_read_skill`.",
        "",
        "## Gotchas",
        "",
        "- Absolute paths are safer. Xcode's MCP environment is more restricted than your terminal.",
        "- Restart Xcode after config changes. Editing the file while Xcode is open usually has no effect.",
        "- Apple Text does not replace `xcrun mcpbridge`. Run both if you want Xcode actions plus Apple Text guidance.",
        "- This is different from the Claude Code plugin path. In Xcode you get the MCP surface, not the `/plugin` menu or hooks.",
        "",
        "If you are contributing and want live skill edits without rebundling, add these env values to the MCP config:",
        "",
        "```json",
        "{",
        '  "APPLE_TEXT_MCP_MODE": "development",',
        f'  "APPLE_TEXT_DEV_PATH": "{root_path}",',
        '  "APPLE_TEXT_APPLE_DOCS": "true"',
        "}",
        "```",
        "",
        "## Troubleshooting",
        "",
        "### MCP not appearing in `/context`",
        "",
        "- Check that the config file exists at the correct path",
        "- Verify the `node` path is absolute and correct by running it in Terminal",
        "- Confirm `mcp-server/dist/index.js` exists and you already ran `npm run mcp:bundle`",
        "",
        "### Skills not loading",
        "",
        "Enable debug logging and run the server directly:",
        "",
        "```bash",
        f"APPLE_TEXT_MCP_LOG_LEVEL=debug {node_path} {dist_path} 2>&1 | head -20",
        "```",
        "",
        "If the server starts and reports resources, the issue is usually in Xcode's MCP connection rather than Apple Text itself.",
        "",
        "## What's Next",
        "",
    ]
    lines.extend(
        render_linkcard_grid_mdx(
            [
                ("MCP Server", docs_page_link("mcp-server", "guide"), "Setup for Claude Desktop, Cursor, VS Code, Gemini CLI, and OpenCode."),
                ("Skills", docs_page_link("skills", "root"), "Browse the Apple Text skill catalog."),
                ("Quick Start", docs_page_link("quick-start", "guide"), "Return to the main Apple Text install flow."),
            ]
        )
    )
    return "\n".join(lines)


def render_skill_page(skill: Dict, skills: List[Dict], owner: str, plugin_name: str) -> str:
    by_name = {entry["name"]: entry for entry in skills}
    related = [by_name[name] for name in skill.get("related_skills", []) if name in by_name]
    content = mdx_escape_body(strip_sidecar_links(body_without_leading_h1(skill["body"])))
    badge_variant = KIND_BADGE_VARIANTS.get(skill["kind"], "default")

    lines = [
        "import { Code, Badge } from '@astrojs/starlight/components';",
        "import skillSource from './SKILL-source.txt?raw';",
        "",
        f'<Badge text="{KIND_TITLES[skill["kind"]]}" variant="{badge_variant}" />',
        "",
        skill["full_description"],
        "",
    ]

    if skill.get("category") in CATEGORY_TITLES:
        lines.extend(
            [
                f"**Family:** {CATEGORY_TITLES[skill['category']]}",
                "",
            ]
        )

    if content:
        lines.extend([content, ""])

    lines.extend(
        [
            "## Documentation Scope",
            "",
            documentation_scope_text(skill),
            "",
        ]
    )

    if related:
        lines.extend(
            [
                "## Related",
                "",
            ]
        )
        lines.extend(render_skill_list(related, "skill"))

    if skill.get("sidecars"):
        lines.extend(
            [
                "## Sidecar Files",
                "",
            ]
        )
        for sidecar in skill["sidecars"]:
            lines.append(f"- `skills/{skill['name']}/{sidecar}`")
        lines.append("")

    lines.extend(
        [
            "<details>",
            "<summary>Full SKILL.md source</summary>",
            "",
            render_code_component("skillSource", "md", "SKILL.md"),
            "",
            "</details>",
            "",
        ]
    )
    return "\n".join(lines)


def generated_docs(root: Path) -> Dict[Path, str]:
    global _BASE
    plugin = load_json(root / ".claude-plugin" / "plugin.json")
    output_root = docs_root(root)
    _BASE = f"/{plugin['name']}"
    marketplace = load_json(root / ".claude-plugin" / "marketplace.json")
    skills = load_skill_entries(root)
    commands = load_commands(root, plugin["name"])
    agents = load_agents(root)

    docs = {
        root / "README.md": render_readme(plugin, marketplace, skills, commands, agents),
        output_root / "index.mdx": with_doc_frontmatter(
            display_plugin_name(plugin["name"]),
            render_home(plugin, marketplace, skills, commands, agents),
            "Focused docs for Apple text-system work.",
            [
                "hero:",
                f"  title: {json.dumps(render_retro_wordmark_html(display_plugin_name(plugin['name'])))}",
                '  tagline: "Focused docs for Apple platform text systems."',
            ],
        ),
        output_root / "setup.md": with_doc_frontmatter(
            "Setup",
            render_setup_page(marketplace, plugin, commands, agents),
            "Install the Apple Text plugin or individual skills.",
        ),
        output_root / "skills" / "index.mdx": with_doc_frontmatter(
            "Skills",
            render_skills_overview(skills, commands),
            "Browse Apple Text skills by topic family and routing role.",
            [
                "sidebar:",
                "  order: 1",
            ],
        ),
        output_root / "commands.mdx": with_doc_frontmatter(
            "Commands",
            render_commands_page(root, commands, skills),
            "Command overview for the Apple Text plugin.",
        ),
        output_root / "agents.mdx": with_doc_frontmatter(
            "Agents",
            render_agents_page(root, agents, skills),
            "Agent overview for the Apple Text plugin.",
        ),
        output_root / "guide" / "index.mdx": with_doc_frontmatter(
            "Overview",
            render_guide_index(skills),
            "Repo-level overview and routing guidance for the Apple Text plugin.",
            [
                "sidebar:",
                "  order: 1",
            ],
        ),
        output_root / "guide" / "quick-start.mdx": with_doc_frontmatter(
            "Quick Start",
            render_quick_start(marketplace, plugin, skills, commands),
            extra_frontmatter=[
                "sidebar:",
                "  order: 2",
            ],
        ),
        output_root / "guide" / "mcp-server.mdx": with_doc_frontmatter(
            "MCP Server",
            render_mcp_server(plugin, skills, commands, agents),
            extra_frontmatter=[
                "sidebar:",
                "  order: 3",
            ],
        ),
        output_root / "guide" / "xcode-integration.mdx": with_doc_frontmatter(
            "Xcode Integration",
            render_xcode_integration(plugin, skills, commands, agents),
            extra_frontmatter=[
                "sidebar:",
                "  order: 4",
            ],
        ),
        output_root / "guide" / "install.md": with_doc_frontmatter(
            "Install",
            render_install(marketplace, plugin, agents),
            extra_frontmatter=[
                "sidebar:",
                "  order: 5",
            ],
        ),
        output_root / "guide" / "entry-points.md": with_doc_frontmatter(
            "Entry Points",
            render_entry_points(skills, commands),
            extra_frontmatter=[
                "sidebar:",
                "  order: 6",
            ],
        ),
        output_root / "guide" / "routing-model.md": with_doc_frontmatter(
            "Routing Model",
            render_routing_model(skills, commands),
            extra_frontmatter=[
                "sidebar:",
                "  order: 7",
            ],
        ),
        output_root / "guide" / "problem-routing.mdx": with_doc_frontmatter(
            "Problem Routing",
            render_problem_routing(skills),
            extra_frontmatter=[
                "sidebar:",
                "  order: 8",
            ],
        ),
        output_root / "guide" / "commands-and-agents.md": with_doc_frontmatter(
            "Commands And Agents",
            render_commands_and_agents(root, commands, agents),
            extra_frontmatter=[
                "sidebar:",
                "  order: 9",
            ],
        ),
    }

    for skill in skills:
        docs[output_root / "skills" / skill["name"] / "index.mdx"] = with_doc_frontmatter(
            skill_page_title(skill),
            render_skill_page(skill, skills, marketplace["owner"]["name"], plugin["name"]),
            skill["description"],
        )
        docs[output_root / "skills" / skill["name"] / "SKILL-source.txt"] = (
            skill["source"].rstrip() + "\n"
        )

    return docs


def write_docs(root: Path) -> List[Path]:
    changed = []
    for path, content in generated_docs(root).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized = content.rstrip() + "\n"
        existing = path.read_text(encoding="utf-8") if path.exists() else None
        if existing != normalized:
            path.write_text(normalized, encoding="utf-8")
            changed.append(path)
    return changed


def stale_docs(root: Path) -> List[Path]:
    stale = []
    for path, content in generated_docs(root).items():
        normalized = content.rstrip() + "\n"
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if existing != normalized:
            stale.append(path)
    return stale


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Apple Text docs from package metadata.")
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="Plugin root to generate docs for (default: repository root).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check whether generated docs are up to date without writing changes.",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.check:
        stale = stale_docs(root)
        if stale:
            for path in stale:
                rel = path.relative_to(root).as_posix()
                print("STALE: " + rel, file=sys.stderr)
            print("Run python3 tooling/scripts/docs/generate_docs.py to regenerate docs.", file=sys.stderr)
            return 1
        print("Generated docs are up to date.")
        return 0

    changed = write_docs(root)
    if not changed:
        print("Generated docs are already up to date.")
        return 0

    for path in changed:
        print("Updated " + path.relative_to(root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
