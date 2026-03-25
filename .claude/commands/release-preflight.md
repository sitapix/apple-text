---
description: Pre-release validation with guided fixes — checks versions, regenerates derived files, runs full validation, and reports blockers
allowed-tools: Agent, Read, Bash
model: sonnet
---

# Release Preflight

Validate everything before running `npm run release -- X.Y.Z`. Catches problems early with fix suggestions so the release script doesn't fail mid-pipeline.

## Phase 1: Version Consistency

Launch general-purpose agent:
- **Description**: "Check version consistency"
- **Prompt**:
  ```
  Read /Users/steven/dev/apple-text/tasks/step-1-release-preflight-version.md and execute all instructions. Working directory is /Users/steven/dev/apple-text.
  ```

**Capture**: Current version, manifest consistency, git state, blockers.

If there are version mismatches, **stop and report** — the user needs to run `npm run version:set -- X.Y.Z` first.

## Phase 2: Regenerate Derived Files

Launch general-purpose agent:
- **Description**: "Regenerate derived files"
- **Prompt**:
  ```
  Read /Users/steven/dev/apple-text/tasks/step-2-release-preflight-regenerate.md and execute all instructions. Working directory is /Users/steven/dev/apple-text.
  ```

**Capture**: What was rebuilt, staleness check results.

If MCP server build fails, **stop and report** — this blocks everything downstream.

## Phase 3: Full Validation

Launch general-purpose agent:
- **Description**: "Run full validation suite"
- **Prompt**:
  ```
  Read /Users/steven/dev/apple-text/tasks/step-3-release-preflight-validate.md and execute all instructions. Working directory is /Users/steven/dev/apple-text.
  ```

**Capture**: Per-check pass/fail, failure details, fix suggestions.

## Verdict

Combine all three phases into a final report:

```
# Release Preflight Report

## Current State
Version: X.Y.Z
Manifests consistent: YES/NO
Git clean: YES/NO

## Regeneration
Files rebuilt: N
All artifacts current: YES/NO

## Validation
Checks passed: N/8
Checks failed: N/8

## Verdict: READY / NOT READY

<If NOT READY, list blockers in priority order with fix commands>
<If READY>
Run: npm run release -- X.Y.Z
```

Print the full report. Do not write it to a file unless asked.
