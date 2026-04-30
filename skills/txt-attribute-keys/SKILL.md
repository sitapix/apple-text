---
name: txt-attribute-keys
description: Look up NSAttributedString.Key values, value types, and view-compatibility rules — typography, color, decoration, paragraph style, attachments, links, AppKit-only keys. Use when picking the right key, debugging an attribute that "does nothing," or checking whether an attribute survives in SwiftUI Text vs UITextView vs NSTextView. The key catalog and view-compatibility matrix change with each Foundation release; before claiming any signature is current, fetch via Sosumi (`sosumi.ai/documentation/foundation/nsattributedstring/key`). Do NOT use for the AttributedString-vs-NSAttributedString decision — see txt-attributed-string. Do NOT use for inline image/Genmoji embedding — see txt-attachments. Do NOT use for color-specific dark-mode behavior — see txt-colors.
license: MIT
---

# Attribute Keys Reference

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill catalogs `NSAttributedString.Key` values, their value types, and which keys actually render in each text view. The catalog and view-compatibility matrix shift with each Foundation release — Apple has added keys (`.adaptiveImageGlyph`, `.textAlternatives`) and changed which SwiftUI text APIs honor which keys without warning. Before quoting any specific key, value type, or compatibility cell as current, fetch the official entry via Sosumi (`sosumi.ai/documentation/foundation/nsattributedstring/key`). The tables here are a starting point, not a contract.

The compatibility matrix in particular is empirical, not declared. SwiftUI Text silently drops attributes it does not understand; UITextView in TextKit 1 mode renders attributes TextKit 2 mode does not; AppKit text views support keys (`superscript`, `toolTip`, `textBlock`) that have no UIKit equivalent at all. If an attribute "does nothing," verify against a runtime test before assuming a bug — the more common cause is a key that the destination view ignores by design.

## Contents

