---
description: Pre-release validation with guided fixes — checks versions, regenerates derived files, runs full validation, and reports blockers
allowed-tools: Bash, Read
model: haiku
---

# Release Preflight

Validate everything before running `npm run release -- X.Y.Z`.

## Step 1: Version consistency

```bash
python3 -c "
import json
files = {
    'claude-code.json': json.load(open('claude-code.json'))['version'],
    '.claude-plugin/plugin.json': json.load(open('.claude-plugin/plugin.json'))['version'],
    '.claude-plugin/marketplace.json': json.load(open('.claude-plugin/marketplace.json'))['metadata']['version'],
    'mcp-server/package.json': json.load(open('mcp-server/package.json'))['version'],
}
for f, v in files.items():
    print(f'{f}: {v}')
versions = set(files.values())
if len(versions) == 1:
    print(f'\nAll manifests at {versions.pop()}')
else:
    print(f'\nMISMATCH: {versions}')
"
```

If there's a mismatch, stop and tell the user to run `npm run version:set -- X.Y.Z`.

## Step 2: Check git state

```bash
git status --short
git tag --sort=-v:refname | head -5
```

## Step 3: Regenerate derived files

```bash
./scripts/regenerate.sh
```

## Step 4: Full validation

```bash
./scripts/quality-check.sh --full
```

## Step 5: Report

Print a summary:

```
# Release Preflight Report

Version: X.Y.Z
Manifests consistent: YES/NO
Git clean: YES/NO

Regeneration: done
Validation: N/N passed

Verdict: READY / NOT READY
<blockers if any>

Run: npm run release -- X.Y.Z
```
