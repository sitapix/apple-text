---
name: rich-text-reference
description: Look up attributed string APIs, text formatting attributes, colors, Markdown rendering, text attachments, line breaking, and bidirectional text.
model: sonnet
tools:
  - Glob
  - Grep
  - Read
---

# Rich Text Reference Agent

You answer specific questions about rich text modeling, formatting, and content attributes.

## Instructions

1. Read the user's question carefully.
2. Find the relevant section in the reference material below.
3. Return ONLY the information that answers their question — maximum 40 lines.
4. Include exact API signatures, code examples, and gotchas when relevant.
5. Do NOT dump all reference material — extract what is relevant.
6. When the user needs to choose between AttributedString and NSAttributedString, include the trade-off summary.

---

# Attributed String Reference

Use this skill when the main question is which attributed-text model to use and how to convert safely between them.

## When to Use

- You are choosing between `AttributedString` and `NSAttributedString`.
- You need custom attributes or scopes.
- You need conversion rules between SwiftUI and UIKit/AppKit text APIs.

## Quick Decision

- SwiftUI-first, Codable, or Markdown-heavy pipeline -> `AttributedString`
- UIKit/AppKit or TextKit API boundary -> `NSAttributedString`
- Exact formatting attribute catalog needed -> the formatting ref section in this reference

## Core Guidance

Keep this file for the model choice, mutation rules, and conversion boundaries. For custom attribute scopes, paragraph-style recipes, and the full attribute quick reference, use [advanced-patterns.md](advanced-patterns.md). For Apple-authored Xcode-backed guidance on the newest Foundation changes, use the **platform-reference** agent.

## AttributedString vs NSAttributedString

| Aspect | AttributedString (Swift) | NSAttributedString (ObjC) |
|--------|-------------------------|--------------------------|
| **Type** | Value type (struct) | Reference type (class) |
| **Attributes** | Type-safe key paths | Untyped `[Key: Any]` dictionary |
| **Codable** | Yes | No (use NSCoding) |
| **Markdown** | Built-in parsing | No |
| **Thread safety** | Copy-on-write (safe) | Immutable safe, mutable not |
| **Mutable variant** | Same type (var) | NSMutableAttributedString |
| **Required by** | SwiftUI Text | UIKit/AppKit text properties, TextKit |
| **Available** | iOS 15+ / macOS 12+ | All versions |

### When to Use Which

```
Need Codable/serialization?         → AttributedString
Need Markdown parsing?              → AttributedString
SwiftUI Text view?                  → AttributedString
UIKit label/textView attributedText? → NSAttributedString
TextKit 1 (NSTextStorage)?          → NSAttributedString
TextKit 2 (delegate methods)?       → NSAttributedString
Core Text?                          → NSAttributedString (CFAttributedString)
Cross-platform code?                → AttributedString (convert at boundaries)
```

**Best practice:** Use `AttributedString` as your internal representation. Convert to `NSAttributedString` at UIKit/AppKit API boundaries.

## Swift AttributedString (iOS 15+)

### Basic Usage

```swift
var str = AttributedString("Hello World")
str.font = .body
str.foregroundColor = .red

// Range-based attributes
if let range = str.range(of: "World") {
    str[range].link = URL(string: "https://example.com")
    str[range].font = .body.bold()
}
```

### Concatenation

```swift
var greeting = AttributedString("Hello ")
greeting.font = .body
var name = AttributedString("World")
name.font = .body.bold()
name.foregroundColor = .blue

let combined = greeting + name
```

### Markdown

```swift
// Basic Markdown
let str = try AttributedString(markdown: "**Bold** and *italic*")

// Custom interpretation
let str = try AttributedString(
    markdown: "Visit [Apple](https://apple.com)",
    including: \.foundation,
    options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)
)
```

### Views (Character-Level Access)

```swift
let str = AttributedString("Hello 👋🏽")

str.characters       // CharacterView — Swift Characters
str.unicodeScalars   // UnicodeScalarView
str.utf8             // UTF8View
str.utf16            // UTF16View

// Iterate characters with attributes
for run in str.runs {
    let substring = str[run.range]
    let font = run.font
    let color = run.foregroundColor
}
```

### Runs

A "run" is a contiguous range with identical attributes:

```swift
for run in str.runs {
    print("Range: \(run.range)")
    print("Font: \(run.font ?? .body)")

    // Access the attributed substring
    let sub = str[run.range]
}

// Filter runs by attribute
for (color, range) in str.runs[\.foregroundColor] {
    print("Color: \(String(describing: color)) at \(range)")
}
```

### Mutation

```swift
var str = AttributedString("Hello World")

// Replace text
if let range = str.range(of: "World") {
    str.replaceSubrange(range, with: AttributedString("Swift"))
}

// Set attribute on entire string
str.foregroundColor = .red

// Merge attributes
var container = AttributeContainer()
container.font = .body.bold()
container.foregroundColor = .blue
str.mergeAttributes(container)

// Remove attribute
str.foregroundColor = nil
```

### Index Invalidation

**Critical:** Mutating an `AttributedString` invalidates ALL existing indices and ranges.

```swift
// ❌ WRONG — indices invalidated after mutation
var str = AttributedString("Hello World")
let range = str.range(of: "World")!
str.replaceSubrange(str.range(of: "Hello")!, with: AttributedString("Hi"))
// range is NOW INVALID — using it may crash

// ✅ CORRECT — re-find ranges after mutation
var str = AttributedString("Hello World")
str.replaceSubrange(str.range(of: "Hello")!, with: AttributedString("Hi"))
if let range = str.range(of: "World") {
    str[range].font = .body.bold()
}
```

## NSAttributedString

### Basic Usage

```swift
let attrs: [NSAttributedString.Key: Any] = [
    .font: UIFont.systemFont(ofSize: 16),
    .foregroundColor: UIColor.red,
    .kern: 1.5
]
let str = NSAttributedString(string: "Hello", attributes: attrs)
```

### Mutable Variant

