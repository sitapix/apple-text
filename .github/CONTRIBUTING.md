# Contributing

Optimize this repo for the people installing skills. Keep entry points obvious and the layout predictable.

## Repo Layout

- `skills/`: one directory per skill (`SKILL.md` plus optional `references/` sidecars)
- `.claude-plugin/`: marketplace metadata
- `.github/`: CI workflows and contributor docs

## Editing Rules

- Edit skills directly in `skills/<skill-name>/SKILL.md`.
- Sidecar material goes in `skills/<skill-name>/references/`. Link from `SKILL.md` with relative paths like `[name](references/name.md)`.
- Keep skill front matter (`name`, `description`, `license`) accurate. Use trigger phrasing in descriptions (`Use when...`).
- Prefer focused skills and clear routing over large catch-all documents.

## Adding a Skill

1. Create `skills/<skill-name>/SKILL.md` with Agent Skills front matter. The directory name must match the `name` field.
2. Add any sidecar files under `skills/<skill-name>/references/`.
3. Verify the skill loads correctly in your Agent Skills client.

See [AGENTS.md](../AGENTS.md) for the full conventions.
