---
name: apple-text-formatting-ref
description: Use when working with text formatting attributes, NSAttributedString.Key catalog, NSUnderlineStyle options, NSShadow, text effects, NSTextList marker formats, NSTextTable, or understanding which formatting works in which text view — complete formatting reference for UIKit and AppKit
license: MIT
---

# Text Formatting Reference

Use this skill when you already know the formatting problem and need the exact attribute or compatibility rules.

## When to Use

- You need an `NSAttributedString.Key` reference.
- You are checking which formatting works in which view.
- You need paragraph-style, underline, shadow, or table-formatting details.

## Quick Decision

- Need type choice or custom attribute scopes -> `/skill apple-text-attributed-string`
- Need exact formatting keys and compatibility -> stay here
- Need semantic text colors rather than general formatting -> `/skill apple-text-colors`

## Core Guidance

## Character-Level Attributes (NSAttributedString.Key)

### Typography

| Key | Value Type | Effect | Min OS |
|-----|-----------|--------|--------|
| `.font` | UIFont / NSFont | Typeface, size, weight | All |
| `.kern` | NSNumber (CGFloat) | Inter-character spacing (points) | All |
| `.tracking` | NSNumber (CGFloat) | Tracking (scales with font size) | iOS 14+ |
| `.ligature` | NSNumber (Int) | 0=none, 1=default, 2=all (macOS only) | All |
| `.baselineOffset` | NSNumber (CGFloat) | Vertical shift from baseline | All |
| `.obliqueness` | NSNumber (CGFloat) | Synthetic italic (0=none, positive=right lean) | All |
| `.expansion` | NSNumber (CGFloat) | Horizontal stretch (0=normal, positive=wider) | All |
| `.verticalGlyphForm` | NSNumber (Int) | 0=horizontal, 1=vertical (CJK) | All |

### Color

| Key | Value Type | Effect | Min OS |
|-----|-----------|--------|--------|
| `.foregroundColor` | UIColor / NSColor | Text color | All |
| `.backgroundColor` | UIColor / NSColor | Background behind text | All |
| `.strokeColor` | UIColor / NSColor | Text outline color | All |
| `.strokeWidth` | NSNumber (CGFloat) | Outline width. Negative = fill + stroke | All |
| `.shadow` | NSShadow | Drop shadow | All |

### Decoration

| Key | Value Type | Effect | Min OS |
|-----|-----------|--------|--------|
| `.underlineStyle` | NSNumber (NSUnderlineStyle) | Underline pattern | All |
| `.underlineColor` | UIColor / NSColor | Underline color (nil = foreground color) | All |
| `.strikethroughStyle` | NSNumber (NSUnderlineStyle) | Strikethrough pattern | All |
| `.strikethroughColor` | UIColor / NSColor | Strikethrough color | All |

### Layout & Structure

| Key | Value Type | Effect | Min OS |
|-----|-----------|--------|--------|
| `.paragraphStyle` | NSParagraphStyle | Paragraph formatting (see below) | All |
| `.writingDirection` | [NSNumber] | Embedding/override direction | All |
| `.textEffect` | NSAttributedString.TextEffectStyle | Visual effect | iOS 7+ |

### Content

| Key | Value Type | Effect | Min OS |
|-----|-----------|--------|--------|
| `.attachment` | NSTextAttachment | Inline image/view | All |
| `.link` | URL or String | Hyperlink | All |
| `.textAlternatives` | NSTextAlternatives | Alternative text interpretations | iOS 18+ |
| `.adaptiveImageGlyph` | NSAdaptiveImageGlyph | Genmoji/stickers | iOS 18+ |

### AppKit-Only

| Key | Value Type | Effect |
|-----|-----------|--------|
| `.superscript` | NSNumber (Int) | Superscript (positive) or subscript (negative) |
| `.cursor` | NSCursor | Mouse cursor when hovering |
| `.toolTip` | String | Hover tooltip |
| `.markedClauseSegment` | NSNumber (Int) | CJK input clause segment |
| `.spellingState` | NSNumber (Int) | Spelling/grammar error indicator |
| `.glyphInfo` | NSGlyphInfo | Glyph substitution |
| `.textBlock` | NSTextBlock | Text block (table cell, etc.) |

## NSUnderlineStyle

Combine with bitwise OR for compound styles:

### Line Style

| Style | Visual |
|-------|--------|
| `.single` | Single line |
| `.thick` | Thick line |
| `.double` | Double line |

### Pattern (Combine with style)

