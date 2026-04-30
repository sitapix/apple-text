---
name: txt-line-breaking
description: Configure NSParagraphStyle line wrapping, hyphenation, truncation, line height, paragraph spacing, and tab stops in TextKit and AttributedString. Covers lineBreakMode, lineBreakStrategy, hyphenationFactor, usesDefaultHyphenation, soft hyphens, allowsDefaultTighteningForTruncation, lineHeightMultiple, minimumLineHeight, maximumLineHeight, lineSpacing, paragraphSpacing, firstLineHeadIndent, headIndent, NSTextTab. Use when text wraps at the wrong points, an ellipsis fails to appear, lines look too tight or too loose, paragraphs ignore vertical spacing, or tab columns are misaligned. Use whenever the user mentions truncation, hyphenation, line height, leading, or paragraph spacing — even if they do not name NSParagraphStyle. Do NOT use for text that must wrap around shapes or flow across columns — see txt-exclusion-paths. Do NOT use for measuring how tall the result will be — see txt-measurement.
license: MIT
---

# Line Breaking, Hyphenation, and Line Geometry

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

NSParagraphStyle controls how a paragraph wraps, where it allows hyphens, how its line heights stack, and how it relates to the paragraphs around it. Almost every "text looks wrong" complaint that isn't a font choice resolves to one of these properties. The patterns below are starting points; before quoting a property's behavior from this document, fetch the current Apple docs via Sosumi (`sosumi.ai/documentation/uikit/nsparagraphstyle`) and read the actual code applying the style — many bugs are an attribute applied to the wrong range, or a `lineHeightMultiple` interacting with `minimumLineHeight` in a way the author did not anticipate.

A paragraph style applies to the run of characters tagged with it, but several properties (line break mode, base writing direction, alignment) take their final value from the **first paragraph style** in the paragraph. Mid-paragraph attribute changes for those properties are silently ignored.

## Contents