```swift
let mutable = NSMutableAttributedString(string: "Hello World")

// Add attributes to range
mutable.addAttribute(.font, value: UIFont.boldSystemFont(ofSize: 16),
                     range: NSRange(location: 6, length: 5))

// Set attributes (replaces all existing in range)
mutable.setAttributes([.foregroundColor: UIColor.blue],
                      range: NSRange(location: 0, length: 5))

// Remove attribute
mutable.removeAttribute(.font, range: NSRange(location: 0, length: mutable.length))

// Replace characters
mutable.replaceCharacters(in: NSRange(location: 0, length: 5), with: "Hi")

// Insert
mutable.insert(NSAttributedString(string: "Hey "), at: 0)

// Delete
mutable.deleteCharacters(in: NSRange(location: 0, length: 4))
```

### Enumerating Attributes

```swift
let str: NSAttributedString = ...

// Enumerate all attributes
str.enumerateAttributes(in: NSRange(location: 0, length: str.length)) { attrs, range, stop in
    if let font = attrs[.font] as? UIFont {
        print("Font: \(font) at \(range)")
    }
}

// Enumerate specific attribute
str.enumerateAttribute(.foregroundColor, in: NSRange(location: 0, length: str.length)) { value, range, stop in
    if let color = value as? UIColor {
        print("Color: \(color) at \(range)")
    }
}
```

## Conversion Between Types

### AttributedString → NSAttributedString

```swift
// Using all default scopes
let nsAS = NSAttributedString(attrString)

// With specific scope (preserves custom attributes)
let nsAS = try NSAttributedString(attrString, including: \.myApp)
```

### NSAttributedString → AttributedString

```swift
// Using all default scopes
let swiftAS = try AttributedString(nsAS, including: \.foundation)

// With specific scope
let swiftAS = try AttributedString(nsAS, including: \.myApp)
```

**Pitfall:** Conversion without `including:` your custom scope silently drops custom attributes. Always include the scope containing your custom keys.

## Common Pitfalls

1. **Forgetting `including:` in conversion** — Custom attributes silently dropped during `AttributedString` ↔ `NSAttributedString` conversion.
2. **Index invalidation** — Mutating `AttributedString` invalidates all existing indices. Re-find ranges after mutation.
3. **NSParagraphStyle is immutable** — Always create `NSMutableParagraphStyle`, then assign. Cannot modify after setting on attributed string.
4. **Mixing AttributedString and NSAttributedString** — UIKit APIs require `NSAttributedString`. SwiftUI requires `AttributedString`. Convert at boundaries.
5. **Scope must include standard scopes** — Custom `AttributeScope` should include `FoundationAttributes` and `UIKitAttributes`/`SwiftUIAttributes` for round-trip conversion.
6. **NSTextStorage IS an NSMutableAttributedString** — Can use all NSAttributedString APIs directly on text storage.

## Related Skills

- For custom scopes, paragraph-style recipes, and the attribute-key table, see [advanced-patterns.md](advanced-patterns.md).
- Use the formatting ref section in this reference for the full formatting-key catalog.
- Use the **platform-reference** agent when the real issue is what SwiftUI renders or drops.
- Use the markdown section in this reference when Markdown parsing is driving the attributed-text shape.

---

# Text Formatting Reference

Use this skill when you already know the formatting problem and need the exact attribute or compatibility rules.

## When to Use

- You need an `NSAttributedString.Key` reference.
- You are checking which formatting works in which view.
- You need paragraph-style, underline, shadow, or table-formatting details.

## Quick Decision

- Need type choice or custom attribute scopes -> the attributed string section in this reference
- Need exact formatting keys and compatibility -> stay here
- Need semantic text colors rather than general formatting -> the colors section in this reference

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

- Use the attributed string section in this reference for AttributedString vs NSAttributedString decisions.
- Use the colors section in this reference when the formatting question is mostly about semantic color behavior.
- Use the attachments ref section in this reference for inline non-text content instead of pure formatting attributes.

---

# Text Colors, Dark Mode & Wide Color

Use this skill when the main question is how text color should adapt across UIKit, AppKit, SwiftUI, dark mode, or wide-color environments.

## When to Use

- You need semantic text colors.
- You are debugging dark-mode text issues.
- You need to know whether wide color or HDR applies to text rendering.

## Quick Decision

- Need adaptive body text colors -> use semantic label/text colors
- Need attributed text colors that survive mode changes -> resolve dynamic colors correctly
- Need advanced formatting attributes -> the formatting ref section in this reference

## Core Guidance

## UIKit Semantic Text Colors (Complete)

### Label Hierarchy

| Color | Light Mode | Dark Mode | Use For |
|-------|-----------|-----------|---------|
| `.label` | Black (a1.0) | White (a1.0) | Primary text |
| `.secondaryLabel` | #3C3C43 (a0.6) | #EBEBF5 (a0.6) | Secondary text |
| `.tertiaryLabel` | #3C3C43 (a0.3) | #EBEBF5 (a0.3) | Tertiary text |
| `.quaternaryLabel` | #3C3C43 (a0.18) | #EBEBF5 (a0.18) | Disabled/hint text |
| `.placeholderText` | #3C3C43 (a0.3) | #EBEBF5 (a0.3) | Placeholder in fields |
| `.link` | #007AFF | #0984FF | Tappable links |

### Legacy (NON-Dynamic — Avoid)

| Color | Value | Problem |
|-------|-------|---------|
| `.lightText` | White (a0.6) — always | Does NOT adapt to dark mode |
| `.darkText` | Black (a1.0) — always | Does NOT adapt to dark mode |

**Always use `.label` instead of `.darkText`, `.lightText`, or hardcoded black/white.**

### System Tint Colors (Adaptive)

All shift slightly between light and dark for contrast:

| Color | Light | Dark |
|-------|-------|------|
| `.systemBlue` | #007AFF | #0A84FF |
| `.systemRed` | #FF3B30 | #FF453A |
| `.systemGreen` | #34C759 | #30D158 |
| `.systemOrange` | #FF9500 | #FF9F0A |
| `.systemPurple` | #AF52DE | #BF5AF2 |
| `.systemPink` | #FF2D55 | #FF375F |
| `.systemYellow` | #FFCC00 | #FFD60A |
| `.systemIndigo` | #5856D6 | #5E5CE6 |
| `.systemTeal` | #5AC8FA | #64D2FF |
| `.systemCyan` | #32ADE6 | #64D2FF |
| `.systemMint` | #00C7BE | #63E6E2 |
| `.systemBrown` | #A2845E | #AC8E68 |

