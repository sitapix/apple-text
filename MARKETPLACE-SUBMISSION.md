# Marketplace Submission Checklist

Use this before publishing or updating the plugin marketplace entry.

## Package Integrity

- Run `uv run python scripts/validate_plugin.py`
- Confirm `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `claude-code.json` agree on version and core metadata
- Confirm every skill directory contains `SKILL.md`
- Confirm no `SKILL.md` exceeds the size budget enforced by the validator
- Confirm the validation hook in `hooks/hooks.json` still targets the right script
- Confirm `scripts/install_skill.py` still works for selective installs

## Public-Facing Review

- README explains what the plugin is for in the first screenful
- Installation is obvious for marketplace users
- Entry points are explicit: `apple-text`, `text-audit`, major reference skills
- `/apple-text:ask` works as the plain-language front door
- The docs site navigation is coherent and the main guide pages build cleanly
- Relative markdown links work on GitHub
- `CHANGELOG.md` reflects the release being submitted
- `homepage` and `repository` are filled in once the public repo URL exists

## Spot Checks

- `apple-text` routes to the right specialist skill for at least three common prompts
- `/apple-text:ask` chooses the right specialist route for at least three common prompts
- `text-views` stays concise and points to `reference.md` / `examples.md`
- `text-audit` invokes the `textkit-auditor` workflow cleanly
- Agent and skill names are consistent across docs and manifests
- Editing a watched file in `commands/`, `skills/`, `agents/`, `hooks/`, or `.claude-plugin/` triggers `scripts/validate_after_edit.py`
- `uv run python scripts/install_skill.py text-audit` installs both the skill and its dependent agent

## Release Notes Inputs

- Summarize any new skills or renamed entry points
- Call out major routing changes
- Note any validator rule additions that maintainers need to know about
