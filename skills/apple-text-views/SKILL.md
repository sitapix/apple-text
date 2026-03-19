---
name: apple-text-views
description: Use when choosing among Apple text views or deciding whether a problem belongs in SwiftUI text, UIKit/AppKit text views, or TextKit 1 vs TextKit 2 mode — covers Text, TextField, TextEditor, UILabel, UITextView, NSTextView, field editor, and platform-specific tradeoffs.
license: MIT
---

# Apple Text Views

Use this skill when the main question is "which text view should I use?" or when behavior depends on the capabilities of a specific view class.

## When to Use

- You are choosing among SwiftUI, UIKit, and AppKit text views.
- The question is mostly about capability tradeoffs, not low-level TextKit APIs.
- You need to know whether the problem belongs in `Text`, `TextField`, `TextEditor`, `UITextView`, or `NSTextView`.

## Quick Decision

**Read-only text in SwiftUI** -> `Text`

**Single-line input in SwiftUI** -> `TextField`

**Multi-line plain-text editing in SwiftUI** -> `TextEditor`

**Rich text, TextKit access, syntax highlighting, attachments, or custom layout on iOS** -> `UITextView`

**Rich text, field editor behavior, text tables, rulers, printing, or advanced desktop editing on macOS** -> `NSTextView`

**Static UIKit label** -> `UILabel`

**Simple UIKit/AppKit form input** -> `UITextField` / `NSTextField`

## Core Guidance

## Decision Guide

### 1. Are you editing text?

**No** -> Prefer `Text` or `UILabel`.

**Yes** -> Go to step 2.

### 2. Is plain-text SwiftUI editing enough?

Use `TextField` or `TextEditor` when all of these are true:

- You only need plain `String` editing
- You do not need TextKit APIs
- You do not need inline attachments or rich attributed editing
- You can accept SwiftUI's editing limitations

If any of those are false, move to `UITextView` or `NSTextView`.

### 3. Do you need TextKit or attributed text control?

Use `UITextView` / `NSTextView` when you need:

- `NSAttributedString` or advanced `AttributedString` bridging
- Layout inspection or fragment-level queries
- Syntax highlighting or custom rendering
- Inline attachments or custom attachment views
- Rich editing commands, menus, or selection behavior
- Writing Tools coordination beyond basic defaults

### 4. Do you need TextKit 2 specifically?

Prefer TextKit 2 when you need:

- Viewport-based layout
- `NSTextLayoutManager`
- Writing Tools inline behavior
- Modern rendering and layout APIs

Stay on TextKit 1 when you explicitly need:

- Glyph APIs
- Mature multi-container patterns
- Legacy code that depends on `NSLayoutManager`
- AppKit features still tied to older APIs

For the actual TextKit 1 vs 2 choice, jump to `/skill apple-text-layout-manager-selection`.

## Common Decisions

**Chat composer that grows vertically** -> `TextField(axis: .vertical)` first, `UITextView` if you need richer editing behavior.

**Notes editor with rich text** -> `UITextView` on iOS, `NSTextView` on macOS.

**Syntax-highlighted code editor** -> `UITextView` / `NSTextView`, usually with TextKit 2 if your feature set allows it.

**Simple settings field** -> `TextField`, `UITextField`, or `NSTextField`.

**Markdown display only** -> `Text` if the supported inline subset is enough; otherwise use TextKit-backed rendering.

**Need AppKit-only document editor features** -> `NSTextView`.

## Related Skills

- For the full catalog, capabilities tables, and platform-by-platform reference, see [reference.md](reference.md).
- For usage-oriented examples, see [examples.md](examples.md).
- For wrapping `UITextView` or `NSTextView` in SwiftUI, use `/skill apple-text-representable`.
- For TextKit 1 vs 2 architecture, use `/skill apple-text-textkit1-ref` or `/skill apple-text-textkit2-ref`.
- For a migration or performance decision, use `/skill apple-text-layout-manager-selection`.
- For debugging weird editor behavior, use `/skill apple-text-textkit-diag`.