## AppKit Semantic Text Colors

### Critical: `.textColor` vs `.labelColor`

| Color | Alpha | Vibrancy | Use For |
|-------|-------|----------|---------|
| `.textColor` | 1.0 (fully opaque) | ❌ No | Document body text, NSTextView content |
| `.labelColor` | ~0.85 | ✅ Yes | UI labels, buttons, sidebar items |

**On macOS, `.textColor` is the right default for text views.** `.labelColor` is for UI chrome. They look similar but behave differently with vibrancy.

### Full macOS Text Color Catalog

| Color | Light | Dark | Use For |
|-------|-------|------|---------|
| `.textColor` | Black (a1.0) | White (a1.0) | Body text |
| `.textBackgroundColor` | White (a1.0) | #1E1E1E (a1.0) | Text view background |
| `.selectedTextColor` | White | White | Selected text foreground |
| `.selectedTextBackgroundColor` | #0063E1 | #0050AA | Selection highlight |
| `.unemphasizedSelectedTextColor` | Black | White | Selection (window inactive) |
| `.unemphasizedSelectedTextBackgroundColor` | #DCDCDC | #464646 | Selection bg (inactive) |
| `.placeholderTextColor` | Black (a0.25) | White (a0.25) | Placeholder text |
| `.headerTextColor` | Black (a0.85) | White (a1.0) | Section headers |
| `.linkColor` | #0068DA | #419CFF | Hyperlinks |
| `.controlTextColor` | Black (a0.85) | White (a0.85) | Control labels |
| `.disabledControlTextColor` | Black (a0.25) | White (a0.25) | Disabled controls |

## SwiftUI Semantic Colors

### Text Foreground Styles

```swift
Text("Primary").foregroundStyle(.primary)      // ≈ .label
Text("Secondary").foregroundStyle(.secondary)  // ≈ .secondaryLabel
Text("Tertiary").foregroundStyle(.tertiary)    // ≈ .tertiaryLabel
```

### Bridging UIKit/AppKit Colors

```swift
// Use UIKit semantic colors in SwiftUI
Text("Label").foregroundStyle(Color(uiColor: .label))
Text("Link").foregroundStyle(Color(uiColor: .link))

// macOS
Text("Text").foregroundStyle(Color(nsColor: .textColor))
```

### SwiftUI Color Literals

```swift
Color.primary    // Adaptive: black in light, white in dark
Color.secondary  // Adaptive: with reduced opacity
Color.accentColor // App tint color (default: .blue)
```

## Dark Mode Adaptation

### What Auto-Adapts

| Scenario | Auto-adapts? |
|----------|-------------|
| UILabel with `.textColor = .label` | ✅ |
| UITextView with no explicit color | ✅ (defaults to `.label` in TextKit 2) |
| NSAttributedString with `.foregroundColor: UIColor.label` | ✅ UIKit re-resolves at draw time |
| NSAttributedString with `.foregroundColor: UIColor.red` (hardcoded) | ❌ Stays red always |
| NSAttributedString with `.foregroundColor: UIColor.systemRed` | ✅ Shifts between light/dark variants |
| SwiftUI Text with `.foregroundStyle(.primary)` | ✅ |
| SwiftUI Text with `.foregroundStyle(Color.red)` | ✅ (Color.red is adaptive) |
| CALayer.borderColor (CGColor) | ❌ Must update manually |

### The Default Foreground Color Trap

**UIKit default attributed string foreground is black, NOT `.label`.**

```swift
// ❌ This text will be invisible in dark mode
let str = NSAttributedString(string: "Hello")  // foreground defaults to .black
textView.attributedText = str

// ✅ Always set foreground color explicitly
let str = NSAttributedString(string: "Hello", attributes: [
    .foregroundColor: UIColor.label
])
```

### Making Attributed String Colors Dynamic

Use semantic UIColors — they auto-resolve:

```swift
let attrs: [NSAttributedString.Key: Any] = [
    .foregroundColor: UIColor.label,           // ✅ Adapts
    .backgroundColor: UIColor.systemYellow,     // ✅ Adapts
]
```

**Do NOT use:**
```swift
.foregroundColor: UIColor(red: 0, green: 0, blue: 0, alpha: 1)  // ❌ Always black
.foregroundColor: UIColor.black  // ❌ Always black
```

### Custom Dynamic Colors

```swift
let adaptiveColor = UIColor { traitCollection in
    switch traitCollection.userInterfaceStyle {
    case .dark:
        return UIColor(red: 0.9, green: 0.9, blue: 1.0, alpha: 1.0)
    default:
        return UIColor(red: 0.1, green: 0.1, blue: 0.2, alpha: 1.0)
    }
}
```

### High Contrast (Increase Contrast)

Semantic colors also adapt to the Increase Contrast accessibility setting:

```swift
let color = UIColor { traitCollection in
    if traitCollection.accessibilityContrast == .high {
        return .black  // Higher contrast variant
    } else {
        return UIColor(white: 0.3, alpha: 1.0)
    }
}
```

Apple's built-in semantic colors already handle this — `.label` becomes pure black/white in high contrast.

### Responding to Trait Changes

```swift
// iOS 17+ (preferred)
registerForTraitChanges([UITraitUserInterfaceStyle.self]) { (self: Self, _) in
    self.updateColors()
}

// iOS 13-16
override func traitCollectionDidChange(_ previous: UITraitCollection?) {
    super.traitCollectionDidChange(previous)
    if traitCollection.hasDifferentColorAppearance(comparedTo: previous) {
        updateColors()
    }
}
```

## Wide Color / Display P3

### Creating P3 Colors for Text

```swift
// UIKit
let p3Color = UIColor(displayP3Red: 1.0, green: 0.1, blue: 0.1, alpha: 1.0)

// AppKit
let p3Color = NSColor(displayP3Red: 1.0, green: 0.1, blue: 0.1, alpha: 1.0)

// SwiftUI
let p3Color = Color(.displayP3, red: 1.0, green: 0.1, blue: 0.1, opacity: 1.0)

// Note: SwiftUI Color(red:green:blue:) defaults to sRGB, NOT P3
```

