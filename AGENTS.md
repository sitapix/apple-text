# AGENTS.md

This repository is the Apple Text workspace. It ships one Apple text skills collection across multiple surfaces: direct Agent Skills discovery, Claude plugin packaging, a standalone MCP server, and a generated docs site. Keep the package small, predictable, and easy to validate.

## Structure

- Product surface: [`skills/`](apple-text/skills), [`commands/`](apple-text/commands), [`agents/`](apple-text/agents), [`.agents/`](apple-text/.agents), and [`.claude-plugin/`](apple-text/.claude-plugin)
- MCP surface: [`mcp-server/`](apple-text/mcp-server) contains the standalone MCP package, bundle, and server implementation
- Docs surface: [`docs/`](apple-text/docs) contains the Astro docs app, generated content, and site config in one place
- Support infrastructure: [`tooling/scripts/`](apple-text/tooling/scripts), [`tooling/tests/`](apple-text/tooling/tests), [`tooling/config/`](apple-text/tooling/config), [`tooling/hooks/`](apple-text/tooling/hooks), and [`tooling/evals/`](apple-text/tooling/evals)

## Conventions

- One skill per directory, with the directory name matching the skill `name` in front matter.
- Every skill must have Agent Skills front matter with `name`, `description`, and `license`.
- Skill descriptions should use trigger phrasing such as `Use when...`, not label-style summaries.
- Custom per-skill fields belong under `metadata`, not as extra top-level front matter keys.
- Broad Apple text requests should route through [`apple-text`](apple-text/skills/apple-text/SKILL.md).
- Apple-authored docs lookup should route through [`apple-text-apple-docs`](apple-text/skills/apple-text-apple-docs/SKILL.md), with Xcode-backed docs preferred when available.
- When linking to another skill inside content, use `/skill skill-name`.
- Prefer focused reference or diagnostic skills over giant catch-all documents.
- If a skill grows too large, add a short decision summary near the top or split it.
- Keep examples concrete and Apple-framework specific.

## When Adding A Skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Add front matter that matches the directory name.
3. Link it from [`apple-text`](apple-text/skills/apple-text/SKILL.md) if it should be discoverable from the router.
4. Update [`README.md`](apple-text/README.md) if the new skill is an important public entry point.
5. Run `npm run setup`.
6. Run `uv run python tooling/scripts/quality/validate_plugin.py`.
7. Run `npm run descriptions:dataset`.

## When Changing Packaging

- Keep `.agents/skills` and `.agents/agents` resolving to the source directories so Agent Skills clients can discover the repo directly.
- Keep versions aligned across [`claude-code.json`](apple-text/claude-code.json), [`.claude-plugin/plugin.json`](apple-text/.claude-plugin/plugin.json), and [`.claude-plugin/marketplace.json`](apple-text/.claude-plugin/marketplace.json).
- Keep the root workspace, docs site, and [`mcp-server/`](apple-text/mcp-server) telling the same install and routing story.
- Do not add generated indexes unless they are validated in CI.
- Avoid adding runtime dependencies for simple validation tasks.

## Review Standard

Public-facing packaging quality matters here:

- installation should be obvious
- naming should be consistent
- entry points should be clear
- routing should not rely on hidden tribal knowledge
- validation should fail fast when metadata drifts
