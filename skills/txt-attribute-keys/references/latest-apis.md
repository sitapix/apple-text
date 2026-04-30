# Latest API surface — txt-attribute-keys

Authored against iOS 26.x / Swift 6.x / Xcode 26.x. Last refreshed 2026-04-29 against Sosumi.

Each row is verified against the canonical Sosumi page at
`https://sosumi.ai/documentation/foundation/nsattributedstring/key/<key>`. Value types
follow Sosumi's documented type, which uses Objective-C bridging conventions
(`NSNumber` wrappers around `CGFloat` / `Int`, `UIColor` cross-listed with `NSColor`
under the macOS docs). Availability is taken from each page's `since:` annotation.

## Font and color

- `.font` — `UIFont` / `NSFont`. Typeface for the run. since: iOS 6.0, macOS 10.0
- `.foregroundColor` — `UIColor` / `NSColor`. Glyph fill color; default is opaque black, not the semantic label color. since: iOS 6.0, macOS 10.0
- `.backgroundColor` — `UIColor` / `NSColor`. Fill behind the glyphs (does not extend to the line fragment). since: iOS 6.0, macOS 10.0
- `.strokeColor` — `UIColor` / `NSColor`. Outline color for stroked glyphs. since: iOS 6.0, macOS 10.0
- `.strokeWidth` — `NSNumber` (floating-point). Stroke width as a percentage of font size; sign chooses fill+stroke vs stroke-only. since: iOS 6.0, macOS 10.0
- `.shadow` — `NSShadow`. Drop shadow under the glyphs. since: iOS 6.0, macOS 10.0

## Underline and strikethrough

- `.underlineStyle` — `NSNumber` (Int, raw value of `NSUnderlineStyle`). Pattern + line + modifier combined with `.union(_:)`. since: iOS 6.0, macOS 10.0
- `.underlineColor` — `UIColor` / `NSColor`. Default `nil` inherits the foreground color. since: iOS 7.0, macOS 10.0
- `.strikethroughStyle` — `NSNumber` (Int, `NSUnderlineStyle` raw value). Same option set as underline. since: iOS 6.0, macOS 10.0
- `.strikethroughColor` — `UIColor` / `NSColor`. Default `nil` inherits the foreground color. since: iOS 7.0, macOS 10.0

## Spacing and kerning

- `.kern` — `NSNumber` (CGFloat). Inter-character spacing in absolute points. since: iOS 6.0, macOS 10.0
- `.tracking` — `NSNumber` (CGFloat). Spacing that scales with font size; preferred over `.kern` for proportional adjustments. since: iOS 14.0, macOS 11.0
- `.ligature` — `NSNumber` (Int). 0 = none, 1 = default, 2 = all (AppKit). since: iOS 6.0, macOS 10.0
- `.baselineOffset` — `NSNumber` (CGFloat). Vertical shift from baseline in points. since: iOS 7.0, macOS 10.0
- `.expansion` — `NSNumber` (CGFloat). Logarithmic horizontal stretch; 0 = normal. since: iOS 7.0, macOS 10.0
- `.obliqueness` — `NSNumber` (CGFloat). Synthetic italic; positive leans right. since: iOS 7.0, macOS 10.0
- `.verticalGlyphForm` — `NSNumber` (Int). 0 = horizontal, 1 = vertical (intended for CJK). since: iOS 7.0, macOS 10.7

## Attachments and substitution

- `.attachment` — `NSTextAttachment`. Inline image, view provider, or adaptive-glyph carrier in a `\u{FFFC}` slot. since: iOS 7.0, macOS 10.0
- `.link` — `URL` (preferred) or `String`. SwiftUI Text only renders `URL` values. since: iOS 7.0, macOS 10.0
- `.textEffect` — `NSAttributedString.TextEffectStyle` (`NSString`). Letterpress is the only public value. since: iOS 6.0, macOS 10.10
- `.adaptiveImageGlyph` — `NSAdaptiveImageGlyph`. Genmoji and stickers carrier; pairs with a `\u{FFFD}` attachment slot. since: iOS 18.0, macOS 15.0
- `.textAlternatives` — `NSTextAlternatives`. Alternative interpretations (autocorrect candidates). since: macOS 10.8 (cross-listed under Foundation today)
- `.replacementIndex` — `NSNumber` (Int). Ordinal position of a replacement value in a format-string-based attributed string. since: iOS 15.0, macOS 12.0