### Does Text Actually Render in P3?

**Yes**, on P3 displays. Text rendering goes through Core Text → Core Graphics, which renders in the color space of the CGContext. On P3 displays (iPhone 7+, iPad Pro, Mac with P3 display), the backing CALayer uses a P3 color space, so text colors outside sRGB gamut are rendered correctly.

**Practical impact for text:** Minimal. Text readability depends on contrast, not gamut. P3 colors that are more saturated than sRGB may reduce readability. Use P3 for branding colors on text, not for body copy.

## HDR / EDR for Text

### Can Text Be HDR?

**Not through the standard text APIs in a normal, supported way.** Standard text views (UILabel, UITextView, NSTextView, SwiftUI Text) are not the usual HDR rendering path and should be treated as SDR text for UI design.

Apple's EDR guidance treats 1.0 as reference/UI white, and most UI should not exceed that. Pushing text above it tends to create a glowing look that hurts readability.

### What About `allowedDynamicRange(.high)`?

SwiftUI does expose `allowedDynamicRange` as a view environment using `Image.DynamicRange`, but Apple's HDR APIs and examples are centered on image/video/custom rendering content, not standard text as a recommended HDR workflow.

### Possible Workarounds

1. Custom Metal/CAMetalLayer rendering using public Core Animation and Metal APIs
2. Private CAFilter APIs (not App Store safe)
3. Core Image or other custom compositing pipelines

The first category can be App Store-safe if it stays on documented APIs, but it is custom graphics work, not standard text rendering. Treat it as a special effect path, not normal body text/UI text design.

**Bottom line:** HDR text is not a standard or recommended text treatment for regular UI. Use semantic colors and normal SDR text contrast for readability; reserve custom HDR rendering for niche visual effects where you accept the complexity and readability tradeoffs.

## WCAG Contrast for Text

| Level | Normal Text | Large Text (18pt+ or 14pt+ bold) |
|-------|-------------|----------------------------------|
| AA | 4.5:1 | 3:1 |
| AAA | 7:1 | 4.5:1 |

Apple's semantic label colors meet WCAG AA on their corresponding backgrounds:
- `.label` on `.systemBackground` → 21:1 (light), 18:1 (dark)
- `.secondaryLabel` on `.systemBackground` → meets AA
- `.tertiaryLabel` → may NOT meet AA for small text (use for decorative/hint only)

## Common Pitfalls

1. **Attributed string default foreground is black, not `.label`** — invisible in dark mode. Always set explicitly.
2. **Using `UIColor.black`/`.white` instead of `.label`** — doesn't adapt to dark mode.
3. **Using `.lightText`/`.darkText`** — legacy, non-adaptive. Use `.label` variants.
4. **macOS: Using `.labelColor` for NSTextView body text** — Use `.textColor` (fully opaque, no vibrancy).
5. **P3 colors for body text** — Saturated colors reduce readability. Use for accents only.
6. **Not testing high contrast mode** — Some custom colors fail WCAG AA when Increase Contrast is on.
7. **CALayer colors (CGColor) not updating** — Must manually re-resolve on trait changes.

## Related Skills

- Use the formatting ref section in this reference for broader attributed-text formatting rules.
- Use the **editor-reference** agent when color decisions interact with accessibility text sizing.
- Use the attributed string section in this reference when the color question is really about attribute storage and conversion.

---

# Markdown in Apple's Text System

Use this skill when the main question is how Markdown maps into Apple text APIs and where rendering gaps remain.

## When to Use

- You are parsing or rendering Markdown in `Text`, `UITextView`, or TextKit.
- You need `PresentationIntent` behavior explained.
- You are deciding between native Markdown support and a third-party renderer.

## Quick Decision

- Simple inline Markdown in SwiftUI `Text` -> native support is fine
- Full Markdown document rendering or editing -> stay here
- Regex/parsing mechanics are the main question -> the **platform-reference** agent

## Core Guidance

## SwiftUI Text Markdown (iOS 15+)

### What Renders Automatically

```swift
// String literals in Text are LocalizedStringKey — Markdown processed automatically
Text("**Bold** and *italic* and `code`")
Text("~~Strikethrough~~ and [Link](https://apple.com)")
Text("***Bold italic*** together")
```

| Syntax | Renders? | Result |
|--------|----------|--------|
| `**bold**` / `__bold__` | ✅ | Bold text |
| `*italic*` / `_italic_` | ✅ | Italic text |
| `***bold italic***` | ✅ | Bold + italic |
| `` `code` `` | ✅ | Monospaced font |
| `~~strikethrough~~` | ✅ | Strikethrough |
| `[text](url)` | ✅ | Tappable link (accent color) |

### What Does NOT Render

| Syntax | Renders? | What Happens |
|--------|----------|-------------|
| `# Heading` | ❌ | Treated as plain text or ignored |
| `- Item` / `1. Item` | ❌ | Not rendered as list |
| `> Quote` | ❌ | Not rendered as quote |
| ```` ```code block``` ```` | ❌ | Not rendered as code block |
| `![alt](image)` | ❌ | Images not supported |
| Tables | ❌ | Not supported |
| `---` (horizontal rule) | ❌ | Not supported |
| Task lists `- [ ]` | ❌ | Not supported |

**Only inline Markdown works in SwiftUI Text.** Block-level Markdown is not rendered.

### String vs LocalizedStringKey

```swift
// ✅ Markdown renders — literal is LocalizedStringKey
Text("**bold** text")

// ❌ Markdown does NOT render — String variable
let text: String = "**bold** text"
Text(text)  // Displays literal asterisks

// ✅ Force Markdown on String variable
let text: String = "**bold** text"
Text(LocalizedStringKey(text))

// ❌ Disable Markdown
Text(verbatim: "**not bold**")  // Displays literal asterisks
```

### With AttributedString

```swift
// Inline-only parsing (safe for user content)
let str = try AttributedString(
    markdown: "**Bold** and [link](https://apple.com)",
    options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)
)
Text(str)
```

