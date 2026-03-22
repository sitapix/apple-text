# Changelog

## Unreleased

### Architecture: Context-Aware Skill Delivery

Restructured how skills are delivered to keep AI context clean:

- Reduced registered Claude Code skills from 39 to 5 entry points (apple-text, apple-text-audit, apple-text-views, apple-text-textkit-diag, apple-text-recipes)
- Created 4 domain agents (textkit-reference, editor-reference, rich-text-reference, platform-reference) that bundle the other 34 skills and run in isolated context
- Added `scripts/build-agents.mjs` to generate domain agents from source skills, with `--check` mode for staleness validation
- MCP server unchanged — still serves all 39 skills directly to MCP clients
- Added routing tests (12 test cases) and content verification to MCP smoke tests
- Updated README to explain the two-tier architecture (entry skills + domain agents)
- Added `npm run release -- X.Y.Z` for one-command releases (version bump, rebuild, validate, commit, tag, push)
- Split git hooks: pre-commit is fast (~2s, lint + regenerate), pre-push runs full validation (~12s)

### Earlier Unreleased

- Split `apple-text-views` into a short `SKILL.md` plus `reference.md` and `examples.md` to improve retrieval quality.
- Added `/skill apple-text-audit` as a public audit entry point backed by the `textkit-auditor` agent.
- Added `/apple-text:ask` as a natural-language command that routes users to the right Apple Text skill or agent.
- Added marketplace metadata for agents, license, author, and tags.
- Added a plugin hook and helper script to rerun validation after relevant edits.
- Hardened `tooling/scripts/quality/validate_plugin.py` with `SKILL.md` size checks, markdown link validation, and manifest metadata drift checks.
- Added `docs/src/content/docs/example-conversations.md` and `MARKETPLACE-SUBMISSION.md`.
- Added a VitePress docs site scaffold with guide, catalog, command, agent, and maintenance pages.
- Added `tooling/scripts/dev/install_skill.py` for selective skill installs and GitHub Pages deployment for the docs site.

## 1.0.0

- Packaged Apple Text as a Claude plugin marketplace entry with focused Apple text skills and a TextKit auditor agent.
