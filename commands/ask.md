---
description: Natural-language entry point for Apple Text. Use when the user has an Apple text question but does not know which skill or agent to invoke.
argument-hint: [question]
---

# Apple Text Ask

Use this command when the user has an Apple text problem but not a skill name.

## Quick Decision

- Broad Apple text question -> `/skill apple-text`
- Code review, anti-pattern scan, or risk audit -> `/skill apple-text-audit`
- Debugging stale layout, crashes, fallback, or rendering -> `/skill apple-text-textkit-diag`
- Choosing between text views -> `/skill apple-text-views`
- "How do I..." cookbook -> `/skill apple-text-recipes`
- TextKit 1/2 API details, layout, storage -> launch **textkit-reference** agent
- Editor features (Writing Tools, input, undo, paste, etc.) -> launch **editor-reference** agent
- Formatting, attributed strings, colors, Markdown -> launch **rich-text-reference** agent
- SwiftUI bridging, platform comparison, Core Text -> launch **platform-reference** agent

## Core Guidance

Treat `$ARGUMENTS` as the user's Apple text problem statement.

### Routing rules

1. If the request is clearly about code audit or scanning, use `/skill apple-text-audit`.
2. If the request is clearly about choosing a text view, use `/skill apple-text-views`.
3. If the request needs specific API details or reference content, launch the appropriate domain agent using the Agent tool with the `subagent_type` shown below.
4. If the request is broad or ambiguous but still obviously Apple text work, use `/skill apple-text`.
5. If the request is too ambiguous to route safely, ask exactly one concise clarification question.

### How to launch domain agents

Use the Agent tool with `subagent_type` set to one of these registered agents. Pass the user's question as the prompt. The agent runs in isolated context and returns a focused answer.

| Agent | subagent_type | Covers |
|-------|--------------|--------|
| textkit-reference | `apple-text:textkit-reference` | TextKit 1/2 APIs, layout, viewport, measurement, exclusion paths, storage, fallback |
| editor-reference | `apple-text:editor-reference` | Writing Tools, interaction, input, undo, find/replace, pasteboard, spelling, drag-drop, accessibility, Dynamic Type |
| rich-text-reference | `apple-text:rich-text-reference` | AttributedString, formatting, colors, Markdown, attachments, line breaking, bidi |
| platform-reference | `apple-text:platform-reference` | UIViewRepresentable, SwiftUI bridging, TextEditor 26+, AppKit vs UIKit, TextKit 1 vs 2 choice, Core Text, Foundation, parsing |
| textkit-auditor | `apple-text:textkit-auditor` | Automated code scan for TextKit anti-patterns |

Example: if the user asks "how do I measure text bounding rects", launch the agent like this:

```
Agent tool:
  subagent_type: "apple-text:textkit-reference"
  prompt: "How do I measure text bounding rects?"
```

### Why agents for reference

Domain agents run in isolated context. They have the full reference material as their instructions, answer the specific question, and return a focused response. This keeps the main conversation clean and avoids dumping hundreds of lines of API tables into context.

## Response style

- Do not explain the full plugin taxonomy unless the user asks.
- Do not drift into generic SwiftUI advice when the problem is really TextKit, UIKit, or AppKit text.
- Prefer acting over describing which route you might take.