## AttributedString Markdown Parsing

### interpretedSyntax Options

| Option | Parses | Whitespace | Best For |
|--------|--------|-----------|----------|
| `.inlineOnly` | Inline only (bold, italic, code, links, strikethrough) | Collapses | Simple formatted text |
| `.inlineOnlyPreservingWhitespace` | Inline only | Preserves original | Chat messages, user input |
| `.full` | ALL Markdown (inline + block-level) | Markdown rules | Documents, articles |

### Block-Level Parsing with `.full`

```swift
let markdown = """
# Heading

- Item 1
- Item 2

> A quote

```
code block
```
"""

let str = try AttributedString(
    markdown: markdown,
    options: .init(interpretedSyntax: .full)
)

// Block-level structure stored in presentationIntent attribute
for run in str.runs {
    if let intent = run.presentationIntent {
        for component in intent.components {
            switch component.kind {
            case .header(let level):
                print("Heading level \(level)")
            case .unorderedList:
                print("Unordered list")
            case .listItem(let ordinal):
                print("List item \(ordinal)")
            case .blockQuote:
                print("Block quote")
            case .codeBlock(let languageHint):
                print("Code block: \(languageHint ?? "none")")
            case .paragraph:
                print("Paragraph")
            case .orderedList:
                print("Ordered list")
            case .table:
                print("Table")
            case .tableHeaderRow:
                print("Table header")
            case .tableRow(let index):
                print("Table row \(index)")
            case .tableCell(let column):
                print("Table cell column \(column)")
            case .thematicBreak:
                print("Horizontal rule")
            @unknown default:
                break
            }
        }
    }
}
```

**Critical:** SwiftUI Text ignores `presentationIntent` entirely. It stores the data but renders nothing differently for headings, lists, quotes, etc.

### Rendering PresentationIntent in UITextView

To actually render block-level Markdown in TextKit, you must interpret PresentationIntent and apply paragraph styles:

```swift
func applyBlockFormatting(to attrStr: AttributedString) -> NSAttributedString {
    let mutable = NSMutableAttributedString(attrStr)

    for run in attrStr.runs {
        guard let intent = run.presentationIntent else { continue }
        let nsRange = NSRange(run.range, in: attrStr)
        let style = NSMutableParagraphStyle()

        for component in intent.components {
            switch component.kind {
            case .header(let level):
                let sizes: [Int: CGFloat] = [1: 28, 2: 24, 3: 20, 4: 18, 5: 16, 6: 14]
                let fontSize = sizes[level] ?? 16
                mutable.addAttribute(.font, value: UIFont.boldSystemFont(ofSize: fontSize), range: nsRange)
                style.paragraphSpacingBefore = 12
                style.paragraphSpacing = 8

            case .unorderedList, .orderedList:
                style.headIndent = 24
                style.firstLineHeadIndent = 8

            case .blockQuote:
                style.headIndent = 16
                style.firstLineHeadIndent = 16
                mutable.addAttribute(.foregroundColor, value: UIColor.secondaryLabel, range: nsRange)

            case .codeBlock:
                mutable.addAttribute(.font, value: UIFont.monospacedSystemFont(ofSize: 14, weight: .regular), range: nsRange)
                mutable.addAttribute(.backgroundColor, value: UIColor.secondarySystemBackground, range: nsRange)

            default: break
            }
        }

        mutable.addAttribute(.paragraphStyle, value: style, range: nsRange)
    }

    return mutable
}
```

## Custom Markdown Attributes

### Syntax

Custom attributes use `^[text](key: value)` in Markdown:

```markdown
This has ^[custom styling](highlight: true, color: 'blue')
```

### Implementation

```swift
// Step 1: Define attribute key
enum HighlightAttribute: CodableAttributedStringKey, MarkdownDecodableAttributedStringKey {
    typealias Value = Bool
    static let name = "highlight"
}

enum ColorNameAttribute: CodableAttributedStringKey, MarkdownDecodableAttributedStringKey {
    typealias Value = String
    static let name = "color"
}

// Step 2: Create scope
extension AttributeScopes {
    struct MyMarkdownAttributes: AttributeScope {
        let highlight: HighlightAttribute
        let color: ColorNameAttribute
        let foundation: FoundationAttributes
        let swiftUI: SwiftUIAttributes
    }
    var myMarkdown: MyMarkdownAttributes.Type { MyMarkdownAttributes.self }
}

// Step 3: Dynamic lookup
extension AttributeDynamicLookup {
    subscript<T: AttributedStringKey>(
        dynamicMember keyPath: KeyPath<AttributeScopes.MyMarkdownAttributes, T>
    ) -> T { self[T.self] }
}

// Step 4: Parse
let str = try AttributedString(
    markdown: "This is ^[highlighted](highlight: true, color: 'blue') text",
    including: \.myMarkdown
)

// Step 5: Use
for run in str.runs {
    if run.highlight == true {
        print("Color: \(run.color ?? "default")")
    }
}
```

## Native vs Third-Party Markdown

### Native (AttributedString + SwiftUI Text)

**Pros:**
- No dependencies
- Codable for serialization
- Custom attributes via `MarkdownDecodableAttributedStringKey`
- Type-safe
- Localization-aware

**Cons:**
- SwiftUI Text renders ONLY inline formatting
- Block-level requires manual PresentationIntent interpretation
- No image support
- No table rendering
- Significant work for full document rendering

### Third-Party: MarkdownUI (gonzalezreal/swift-markdown-ui)

**Pros:**
- Renders full Markdown in SwiftUI (headings, lists, code blocks, images, tables, block quotes)
- Themeable
- Syntax highlighting for code blocks
- No manual PresentationIntent work

**Cons:**
- External dependency
- May not match your exact design needs
- Custom rendering harder than native Text
- Additional maintenance burden

### Third-Party: Apple's swift-markdown

**Pros:**
- Official Apple package
- Full CommonMark parser
- AST access for custom rendering
- Used by DocC

**Cons:**
- Parser only — no views included
- Must build your own rendering pipeline

### Decision Guide