## Paragraph-level keys

- `.paragraphStyle` — `NSParagraphStyle`. Per-paragraph layout (alignment, spacing, indents, line-break, hyphenation, tab stops, lists). `fixAttributes` extends a sub-range style to the whole paragraph at draw time. since: iOS 6.0, macOS 10.0
- `.writingDirection` — `[NSNumber]` (array of Int). Bidi embedding/override levels corresponding to LRE/RLE/LRO/RLO control characters. since: iOS 6.0, macOS 10.6
- `.languageIdentifier` — `String` (BCP 47). Language tag for the run; consulted by translation and locale-aware shaping. since: iOS 15.0, macOS 12.0

## Modern keys (iOS 18+)

- `.adaptiveImageGlyph` — `NSAdaptiveImageGlyph`. Genmoji/sticker payload introduced for image playgrounds and rich messaging. since: iOS 18.0, macOS 15.0
- `.textHighlightStyle` — `NSAttributedString.TextHighlightStyle`. Background highlight with automatic foreground contrast adjustment. since: iOS 18.0, macOS 15.0
- `.textHighlightColorScheme` — `NSAttributedString.TextHighlightColorScheme`. Custom highlight palette paired with `.textHighlightStyle`. since: iOS 18.0, macOS 15.0

## AppKit-only keys

These resolve at `https://sosumi.ai/documentation/foundation/nsattributedstring/key/<key>`
but are documented as macOS-only (no UIKit counterpart). Apply inside `#if os(macOS)`.

- `.superscript` — `NSNumber` (Int). Positive = superscript, negative = subscript. since: macOS 10.0
- `.cursor` — `NSCursor`. Hover cursor; defaults to I-beam. since: macOS 10.0
- `.toolTip` — `String`. Hover tooltip text. since: macOS 10.0
- `.markedClauseSegment` — `NSNumber` (Int). CJK marked-text clause index. since: macOS 10.0
- `.spellingState` — `NSNumber` (Int). Spelling/grammar squiggle bitmask (10.5+ separates spelling from grammar bits). since: macOS 10.0
- `.glyphInfo` — `NSGlyphInfo`. Glyph substitution; layout manager applies the substitute glyph if the font supplies it. since: macOS 10.0

## Old patterns

- `.textBlock` — referenced in SKILL.md as the carrier for `NSTextTable` table cells, but does not resolve as a standalone `NSAttributedString.Key` page on Sosumi (404 at the foundation/nsattributedstring/key path). The underlying types (`NSTextBlock`, `NSTextTable`) remain documented under `https://sosumi.ai/documentation/appkit/nstextblock` and `https://sosumi.ai/documentation/appkit/nstexttable`. Treat the key reference as AppKit-only and verify against the Xcode-bundled headers if precise spelling matters; cross-platform code should not rely on it. Note: `.textBlock` forces a TextKit 2 view back to TextKit 1.

## Signatures verified against Sosumi

| URL | Status | Last fetched |
|---|---|---|
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/font | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/foregroundcolor | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/backgroundcolor | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/strokecolor | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/strokewidth | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/shadow | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/underlinestyle | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/underlinecolor | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/strikethroughstyle | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/strikethroughcolor | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/kern | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/tracking | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/ligature | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/baselineoffset | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/expansion | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/obliqueness | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/verticalglyphform | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/attachment | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/link | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/texteffect | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/adaptiveimageglyph | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/textalternatives | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/replacementindex | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/paragraphstyle | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/writingdirection | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/languageidentifier | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/texthighlightstyle | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/texthighlightcolorscheme | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/superscript | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/cursor | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/tooltip | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/markedclausesegment | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/spellingstate | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/glyphinfo | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring/key/textblock | 404 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nstextblock | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/appkit/nstexttable | 200 | 2026-04-29 |
