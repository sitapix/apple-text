# Changelog

## Unreleased

Breaking release. Skill paths changed; reinstall required.

### Renamed 10 skills

| Was | Is |
|---|---|
| `txt-formatting` | `txt-attribute-keys` |
| `txt-foundation-utils` | `txt-detectors-tagger` |
| `txt-input` | `txt-uitextinput` |
| `txt-interaction` | `txt-selection-menus` |
| `txt-parsing` | `txt-regex` |
| `txt-recipes` | `txt-snippets` |
| `txt-representable` | `txt-wrap-textview` |
| `txt-storage` | `txt-nstextstorage` |
| `txt-swiftui-bridging` | `txt-swiftui-interop` |
| `txt-views` | `txt-view-picker` |

New names lead with the framework or intent. Old names led with generic nouns.

### New skill

- `txt-refresh-against-sosumi` — maintenance sub-skill that refreshes the `references/latest-apis.md` companions in time-sensitive skills after each Xcode point release.

### Skill rewrites (all 39)

Bodies trimmed from ~12,500 lines to ~9,400 across the repo.

Removed from every skill: decision trees, `## Quick Decision` sections, Symptom|Cause|Fix tables for non-tabular content, mid-content `→ /skill` rerouting, and `MUST` / `NEVER` / `ALWAYS` outside code comments.

Added: subject-named sections, prose explanations of *why* a failure happens, `## Common Mistakes` with WRONG/CORRECT code blocks, and `## References` at the bottom.

### Freshness contract

- Every skill's first body line declares `Authored against iOS 26.x / Swift 6.x / Xcode 26.x.`
- Time-sensitive skills (`txt-swiftui-texteditor`, `txt-writing-tools`, `txt-textkit2`, `txt-attribute-keys`, `txt-attributed-string`) carry `references/latest-apis.md` companions verified against Sosumi.
- All Apple documentation links use `sosumi.ai`. Apple's docs render with JavaScript and return a stub to non-browser fetches; Sosumi serves the same content as clean Markdown agents can read.

### Authoring spec

- `AGENTS.md` now lives at the repo root with the full authoring rules, anti-patterns, freshness contract, and review standard.
- `references/topic-boundaries.md` documents deliberate splits between sibling skills.

## 2.0.0

Breaking release. Every skill path changed; v1.x users must reinstall.

### Renamed all 38 specialist skills from `apple-text-*` to `txt-*`

The router stayed as `apple-text`. The specialist prefix changed for shorter `/skill` invocations.

Notable renames beyond the prefix swap:

- `apple-text-textkit-diag` → `txt-textkit-debug`
- `apple-text-attachments-ref` → `txt-attachments`
- `apple-text-formatting-ref` → `txt-attribute-keys`
- `apple-text-foundation-ref` → `txt-detectors-tagger`
- `apple-text-input-ref` → `txt-uitextinput`
- `apple-text-textkit1-ref` → `txt-textkit1`
- `apple-text-textkit2-ref` → `txt-textkit2`
- `apple-text-texteditor-26` → `txt-swiftui-texteditor`
- `apple-text-layout-manager-selection` → `txt-textkit-choice`

### Repo restructure

- Removed the `apple-text` router skill. Specialists auto-activate from descriptions or run from a slash command.
- Removed the domain-agent layer (`textkit-reference`, `editor-reference`, `rich-text-reference`, `platform-reference`, `textkit-auditor`).
- Removed generated docs site, MCP server, build/validation tooling, and contributor scripts. Repo is now a flat skills collection.
- Plugin manifests now list all skills instead of just 5 entry points.
- README adopted a categorized skills table.

### Reinstall

```sh
npx skills add sitapix/apple-text
```

Or via Claude Code:

```sh
/plugin marketplace add sitapix/apple-text
/plugin install apple-text@apple-text
```

## 1.0.0

Packaged Apple Text as a Claude plugin marketplace entry with focused Apple text skills and a TextKit auditor agent.
