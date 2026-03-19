# Changelog

## 1.0.0

- Packaged Apple Text as a Claude plugin marketplace entry with focused Apple text skills and a TextKit auditor agent.

## Unreleased

- Split `text-views` into a short `SKILL.md` plus `reference.md` and `examples.md` to improve retrieval quality.
- Added `/skill text-audit` as a public audit entry point backed by the `textkit-auditor` agent.
- Added `/apple-text:ask` as a natural-language command that routes users to the right Apple Text skill or agent.
- Added marketplace metadata for agents, license, author, and tags.
- Added a plugin hook and helper script to rerun validation after relevant edits.
- Hardened `scripts/validate_plugin.py` with `SKILL.md` size checks, markdown link validation, and manifest metadata drift checks.
- Added `docs/example-conversations.md` and `MARKETPLACE-SUBMISSION.md`.
- Added a VitePress docs site scaffold with guide, catalog, command, agent, and maintenance pages.
- Added `scripts/install_skill.py` for selective skill installs and GitHub Pages deployment for the docs site.
