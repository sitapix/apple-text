---
name: txt-measurement
description: Use when text is clipping, truncating unexpectedly, or when measuring text size, calculating boundingRect, or sizing views to fit text content
license: MIT
---

# Text Measurement & Sizing Reference

Use this skill when you need to know how big text will be before (or after) rendering it.

## When to Use

- You need `boundingRect` or `size(withAttributes:)` and it's returning wrong values.
- You're sizing a view to fit text content.
- You need line-by-line metrics (line heights, fragment rects).
- You're calculating `intrinsicContentSize` for a custom text view.
- Text is clipping, truncating unexpectedly, or leaving extra space.

## Quick Decision

- Quick single-line measurement -> `NSAttributedString.size()`
- Multi-line measurement in a constrained width -> `boundingRect(with:options:context:)`
- Per-line metrics in TextKit 1 -> `NSLayoutManager.enumerateLineFragments`
- Per-line metrics in TextKit 2 -> `NSTextLayoutManager.enumerateTextLayoutFragments`
- "How tall should my text view be?" -> use the text system, not manual calculation

## The #1 Mistake

```swift
// WRONG — returns single-line size, ignores line wrapping
let size = myString.size(withAttributes: attrs)

// RIGHT — constrains to width, enables multi-line measurement
let rect = myString.boundingRect(
    with: CGSize(width: maxWidth, height: .greatestFiniteMagnitude),
    options: [.usesLineFragmentOrigin, .usesFontLeading],
    attributes: attrs,
    context: nil
)
let measuredSize = CGSize(width: ceil(rect.width), height: ceil(rect.height))
```

**You must pass `.usesLineFragmentOrigin`** for multi-line measurement. Without it, `boundingRect` measures as if the text is a single line.

## NSString / NSAttributedString Measurement

### size(withAttributes:) / size()

```swift
// NSString — single line only
let size = "Hello".size(withAttributes: [.font: UIFont.systemFont(ofSize: 17)])

// NSAttributedString — single line only
let size = attributedString.size()
```

**Limitations:** Always returns the single-line size. No width constraint. Useless for multi-line text.

**Use for:** Badge labels, single-line metrics, width-only calculations.

### boundingRect (the workhorse)

```swift
// NSString version
let rect = string.boundingRect(
    with: CGSize(width: containerWidth, height: .greatestFiniteMagnitude),
    options: [.usesLineFragmentOrigin, .usesFontLeading],
    attributes: [.font: font, .paragraphStyle: paragraphStyle],
    context: nil
)

// NSAttributedString version (attributes come from the string itself)
let rect = attributedString.boundingRect(
    with: CGSize(width: containerWidth, height: .greatestFiniteMagnitude),
    options: [.usesLineFragmentOrigin, .usesFontLeading],
    context: nil
)
```

**Always `ceil()` the result.** `boundingRect` returns fractional values. Passing them directly to layout causes 1-pixel clipping:

```swift
let height = ceil(rect.height)  // Not rect.height
let width = ceil(rect.width)    // Not rect.width
```

### NSStringDrawingOptions

| Option | Effect | When to use |
|--------|--------|-------------|
| `.usesLineFragmentOrigin` | Measures multi-line text using line fragment origins | **Almost always.** Without this, you get single-line measurement. |
| `.usesFontLeading` | Includes font leading (inter-line spacing from the font) in height | **Almost always.** Matches what UILabel/UITextView actually renders. |
| `.usesDeviceMetrics` | Uses actual glyph bounds instead of typographic bounds | Pixel-perfect rendering. Rarely needed. |
| `.truncatesLastVisibleLine` | Accounts for truncation ellipsis in height-constrained measurement | When you're constraining height and want accurate truncated size. |

**The standard combo:** `[.usesLineFragmentOrigin, .usesFontLeading]` — use this by default.

### NSStringDrawingContext