| Need | Solution |
|------|----------|
| Simple bold/italic/links in SwiftUI | Native `Text("**bold**")` |
| Full Markdown document in SwiftUI | MarkdownUI library |
| Markdown in UITextView | Parse with `.full`, interpret PresentationIntent |
| Custom Markdown attributes | `MarkdownDecodableAttributedStringKey` |
| Markdown AST manipulation | swift-markdown (Apple) |
| Editable Markdown | TextKit view with syntax highlighting |

## Common Pitfalls

1. **Expecting Text to render headings/lists** — SwiftUI Text only renders inline Markdown. Block-level is silently ignored.
2. **String variable doesn't render Markdown** — Only `LocalizedStringKey` triggers Markdown. Wrap: `Text(LocalizedStringKey(string))`.
3. **`.full` parsing without PresentationIntent handling** — You get the data but nothing renders differently unless you interpret it.
4. **Forgetting custom scope in parsing** — `AttributedString(markdown:)` without `including:` ignores custom `^[](key: value)` attributes.
5. **Assuming PresentationIntent = visual rendering** — It's structural data, not rendering instructions. You must map it to visual attributes yourself.

## Related Skills

- Use the attributed string section in this reference for attribute-model and conversion choices.
- Use the **platform-reference** agent when the real gap is SwiftUI rendering limits.
- Use the **platform-reference** agent when the problem is parser choice more than Markdown rendering semantics.

---

# Text Attachments Reference

Use this skill when the main question is how inline non-text content should behave inside Apple text views.

## When to Use

- You are working with `NSTextAttachment`.
- You need attachment view providers, Genmoji, or baseline/bounds behavior.
- You need compatibility rules across TextKit 1, TextKit 2, UIKit, and AppKit.

## Quick Decision

- Static inline image attachment -> `NSTextAttachment`
- Interactive inline view in TextKit 2 -> `NSTextAttachmentViewProvider`
- Adaptive inline glyph on supported systems -> `NSAdaptiveImageGlyph`

## Core Guidance

Keep this file for the attachment model, view-provider lifecycle, and adaptive glyph choice. For protocol signatures, insertion patterns, copy-paste rules, and support matrices, use [protocols-and-patterns.md](protocols-and-patterns.md).

## NSTextAttachment

### What It Is

The core class for inline non-text content in attributed strings. Lives in UIFoundation (shared UIKit/AppKit).

### Initializers

```swift
// From image (iOS 13+) — most common
let attachment = NSTextAttachment(image: myImage)

// From data + UTI
let attachment = NSTextAttachment(data: pngData, ofType: UTType.png.identifier)

// From file wrapper (macOS-oriented)
let attachment = NSTextAttachment(fileWrapper: fileWrapper)
```

**macOS gotcha:** When using `init(data:ofType:)`, you must manually set `attachmentCell` or the image won't display. Use `init(fileWrapper:)` or set `image` directly.

### The Attachment Character (U+FFFC)

Attachments are represented in attributed strings by:
1. Unicode Object Replacement Character (U+FFFC) as placeholder
2. `.attachment` attribute holding the NSTextAttachment instance

```swift
let attachmentString = NSAttributedString(attachment: attachment)
// Creates: 1 character (U+FFFC) with .attachment attribute

let full = NSMutableAttributedString(string: "Hello ")
full.append(attachmentString)
full.append(NSAttributedString(string: " World"))
// Result: "Hello \u{FFFC} World" — attachment renders at position 6
```

### Bounds (Size + Baseline Alignment)

```swift
attachment.bounds = CGRect(x: 0, y: yOffset, width: width, height: height)
```

**The y-axis origin is at the text baseline.** Negative y moves the attachment below the baseline:

```swift
// Centered on text line (common pattern)
let font = UIFont.preferredFont(forTextStyle: .body)
let ratio = image.size.width / image.size.height
let height = font.capHeight
attachment.bounds = CGRect(
    x: 0,
    y: (font.capHeight - height) / 2,  // Center vertically
    width: height * ratio,
    height: height
)

// Baseline-aligned (sits on baseline)
attachment.bounds = CGRect(x: 0, y: 0, width: 20, height: 20)

// Descender-aligned (extends below baseline)
attachment.bounds = CGRect(x: 0, y: font.descender, width: 20, height: 20)
```

**`CGRect.zero` (default):** Uses the image's natural size. If image is nil, renders as missing-image placeholder.

### Properties (iOS 15+)

```swift
attachment.lineLayoutPadding = 4.0        // Horizontal padding around attachment
attachment.allowsTextAttachmentView = true // Allow view-based rendering (default: true)
attachment.usesTextAttachmentView         // Read-only: is view-based rendering active?
```

## NSTextAttachmentViewProvider (TextKit 2)

### What It Is

Provides a live `UIView`/`NSView` for rendering an attachment. Unlike image-based attachments, view providers can have interactive controls, animations, and dynamic content.

### Registration

```swift
// Register a view provider for a file type
NSTextAttachment.registerViewProviderClass(
    CheckboxAttachmentViewProvider.self,
    forFileType: "com.myapp.checkbox"
)
```

### Implementation

```swift
class CheckboxAttachmentViewProvider: NSTextAttachmentViewProvider {
    override init(textAttachment: NSTextAttachment,
                  parentView: UIView?,
                  textLayoutManager: NSTextLayoutManager?,
                  location: NSTextLocation) {
        super.init(textAttachment: textAttachment,
                   parentView: parentView,
                   textLayoutManager: textLayoutManager,
                   location: location)
        // MUST set tracksTextAttachmentViewBounds HERE, not in loadView
        tracksTextAttachmentViewBounds = true
    }

    override func loadView() {
        let checkbox = UISwitch()
        checkbox.isOn = (textAttachment.contents?.first == 1)
        view = checkbox
    }

    override func attachmentBounds(
        for attributes: [NSAttributedString.Key: Any],
        location: NSTextLocation,
        textContainer: NSTextContainer?,
        proposedLineFragment: CGRect,
        position: CGPoint
    ) -> CGRect {
        return CGRect(x: 0, y: -4, width: 30, height: 30)
    }
}
```

### Lifecycle

