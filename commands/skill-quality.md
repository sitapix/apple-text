---
description: Audit all skills for quality gaps — freshness, descriptions, routing, lint — and produce a prioritized fix list
allowed-tools: Bash, Read
model: haiku
---

# Skill Quality Audit

Run the quality check script and interpret the results.

## Step 1: Run checks

```bash
./scripts/quality-check.sh
```

Capture the full output regardless of exit code.

## Step 2: Report

Print the results to the user. If there are FAILs, group them by check name and suggest fixes. If all pass, say so briefly.
