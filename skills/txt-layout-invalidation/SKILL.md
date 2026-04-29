---
name: txt-layout-invalidation
description: Use when debugging stale layout or working with ensureLayout, invalidateLayout, or the invalidation model in TextKit 1 and 2
license: MIT
---

# Text Layout Invalidation

Use this skill when the main question is why text layout or rendering did not refresh when expected.

Keep this file for the invalidation model, forced layout, and comparison tables. For symptom-based debugging, symbolic breakpoints, profiling, and viewport controller deep patterns, use [debugging-patterns.md](references/debugging-patterns.md).

## When to Use

- Layout is stale after edits.
- You need to know what actually invalidates layout.
- You are comparing TextKit 1 and TextKit 2 invalidation behavior.

## Quick Decision

- Need a symptom-first debugger -> `/skill txt-textkit-debug`
- Need the invalidation model itself -> stay here
- Need storage/editing lifecycle background -> `/skill txt-storage`

## Core Guidance

## TextKit 1 Invalidation Model

### What Invalidates Layout

| Trigger | Invalidates | Automatic? |
|---------|------------|------------|
| Character edit in NSTextStorage | Glyphs + layout in edited range | Yes (via processEditing) |
| Attribute change in NSTextStorage | Layout in changed range | Yes (via processEditing) |
| Text container size change | All layout in container | Yes |
| Exclusion path change | All layout in container | Yes |
| `invalidateGlyphs(forCharacterRange:)` | Glyphs for range | Manual call |
| `invalidateLayout(forCharacterRange:)` | Layout for range | Manual call |

### Invalidation Flow

```
NSTextStorage edit
    → processEditing()
        → NSLayoutManager.processEditing(for:edited:range:changeInLength:invalidatedRange:)
            → Marks glyphs invalid in affected range
            → Marks layout invalid in affected range
            → Defers actual recomputation (lazy)
```

**Layout is rebuilt lazily** — only when something queries the invalidated range (e.g., display, hit testing, rect calculation).

### Forcing Layout (TextKit 1)

```swift
let layoutManager: NSLayoutManager

// Entire container (expensive for large documents)
layoutManager.ensureLayout(for: textContainer)

// Specific character range
layoutManager.ensureLayout(forCharacterRange: range)

// Specific glyph range
layoutManager.ensureLayout(forGlyphRange: glyphRange)

// Specific rect in container (most efficient for visible content)
layoutManager.ensureLayout(forBoundingRect: visibleRect, in: textContainer)
```

### Forcing Glyph Generation

```swift
layoutManager.ensureGlyphs(forCharacterRange: range)
layoutManager.ensureGlyphs(forGlyphRange: glyphRange)
```

### Manual Invalidation

```swift
// Invalidate glyphs (forces regeneration)
layoutManager.invalidateGlyphs(
    forCharacterRange: range,
    changeInLength: 0,
    actualCharacterRange: nil
)

// Invalidate layout only (keeps glyphs, re-lays out)
layoutManager.invalidateLayout(
    forCharacterRange: range,
    actualCharacterRange: nil
)

// Invalidate display (just redraw, no layout recalc)
layoutManager.invalidateDisplay(forCharacterRange: range)
layoutManager.invalidateDisplay(forGlyphRange: glyphRange)
```

### What Does NOT Invalidate Layout

- Setting temporary attributes (`setTemporaryAttributes`) — visual only, no layout change
- Reading layout information (bounding rects, line fragments) — read-only queries
- Changing the text view's frame without changing the text container size
- Scrolling the text view

## TextKit 2 Invalidation Model

### What Invalidates Layout

| Trigger | Invalidates | Automatic? |
|---------|------------|------------|
| Edit via `performEditingTransaction` | Elements + layout fragments | Yes |
| `invalidateLayout(for: NSTextRange)` | Layout fragments in range | Manual call |
| Rendering attribute change | Visual only (no layout fragments) | Partial |
| Text container size change | All layout fragments | Yes |

### Invalidation Flow

```
performEditingTransaction {
    textStorage.replaceCharacters(...)
}
    → NSTextContentStorage regenerates affected NSTextParagraph elements
        → NSTextLayoutManager invalidates layout fragments for changed elements
            → NSTextViewportLayoutController re-layouts visible fragments
                → Delegate callbacks: willLayout → configureRenderingSurface × N → didLayout
```

### Forcing Layout (TextKit 2)

```swift
let textLayoutManager: NSTextLayoutManager

// Ensure layout for a range (EXPENSIVE — avoid for large ranges)
textLayoutManager.ensureLayout(for: textRange)

// Enumerate with layout guarantee
textLayoutManager.enumerateTextLayoutFragments(
    from: location,
    options: [.ensuresLayout]
) { fragment in
    return true
}

// Trigger viewport re-layout (preferred for visible content)
textLayoutManager.textViewportLayoutController.layoutViewport()
```

### Manual Invalidation

```swift
// Invalidate layout for range
textLayoutManager.invalidateLayout(for: textRange)

// Invalidate rendering (visual only, no layout recalc)
textLayoutManager.invalidateRenderingAttributes(for: textRange)
```

### What Does NOT Invalidate Layout

