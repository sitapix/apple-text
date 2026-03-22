---
title: "Commands And Agents"
sidebar:
  order: 9
---

1 command and 5 agents.

Use commands for broad questions. Use reference agents for focused API lookups in isolated context. Use the auditor agent for code review scans.

## Commands

### `apple-text:ask`

Natural-language entry point for Apple Text. Use when the user has an Apple text question but does not know which skill or agent to invoke.

## Agents

### `editor-reference`

Look up editor feature APIs — Writing Tools, text interaction, text input, undo/redo, find/replace, pasteboard, spelling, drag-and-drop, accessibility, and Dynamic Type.

### `platform-reference`

Look up SwiftUI bridging, UIViewRepresentable wrappers, TextEditor iOS 26+, AppKit vs UIKit differences, TextKit 1 vs 2 selection, Core Text, Foundation text utilities, and parsing.

### `rich-text-reference`

Look up attributed string APIs, text formatting attributes, colors, Markdown rendering, text attachments, line breaking, and bidirectional text.

### `textkit-auditor`

Use this agent when the user mentions TextKit review, text view code review, or asks to scan for TextKit anti-patterns. Automatically scans Swift/Objective-C code for TextKit issues — detects TextKit 1 fallback triggers, deprecated glyph APIs, missing editing lifecycle calls, unsafe text storage patterns, and Writing Tools compatibility problems.

### `textkit-reference`

Look up TextKit 1/2 APIs, layout mechanics, viewport rendering, text measurement, exclusion paths, fallback triggers, and text storage patterns.
