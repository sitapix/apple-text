---
name: apple-text-line-breaking
description: Use when configuring line break mode, hyphenation, truncation, line height, paragraph spacing, or tab stops via NSParagraphStyle
license: MIT
---

# Line Breaking, Hyphenation & Truncation

Use this skill when you need to control how text wraps, breaks, truncates, or spaces vertically.

## When to Use

- Configuring line break mode or strategy.
- Enabling or tuning hyphenation.
- Custom truncation behavior (ellipsis, "Read more", etc.).
- Controlling line height, paragraph spacing, or first-line indent.
- Setting up tab stops.
- Text is wrapping at wrong points or not truncating as expected.

## Quick Decision

- How text wraps at container edge -> `lineBreakMode`
- Smart word-level line breaking -> `lineBreakStrategy`
- Whether to hyphenate long words -> `hyphenationFactor`
- Ellipsis at end of text -> `lineBreakMode = .byTruncatingTail` + `maximumNumberOfLines`
- Consistent line heights -> `minimumLineHeight` + `maximumLineHeight`
- Vertical spacing between paragraphs -> `paragraphSpacing` / `paragraphSpacingBefore`

## Line Break Modes (NSLineBreakMode)

Set on `NSParagraphStyle.lineBreakMode`:

| Mode | Behavior | Use case |
|------|----------|----------|
| `.byWordWrapping` | Wraps at word boundaries | Default. Body text. |
| `.byCharWrapping` | Wraps at character boundaries | CJK text, monospaced code |
| `.byClipping` | Clips at container edge, no ellipsis | Fixed-width fields |
| `.byTruncatingHead` | `...end of text` | File paths |
| `.byTruncatingTail` | `Beginning of te...` | Labels, cells |
| `.byTruncatingMiddle` | `Begin...of text` | File names |

```swift
let style = NSMutableParagraphStyle()
style.lineBreakMode = .byTruncatingTail
```

**TextKit behavior:** Truncation modes only take effect on the **last** line that fits in the container. All preceding lines use word wrapping regardless of the mode set.

## Line Break Strategy (NSLineBreakStrategy)

Controls how the text system makes word-wrapping decisions. Set on `NSParagraphStyle.lineBreakStrategy`:

| Strategy | Effect |
|----------|--------|
| `.standard` | Default system behavior — same as UILabel |
| `.pushOut` | Avoids orphan words on the last line by "pushing" content to fill lines more evenly |
| `.hangulWordPriority` | Prevents breaking between Hangul (Korean) characters |

```swift
let style = NSMutableParagraphStyle()
style.lineBreakStrategy = .pushOut  // Prevents orphaned last words

// Combine strategies (it's an OptionSet)
style.lineBreakStrategy = [.standard, .hangulWordPriority]
```

**`.pushOut` explained:** Without it, a paragraph might end with a very short last line containing just one word. With `.pushOut`, the system redistributes words across lines to avoid this, producing more visually balanced paragraphs.

**UILabel default:** As of iOS 14+, UILabel uses `.standard` by default (which includes push-out behavior). If you're building a custom text view and want the same look, set `.standard`.

## Hyphenation

### hyphenationFactor

```swift
let style = NSMutableParagraphStyle()
style.hyphenationFactor = 1.0  // 0.0 = never, 1.0 = always when beneficial
```

| Value | Behavior |
|-------|----------|
| `0.0` | No hyphenation (default) |
| `0.0 < x < 1.0` | Hyphenate when word extends past this fraction of the line width |
| `1.0` | Hyphenate whenever it produces tighter lines |

### usesDefaultHyphenation (iOS 15+)

```swift
style.usesDefaultHyphenation = true  // Use system default for the locale
```

When `true`, the system decides based on the text's language. Some languages (German) hyphenate aggressively by default; others (English) are conservative.

### Soft Hyphens

Insert U+00AD (soft hyphen) to suggest break points in specific words:

```swift
let text = "super\u{00AD}cali\u{00AD}fragilistic"
// Breaks at soft-hyphen points only when needed
```

Soft hyphens are invisible unless the text system uses them for a line break, at which point a hyphen character appears.

## Truncation

### Basic Truncation

```swift
// UILabel
label.lineBreakMode = .byTruncatingTail
label.numberOfLines = 2  // Show at most 2 lines

// NSTextContainer
textContainer.maximumNumberOfLines = 2
textContainer.lineBreakMode = .byTruncatingTail
```

### allowsDefaultTighteningForTruncation

```swift
let style = NSMutableParagraphStyle()
style.allowsDefaultTighteningForTruncation = true
```

When `true`, the text system slightly reduces inter-character spacing before resorting to truncation. This can save a word from being truncated. UILabel enables this by default.

### Custom Truncation Token (TextKit 1)

```swift
// Replace "..." with " Read more"
let token = NSAttributedString(
    string: "\u{2026} Read more",
    attributes: [
        .font: UIFont.systemFont(ofSize: 15),
        .foregroundColor: UIColor.systemBlue
    ]
)
layoutManager.truncatedGlyphRange(inLineFragmentForGlyphAt: glyphIndex)

// For full custom truncation, subclass NSLayoutManager:
class CustomTruncationLayoutManager: NSLayoutManager {
    var truncationToken: NSAttributedString?

    override func drawGlyphs(forGlyphRange glyphsToShow: NSRange, at origin: CGPoint) {
        // Check if this range includes truncated glyphs
        // Draw custom token at truncation point
        super.drawGlyphs(forGlyphRange: glyphsToShow, at: origin)
    }
}
```