- Setting rendering attributes — visual only overlay
- Reading layout fragments — read-only
- Scrolling (viewport controller handles this automatically)

## TextKit 1 vs TextKit 2 Invalidation Comparison

| Aspect | TextKit 1 | TextKit 2 |
|--------|-----------|-----------|
| **Scope** | Can be full-document | Always viewport-scoped |
| **Granularity** | Glyph + layout | Element + fragment |
| **Lazy** | Yes (computed on query) | Yes (computed on viewport update) |
| **ensureLayout cost** | O(range_size) | O(range_size) — avoid for large ranges |
| **Full-doc layout** | `ensureLayout(for: container)` | **Don't do this** — viewport only |
| **Visual-only overlay** | Temporary attributes | Rendering attributes |
| **Overlay invalidates layout?** | No | No |
| **Edit wrapper** | `beginEditing()`/`endEditing()` | `performEditingTransaction { }` |

## What Rebuilds Text Storage

Text storage (`NSTextStorage`) is rebuilt when:

1. **Direct mutations** — `replaceCharacters(in:with:)`, `setAttributes(_:range:)`, etc.
2. **Setting `text`/`attributedText` on text view** — Replaces entire storage content
3. **User typing** — Inserts characters at cursor
4. **Paste/drop** — Inserts attributed content
5. **Undo/redo** — Restores previous state

Text storage is **NOT** rebuilt by:
- Layout invalidation (layout is separate from storage)
- Temporary/rendering attribute changes
- Container geometry changes
- Scrolling

## What Rebuilds Text Elements (TextKit 2)

`NSTextContentStorage` regenerates `NSTextParagraph` elements when:

1. **Text storage edit within `performEditingTransaction`** — Affected paragraphs regenerated
2. **Entire text storage replacement** — All elements regenerated

Elements are **NOT** regenerated by:
- `invalidateLayout(for:)` — Only layout fragments, not elements
- Rendering attribute changes
- Viewport scrolling

## Forcing a Complete Re-Render

### TextKit 1

```swift
// Nuclear option: invalidate everything
let fullRange = NSRange(location: 0, length: textStorage.length)
layoutManager.invalidateGlyphs(forCharacterRange: fullRange, changeInLength: 0, actualCharacterRange: nil)
layoutManager.invalidateLayout(forCharacterRange: fullRange, actualCharacterRange: nil)

// Or trigger via text storage (preferred)
textStorage.beginEditing()
textStorage.edited(.editedAttributes, range: fullRange, changeInLength: 0)
textStorage.endEditing()
```

### TextKit 2

```swift
// Invalidate all layout
textLayoutManager.invalidateLayout(for: textLayoutManager.documentRange)

// Then trigger viewport update
textLayoutManager.textViewportLayoutController.layoutViewport()
```

## Common Patterns

### Syntax Highlighting After Edit

```swift
// TextKit 1: In NSTextStorageDelegate
func textStorage(_ textStorage: NSTextStorage,
                 didProcessEditing editedMask: NSTextStorage.EditActions,
                 range editedRange: NSRange,
                 changeInLength delta: Int) {
    guard editedMask.contains(.editedCharacters) else { return }
    // Re-highlight affected range (extend to paragraph boundaries)
    let paragraphRange = (textStorage.string as NSString).paragraphRange(for: editedRange)
    highlightSyntax(in: paragraphRange, textStorage: textStorage)
}
```

### Deferred Layout Update

```swift
// TextKit 1: Don't query layout during editing
textStorage.beginEditing()
// ... multiple edits ...
textStorage.endEditing()
// NOW it's safe to query layout
let rect = layoutManager.usedRect(for: textContainer)
```

### Content Size Calculation

```swift
// TextKit 1
layoutManager.ensureLayout(for: textContainer)
let usedRect = layoutManager.usedRect(for: textContainer)
let contentSize = CGSize(width: usedRect.width + textContainer.lineFragmentPadding * 2,
                         height: usedRect.height + textView.textContainerInset.top + textView.textContainerInset.bottom)
```

## Common Pitfalls

1. **Querying layout during editing** — Layout may not be valid between `beginEditing()` and `endEditing()`.
2. **Full-document ensureLayout in TextKit 2** — Defeats the viewport optimization. Only ensure layout for visible ranges.
3. **Expecting rendering attributes to invalidate layout** — They don't. They're visual-only overlays.
4. **Not wrapping TextKit 2 edits in transaction** — Direct NSTextStorage edits without `performEditingTransaction` may not trigger proper element regeneration.
5. **Invalidating layout after every keystroke** — Layout invalidation happens automatically through the text storage editing lifecycle. Manual invalidation is only needed for non-storage changes.

## Going Deeper

Read `debugging-patterns.md` in this skill directory for:

- Symptom decision tree for stale layout diagnosis
- Symbolic breakpoints for invalidation tracking
- os_signpost instrumentation for profiling invalidation cost
- Viewport controller deep patterns (fragment recycling, scroll performance)
- Common bugs by symptom with fixes

## Related Skills

- Use `/skill txt-textkit-debug` for broader troubleshooting.
- Use `/skill txt-storage` when invalidation questions are really about editing lifecycle.
- Use `/skill txt-textkit2` for direct API details around layout fragments and viewport behavior.