- [Typography keys](#typography-keys)
- [Color keys](#color-keys)
- [Decoration keys](#decoration-keys)
- [Layout and structure keys](#layout-and-structure-keys)
- [Content keys](#content-keys)
- [AppKit-only keys](#appkit-only-keys)
- [Underline and strikethrough styles](#underline-and-strikethrough-styles)
- [Paragraph style and lists](#paragraph-style-and-lists)
- [View compatibility](#view-compatibility)
- [RTF round-trip](#rtf-round-trip)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Typography keys

These control glyph selection, sizing, spacing, and synthetic transforms. Value types are bridged to their Objective-C equivalents — Swift `CGFloat` is wrapped in `NSNumber` when stored in the dictionary.

| Key | Value type | Effect |
|-----|-----------|--------|
| `.font` | `UIFont` / `NSFont` | Typeface, size, weight |
| `.kern` | `NSNumber` (CGFloat) | Inter-character spacing in points (absolute) |
| `.tracking` | `NSNumber` (CGFloat) | Tracking that scales with font size (iOS 14+, macOS 11+) |
| `.ligature` | `NSNumber` (Int) | 0 = none, 1 = default, 2 = all (AppKit) |
| `.baselineOffset` | `NSNumber` (CGFloat) | Vertical shift from baseline |
| `.obliqueness` | `NSNumber` (CGFloat) | Synthetic italic, positive leans right |
| `.expansion` | `NSNumber` (CGFloat) | Horizontal stretch, 0 = normal |
| `.verticalGlyphForm` | `NSNumber` (Int) | 0 = horizontal, 1 = vertical (CJK) |

`.kern` and `.tracking` look interchangeable but differ at scale. `.kern` is in points and stays constant — 2pt of kern reads thin at 12pt and barely visible at 48pt. `.tracking` scales with the font and is the right choice when an attribute should look proportional across sizes.

## Color keys

| Key | Value type | Effect |
|-----|-----------|--------|
| `.foregroundColor` | `UIColor` / `NSColor` | Text color |
| `.backgroundColor` | `UIColor` / `NSColor` | Background fill behind glyphs |
| `.strokeColor` | `UIColor` / `NSColor` | Outline color |
| `.strokeWidth` | `NSNumber` (CGFloat) | Outline width — sign matters (see below) |
| `.shadow` | `NSShadow` | Drop shadow |

`.strokeWidth` has a sign convention that catches everyone. A positive value renders stroke only — outlined hollow glyphs. A negative value renders fill plus stroke — solid glyphs with an outline on top. Setting `.strokeColor: .blue` and `.strokeWidth: 3.0` produces hollow blue letters; setting `.strokeWidth: -3.0` keeps the foreground fill and adds a blue border.

The default `.foregroundColor` is black, not the semantic label color. Attributed strings created without an explicit foreground render as invisible black text in dark mode. The fix is always-explicit: `.foregroundColor: UIColor.label`.

## Decoration keys

| Key | Value type | Effect |
|-----|-----------|--------|
| `.underlineStyle` | `NSNumber` (NSUnderlineStyle raw value) | Underline pattern |
| `.underlineColor` | `UIColor` / `NSColor` | Underline color (nil inherits foreground) |
| `.strikethroughStyle` | `NSNumber` (NSUnderlineStyle raw value) | Strikethrough pattern |
| `.strikethroughColor` | `UIColor` / `NSColor` | Strikethrough color |

Underline and strikethrough share the `NSUnderlineStyle` option set, combined with bitwise OR. See [Underline and strikethrough styles](#underline-and-strikethrough-styles) below.

## Layout and structure keys

| Key | Value type | Effect |
|-----|-----------|--------|
| `.paragraphStyle` | `NSParagraphStyle` | Per-paragraph layout (see section below) |
| `.writingDirection` | `[NSNumber]` | Bidi embedding/override levels |
| `.textEffect` | `NSAttributedString.TextEffectStyle` | Letterpress is the only public value |

A paragraph style applied to a sub-range gets extended to the full paragraph at draw time by `fixAttributes` — there is no such thing as half-a-paragraph indentation. If a sub-range needs different alignment or indentation, split the paragraph (insert a `\n`).

## Content keys

| Key | Value type | Effect |
|-----|-----------|--------|
| `.attachment` | `NSTextAttachment` | Inline image, view provider, or adaptive glyph carrier |
| `.link` | `URL` or `String` | Hyperlink |
| `.textAlternatives` | `NSTextAlternatives` | Alternative interpretations (autocorrect candidates) |
| `.adaptiveImageGlyph` | `NSAdaptiveImageGlyph` | Genmoji and stickers, iOS 18+ |

`.link` accepts either a `URL` or a `String`. UITextView and NSTextView render both; SwiftUI Text only renders `URL`. If a link "doesn't tap" in SwiftUI, the value is probably a `String`.

## AppKit-only keys

These are AppKit-specific and have no UIKit counterpart. Using them in cross-platform code requires `#if os(macOS)` guards.

| Key | Value type | Effect |
|-----|-----------|--------|
| `.superscript` | `NSNumber` (Int) | Positive = superscript, negative = subscript |
| `.cursor` | `NSCursor` | Hover cursor |
| `.toolTip` | `String` | Hover tooltip |
| `.markedClauseSegment` | `NSNumber` (Int) | CJK marked-text clause index |
| `.spellingState` | `NSNumber` (Int) | Spelling/grammar squiggle indicator |
| `.glyphInfo` | `NSGlyphInfo` | Glyph substitution |
| `.textBlock` | `NSTextBlock` | Table cell — note: forces TextKit 1 |

`.textBlock` is part of the AppKit-only `NSTextTable` system and forces a TextKit 2 view to fall back to TextKit 1 the moment it appears. If preserving TextKit 2 features (Writing Tools, viewport rendering) matters, do not use `NSTextTable`.

## Underline and strikethrough styles

`NSUnderlineStyle` is an option set. Combine line style, pattern, and modifier with `.union(_:)` or array literal syntax, then store as `rawValue`:

```swift
// Thick dashed underline, words only
let style: NSUnderlineStyle = [.thick, .patternDash, .byWord]

let attrs: [NSAttributedString.Key: Any] = [
    .underlineStyle: style.rawValue,
    .underlineColor: UIColor.systemRed,
]
```

Line style: `.single`, `.thick`, `.double`. Pattern (combined with style): `.patternDot`, `.patternDash`, `.patternDashDot`, `.patternDashDotDot`. Modifier: `.byWord` skips spaces. The same option set is used for `.strikethroughStyle`.

## Paragraph style and lists

`NSParagraphStyle` is immutable — to change anything, instantiate `NSMutableParagraphStyle`, configure it, then set it as the value:

```swift
let style = NSMutableParagraphStyle()
style.alignment = .natural          // .left / .right / .center / .justified / .natural
style.lineSpacing = 4               // additional space between lines
style.paragraphSpacing = 12         // space after this paragraph
style.paragraphSpacingBefore = 8    // space before this paragraph
style.firstLineHeadIndent = 20
style.headIndent = 10               // subsequent-line indent
style.tailIndent = -10              // negative = inset from right edge
style.lineBreakMode = .byWordWrapping
style.lineBreakStrategy = .standard
style.hyphenationFactor = 0.5       // 0.0 (off) to 1.0 (max)
style.tabStops = [NSTextTab(textAlignment: .left, location: 100)]
```

`NSTextList` markers (UIKit iOS 17+, AppKit always): `.disc`, `.circle`, `.square`, `.decimal`, `.lowercaseAlpha`, `.uppercaseAlpha`, `.lowercaseRoman`, `.uppercaseRoman`. AppKit adds Latin, hexadecimal, octal, hyphen, and check formats.

```swift
style.textLists = [NSTextList(markerFormat: .disc, options: 0)]
```

## View compatibility

This matrix is empirical — verify with a runtime test before assuming a key works. SwiftUI Text in particular drops most attributes silently.

| Attribute | SwiftUI Text | TextEditor (iOS 26+) | UITextView | UILabel | NSTextView |
|-----------|:-:|:-:|:-:|:-:|:-:|
| `.font` | yes | yes | yes | yes | yes |
| `.foregroundColor` | yes | yes | yes | yes | yes |
| `.backgroundColor` | yes | yes | yes | yes | yes |
| `.kern` / `.tracking` | yes | yes | yes | yes | yes |
| `.underlineStyle` | yes | yes | yes | yes | yes |
| `.strikethroughStyle` | yes | yes | yes | yes | yes |
| `.baselineOffset` | yes | yes | yes | yes | yes |
| `.link` | yes (URL only) | yes | yes | no | yes |
| `.paragraphStyle` | no | partial (alignment, line height) | yes | yes | yes |
| `.shadow` | no (use `.shadow()` modifier) | no | yes | yes | yes |
| `.strokeColor` / `.strokeWidth` | no | no | yes | yes | yes |
| `.obliqueness` | no | no | yes | yes | yes |
| `.expansion` | no | no | yes | yes | yes |
| `.textEffect` | no | no | yes | yes | yes |
| `.attachment` | no | no | yes | display only | yes |
| `.adaptiveImageGlyph` | no | yes | yes | yes | yes |
| `.superscript` | no | no | no | no | yes (AppKit) |
| `.toolTip` | no | no | no | no | yes (AppKit) |
| `.textBlock` (TextKit 1 only) | no | no | no | no | yes (AppKit) |
| `.textList` | no | no | yes (iOS 17+) | yes | yes |

UITextView with `allowsEditingTextAttributes = true` shows a B/I/U menu — the only built-in formatting UI. Anything else (size, color, alignment) requires custom UI.

## RTF round-trip

Attributes that survive `NSAttributedString.DocumentType.rtf` archiving:

- `.font`, `.foregroundColor`, `.backgroundColor`, `.paragraphStyle`
- `.underlineStyle`, `.underlineColor`, `.strikethroughStyle`, `.strikethroughColor`
- `.kern`, `.baselineOffset`
- `.link`, `.attachment`, `.shadow`, `.strokeColor`, `.strokeWidth`
- `.superscript` (AppKit), `.textList`, `.textBlock`

Attributes that are lost in RTF:

- `.obliqueness`, `.expansion` — may survive if the font supports them as descriptors
- `.textEffect` (letterpress)
- `.adaptiveImageGlyph` — Genmoji has its own RTFD-style handling; plain RTF drops it
- Custom attributes — unless you handle RTF custom tags via `NSAttributedString.DocumentReadingOptionKey.documentType`

For format-preserving storage, RTFD archives or `AttributedString` Codable encoding preserves more.

## Common Mistakes

1. **Using `String` for `.link` in SwiftUI Text.** SwiftUI only renders `URL` values; a `String` link is silently ignored. The fix is always `.link: URL(string: "...")!`.

2. **Setting `.paragraphStyle` on a sub-range and expecting only that range to indent.** TextKit's `fixAttributes` extends paragraph styles to the full paragraph at draw time. Half-a-paragraph indentation does not exist; split the paragraph with `\n` if you need different formatting.

   ```swift
   // WRONG — second half won't indent because first half wins
   let mutable = NSMutableAttributedString(string: "Header\nBody")
   mutable.addAttribute(.paragraphStyle, value: indented, range: NSRange(location: 7, length: 4))

   // CORRECT — paragraph break separates the styles
   let mutable = NSMutableAttributedString(string: "Header\nBody")
   mutable.addAttribute(.paragraphStyle, value: header, range: NSRange(location: 0, length: 6))
   mutable.addAttribute(.paragraphStyle, value: indented, range: NSRange(location: 7, length: 4))
   ```

3. **Mutating `NSParagraphStyle` directly.** `NSParagraphStyle` is immutable — there are no setters. The error is silent: code compiles, runtime does nothing. Always start from `NSMutableParagraphStyle`, configure, then set as the attribute value.

4. **Hardcoded `.foregroundColor: UIColor.black` instead of `.label`.** The default attributed-string foreground is opaque black, which becomes invisible in dark mode. Always set `.foregroundColor: UIColor.label` (or another semantic color) for adaptive behavior.

5. **`NSTextTable` in code that needs Writing Tools.** `.textBlock` forces TextKit 1 fallback the moment it appears in storage. The TextKit 2-only features (inline Writing Tools rewrites, viewport rendering) stop working for the entire view, not just the table. If a layout calls for tables, decide between TextKit 2 features and table rendering before adding the attribute.

6. **`.kern` for "tighter spacing across all sizes."** Kern is absolute points; it makes 12pt text look thin and 48pt text look unchanged. For proportional spacing across sizes, use `.tracking`.

7. **AppKit-only keys in cross-platform code.** `.superscript`, `.toolTip`, `.cursor`, `.textBlock`, `.textTable` exist only on AppKit. Apply them inside `#if os(macOS)` or extract from the iOS code path entirely.

8. **Assuming `typingAttributes` survives an `attributedText` set or a selection change.** Assigning `attributedText` on `UITextView` resets `typingAttributes` to whatever the new attributed string's last run carries. Selection-change events also clear them. An editor that customizes typing fonts — for example, a Markdown editor that toggles italic for the next-typed run — loses its typing styles every time the user moves the cursor or any code reassigns `attributedText`. The fix is to keep a sidecar `currentTypingAttributes` dictionary on the controller and re-apply it inside `DispatchQueue.main.async` from `textViewDidChangeSelection(_:)`; the async hop is necessary because UIKit clears typing attributes after the delegate returns synchronously.

   ```swift
   var currentTypingAttributes: [NSAttributedString.Key: Any] = [.font: UIFont.preferredFont(forTextStyle: .body)]

   func textViewDidChangeSelection(_ textView: UITextView) {
       DispatchQueue.main.async {
           textView.typingAttributes = self.currentTypingAttributes
       }
   }
   ```

   Related: `attributedText` *getter* has copy semantics. Reading `textView.attributedText` inside `textViewDidChange(_:)` copies the entire attributed string on every keystroke — at 50KB the per-keystroke cost becomes visible in Time Profiler. For read-only access in hot paths, use `textView.textStorage` directly; it is the live `NSTextStorage` and does not copy. The `.attributedText` getter is only worth it when the caller actually needs an isolated snapshot.

## References

- `txt-attributed-string` — picking AttributedString vs NSAttributedString and converting between them
- `txt-attachments` — `.attachment` and `.adaptiveImageGlyph` lifecycle, view providers, baseline alignment
- `txt-colors` — semantic colors, dark-mode adaptation, wide-color rendering
- `txt-line-breaking` — `NSParagraphStyle` line break, hyphenation, tab stops
- [`references/latest-apis.md`](references/latest-apis.md) — per-key value type, availability, and Sosumi URL liveness; refreshed against current Apple docs
- [NSAttributedString.Key](https://sosumi.ai/documentation/foundation/nsattributedstring/key)
- [NSParagraphStyle](https://sosumi.ai/documentation/uikit/nsparagraphstyle)
- [NSTextList](https://sosumi.ai/documentation/uikit/nstextlist)
- [NSUnderlineStyle](https://sosumi.ai/documentation/uikit/nsunderlinestyle)
- [NSTextTable (AppKit)](https://sosumi.ai/documentation/appkit/nstexttable)
