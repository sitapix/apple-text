---
title: "Commands And Agents"
sidebar:
  order: 9
---

1 command and 1 agent.

Use commands for broad questions. Use agents for specialist scans over real code.

## Commands

### `apple-text:ask`

Natural-language entry point for Apple Text. Use when the user has an Apple text question but does not know which skill or agent to invoke.

## Agents

### `textkit-auditor`

Use this agent when the user mentions TextKit review, text view code review, or asks to scan for TextKit anti-patterns. Automatically scans Swift/Objective-C code for TextKit issues — detects TextKit 1 fallback triggers, deprecated glyph APIs, missing editing lifecycle calls, unsafe text storage patterns, and Writing Tools compatibility problems.
