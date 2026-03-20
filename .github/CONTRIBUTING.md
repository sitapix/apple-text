# Contributing

This repository is packaged for skill consumers first. Keep user-facing entry points obvious, generated artifacts current, and packaging behavior predictable.

## Repo Layout

- `skills/` contains installable skills
- `agents/` contains optional specialist agents
- `.agents/` mirrors the collection for Agent Skills discovery
- `.claude-plugin/` contains marketplace metadata
- `mcp-server/` contains the standalone MCP package
- `tooling/scripts/` contains validation, generation, and packaging helpers

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

You should not need to run extra validation commands before every push unless you want a manual check.

The Git hooks already do it:

- pre-commit regenerates docs and MCP artifacts, restages generated files, and runs `npm run check`
- pre-push runs `npm run check`

Both of those paths run Python scripts as part of validation, so Python is a normal part of the repo workflow.

If you want to run the main validation manually before committing:

```bash
npm run check
```

For a faster style and hygiene pass:

```bash
npm run lint
```

## Common Commands

```bash
npm run lint
npm run check
npm run docs:generate
npm run mcp:generate
npm run mcp:build
npm run mcp:smoke
```

- `lint` runs the repo hygiene checks and skill-description linting
- `check` runs docs checks, plugin validation, MCP generation checks, MCP build and smoke tests, description checks, and the Python test suite
- `docs:generate` refreshes `README.md` and docs pages
- `mcp:generate` refreshes MCP annotations and the committed bundle
- `mcp:build` compiles the standalone MCP server
- `mcp:smoke` verifies a full MCP client handshake against the built server

## Editing Rules

- Do not hand-edit generated `README.md`; update `tooling/scripts/docs/generate_docs.py` and regenerate docs instead
- Keep versions aligned across `claude-code.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `mcp-server/package.json`
- If skills, agents, commands, or MCP metadata change, regenerate docs and MCP artifacts before committing
- Prefer focused skills and clear routing over large catch-all documents

## MCP Package

The standalone package lives in `mcp-server/`.

Typical validation flow:

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

Use:

```bash
npm run version:set -- X.Y.Z
```

That updates the consumer-facing manifests and the MCP package version together.