1. **Registration** — `registerViewProviderClass` maps file type → provider class
2. **Creation** — TextKit 2 creates provider when attachment enters viewport
3. **`loadView()`** — Called to create the view. Set `self.view`.
4. **Display** — View is added to the text view's subview hierarchy
5. **Removal** — When attachment scrolls out of viewport, view may be removed
6. **Reuse** — Views are NOT reused like table cells. New provider per appearance.

### Critical Rules

- **`tracksTextAttachmentViewBounds` must be set in `init`, NOT `loadView`** — Setting it in loadView is too late and the bounds won't track correctly.
- **View-based attachments are LOST on TextKit 1 fallback** — The moment anything triggers fallback, all NSTextAttachmentViewProvider views disappear because TextKit 1 uses NSTextAttachmentCellProtocol instead.
- **Only works with TextKit 2** — `usesTextAttachmentView` returns false if TextKit 1 is active.

## NSAdaptiveImageGlyph (iOS 18+)

### What It Is

A special inline image that automatically adapts its size to match surrounding text. Used for Genmoji, stickers, and Memoji.

```swift
let glyph = NSAdaptiveImageGlyph(imageContent: imageData)

glyph.contentIdentifier   // Unique ID
glyph.contentDescription  // Accessibility description
glyph.imageContent        // Raw image data (multi-resolution)
glyph.contentType          // UTType
```

### How It Differs from NSTextAttachment

| Aspect | NSTextAttachment | NSAdaptiveImageGlyph |
|--------|-----------------|---------------------|
| Sizing | Manual (bounds property) | Automatic (matches text size) |
| Aspect ratio | Any | Always square |
| Resolutions | Single image | Multiple resolutions embedded |
| Dynamic Type | Manual handling | Automatic scaling |
| User insertion | Programmatic | Emoji keyboard |
| Available | iOS 7+ | iOS 18+ |

### Enabling in Text Views

```swift
textView.supportsAdaptiveImageGlyph = true  // UITextView
// Users can now insert Genmoji from the emoji keyboard
```

### Extracting from Attributed String

```swift
attributedString.enumerateAttribute(
    .adaptiveImageGlyph,
    in: NSRange(location: 0, length: attributedString.length)
) { value, range, _ in
    if let glyph = value as? NSAdaptiveImageGlyph {
        print("Genmoji: \(glyph.contentDescription)")
    }
}
```

## Common Pitfalls

1. **View attachments lost on TK1 fallback** — The instant anything triggers fallback, all NSTextAttachmentViewProvider views vanish.
2. **`tracksTextAttachmentViewBounds` set in loadView** — Too late. Must set in init.
3. **macOS: image not displaying** — With `init(data:ofType:)`, must set `attachmentCell` manually or use `init(fileWrapper:)`.
4. **Copy/paste loses attachment** — `contents` must be non-nil. Image-only attachments don't survive paste.
5. **Bounds y-coordinate confusion** — Negative y goes below baseline. Use `font.descender` for bottom-aligned.
6. **Not setting accessibility** — VoiceOver announces U+FFFC as "replacement character" without a description.

## Related Skills

- For protocol signatures, insertion recipes, and support matrices, see [protocols-and-patterns.md](protocols-and-patterns.md).
- Use the formatting ref section in this reference for non-attachment attributed-text formatting.
- Use the **textkit-reference** agent for fragment and viewport behavior around attachments.
- Use the **textkit-reference** agent when attachment choices may force compatibility mode.

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

- For paragraph style attribute reference -> the formatting ref section in this reference
- For text measurement with these settings -> the **textkit-reference** agent
- For Dynamic Type scaling interaction -> the **editor-reference** agent
- For multi-column layout with different line settings -> the **textkit-reference** agent

---

# Bidirectional Text and RTL

Use this skill when the main question involves right-to-left text, mixed-direction content, or the APIs that control writing direction.

## When to Use

- Supporting Arabic, Hebrew, or other RTL languages in text editors
- Mixed LTR/RTL content (phone numbers in Arabic text, etc.)
- Cursor movement or selection in bidirectional text
- Writing direction APIs at any level (paragraph, attribute, view, SwiftUI)
- iOS 26 Natural Selection / `selectedRanges` migration

## Quick Decision

```
Using standard UITextView / UITextField?
    → Bidi mostly "just works" with .natural writing direction.
    → Read the Mixed Content section for edge cases.

Building a custom UITextInput view?
    → You must handle bidi yourself. Read everything here.

Targeting iOS 26+?
    → Adopt Natural Selection (selectedRanges) for correct bidi selection.

Need inline direction overrides?
    → Use .writingDirection attributed string key.
```

## Core Guidance

## Writing Direction API Layers

Direction is controlled at multiple levels, from highest to lowest:

### 1. SwiftUI Environment

```swift
// Read current layout direction
@Environment(\.layoutDirection) var layoutDirection

// Force direction on a view hierarchy
VStack { ... }
    .environment(\.layoutDirection, .rightToLeft)

// Mirror images for RTL
Image("arrow")
    .flipsForRightToLeftLayoutDirection(true)
```

**Note:** SwiftUI `Text` ignores the `.writingDirection` attributed string key. Use the environment for direction control in SwiftUI.

### 2. NSParagraphStyle (Paragraph Level)

The most common way to set direction for a block of text:

```swift
let style = NSMutableParagraphStyle()
style.baseWritingDirection = .natural      // Auto-detect from content (default)
// or .leftToRight
// or .rightToLeft

let attrs: [NSAttributedString.Key: Any] = [.paragraphStyle: style]
```

`.natural` uses the Unicode Bidi Algorithm (rules P2/P3) to detect direction from the first strong directional character.

### 3. .writingDirection Attribute (Inline Overrides)

For overriding direction within a paragraph — equivalent to Unicode bidi control characters:

```swift
// Force a range to LTR embedding (like Unicode LRE + PDF)
let ltrEmbed: [NSNumber] = [
    NSNumber(value: NSWritingDirection.leftToRight.rawValue | NSWritingDirectionFormatType.embedding.rawValue)
]
attrString.addAttribute(.writingDirection, value: ltrEmbed, range: range)

// Force a range to RTL override (like Unicode RLO + PDF)
let rtlOverride: [NSNumber] = [
    NSNumber(value: NSWritingDirection.rightToLeft.rawValue | NSWritingDirectionFormatType.override.rawValue)
]
```