| Pattern | Visual |
|---------|--------|
| (none) | Solid line |
| `.patternDot` | Dotted |
| `.patternDash` | Dashed |
| `.patternDashDot` | Dash-dot |
| `.patternDashDotDot` | Dash-dot-dot |

### Modifier

| Modifier | Effect |
|----------|--------|
| `.byWord` | Only under words, not spaces |

### Examples

```swift
// Thick dashed underline, words only
let style: NSUnderlineStyle = [.thick, .patternDash, .byWord]

// Double solid underline
let style: NSUnderlineStyle = [.double]

// Single dotted strikethrough
let attrs: [NSAttributedString.Key: Any] = [
    .strikethroughStyle: NSUnderlineStyle.single.union(.patternDot).rawValue,
    .strikethroughColor: UIColor.red
]
```

## NSShadow

```swift
let shadow = NSShadow()
shadow.shadowOffset = CGSize(width: 2, height: -2) // Right and up
shadow.shadowBlurRadius = 4.0
shadow.shadowColor = UIColor.black.withAlphaComponent(0.3)

let attrs: [NSAttributedString.Key: Any] = [.shadow: shadow]
```

**Note:** SwiftUI Text ignores the `.shadow` attribute. Use `.shadow()` modifier instead (applies to entire view).

## Text Effects

```swift
// The only public text effect
attrs[.textEffect] = NSAttributedString.TextEffectStyle.letterpressStyle
```

**Letterpress style:** Embossed appearance with light source. Purely visual. Only one public effect exists.

## NSParagraphStyle (Complete)

### All Properties

```swift
let style = NSMutableParagraphStyle()

// Alignment
style.alignment = .natural          // .left, .right, .center, .justified, .natural

// Line Spacing
style.lineSpacing = 4               // Extra space between lines (after leading)
style.minimumLineHeight = 20        // Floor for line height
style.maximumLineHeight = 30        // Ceiling for line height
style.lineHeightMultiple = 1.2      // Multiplier on natural line height

// Paragraph Spacing
style.paragraphSpacing = 12         // Space AFTER paragraph
style.paragraphSpacingBefore = 8    // Space BEFORE paragraph

// Indentation
style.firstLineHeadIndent = 20      // First line indent
style.headIndent = 10               // Subsequent lines indent
style.tailIndent = -10              // Trailing margin (negative = from right edge)

// Line Breaking
style.lineBreakMode = .byWordWrapping    // .byCharWrapping, .byClipping,
                                          // .byTruncatingHead/Tail/Middle
style.lineBreakStrategy = .standard      // .pushOut, .hangulWordPriority

// Hyphenation
style.hyphenationFactor = 0.5       // 0.0 (none) to 1.0 (max)
style.usesDefaultHyphenation = true // iOS 15+ (system-determined)

// Writing Direction
style.baseWritingDirection = .natural  // .leftToRight, .rightToLeft

// Tabs
style.tabStops = [
    NSTextTab(textAlignment: .left, location: 100),
    NSTextTab(textAlignment: .decimal, location: 200),
]
style.defaultTabInterval = 36

// Tightening
style.allowsDefaultTighteningForTruncation = true // Reduce spacing before truncating

// Lists (AppKit + UIKit iOS 16+)
style.textLists = [NSTextList(markerFormat: .disc, options: 0)]
```

### NSTextList Marker Formats

| Format | Example | Platform |
|--------|---------|----------|
| `.disc` | • | All |
| `.circle` | ○ | All |
| `.square` | ■ | All |
| `.decimal` | 1. 2. 3. | All |
| `.lowercaseAlpha` | a. b. c. | All |
| `.uppercaseAlpha` | A. B. C. | All |
| `.lowercaseRoman` | i. ii. iii. | All |
| `.uppercaseRoman` | I. II. III. | All |
| `.lowercaseLatin` | a. b. c. | macOS |
| `.uppercaseLatin` | A. B. C. | macOS |
| `.lowercaseHexadecimal` | 1. 2. ... a. b. | macOS |
| `.uppercaseHexadecimal` | 1. 2. ... A. B. | macOS |
| `.octal` | 1. 2. ... 10. | macOS |
| `.hyphen` | - | macOS |
| `.check` | ✓ | macOS |

### NSTextTable / NSTextTableBlock (AppKit Only)

