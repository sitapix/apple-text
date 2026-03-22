# Contributing

This repository is packaged for skill consumers first. Keep user-facing entry points obvious, generated artifacts current, and packaging behavior predictable.

## Repo Layout

- `skills/` contains all 39 skill source files (SKILL.md per directory)
- `agents/` contains the textkit-auditor agent and 4 generated domain agents
- `scripts/build-agents.mjs` combines skill content into domain agent files
- `.agents/` mirrors skills/ and agents/ via symlinks for Agent Skills discovery
- `.claude-plugin/` contains marketplace metadata
- `mcp-server/` contains the standalone MCP package
- `tooling/` contains validation, generation, and packaging helpers

## Architecture

Apple Text uses a two-tier architecture to keep AI context clean:

- **5 registered skills** load inline in Claude Code (apple-text, apple-text-audit, apple-text-views, apple-text-textkit-diag, apple-text-recipes)
- **4 domain agents** bundle the other 34 skills into isolated-context reference lookups (textkit-reference, editor-reference, rich-text-reference, platform-reference)
- **1 audit agent** (textkit-auditor) scans code for anti-patterns
- **MCP server** serves all 39 skills directly for non-Claude clients

The domain agents are **generated files** — do not edit them directly. Edit the source skill in `skills/*/SKILL.md` and run `node scripts/build-agents.mjs` to rebuild.

## Local Setup

```bash
npm run setup
```

That installs root dependencies, MCP server dependencies, validation tools, and the repo Git hooks.

If you also want the full generated surface refreshed after setup:

```bash
npm run setup:all
```

## Prerequisites

- `python3`
- `node` and `npm`
- `uv`

`npm run setup` installs the repo dependencies and validation tools that the hooks rely on.
It also configures `core.hooksPath` to use the repo's `.githooks/` directory.

## Daily Workflow

For normal work, after initial setup:

```bash
git add ...
git commit
git push
```

You should not need to run extra commands. The Git hooks handle everything:

- **pre-commit** (~2s): regenerates agents, docs, MCP artifacts, stages them, runs lint + agents staleness check
- **pre-push** (~12s): runs full `npm run check` — routing tests, smoke tests, Python suite, packaging validation

If you want to run validation manually:

```bash
npm run check          # full validation
npm run lint           # fast style check only
npm run agents:check   # verify generated agents match source skills
```

## Common Commands

```bash
npm run lint              # repo hygiene + skill descriptions
npm run agents:build      # rebuild domain agents from skills
npm run agents:check      # fail if agents are stale vs source skills
npm run check             # full validation pipeline (~12s)
npm run docs:generate     # refresh README and docs pages
npm run mcp:generate      # refresh MCP annotations and bundle
npm run mcp:build         # compile standalone MCP server
npm run mcp:smoke         # routing + content tests against MCP server
```

## Editing Rules

- Do not hand-edit generated files: `README.md`, `agents/*-reference.md`, `mcp-server/bundle.json`, `mcp-server/skill-annotations.json`, `docs/src/content/docs/`
- Edit the source (`skills/*/SKILL.md`, `generate_docs.py`, `build-agents.mjs`) and regenerate
- Keep versions aligned — use `npm run version:set -- X.Y.Z` or `npm run release -- X.Y.Z`
- Prefer focused skills and clear routing over large catch-all documents

## Adding a Skill

1. Create `skills/<skill-name>/SKILL.md` with Agent Skills front matter.
2. Add it to the appropriate domain agent in `scripts/build-agents.mjs`.
3. Add a catalog entry in `skills/catalog.json`.
4. Run `node scripts/build-agents.mjs` to regenerate agent files.
5. If the skill should be a registered entry point (rare — only 5 today), add it to `plugin.json` and update the router.
6. Run `npm run setup` then `npm run check`.

## MCP Package

The standalone package lives in `mcp-server/`. It serves all 39 skills to MCP clients.

Typical validation:

```bash
npm run mcp:generate
npm run mcp:build
npm run mcp:smoke
```

For packaging dry runs:

```bash
npm run mcp:pack:dry-run
npm run mcp:publish:dry-run
```

## Releases

One command:

```bash
npm run release -- X.Y.Z
```

This bumps version across all manifests, rebuilds all derived files, runs full validation, commits, tags (`vX.Y.Z` + `mcp-vX.Y.Z`), and pushes.

CI then automatically deploys docs and publishes the MCP package to npm.

To bump the version without releasing:

```bash
npm run version:set -- X.Y.Z
```