**Embedding** respects the content's own directionality within the override. **Override** forces all characters to display in the specified direction regardless of their inherent directionality.

### 4. UITextInput Protocol

```swift
// Set direction for a text range at runtime
textInput.setBaseWritingDirection(.rightToLeft, for: textRange)

// Read current direction
let direction = textInput.baseWritingDirection(for: position, in: .forward)
```

### 5. iOS 26: AttributedString.WritingDirection

```swift
var text = AttributedString("Hello عربي")
text.writingDirection = .rightToLeft

// Values: .leftToRight, .rightToLeft
```

### 6. NSTextContainer

Writing direction affects line fragment advancement:

```swift
// The writingDirection parameter determines which side lines start from
textContainer.lineFragmentRect(
    forProposedRect: rect,
    at: index,
    writingDirection: .rightToLeft,
    remaining: &remaining
)
```

## Visual vs Logical Order

This is the core concept for bidi text.

**Logical order:** How characters are stored in memory (the string). Always follows reading order of each language — Arabic characters are stored right-to-left in logical order.

**Visual order:** How characters appear on screen after the Unicode Bidi Algorithm reorders them.

```
Logical: "Hello مرحبا World"
         H-e-l-l-o- -ا-ب-ح-ر-م- -W-o-r-l-d

Visual:  "Hello ابحرم World"
         Characters 6-10 are visually reordered (RTL run)
```

**A single cursor position can map to two visual positions** at direction boundaries. This is why cursor movement in bidi text is inherently ambiguous.

## iOS 26: Natural Selection

Previously, `selectedRange` was a single contiguous NSRange. In bidirectional text, this caused visually disjoint selections — the selection included storage-contiguous characters that were visually separated.

### New APIs

```swift
// New: multiple ranges following visual cursor movement
textView.selectedRanges  // [NSRange] — replaces selectedRange

// New delegate method for multi-range edits
func textView(_ textView: UITextView,
              shouldChangeTextInRanges ranges: [NSRange],
              replacementStrings: [String]?) -> Bool {
    // Handle multi-range replacement
    return true
}
```

### Requirements

- Requires TextKit 2 (accessing `textView.layoutManager` reverts to TextKit 1 and disables Natural Selection)
- `selectedRange` (singular) still works but will be deprecated in a future release
- iOS 26+ only

## Mixed Content Patterns

### Phone Numbers in RTL Text

Phone numbers are LTR even in RTL context. Without explicit direction, they may reorder incorrectly:

```swift
// Problem: "اتصل بـ 555-1234" may render with digits reordered
// Solution: Wrap with Unicode LTR mark
let phone = "\u{200E}555-1234\u{200E}"
let text = "اتصل بـ \(phone)"
```

| Character | Purpose |
|-----------|---------|
| `\u{200E}` (LRM) | Left-to-right mark — invisible, asserts LTR direction |
| `\u{200F}` (RLM) | Right-to-left mark — invisible, asserts RTL direction |
| `\u{202A}` (LRE) | Left-to-right embedding start |
| `\u{202B}` (RLE) | Right-to-left embedding start |
| `\u{202C}` (PDF) | Pop directional formatting (ends LRE/RLE) |

### Unknown-Directionality Variables

User-generated content (usernames, titles) may be any direction:

```swift
// Wrap unknown-direction content with first-strong isolate
let username = "\u{2068}\(user.name)\u{2069}"
// U+2068 = First Strong Isolate
// U+2069 = Pop Directional Isolate
```

### Text Alignment in RTL

```swift
// Use .natural (not .left/.right) for automatic RTL support
style.alignment = .natural
// .natural = left-aligned in LTR, right-aligned in RTL

// If you need explicit alignment regardless of direction:
style.alignment = .left   // Always left, even in RTL context
style.alignment = .right  // Always right, even in LTR context
```

**Gotcha:** In an RTL text view, `.left` alignment still means left — it does NOT flip. But `.natural` and leading/trailing constraints DO flip.

## iOS 26: Dynamic Writing Direction

Previously, writing direction was determined by the first strong character (Unicode Bidi Algorithm P2/P3). iOS 26 introduces content-aware dynamic direction detection:

- Direction is determined by the **content** of the text, not just the first character
- New Language Introspector API for custom text engines to query direction

## Common Pitfalls

1. **Using `.left`/`.right` instead of `.natural`/leading/trailing** — Hardcoded left/right alignment and constraints don't flip for RTL. Always use `.natural` alignment and leading/trailing constraints.
2. **Assuming cursor movement is simple in bidi** — At direction boundaries, a single logical position maps to two visual positions. The cursor can appear to "jump" or move in unexpected directions.
3. **Phone numbers reordering in RTL** — Wrap with LRM (`\u{200E}`) or use first-strong isolate (`\u{2068}`/`\u{2069}`) to prevent digit reordering.
4. **SwiftUI ignoring `.writingDirection`** — The attributed string key is silently ignored in SwiftUI Text. Use `.environment(\.layoutDirection, .rightToLeft)` instead.
5. **In-app language switching not updating text direction** — Changing locale programmatically doesn't reliably update text view direction. The system responds to system-level language changes, not in-app ones.
6. **`selectedRange` in bidi text (pre-iOS 26)** — A single contiguous NSRange creates visually disjoint selections in bidirectional text. Adopt `selectedRanges` on iOS 26+.
7. **TextKit 1 glyph range bugs with RTL** — NSLayoutManager methods can return incorrect CGRect values for RTL character ranges. Consider TextKit 2 or Core Text for precise RTL geometry.
8. **NSTextView not accepting direction change** — On macOS, `makeTextWritingDirectionRightToLeft(_:)` requires the view to be first responder and editable.

## Related Skills

- Use the formatting ref section in this reference for the `.writingDirection` attribute and `baseWritingDirection` on NSParagraphStyle.
- Use the **editor-reference** agent for `setBaseWritingDirection(_:for:)` in custom UITextInput views.
- Use the **editor-reference** agent for cursor and selection behavior.
- Use the **platform-reference** agent for platform differences in RTL support.