### Detecting Truncation

```swift
// TextKit 1: Is text truncated?
func isTruncated(layoutManager: NSLayoutManager,
                 textContainer: NSTextContainer,
                 textStorage: NSTextStorage) -> Bool {
    layoutManager.ensureLayout(for: textContainer)
    let glyphRange = layoutManager.glyphRange(for: textContainer)
    let charRange = layoutManager.characterRange(forGlyphRange: glyphRange,
                                                  actualGlyphRange: nil)
    return charRange.upperBound < textStorage.length
}
```

## Line Height

### The Line Height Stack

Line height in Apple text systems is determined by a stack of properties, applied in this order:

1. **Font metrics** — `font.lineHeight` (ascender + descender + leading)
2. **`minimumLineHeight`** — Floor for line height
3. **`maximumLineHeight`** — Ceiling for line height
4. **`lineHeightMultiple`** — Multiplier applied to the font-derived height
5. **`lineSpacing`** — Extra space **added after** the line

### Consistent Line Heights (The Pattern)

```swift
let font = UIFont.systemFont(ofSize: 17)
let desiredLineHeight: CGFloat = 24

let style = NSMutableParagraphStyle()
style.minimumLineHeight = desiredLineHeight
style.maximumLineHeight = desiredLineHeight

// Center text vertically within the line height
let baselineOffset = (desiredLineHeight - font.lineHeight) / 2

let attrs: [NSAttributedString.Key: Any] = [
    .font: font,
    .paragraphStyle: style,
    .baselineOffset: baselineOffset
]
```

**Why both min and max?** Setting only `minimumLineHeight` lets the font's natural height override when it's larger. Setting both clamps to exactly your desired height.

**Why `baselineOffset`?** When you increase line height beyond the font's natural height, extra space goes below the baseline by default. `baselineOffset` shifts text up to center it vertically.

### lineHeightMultiple

```swift
style.lineHeightMultiple = 1.5  // 150% of font's natural line height
```

**Interaction with min/max:** `lineHeightMultiple` is applied first, then clamped by `minimumLineHeight`/`maximumLineHeight`. So:
```
effectiveHeight = clamp(font.lineHeight * lineHeightMultiple,
                        minimumLineHeight, maximumLineHeight)
```

### lineSpacing (Inter-line)

```swift
style.lineSpacing = 4  // 4pt extra space BETWEEN lines (not between paragraphs)
```

**This is NOT paragraph spacing.** `lineSpacing` adds space between every line within a paragraph. For space between paragraphs, use `paragraphSpacing`.

## Paragraph Spacing

```swift
let style = NSMutableParagraphStyle()
style.paragraphSpacing = 12        // Space AFTER this paragraph (before next)
style.paragraphSpacingBefore = 8   // Space BEFORE this paragraph (after previous)
```

**Typical usage:** Set `paragraphSpacing` only (not `paragraphSpacingBefore`). The "before" variant adds space before every paragraph including the first, which usually isn't what you want.

## Indentation

```swift
let style = NSMutableParagraphStyle()
style.firstLineHeadIndent = 24    // First line of paragraph
style.headIndent = 0              // Subsequent lines (hanging indent when > firstLine)
style.tailIndent = -20            // Negative = inset from right edge
```

**Hanging indent pattern** (for lists):
```swift
style.firstLineHeadIndent = 0     // Marker sits at margin
style.headIndent = 24             // Wrapped text indented past marker
```

## Tab Stops

```swift
let style = NSMutableParagraphStyle()

// Default tab interval (when no explicit stops are set)
style.defaultTabInterval = 28

// Explicit tab stops
style.tabStops = [
    NSTextTab(textAlignment: .left, location: 0),
    NSTextTab(textAlignment: .right, location: 200),
    NSTextTab(textAlignment: .decimal, location: 300),
    NSTextTab(textAlignment: .center, location: 400)
]
```

**`.decimal`** alignment aligns on the decimal point — useful for number columns:
```
   12.50
  123.45
    1.00
```

## Pitfalls

1. **`lineSpacing` vs `paragraphSpacing`** — `lineSpacing` affects every line within a paragraph. `paragraphSpacing` only affects the gap between paragraphs. Mixing them up is the #1 spacing mistake.

2. **`lineHeightMultiple` + `minimumLineHeight` interaction** — The multiplier is applied first, then clamped. Setting both can produce confusing results if you don't understand the order.

3. **Truncation only on last line** — `lineBreakMode` truncation only applies to the last visible line. All other lines always word-wrap.

4. **`maximumNumberOfLines = 0`** — Means unlimited (default). Not zero lines.

5. **Missing `baselineOffset` with forced line height** — Text sticks to the bottom of the line when you increase `minimumLineHeight` beyond the font's natural height. Always add `baselineOffset` to center it.

6. **`hyphenationFactor` ignored in single-line mode** — Hyphenation only applies when text can wrap to multiple lines.

7. **Tab stops and proportional fonts** — Tab alignment works precisely with monospaced fonts but can be imprecise with proportional fonts. Use `.decimal` alignment for number columns regardless.

## Related Skills

- For paragraph style attribute reference -> `/skill apple-text-formatting-ref`
- For text measurement with these settings -> `/skill apple-text-measurement`
- For Dynamic Type scaling interaction -> `/skill apple-text-dynamic-type`
- For multi-column layout with different line settings -> `/skill apple-text-exclusion-paths`
