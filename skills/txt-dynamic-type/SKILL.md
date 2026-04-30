---
name: txt-dynamic-type
description: Configure Dynamic Type scaling for system and custom fonts in UIKit, AppKit, and SwiftUI — semantic text styles, UIFontMetrics, ScaledMetric, adjustsFontForContentSizeCategory, dynamicTypeSize, minimumContentSizeCategory, content-size change notifications, large content viewer. Use when text doesn't scale with the user's text-size preference, attributed strings keep their original size after a category change, custom fonts need to follow body or headline curves, layouts break at AX1-AX5, or you need to clamp the scale range for a view. Trigger on 'make text bigger', 'AX sizes', 'large text mode', 'accessibility text size', 'why isn't my custom font scaling' even without Dynamic Type named. Do NOT use for general text-editor accessibility traits or VoiceOver wiring — see txt-accessibility.
license: MIT
---

# Dynamic Type Scaling

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill covers how to make text scale correctly across all twelve content-size categories — from `xSmall` through the five accessibility sizes (AX1-AX5) — across UIKit, AppKit, and SwiftUI. The mental model: semantic text styles scale automatically; raw point sizes don't; custom fonts need `UIFontMetrics`/`relativeTo:` to scale; attributed strings need a manual reapply on size change because the font is baked in. Before treating any specific point-size table or scale curve as authoritative, fetch the current Apple docs via Sosumi (`sosumi.ai/documentation/uikit/uifont/textstyle`) — Apple has tweaked the AX-size curve and added new text styles in past releases.

For VoiceOver, accessibility traits, `UIAccessibilityReadingContent`, and announcement posting in custom editors, see `txt-accessibility`. Dynamic Type is one accessibility surface among several; the boundary is intentional.

## Contents

