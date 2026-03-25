---
name: apple-text-bidi
description: Use when handling bidirectional text, RTL languages, writing direction controls, or cursor behavior in Arabic/Hebrew
license: MIT
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

- Use `/skill apple-text-formatting-ref` for the `.writingDirection` attribute and `baseWritingDirection` on NSParagraphStyle.
- Use `/skill apple-text-input-ref` for `setBaseWritingDirection(_:for:)` in custom UITextInput views.
- Use `/skill apple-text-interaction` for cursor and selection behavior.
- Use `/skill apple-text-appkit-vs-uikit` for platform differences in RTL support.
