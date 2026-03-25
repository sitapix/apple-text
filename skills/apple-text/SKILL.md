---
name: apple-text
description: Use when the user has an Apple text-system problem but the right specialist skill is not obvious, or when the request mixes multiple text subsystems
license: MIT
---

# Apple Text System Router

Use this router when the request is clearly about Apple text systems but not yet scoped to one specialist skill.

## When to Use

- The user has a broad Apple text problem and the right specialist is not obvious yet.
- The prompt mixes routing categories such as TextKit, UIKit/AppKit views, storage, invalidation, parsing, or Writing Tools.
- You need a high-signal route instead of an exhaustive taxonomy dump.

## Quick Decision

Choose the topic family first, then the right destination:

- Broad intake, audits, or debugging triage -> `/skill apple-text-audit`, `/skill apple-text-textkit-diag`
- View choice -> `/skill apple-text-views`
- "How do I..." cookbook -> `/skill apple-text-recipes`
- Apple-authored docs, official API detail, Swift diagnostics -> `/skill apple-text-apple-docs`
- TextKit runtime, layout, storage, measurement, fallback, exclusion paths -> launch **textkit-reference** agent
- Writing Tools, input, interaction, undo, paste, search, spelling, drag-drop, accessibility -> launch **editor-reference** agent
- Attributed content, formatting, Markdown, colors, attachments, line breaking, bidi -> launch **rich-text-reference** agent
- SwiftUI wrappers, TextEditor, platform comparison, Core Text, Foundation text, parsing -> launch **platform-reference** agent

## How to Route

**Registered skills** (invoke via `/skill`):

| Skill | Use for |
|-------|---------|
| `apple-text-audit` | Code review, anti-pattern scans, fallback risk |
| `apple-text-views` | "Which text view should I use?" |
| `apple-text-textkit-diag` | Debugging symptoms, crashes, stale layout |
| `apple-text-recipes` | Quick "how do I..." answers and snippets |
| `apple-text-apple-docs` | Apple-authored docs, official API wording, Swift diagnostics |

**Domain agents** (launch via Agent tool with the given `subagent_type`):

| Agent | subagent_type | Use for |
|-------|--------------|---------|
| textkit-reference | `apple-text:textkit-reference` | TextKit 1/2 APIs, layout mechanics, viewport rendering, measurement, exclusion paths, storage, fallback triggers |
| editor-reference | `apple-text:editor-reference` | Writing Tools, text interaction, input, undo, find/replace, pasteboard, spelling, drag-drop, accessibility, Dynamic Type |
| rich-text-reference | `apple-text:rich-text-reference` | AttributedString, formatting attributes, colors, Markdown, attachments, line breaking, bidirectional text |
| platform-reference | `apple-text:platform-reference` | UIViewRepresentable wrappers, SwiftUI bridging, TextEditor iOS 26+, AppKit vs UIKit, TextKit 1 vs 2 choice, Core Text, Foundation text, parsing |
| textkit-auditor | `apple-text:textkit-auditor` | Automated code scan for TextKit anti-patterns |

To launch an agent, pass the user's question as the prompt. The agent runs in isolated context and returns a focused answer without polluting the main conversation.

## Core Guidance

- Use the **topic family** to pick the subsystem.
- Use the **role** to pick the answer shape:
  - `workflow` means guided implementation or review steps.
  - `diag` means broken behavior and symptom-first debugging.
  - `decision` means tradeoffs or stack choice.
  - `ref` means direct API or mechanics once the subsystem is already known.
- For **reference lookups**, prefer launching the domain agent over loading skill content inline. Agents run in isolated context and return focused answers.

## Multi-Domain Questions

When a question spans two domains, route to the **diagnostic skill first** to isolate the root cause, then to the appropriate reference agent. Don't launch two agents simultaneously for the same question.

| Symptom | Route |
|---------|-------|
| "TextKit 2 but Writing Tools not appearing" | `/skill apple-text-textkit-diag` first (may be fallback), then **editor-reference** if Writing Tools API is the issue |
| "UIViewRepresentable text view has stale layout" | `/skill apple-text-textkit-diag` first (layout invalidation), then **platform-reference** if bridging lifecycle is the issue |
| "Attributed string renders differently in SwiftUI vs UIKit" | **platform-reference** agent (SwiftUI bridging covers this), then **rich-text-reference** if attribute compatibility is the issue |

## Context Management

When handling multiple text questions in one session, prefer launching **domain agents** over inline skills for reference lookups. Agents run in isolated context and keep the main conversation window clean. Reserve inline skills (`apple-text-recipes`, `apple-text-textkit-diag`) for quick answers that directly resolve the question.

## Related Skills and Agents

- Use `/skill apple-text-audit` for code-review style scans and risk ranking.
- Use `/skill apple-text-textkit-diag` for debugging symptoms before drilling into APIs.
- Use `/skill apple-text-views` for text-view selection and capability tradeoffs.
- Launch **textkit-reference** agent for TextKit 1/2 API details.
- Launch **platform-reference** agent for TextKit 1 vs 2 choice or SwiftUI bridging.