```swift
let table = NSTextTable()
table.numberOfColumns = 3
table.collapsesBorders = true

let cell = NSTextTableBlock(
    table: table,
    startingRow: 0, rowSpan: 1,
    startingColumn: 0, columnSpan: 1
)
cell.backgroundColor = .secondarySystemBackground
cell.setWidth(1.0, type: .absoluteValueType, for: .border)
cell.setWidth(4.0, type: .absoluteValueType, for: .padding)

let style = NSMutableParagraphStyle()
style.textBlocks = [cell]

// Apply to the paragraph's attributed string
```

**Triggers TextKit 1 fallback.** No UIKit equivalent.

## Stroke Width Trick

Negative stroke width creates fill + stroke (outlined text):

```swift
// Outlined text (stroke only)
attrs[.strokeWidth] = 3.0
attrs[.strokeColor] = UIColor.blue

// Filled + outlined (negative width)
attrs[.strokeWidth] = -3.0
attrs[.strokeColor] = UIColor.blue
attrs[.foregroundColor] = UIColor.white
```

## Where Formatting Works

| Attribute | SwiftUI Text | TextEditor (iOS 26+) | UITextView | UILabel | NSTextView |
|-----------|-------------|---------------------|------------|---------|------------|
| font | ✅ | ✅ | ✅ | ✅ | ✅ |
| foregroundColor | ✅ | ✅ | ✅ | ✅ | ✅ |
| backgroundColor | ✅ | ✅ | ✅ | ✅ | ✅ |
| paragraphStyle | ❌ | ✅ (alignment, lineHeight) | ✅ | ✅ | ✅ |
| kern/tracking | ✅ | ✅ | ✅ | ✅ | ✅ |
| underlineStyle | ✅ | ✅ | ✅ | ✅ | ✅ |
| strikethroughStyle | ✅ | ✅ | ✅ | ✅ | ✅ |
| shadow | ❌ | ❌ | ✅ | ✅ | ✅ |
| strokeColor/Width | ❌ | ❌ | ✅ | ✅ | ✅ |
| link | ✅ | ✅ | ✅ | ❌ | ✅ |
| attachment | ❌ | ❌ | ✅ | ✅ (display) | ✅ |
| baselineOffset | ✅ | ✅ | ✅ | ✅ | ✅ |
| obliqueness | ❌ | ❌ | ✅ | ✅ | ✅ |
| expansion | ❌ | ❌ | ✅ | ✅ | ✅ |
| textEffect | ❌ | ❌ | ✅ | ✅ | ✅ |
| superscript | N/A | N/A | N/A | N/A | ✅ (AppKit) |
| toolTip | N/A | N/A | N/A | N/A | ✅ (AppKit) |
| textTable | N/A | N/A | N/A | N/A | ✅ (AppKit, TK1) |
| textList | ❌ | ❌ | ✅ (iOS 17+) | ✅ | ✅ |

## UITextView Built-in Formatting UI

```swift
textView.allowsEditingTextAttributes = true
```

When enabled, the text selection menu shows a **BIU** button:
- **B** — Bold (toggles font weight)
- **I** — Italic (toggles font style)
- **U** — Underline (toggles underline style)

That's the only built-in formatting UI. For more (font size, color, alignment), you must build custom UI.

## RTF Round-Trip

Attributes that **survive** RTF archiving:
- font, foregroundColor, backgroundColor, paragraphStyle
- underline, strikethrough, kern, baselineOffset
- link, attachment, shadow, strokeColor/Width
- superscript (AppKit), textList, textTable

Attributes that are **lost** in RTF:
- obliqueness, expansion (stored as font descriptors — may survive if font supports)
- textEffect (letterpress)
- custom attributes (unless you handle RTF custom tags)

## Common Pitfalls

1. **Negative strokeWidth is fill+stroke, positive is stroke only** — counterintuitive but important for outlined text.
2. **NSMutableParagraphStyle is required for changes** — NSParagraphStyle is immutable. Always create mutable variant.
3. **paragraphStyle applies to entire paragraph** — Even if you set it on a sub-range, `fixAttributes` extends it to the full paragraph.
4. **SwiftUI Text ignores most attributes** — Only ~10 work. The rest are silently dropped.
5. **NSTextTable triggers TK1 fallback** — AppKit-only, and forces TextKit 1 mode.
6. **kern vs tracking** — Kern is absolute (points). Tracking scales with font size. Use tracking for proportional spacing.

## Related Skills

- Use `/skill apple-text-attributed-string` for AttributedString vs NSAttributedString decisions.
- Use `/skill apple-text-colors` when the formatting question is mostly about semantic color behavior.
- Use `/skill apple-text-attachments-ref` for inline non-text content instead of pure formatting attributes.
