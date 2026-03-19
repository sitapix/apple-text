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

- Code review, risk scan, or "audit this editor" -> `/skill text-audit`
- Debugging stale layout, crashes, fallback, or rendering -> `/skill text-textkit-diag`
- Choosing between `TextEditor`, `UITextView`, `NSTextView`, or related views -> `/skill text-views`
- Wrapping UIKit/AppKit text views inside SwiftUI -> `/skill text-representable`
- Choosing TextKit 1 vs TextKit 2 -> `/skill text-layout-manager-selection`
- Writing Tools integration or coordinator APIs -> `/skill text-writing-tools`
- SwiftUI TextEditor with AttributedString (iOS 26+) -> `/skill text-texteditor-26`
- Need glyph access or dropping to Core Text -> `/skill text-core-text`
- Spell checking, autocorrect, or text completion -> `/skill text-spell-autocorrect`
- Text drag and drop customization -> `/skill text-drag-drop`
- RTL, bidirectional text, or writing direction -> `/skill text-bidi`
- Direct API reference already clear -> jump to the matching `*-ref` skill

## Core Guidance

Use the routing categories from `skills/catalog.json` rather than memorizing ad hoc phrase mappings:

- `workflow`: `text-audit`, `text-representable`, `text-writing-tools`
- `diag`: `text-textkit-diag`, `text-fallback-triggers`
- `decision`: `text-views`, `text-layout-manager-selection`, `text-attributed-string`, `text-parsing`
- `ref`: direct API/reference skills such as `text-textkit2-ref`, `text-input-ref`, `text-formatting-ref`, and `text-attachments-ref`

Major route classes:

- Architecture and storage: `/skill text-textkit1-ref`, `/skill text-textkit2-ref`, `/skill text-storage`, `/skill text-layout-invalidation`, `/skill text-core-text`
- Views and platform boundaries: `/skill text-views`, `/skill text-representable`, `/skill text-swiftui-bridging`, `/skill text-appkit-vs-uikit`, `/skill text-texteditor-26`
- Content and formatting: `/skill text-attributed-string`, `/skill text-formatting-ref`, `/skill text-colors`, `/skill text-markdown`, `/skill text-parsing`
- Editing and input: `/skill text-input-ref`, `/skill text-writing-tools`, `/skill text-attachments-ref`, `/skill text-spell-autocorrect`
- Editor features: `/skill text-undo`, `/skill text-find-replace`, `/skill text-pasteboard`, `/skill text-interaction`, `/skill text-drag-drop`
- Internationalization: `/skill text-bidi`
- Accessibility: `/skill text-accessibility`, `/skill text-dynamic-type`, `/skill text-colors`
- Troubleshooting and review: `/skill text-textkit-diag`, `/skill text-fallback-triggers`, `/skill text-audit`

## Related Skills

- Use `/skill text-audit` for code-review style scans and risk ranking.
- Use `/skill text-textkit-diag` for debugging symptoms before drilling into APIs.
- Use `/skill text-views` for text-view selection and capability tradeoffs.
- Use `/skill text-layout-manager-selection` for TextKit 1 vs TextKit 2 choice.
- Use `/skill text-textkit1-ref` or `/skill text-textkit2-ref` when the API family is already known.
