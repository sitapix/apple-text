---
description: Natural-language entry point for Apple Text. Use when the user has an Apple text question but does not know which skill or agent to invoke.
argument-hint: [question]
---

# Apple Text Ask

Use this command when the user has an Apple text problem but not a skill name.

## When to Use

Use this front door for broad Apple text questions, routing-heavy prompts, or requests that mention symptoms instead of APIs.

## Quick Decision

- Broad Apple text question -> `/skill apple-text`
- Code review, anti-pattern scan, or risk audit -> `/skill text-audit`
- Debugging stale layout, crashes, fallback, or rendering -> `/skill text-textkit-diag`
- Choosing between text views -> `/skill text-views`

## Core Guidance

Treat `$ARGUMENTS` as the user's Apple text problem statement.

Use the shared routing taxonomy from `skills/catalog.json`:

- `router`: broad intake and redirection
- `workflow`: guided scan or integration flow
- `diag`: symptom-first troubleshooting
- `decision`: choosing between competing approaches
- `ref`: direct API and behavior reference

Prefer these prominent entry points:

- `/skill apple-text` for broad non-SwiftUI Apple text questions
- `/skill text-audit` for code review, anti-pattern scans, fallback risk, or editor audits
- `/skill text-views` for "which view should I use?" questions
- `/skill text-textkit-diag` for debugging behavior, crashes, stale layout, or rendering failures

Jump directly to specialist skills when the request is already narrow:

- `/skill text-texteditor-26` for SwiftUI TextEditor with AttributedString (iOS 26+)
- `/skill text-representable` for SwiftUI wrappers around `UITextView` / `NSTextView`
- `/skill text-writing-tools` for Writing Tools integration
- `/skill text-layout-manager-selection` for TextKit 1 vs 2 choice or migration
- `/skill text-fallback-triggers` for compatibility-mode investigation
- `/skill text-attributed-string` for AttributedString vs NSAttributedString decisions

## Routing rules

1. If the request is clearly about code audit or scanning, use `/skill text-audit`.
2. If the request is clearly about choosing a text view, use `/skill text-views`.
3. If the request is clearly about a specific specialist area, jump directly to that skill instead of stopping at `apple-text`.
4. If the request is broad or ambiguous but still obviously Apple text work, use `/skill apple-text`.
5. If the request is too ambiguous to route safely, ask exactly one concise clarification question.

## Response style

- Do not explain the full plugin taxonomy unless the user asks.
- Do not drift into generic SwiftUI advice when the problem is really TextKit, UIKit, or AppKit text.
- Prefer acting over describing which route you might take.

## Related Skills

- `/skill apple-text` is the broad router when the right specialist is not obvious yet.
- `/skill text-audit` wraps the stricter `textkit-auditor` agent for review-style scans.
- `/skill text-textkit-diag` is the symptom-first debugger.
- `/skill text-views` is the decision skill for view selection and platform tradeoffs.