For auto-shrinking text (like UILabel's `adjustsFontSizeToFitWidth`):

```swift
let context = NSStringDrawingContext()
context.minimumScaleFactor = 0.5  // Allow shrinking to 50%

let rect = attributedString.boundingRect(
    with: constrainedSize,
    options: [.usesLineFragmentOrigin, .usesFontLeading],
    context: context
)

// After measurement:
let actualScale = context.actualScaleFactor  // What scale was applied
let actualBounds = context.totalBounds       // Where text actually landed
```

## TextKit 1 Measurement (NSLayoutManager)

When you need per-line metrics, not just total size.

### Total content size

```swift
// Force layout for entire container
layoutManager.ensureLayout(for: textContainer)

// Get used rect — the actual area text occupies
let usedRect = layoutManager.usedRect(for: textContainer)
let contentHeight = ceil(usedRect.height)
```

### Specific range size

```swift
let glyphRange = layoutManager.glyphRange(forCharacterRange: charRange,
                                           actualCharacterRange: nil)
let boundingRect = layoutManager.boundingRect(forGlyphRange: glyphRange,
                                               in: textContainer)
```

### Line-by-line enumeration

```swift
let fullGlyphRange = layoutManager.glyphRange(for: textContainer)
layoutManager.enumerateLineFragments(forGlyphRange: fullGlyphRange) {
    rect, usedRect, container, glyphRange, stop in
    // rect: full line fragment rectangle (includes padding)
    // usedRect: actual area used by glyphs (tighter)
    // glyphRange: which glyphs are on this line
    print("Line height: \(usedRect.height), y: \(usedRect.origin.y)")
}
```

### Line count

```swift
func lineCount(for layoutManager: NSLayoutManager,
               in textContainer: NSTextContainer) -> Int {
    layoutManager.ensureLayout(for: textContainer)
    var count = 0
    let fullRange = layoutManager.glyphRange(for: textContainer)
    layoutManager.enumerateLineFragments(forGlyphRange: fullRange) { _, _, _, _, _ in
        count += 1
    }
    return count
}
```

## TextKit 2 Measurement (NSTextLayoutManager)

### Total content size

```swift
textLayoutManager.ensureLayout(for: textLayoutManager.documentRange)
let usageBounds = textLayoutManager.usageBoundsForTextContainer
let contentHeight = ceil(usageBounds.height)
```

### Layout fragment enumeration

```swift
textLayoutManager.enumerateTextLayoutFragments(
    from: textLayoutManager.documentRange.location,
    options: [.ensuresLayout]
) { fragment in
    let frame = fragment.layoutFragmentFrame       // Position in container
    let surface = fragment.renderingSurfaceBounds   // Actual rendering area

    for lineFragment in fragment.textLineFragments {
        let lineOrigin = lineFragment.typographicBounds.origin
        let lineHeight = lineFragment.typographicBounds.height
        print("Line at y=\(frame.origin.y + lineOrigin.y), height=\(lineHeight)")
    }
    return true  // continue enumeration
}
```

### NSTextLineFragment metrics

Each `NSTextLineFragment` within a layout fragment gives you:

```swift
lineFragment.typographicBounds  // Bounds based on font metrics
lineFragment.glyphOrigin        // Where glyphs start
lineFragment.characterRange     // Character range for this line
```

## Common Sizing Patterns

### "Size text view to fit content"

**UITextView:**
```swift
// Let the text system do the work
let fittingSize = textView.sizeThatFits(
    CGSize(width: maxWidth, height: .greatestFiniteMagnitude)
)
textView.frame.size.height = fittingSize.height
```

**With Auto Layout (preferred):**
```swift
textView.isScrollEnabled = false  // CRITICAL — enables intrinsicContentSize
// Auto Layout handles the rest via intrinsicContentSize
```

**`isScrollEnabled = false` is the key.** When scrolling is enabled, `intrinsicContentSize` returns `(.noIntrinsicMetric, .noIntrinsicMetric)`. When disabled, it returns the full content size.

### "How tall is N lines of text?"

```swift
func heightForLines(_ n: Int, font: UIFont, width: CGFloat) -> CGFloat {
    let paragraphStyle = NSMutableParagraphStyle()
    paragraphStyle.lineBreakMode = .byWordWrapping

    // Build a string with N-1 newlines
    let sampleText = String(repeating: "Wy\n", count: n).dropLast()
    let attrs: [NSAttributedString.Key: Any] = [
        .font: font,
        .paragraphStyle: paragraphStyle
    ]
    let rect = (sampleText as NSString).boundingRect(
        with: CGSize(width: width, height: .greatestFiniteMagnitude),
        options: [.usesLineFragmentOrigin, .usesFontLeading],
        attributes: attrs,
        context: nil
    )
    return ceil(rect.height)
}
```

### "Does text fit in this rect?"

```swift
func textFits(_ text: NSAttributedString, in size: CGSize) -> Bool {
    let rect = text.boundingRect(
        with: size,
        options: [.usesLineFragmentOrigin, .usesFontLeading],
        context: nil
    )
    return ceil(rect.height) <= size.height && ceil(rect.width) <= size.width
}
```

## Pitfalls

1. **Forgetting `.usesLineFragmentOrigin`** — Without it, multi-line text is measured as one line. This is the single most common measurement bug.

2. **Not calling `ceil()`** — Fractional heights cause 1px clipping. Always round up.

3. **Mismatched attributes** — Measuring with font A but rendering with font B. Ensure the same paragraph style, font, and line height are used for both measurement and display.

4. **`textContainer.lineFragmentPadding`** — Default is 5pt. This adds 10pt total width (5 each side). If you measure without accounting for it, your widths are 10pt off:
    ```swift
    let effectiveWidth = containerWidth - 2 * textContainer.lineFragmentPadding
    ```

5. **`textContainerInset`** — UITextView default is `UIEdgeInsets(top: 8, left: 0, bottom: 8, right: 0)`. You must add these to the measured text height for the actual view height.

6. **Measuring before layout** — In TextKit, measurements are only valid after layout. Call `ensureLayout(for:)` before reading rects.

7. **Thread safety** — All measurement APIs that touch NSLayoutManager or NSTextLayoutManager must be called from the main thread (or the layout queue for TK2).

## Related Skills

- For text colors and Dynamic Type scaling -> `/skill txt-colors`, `/skill txt-dynamic-type`
- For viewport-based lazy measurement -> `/skill txt-viewport-rendering`
- For layout invalidation after content changes -> `/skill txt-layout-invalidation`
- For Core Text glyph-level measurement -> `/skill txt-core-text`