- [Line break mode and strategy](#line-break-mode-and-strategy)
- [Hyphenation](#hyphenation)
- [Truncation](#truncation)
- [Line height stack](#line-height-stack)
- [Paragraph spacing and indentation](#paragraph-spacing-and-indentation)
- [Tab stops](#tab-stops)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Line break mode and strategy

`lineBreakMode` decides what happens at the trailing edge of a line that does not fit. `.byWordWrapping` is the default for body text and breaks at word boundaries. `.byCharWrapping` breaks anywhere and is the right answer for CJK or for code where word boundaries are not meaningful. `.byClipping` chops the line off without an ellipsis. The three truncation modes (`.byTruncatingHead`, `.byTruncatingTail`, `.byTruncatingMiddle`) only take effect on the **last** line that fits in the container — preceding lines always word-wrap regardless of the mode set. This catches authors who set `.byTruncatingTail` on a multi-line label and wonder why only the last line gets the ellipsis.

`lineBreakStrategy` is an `OptionSet` that influences where the typesetter prefers to break, separately from the trailing edge behavior. `.standard` matches what UILabel does by default on modern iOS — it includes a "push out" behavior that redistributes words across lines to avoid orphan last lines. `.pushOut` alone enables that redistribution explicitly. `.hangulWordPriority` prevents breaks between Hangul characters in Korean text. Strategies combine: `[.standard, .hangulWordPriority]` is a reasonable default for an editor expected to handle mixed scripts.

```swift
let style = NSMutableParagraphStyle()
style.lineBreakMode = .byTruncatingTail
style.lineBreakStrategy = .standard
```

## Hyphenation

`hyphenationFactor` is a float from 0 to 1. At 0 (the default) the typesetter never hyphenates. At 1 it hyphenates whenever doing so produces tighter lines. Values in between gate hyphenation on how much of the line a word would otherwise leave empty — a factor of 0.7 hyphenates only when an unbroken word would push the line below 70% width.

`usesDefaultHyphenation` (iOS 15+) defers the decision to the system using the text's language. Some locales (German) hyphenate aggressively by default; others (English) are conservative. Prefer this over a hand-tuned factor when you do not have a strong opinion about the visual result.

Authors who need hyphens at specific positions in specific words insert U+00AD (soft hyphen). The character is invisible until the typesetter decides to break there, at which point it draws as a hyphen. Useful for proper nouns, technical terms, and translations where the system's hyphenation dictionary is wrong:

```swift
let text = "super\u{00AD}cali\u{00AD}fragilistic"
```

Hyphenation only applies when text can wrap to more than one line. A single-line label with a non-zero `hyphenationFactor` will not hyphenate; truncation kicks in instead.

## Truncation

The minimum recipe is `lineBreakMode = .byTruncatingTail` plus a line cap, which on a UILabel is `numberOfLines` and on a TextKit container is `maximumNumberOfLines`. Set both — the label property only governs the label's own measurement, while the container property governs the underlying layout manager.

`allowsDefaultTighteningForTruncation` lets the typesetter shave a fraction of inter-character spacing before resorting to the ellipsis. UILabel has it on by default; custom containers do not. Turn it on whenever a hairline of tightening would save a word.

A custom truncation token — "Read more" instead of "…" — is not a single property. On TextKit 1, the path is to subclass `NSLayoutManager`, override `drawGlyphs(forGlyphRange:at:)`, detect when the range includes a truncated line, and draw the replacement string at the truncation point. On TextKit 2, attach a rendering attribute to the truncated layout fragment. Either approach is a meaningful project; if the only requirement is "different word at the end," it is often cheaper to stop relying on built-in truncation and split the string manually.

To answer "is this label currently showing truncated text?", measure the visible glyph range and compare against storage length. The result is only valid after layout has run:

```swift
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

## Line height stack

Line height in TextKit is a stack of properties applied in order:

1. `font.lineHeight` — ascender + descender + leading from the font itself
2. `lineHeightMultiple` — multiplier on the font-derived height
3. `minimumLineHeight` — floor
4. `maximumLineHeight` — ceiling
5. `lineSpacing` — extra space added **after** every line within the paragraph

The effective height is `clamp(font.lineHeight × lineHeightMultiple, minimumLineHeight, maximumLineHeight)`, plus `lineSpacing` between lines. Setting only `minimumLineHeight` does not lock the line height — a font with a larger natural height will still expand. To clamp to an exact value, set min and max to the same number.

When line height exceeds the font's natural height, the extra space falls below the baseline by default, so text appears stuck to the bottom of the line box. `baselineOffset` shifts the glyphs back up:

```swift
let font = UIFont.systemFont(ofSize: 17)
let desiredLineHeight: CGFloat = 24

let style = NSMutableParagraphStyle()
style.minimumLineHeight = desiredLineHeight
style.maximumLineHeight = desiredLineHeight

let baselineOffset = (desiredLineHeight - font.lineHeight) / 2

let attrs: [NSAttributedString.Key: Any] = [
    .font: font,
    .paragraphStyle: style,
    .baselineOffset: baselineOffset
]
```

`lineSpacing` is between lines **within** a paragraph, not between paragraphs. The two are constantly confused.

## Paragraph spacing and indentation

`paragraphSpacing` adds vertical space *after* a paragraph, before the next one starts. `paragraphSpacingBefore` adds space *before* this paragraph. Setting only `paragraphSpacing` is the common pattern; `paragraphSpacingBefore` adds space before every paragraph including the first, which is rarely what an author wants and shows up as unexpected top padding.

`firstLineHeadIndent` indents the first line of the paragraph. `headIndent` indents subsequent lines. `tailIndent` insets the trailing edge — negative values measure from the right edge, positive from the leading edge. The hanging-indent pattern (markers in the margin, wrapped text aligned past the marker) sets `firstLineHeadIndent = 0` and `headIndent` to the width of the marker plus its trailing space.

## Tab stops

`tabStops` is an array of `NSTextTab` instances, each with an alignment and a location measured from the leading edge. `defaultTabInterval` controls the implicit grid used after the explicit stops are exhausted.

```swift
let style = NSMutableParagraphStyle()
style.tabStops = [
    NSTextTab(textAlignment: .left, location: 0),
    NSTextTab(textAlignment: .right, location: 200),
    NSTextTab(textAlignment: .decimal, location: 300),
    NSTextTab(textAlignment: .center, location: 400),
]
style.defaultTabInterval = 28
```

`.decimal` alignment aligns on the decimal point — the right answer for columns of currency or measurements. Tab alignment is precise with monospaced fonts and approximate with proportional fonts; for proportional number columns, monospaced digits (`UIFontDescriptor` with `monospacedDigit`) plus `.decimal` give predictable results.

## Common Mistakes

1. **Confusing `lineSpacing` with `paragraphSpacing`.** `lineSpacing` adds space between every line within a paragraph; `paragraphSpacing` adds space only between paragraphs. The names are similar enough that swapping them is the most common spacing mistake here.

2. **Setting only `minimumLineHeight` and expecting a fixed height.** A font whose natural line height exceeds the minimum will still expand the line. Fixed line height needs both `minimumLineHeight` and `maximumLineHeight` set to the same value, otherwise the result depends on the font.

3. **Forced line height without `baselineOffset`.** When `minimumLineHeight` is greater than the font's natural height, the extra space lands below the baseline, so text looks stuck to the bottom of the line box. Add `baselineOffset = (desiredLineHeight - font.lineHeight) / 2` to recenter.

4. **Expecting truncation on every line.** Truncation modes apply only to the last line that fits. A multi-line label with `.byTruncatingTail` shows the ellipsis on the last line only; preceding lines word-wrap. To truncate every line, the model is to clip per line, which TextKit does not do directly — typically the text is split per line ahead of time.

5. **`hyphenationFactor` on a single-line label.** Hyphenation only triggers when the typesetter has more than one line to fill. On a label capped at one line, set `allowsDefaultTighteningForTruncation` instead and let truncation handle overflow.

6. **`minimumScaleFactor` only works on single-line text.** Multi-paragraph or wrap-mode strings ignore it; `actualScaleFactor` lies when `NSParagraphStyle` is present (radar://26575435). For multi-line shrink-to-fit, measure with `boundingRect(with:options:context:)` passing an `NSStringDrawingContext` whose `minimumScaleFactor` is set, then read back `actualScaleFactor` after the call — and even then, paragraph styles can defeat it. Authors who set `minimumScaleFactor` on a UILabel and then add a `NSParagraphStyle` for line height often see the scale factor read back as 1.0 while the text still clips. The only reliable shrink-to-fit for multi-line content is to measure-then-resize the font yourself. See `/skill txt-measurement` for the measurement path.

7. **`maximumNumberOfLines = 0` interpreted as zero lines.** Zero means unlimited and is the default. To hide a label, hide the view, not the line cap.

8. **Mid-paragraph attribute changes for paragraph-level properties.** `lineBreakMode`, `alignment`, and `baseWritingDirection` come from the first paragraph style attribute in the paragraph. Splitting an attributed string and applying a different paragraph style to the second half is silently overridden by the first half's style.

9. **Hyphens in front of numbers and punctuation.** The system hyphenation dictionary will sometimes hyphenate technical terms in places that read poorly. Inserting U+00AD at acceptable break points and lowering `hyphenationFactor` is more controllable than turning hyphenation up globally.

## References

- `/skill txt-measurement` — measuring how tall a paragraph style ends up rendering
- `/skill txt-exclusion-paths` — wrapping text around shapes and across columns
- `/skill txt-dynamic-type` — how line height interacts with Dynamic Type metrics
- `/skill txt-attribute-keys` — full attribute key catalog including paragraph-style adjacent keys
- [NSParagraphStyle](https://sosumi.ai/documentation/uikit/nsparagraphstyle)
- [NSLineBreakMode](https://sosumi.ai/documentation/uikit/nslinebreakmode)
- [NSTextContainer](https://sosumi.ai/documentation/uikit/nstextcontainer)