- [Text styles and scale tables](#text-styles-and-scale-tables)
- [UIKit: making text scale](#uikit-making-text-scale)
- [Custom fonts via UIFontMetrics](#custom-fonts-via-uifontmetrics)
- [Attributed strings and size-category changes](#attributed-strings-and-size-category-changes)
- [SwiftUI Dynamic Type](#swiftui-dynamic-type)
- [Limiting the scale range](#limiting-the-scale-range)
- [Non-Latin script line height](#non-latin-script-line-height)
- [What breaks at AX sizes](#what-breaks-at-ax-sizes)
- [Testing](#testing)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Text styles and scale tables

Apple ships thirteen semantic text styles. Each one carries a default size at the `Large` category and a documented scale curve up through AX5. The styles below are listed at their default (Large) size:

| Text Style | UIKit / SwiftUI | Weight | Default |
|---|---|---|---|
| Extra Large Title 2 | `.extraLargeTitle2` | Bold | 28pt |
| Extra Large Title | `.extraLargeTitle` | Bold | 36pt |
| Large Title | `.largeTitle` | Regular | 34pt |
| Title 1 | `.title1` / `.title` | Regular | 28pt |
| Title 2 | `.title2` | Regular | 22pt |
| Title 3 | `.title3` | Regular | 20pt |
| Headline | `.headline` | Semibold | 17pt |
| Body | `.body` | Regular | 17pt |
| Callout | `.callout` | Regular | 16pt |
| Subheadline | `.subheadline` | Regular | 15pt |
| Footnote | `.footnote` | Regular | 13pt |
| Caption 1 | `.caption1` / `.caption` | Regular | 12pt |
| Caption 2 | `.caption2` | Regular | 11pt |

The Body curve at each content-size category — the shape every other style follows, scaled relative to its own default:

| Category | Body | Constant |
|---|---|---|
| xSmall | 14pt | `.extraSmall` |
| Small | 15pt | `.small` |
| Medium | 16pt | `.medium` |
| Large (default) | 17pt | `.large` |
| xLarge | 19pt | `.extraLarge` |
| xxLarge | 21pt | `.extraExtraLarge` |
| xxxLarge | 23pt | `.extraExtraExtraLarge` |
| AX1 | 28pt | `.accessibilityMedium` |
| AX2 | 33pt | `.accessibilityLarge` |
| AX3 | 40pt | `.accessibilityExtraLarge` |
| AX4 | 47pt | `.accessibilityExtraExtraLarge` |
| AX5 | 53pt | `.accessibilityExtraExtraExtraLarge` |

At AX5, Body text is roughly 3× the default. Layouts that look fine at xxxLarge often break catastrophically at AX1 because the jump from xxxLarge (23pt) to AX1 (28pt) is the largest single step in the curve and is where horizontal layouts start to overflow.

## UIKit: making text scale

`UILabel`, `UITextView`, `UITextField`, and `UIButton` all support Dynamic Type the same way: assign a preferred font and opt into auto-update.

```swift
label.font = UIFont.preferredFont(forTextStyle: .body)
label.adjustsFontForContentSizeCategory = true
```

Without `adjustsFontForContentSizeCategory = true` the font is a snapshot at the current category — it won't follow live changes from Settings or Control Center. The flag defaults to `false` for backwards compatibility, so it must be set explicitly on every Dynamic Type-aware control.

`UIFont.systemFont(ofSize: 17)` is a fixed 17pt font and won't scale, regardless of `adjustsFontForContentSizeCategory`. The flag re-asks for the *preferred* font; a non-preferred font has nothing to re-ask for. Always start from `preferredFont(forTextStyle:)` or `UIFontMetrics.scaledFont(for:)`.

## Custom fonts via UIFontMetrics

For non-system fonts, `UIFontMetrics` translates a base size at the Large category into a category-aware scaled size. Pick the text style whose curve you want the font to follow.

```swift
let custom = UIFont(name: "Avenir-Medium", size: 17)!
let metrics = UIFontMetrics(forTextStyle: .body)

label.font = metrics.scaledFont(for: custom)
// Optionally cap the maximum point size:
label.font = metrics.scaledFont(for: custom, maximumPointSize: 28)
label.adjustsFontForContentSizeCategory = true
```

The base size passed to `UIFont(name:size:)` should be the size you want at the Large (default) category. Passing a tiny base size and expecting AX scaling to compensate produces text that's still too small at Medium.

`UIFontMetrics.scaledValue(for:)` applies the same scale curve to non-font dimensions — padding, icon sizes, spacing, line-height multiples. Wrap any constant that should grow with text to keep iconography proportional with the surrounding type.

## Attributed strings and size-category changes

`adjustsFontForContentSizeCategory` only re-asks for the `font` property. `attributedText` carries fonts inside `.font` attributes that are baked into the storage; the flag does nothing for them. After a content-size change, the attributed string still has the original-size font runs.

The fix is to listen for the size-category change and re-apply fonts to the attributed string.

```swift
NotificationCenter.default.addObserver(
    forName: UIContentSizeCategory.didChangeNotification,
    object: nil, queue: .main
) { [weak self] _ in
    self?.reapplyDynamicFonts()
}
```

For iOS 17+, the trait-change observer is the modern equivalent and gives you typed access:

```swift
registerForTraitChanges([UITraitPreferredContentSizeCategory.self]) { (self: EditorView, _) in
    self.updateFonts()
}
```

`reapplyDynamicFonts()` walks the storage, replaces each font run with `UIFontMetrics.scaledFont(for: baseFont)` for the appropriate style, and writes the result back. For syntax-highlighted code editors, the practical pattern is to keep the *base* fonts in a small dictionary keyed by token type and recompute the scaled font for each token type once per category change.

## SwiftUI Dynamic Type

Semantic fonts in SwiftUI scale automatically — there's no opt-in flag.

```swift
Text("Scales").font(.body)
Text("Scales").font(.headline)
```

Custom fonts use `relativeTo:` to attach to a curve:

```swift
Text("Custom").font(.custom("Avenir", size: 17, relativeTo: .body))
```

`.font(.custom("X", fixedSize: 17))` and `.font(.system(size: 17))` are the non-scaling forms. They're the right choice for typographic ornaments that shouldn't grow (a logo glyph, a fixed-grid label) and the wrong choice for body content.

`@ScaledMetric` scales non-font dimensions:

```swift
@ScaledMetric(relativeTo: .body) var iconSize: CGFloat = 24
@ScaledMetric var padding: CGFloat = 16   // defaults to .body curve

Image(systemName: "star")
    .frame(width: iconSize, height: iconSize)
    .padding(padding)
```

The wrapper recomputes whenever the SwiftUI environment's size category changes, propagating through the view tree without explicit observers.

## Limiting the scale range

iOS 15 added per-view scale clamps for situations where the content can't honor the full AX range — fixed-height widgets, in-line glyph runs, dense table cells.

```swift
// UIKit
view.minimumContentSizeCategory = .medium
view.maximumContentSizeCategory = .accessibilityLarge

// SwiftUI
view.dynamicTypeSize(.medium ... .accessibility3)
```

The clamp affects the view and its descendants. Use it to enforce a lower bound (so text never shrinks below a readable size) and an upper bound (so a constrained container doesn't have to handle AX5). Don't use it as a quick fix for layouts that should be made flexible — clamping accessibility sizes hurts users who actually need them.

For UI elements that genuinely cannot grow (tab bars, toolbars, segmented controls, compact glyphs), the Large Content Viewer presents a HUD with the enlarged content on long-press:

```swift
button.showsLargeContentViewer = true
button.largeContentTitle = "Settings"
button.largeContentImage = UIImage(systemName: "gear")
```

## Non-Latin script line height

iOS 17+ adjusts line height per-line for scripts with taller ascenders or descenders than Latin (Thai, Arabic, Devanagari, Tibetan). Lines containing only Latin keep the standard height; lines containing tall scripts grow.

If `NSParagraphStyle` sets explicit `minimumLineHeight` or `maximumLineHeight`, the system honors those values and may clip tall-script glyphs anyway. For multilingual content, prefer `lineHeightMultiple` (a ratio that scales with the font) over fixed heights. If the editor must support arbitrary scripts, leaving line height unconstrained and letting the system pick is safer than guessing.

## What breaks at AX sizes

The recurring layout failures and their fixes:

- **Text clips in a fixed-height container.** Use `adjustsFontSizeToFitWidth` only as a last resort (it shrinks text below the user's preference). Prefer self-sizing layouts.
- **Horizontal layouts overflow.** Switch to a vertical axis at AX sizes — UIKit `UIStackView.axis` from a trait observer, SwiftUI `ViewThatFits` or a `dynamicTypeSize`-conditional layout.
- **Icons stay small relative to text.** Wrap icon sizes in `@ScaledMetric` (SwiftUI) or `UIFontMetrics.scaledValue(for:)` (UIKit). SF Symbols configured with a text-style font scale automatically.
- **Table cells too short.** Use self-sizing cells: `tableView.rowHeight = UITableView.automaticDimension` plus `estimatedRowHeight`, or in SwiftUI rely on `List` defaults.
- **Buttons truncate text.** Allow multi-line button labels: UIKit `button.titleLabel?.numberOfLines = 0`, SwiftUI is multi-line by default unless `.lineLimit(1)` is applied.

## Testing

Four ways to exercise size categories:

- **Xcode Environment Overrides.** Run the app, open the Debug bar, drag the Text Size slider through the full range including AX1-AX5.
- **Control Center Text Size.** Add the Text Size control in Settings → Control Center, then change the size live while the app runs on device or simulator.
- **Accessibility Inspector.** Xcode → Open Developer Tool → Accessibility Inspector → Settings → Font Size.
- **SwiftUI previews.** Add `.environment(\.sizeCategory, .accessibilityExtraExtraExtraLarge)` to the preview, or wrap multiple previews in a `Group` with one preview per AX size.

Test through AX5, not just to AX1 — the layout differences between AX1 and AX5 are larger than the differences between Small and AX1.

## Common Mistakes

1. **Fixed point sizes.** `.system(size: 17)` and `UIFont.systemFont(ofSize: 17)` are permanently 17pt and never scale. Use semantic styles or wrap a custom font in `UIFontMetrics`.

2. **Forgetting `adjustsFontForContentSizeCategory`.** Without it, UIKit text views keep the snapshot font from when they were configured. The font won't update when the user changes their preference.

3. **Treating `attributedText` like `text` for scaling.** `adjustsFontForContentSizeCategory` is a no-op on attributed strings. Re-apply fonts on `UIContentSizeCategory.didChangeNotification` (or `registerForTraitChanges` on iOS 17+).

4. **Custom fonts re-scale only when *both* conditions are met.** A custom font follows Dynamic Type only when (1) the font is wrapped via `UIFontMetrics.scaledFont(for:)` *and* (2) the text view has `adjustsFontForContentSizeCategory = true`. Either alone is silently inert. Most "I set `adjustsFontForContentSizeCategory` but my custom font doesn't scale" reports are missing the `UIFontMetrics` step; reports that the custom font scales once but not on live category changes are missing the auto-update flag. For attributed runs, scale each run with the matching text style — different runs may want different curves (a `.headline` run vs a `.body` run). When caching laid-out attributed strings, observe `UIContentSizeCategory.didChangeNotification` and rebuild the cache, otherwise the cached string keeps its frozen-size font. The SwiftUI equivalent is `Font.custom("X", size: 17, relativeTo: .body)` — `Font.custom("X", size: 17)` (no `relativeTo:`) is fixed.

5. **Skipping AX testing.** AX1-AX5 are where layout bugs concentrate. Testing only at xxxLarge misses the largest single jump in the curve.

6. **Using `dynamicTypeSize(...)` to dodge layout work.** Clamping the scale range is appropriate for genuinely constrained UI; it's a regression for ordinary content. Make the layout flexible first, then clamp only where you must.

7. **Constraining line height on multilingual content.** Explicit `minimumLineHeight`/`maximumLineHeight` clip tall scripts even with the iOS 17+ per-line adjustment. Prefer `lineHeightMultiple` or leave line height unconstrained.

## References

- `/skill txt-accessibility` — VoiceOver, accessibility traits, announcements in custom text editors
- `/skill txt-view-picker` — choosing a text view that supports Dynamic Type out of the box
- `/skill txt-line-breaking` — paragraph-style line height interactions with Dynamic Type
- `/skill txt-colors` — semantic colors and contrast at large sizes
- [UIFont.TextStyle](https://sosumi.ai/documentation/uikit/uifont/textstyle)
- [UIFontMetrics](https://sosumi.ai/documentation/uikit/uifontmetrics)
- [UIContentSizeCategory](https://sosumi.ai/documentation/uikit/uicontentsizecategory)
- [SwiftUI ScaledMetric](https://sosumi.ai/documentation/swiftui/scaledmetric)
- [SwiftUI DynamicTypeSize](https://sosumi.ai/documentation/swiftui/dynamictypesize)
