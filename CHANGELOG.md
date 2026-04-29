# Changelog

## 2.0.0

Breaking release. Reinstall required for v1.x users — every skill path changed.

### Renamed all 38 specialist skills from `apple-text-*` to `txt-*`

The router stays as `apple-text`. The specialist prefix changed for shorter `/skill` invocations.

Notable renames beyond the prefix swap:

- `apple-text-textkit-diag` → `txt-textkit-debug`
- `apple-text-attachments-ref` → `txt-attachments`
- `apple-text-formatting-ref` → `txt-formatting`
- `apple-text-foundation-ref` → `txt-foundation-utils`
- `apple-text-input-ref` → `txt-input`
- `apple-text-textkit1-ref` → `txt-textkit1`
- `apple-text-textkit2-ref` → `txt-textkit2`
- `apple-text-texteditor-26` → `txt-swiftui-texteditor`
- `apple-text-layout-manager-selection` → `txt-textkit-choice`

### Repo restructure

- Removed the `apple-text` router skill. Specialists auto-activate from descriptions or are invoked directly. Skill count: 38.
- Removed the domain-agent layer (`textkit-reference`, `editor-reference`, `rich-text-reference`, `platform-reference`, `textkit-auditor`).
- Removed generated docs site, MCP server, build/validation tooling, and contributor scripts. Repo is now a flat skills collection conformant with the [Vercel skills CLI](https://github.com/vercel-labs/skills).
- Plugin manifests (`plugin.json`, `marketplace.json`) now list all 39 skills instead of just 5 entry points.
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

- Packaged Apple Text as a Claude plugin marketplace entry with focused Apple text skills and a TextKit auditor agent.
