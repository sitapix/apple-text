# AGENTS.md

Apple Text is a collection of skills for Apple's text-system APIs, distributed through Agent Skills discovery and the Claude plugin marketplace. Keep the package small and predictable.

## Structure

- `skills/`: one directory per skill, each containing `SKILL.md` and an optional `references/` folder for sidecar files
- `.claude-plugin/`: marketplace metadata
- `.github/`: CI workflows and contributor docs
- `AGENTS.md`, `CHANGELOG.md`, `LICENSE`, `README.md`: top-level docs

## Conventions

- One skill per directory, with the directory name matching the skill `name` in front matter.
- Every skill must have Agent Skills front matter with `name`, `description`, and `license`.
- Skill descriptions should use trigger phrasing such as `Use when...`, not label-style summaries.
- Custom per-skill fields belong under `metadata`, not as extra top-level front matter keys.
- Broad Apple text requests should route through `apple-text` (the router skill).
- Sidecar reference content lives in `skills/<skill>/references/*.md`. Link from `SKILL.md` using relative paths like `[name](references/name.md)`.
- Prefer focused reference or diagnostic skills over giant catch-all documents.
- Sibling apple-text skills exist as separate units. Boundaries and overlap are deliberate. Do not merge them without a clear reason.
- Keep examples concrete and Apple-framework specific.

## When Adding a Skill

1. Create `skills/<skill-name>/SKILL.md` with front matter matching the directory name.
2. If the skill needs sidecar reference material, add it under `skills/<skill-name>/references/`.
3. Verify the skill is discoverable by Agent Skills clients pointing at this repo.

## Review Standard

Quality bar for public packaging:

- installation is obvious
- naming is consistent
- entry points are clear
- routing does not rely on hidden tribal knowledge
