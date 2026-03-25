---
description: Audit all skills for quality gaps — freshness, descriptions, routing, lint — and produce a prioritized fix list
allowed-tools: Agent, Read, Bash
model: sonnet
---

# Skill Quality Audit

Run all quality checks across every skill and produce a unified, prioritized report.

## Phase 1: Freshness

Launch general-purpose agent:
- **Description**: "Check skill freshness"
- **Prompt**:
  ```
  Read /Users/steven/dev/apple-text/tasks/step-1-skill-quality-freshness.md and execute all instructions. Working directory is /Users/steven/dev/apple-text.
  ```

**Capture**: Stale/fresh skill list with dates.

## Phase 2: Lint + Validation

Launch general-purpose agent:
- **Description**: "Lint skills and validate routing"
- **Prompt**:
  ```
  Read /Users/steven/dev/apple-text/tasks/step-2-skill-quality-lint.md and execute all instructions. Working directory is /Users/steven/dev/apple-text.
  ```

**Capture**: Repo lint status, description errors/warnings, dataset validation, routing eval results.

## Phase 3: Consolidated Report

Read `/Users/steven/dev/apple-text/tasks/step-3-skill-quality-report.md` for the report template.

Using the results from Phase 1 and Phase 2, produce the consolidated report yourself following the template in step 3. Classify findings into P0/P1/P2 tiers, group by skill, and identify quick wins.

## Output

Print the full quality report to the user. Do not write it to a file unless asked.
