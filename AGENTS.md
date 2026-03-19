# AGENTS.md

This repository is packaged as a Claude plugin, but the real product is the quality of the skill content. Keep the package small, predictable, and easy to validate.

## Structure

- [`skills/`](/Users/steven/dev/text/apple-text/skills) contains installable skills
- [`agents/`](/Users/steven/dev/text/apple-text/agents) contains optional specialist agents
- [`.claude-plugin/`](/Users/steven/dev/text/apple-text/.claude-plugin) contains marketplace metadata
- [`scripts/validate_plugin.py`](/Users/steven/dev/text/apple-text/scripts/validate_plugin.py) enforces basic repo integrity

## Conventions

- One skill per directory, with the directory name matching the skill `name` in front matter.
- Every skill must have front matter with `name`, `description`, and `license`.
- Broad Apple text requests should route through [`apple-text`](/Users/steven/dev/text/apple-text/skills/apple-text/SKILL.md).
- When linking to another skill inside content, use `/skill skill-name`.
- Prefer focused reference or diagnostic skills over giant catch-all documents.
- If a skill grows too large, add a short decision summary near the top or split it.
- Keep examples concrete and Apple-framework specific.

## When Adding A Skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Add front matter that matches the directory name.
3. Link it from [`apple-text`](/Users/steven/dev/text/apple-text/skills/apple-text/SKILL.md) if it should be discoverable from the router.
4. Update [`README.md`](/Users/steven/dev/text/apple-text/README.md) if the new skill is an important public entry point.
5. Run `uv run python scripts/validate_plugin.py`.

## When Changing Packaging

- Keep versions aligned across [`claude-code.json`](/Users/steven/dev/text/apple-text/claude-code.json), [`.claude-plugin/plugin.json`](/Users/steven/dev/text/apple-text/.claude-plugin/plugin.json), and [`.claude-plugin/marketplace.json`](/Users/steven/dev/text/apple-text/.claude-plugin/marketplace.json).
- Do not add generated indexes unless they are validated in CI.
- Avoid adding runtime dependencies for simple validation tasks.

## Review Standard

Public-facing plugin quality matters here:

- installation should be obvious
- naming should be consistent
- entry points should be clear
- routing should not rely on hidden tribal knowledge
- validation should fail fast when metadata drifts
