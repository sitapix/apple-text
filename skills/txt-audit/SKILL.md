---
name: txt-audit
description: Use when reviewing Apple text code for TextKit fallback risk, editing lifecycle bugs, deprecated APIs, or Writing Tools breakage
license: MIT
---

# Text Audit

Use this skill when the user wants a review-style scan instead of a reference answer.

## When to Use

- "Audit this editor"
- "Scan for TextKit issues"
- "Review this text view code for fallback, performance, or Writing Tools risks"

## Quick Decision

- Need concrete findings from code -> stay here
- Need symptom-first debugging without a code scan -> `/skill txt-textkit-debug`
- Need API explanation instead of review findings -> use the relevant specialist skill (e.g. `/skill txt-textkit2`, `/skill txt-input`, `/skill txt-attributed-string`, `/skill txt-swiftui-bridging`)

## Core Guidance

Audit the Apple text system code in `$ARGUMENTS`.

If no arguments are supplied, audit the current workspace for TextKit, UIKit/AppKit text view, text input, and Writing Tools issues.

Use the inline checklist below to run the scan.

## Inline Audit Checklist

Work through these items in order. Each maps to the severity rubric the full auditor uses. Skip items that do not apply to the codebase.

### P0 — Critical (broken behavior, crashes, data loss)

1. **TextKit 1 fallback triggers.** Search for `.layoutManager` access on UITextView or NSTextView. Any access without checking `.textLayoutManager` first forces an irreversible fallback to TextKit 1. Also check `textContainer.layoutManager`.
2. **Missing `edited()` in NSTextStorage subclasses.** Every override of `replaceCharacters(in:with:)` and `setAttributes(_:range:)` must call `edited(_:range:changeInLength:)` with the correct mask and delta. Without it, layout managers never learn about changes.
3. **Character mutation in `didProcessEditing`.** The `didProcessEditing` delegate is attributes-only. Character changes here corrupt the editing lifecycle and can crash.
4. **Wrong `changeInLength` values.** Compare the delta passed to `edited()` against the actual string length change. Off-by-one or encoding confusion (Swift count vs NSString length) causes range errors and layout corruption.
5. **Missing `beginEditing()`/`endEditing()` around batched mutations.** Without batching, each mutation triggers a separate `processEditing()` pass — multiple layout invalidations that can crash mid-batch if ranges shift.

### P1 — Important (correctness, deprecation, performance)

6. **Deprecated glyph APIs without TextKit 1 guard.** `glyph(at:)`, `glyphRange(for:)`, `numberOfGlyphs`, `drawGlyphs(forGlyphRange:at:)` — these are TextKit 1 only. Use them without confirming the editor is on TextKit 1 and the code will crash or silently fail on TextKit 2.
7. **`ensureLayout(for: textContainer)` on large documents.** Forces full-document layout. Use range-scoped or rect-scoped variants instead.
8. **Full-document enumeration with `.ensuresLayout`.** `enumerateTextLayoutFragments` with `.ensuresLayout` over the full document range defeats viewport optimization.
9. **Missing `allowsNonContiguousLayout` for TextKit 1.** Large documents need this for acceptable scroll performance.
10. **`NSLinguisticTagger` usage.** Replaced by the NaturalLanguage framework. Deprecated since iOS 14.
11. **Old `UIMenuController` usage.** Replaced by `UIEditMenuInteraction` in iOS 16.
12. **Direct NSTextStorage edits without `performEditingTransaction` (TextKit 2).** Element tree may not regenerate correctly. Wrap all mutations in `performEditingTransaction { }`.

### P2 — Improvement (compatibility, maintainability)

13. **Explicit TextKit 1 creation without justification.** Check whether there is a documented reason to stay on TextKit 1. If not, flag for review.
14. **Missing `writingToolsIgnoredRangesIn` for code or quote content.** Code blocks and blockquotes should be excluded from Writing Tools rewrites.
15. **No `isWritingToolsActive` check before programmatic text changes.** Programmatic edits during a Writing Tools session can corrupt the rewrite operation.
16. **String/NSString count confusion in range calculations.** `String.count` counts Characters (grapheme clusters). `NSString.length` counts UTF-16 code units. Mixing them produces wrong ranges, especially with emoji and complex scripts.
17. **Thread-unsafe text storage access.** NSTextStorage must be accessed from the main thread (or the thread it was created on). Background access without coordination is a race condition.
18. **Missing `performEditingTransaction` wrapper for TextKit 2 edits.** Even if the edit "works" today, skipping the transaction is a latent bug.

## Reporting Findings

Return findings ordered by severity with file references and concrete fixes.

```
## TextKit Audit Results

### P0 — Critical
- [file:line] Description of issue
  **Fix:** How to fix

### P1 — Important
- [file:line] Description of issue
  **Fix:** How to fix

### P2 — Improvement
- [file:line] Description of issue
  **Fix:** How to fix

### Summary
- X files scanned
- Y issues found (Z critical, W important, V improvements)
```

If no issues are found, say so explicitly and note any residual blind spots (e.g., "no Objective-C files scanned", "no Writing Tools configuration found").

## Related Skills

- Use `/skill txt-textkit-debug` for symptom-first troubleshooting.
- Use `/skill txt-fallback-triggers` for the full fallback trigger catalog.
- Use `/skill txt-storage` for editing lifecycle and storage details.
- Use `/skill txt-views` when the question is "which text view should I use?" rather than a code review.
