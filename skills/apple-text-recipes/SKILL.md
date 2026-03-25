---
name: apple-text-recipes
description: Use when building common text features or looking up quick recipes — background colors, line numbers, character limits, links, placeholders
license: MIT
---

# Text Recipes Cookbook

Quick, working solutions to the most common "how do I..." questions about Apple text views.

## When to Use

- User asks "how do I [specific text thing]?" and you need a direct answer.
- You need a working code snippet, not architecture guidance.
- The question maps to a common text task that doesn't need a full skill.

## Quick Index

Find the recipe number below, then see [recipes.md](recipes.md) for the code.

| # | Recipe | Framework |
|---|--------|-----------|
| 1 | Background color behind a paragraph | TextKit 1 / TextKit 2 |
| 2 | Line numbers in a text view | TextKit 1 |
| 3 | Character/word limit on input | UITextView delegate |
| 4 | Text wrapping around an image | NSTextContainer |
| 5 | Clickable links (not editable) | UITextView |
| 6 | Clickable links (editable) | UITextView delegate |
| 7 | Placeholder text in UITextView | UITextView |
| 8 | Auto-growing text view (no scroll) | Auto Layout |
| 9 | Highlight search results | Temporary attributes |
| 10 | Strikethrough text | NSAttributedString |
| 11 | Letter spacing (tracking/kern) | NSAttributedString |
| 12 | Different line heights per paragraph | NSParagraphStyle |
| 13 | Indent first line of paragraphs | NSParagraphStyle |
| 14 | Bullet/numbered lists | NSTextList / manual |
| 15 | Read-only styled text | UITextView |
| 16 | Detect data (phones, URLs, dates) | UITextView |
| 17 | Custom cursor color | UITextView |
| 18 | Disable text selection | UITextView |
| 19 | Programmatically scroll to range | UITextView |
| 20 | Get current line number | TextKit 1 |

## Platform Coverage

Recipes show UIKit (iOS) code by default. See the **Platform Note** at the top of [recipes.md](recipes.md) for a UIKit → AppKit translation table. Recipes that use only NSTextStorage, NSAttributedString, and NSParagraphStyle work on both platforms without changes.

## Quick Decision

- Need architecture guidance, not a snippet -> `/skill apple-text` (router)
- Need paragraph style details (line height, spacing) -> `/skill apple-text-line-breaking`
- Need formatting attribute catalog -> `/skill apple-text-formatting-ref`
- Need measurement or sizing -> `/skill apple-text-measurement`

## Related Skills and Agents

- For measurement, exclusion paths, or layout details -> launch **textkit-reference** agent
- For paragraph style, line breaking, or formatting attributes -> launch **rich-text-reference** agent
- For attachment views (tables, custom views) -> launch **rich-text-reference** agent
- For find/replace or editor interaction details -> launch **editor-reference** agent
