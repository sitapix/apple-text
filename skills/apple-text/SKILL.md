---
name: apple-text
description: Use when working with ANY non-SwiftUI text rendering, editing, or display — TextKit 1/2 architecture, UITextView, NSTextView, NSLayoutManager, NSTextLayoutManager, text storage, attributed strings, text input, layout invalidation, Writing Tools, Markdown, TextKit fallback, AppKit vs UIKit differences, parsing, viewport rendering, UIViewRepresentable text view bridging, choosing the right text view, or auditing text code. Routes to specialized text system skills.
license: MIT
---

# Apple Text System Router

Use this router when the request is clearly about Apple text systems but not yet scoped to one specialist skill.

## When to Use

- The user has a broad Apple text problem and the right specialist is not obvious yet.
- The prompt mixes routing categories such as TextKit, UIKit/AppKit views, storage, invalidation, parsing, or Writing Tools.
- You need a high-signal route instead of an exhaustive taxonomy dump.

## Quick Decision

- Code review, risk scan, or "audit this editor" -> `/skill apple-text-audit`
- Debugging stale layout, crashes, fallback, or rendering -> `/skill apple-text-textkit-diag`
- Choosing between `TextEditor`, `UITextView`, `NSTextView`, or related views -> `/skill apple-text-views`
- Wrapping UIKit/AppKit text views inside SwiftUI -> `/skill apple-text-representable`
- Choosing TextKit 1 vs TextKit 2 -> `/skill apple-text-layout-manager-selection`
- Writing Tools integration or coordinator APIs -> `/skill apple-text-writing-tools`
- SwiftUI TextEditor with AttributedString (iOS 26+) -> `/skill apple-text-texteditor-26`
- Need glyph access or dropping to Core Text -> `/skill apple-text-core-text`
- Spell checking, autocorrect, or text completion -> `/skill apple-text-spell-autocorrect`
- Text drag and drop customization -> `/skill apple-text-drag-drop`
- RTL, bidirectional text, or writing direction -> `/skill apple-text-bidi`
- Direct API reference already clear -> jump to the matching `*-ref` skill

## Core Guidance

Use the routing categories from `skills/catalog.json` rather than memorizing ad hoc phrase mappings:

- `workflow`: `apple-text-audit`, `apple-text-representable`, `apple-text-writing-tools`
- `diag`: `apple-text-textkit-diag`, `apple-text-fallback-triggers`
- `decision`: `apple-text-views`, `apple-text-layout-manager-selection`, `apple-text-attributed-string`, `apple-text-parsing`
- `ref`: direct API/reference skills such as `apple-text-textkit2-ref`, `apple-text-input-ref`, `apple-text-formatting-ref`, and `apple-text-attachments-ref`

Major route classes:

- Architecture and storage: `/skill apple-text-textkit1-ref`, `/skill apple-text-textkit2-ref`, `/skill apple-text-storage`, `/skill apple-text-layout-invalidation`, `/skill apple-text-core-text`
- Views and platform boundaries: `/skill apple-text-views`, `/skill apple-text-representable`, `/skill apple-text-swiftui-bridging`, `/skill apple-text-appkit-vs-uikit`, `/skill apple-text-texteditor-26`
- Content and formatting: `/skill apple-text-attributed-string`, `/skill apple-text-formatting-ref`, `/skill apple-text-colors`, `/skill apple-text-markdown`, `/skill apple-text-parsing`
- Editing and input: `/skill apple-text-input-ref`, `/skill apple-text-writing-tools`, `/skill apple-text-attachments-ref`, `/skill apple-text-spell-autocorrect`
- Editor features: `/skill apple-text-undo`, `/skill apple-text-find-replace`, `/skill apple-text-pasteboard`, `/skill apple-text-interaction`, `/skill apple-text-drag-drop`
- Internationalization: `/skill apple-text-bidi`
- Accessibility: `/skill apple-text-accessibility`, `/skill apple-text-dynamic-type`, `/skill apple-text-colors`
- Troubleshooting and review: `/skill apple-text-textkit-diag`, `/skill apple-text-fallback-triggers`, `/skill apple-text-audit`

## Related Skills

- Use `/skill apple-text-audit` for code-review style scans and risk ranking.
- Use `/skill apple-text-textkit-diag` for debugging symptoms before drilling into APIs.
- Use `/skill apple-text-views` for text-view selection and capability tradeoffs.
- Use `/skill apple-text-layout-manager-selection` for TextKit 1 vs TextKit 2 choice.
- Use `/skill apple-text-textkit1-ref` or `/skill apple-text-textkit2-ref` when the API family is already known.
