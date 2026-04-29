---
name: txt-dynamic-type
description: Use when implementing Dynamic Type scaling, custom font metrics, accessibility sizes, or content size category changes
license: MIT
---

# Dynamic Type Reference

Use this skill when the main question is how text should scale with content size category and accessibility sizes.

## When to Use

- You are implementing Dynamic Type in UIKit, AppKit, or SwiftUI.
- You are scaling custom fonts.
- You are testing layout behavior at large accessibility sizes.

## Quick Decision

- Native text styles are enough -> use semantic text styles directly
- Custom font but standard scaling -> use `UIFontMetrics`
- Rich text or attributed text does not update -> handle size-category changes explicitly

## Core Guidance

## Text Styles and Default Sizes (at Large / Default)

| Text Style | UIKit | SwiftUI | Weight | Default Size |
|------------|-------|---------|--------|-------------|
| Extra Large Title 2 | `.extraLargeTitle2` | `.extraLargeTitle2` | Bold | 28pt |
| Extra Large Title | `.extraLargeTitle` | `.extraLargeTitle` | Bold | 36pt |
| Large Title | `.largeTitle` | `.largeTitle` | Regular | 34pt |
| Title 1 | `.title1` | `.title` | Regular | 28pt |
| Title 2 | `.title2` | `.title2` | Regular | 22pt |
| Title 3 | `.title3` | `.title3` | Regular | 20pt |
| Headline | `.headline` | `.headline` | **Semibold** | 17pt |
| Body | `.body` | `.body` | Regular | 17pt |
| Callout | `.callout` | `.callout` | Regular | 16pt |
| Subheadline | `.subheadline` | `.subheadline` | Regular | 15pt |
| Footnote | `.footnote` | `.footnote` | Regular | 13pt |
| Caption 1 | `.caption1` | `.caption` | Regular | 12pt |
| Caption 2 | `.caption2` | `.caption2` | Regular | 11pt |

## Point Size Scaling Table (Body Style)

| Category | Body Size | API Constant |
|----------|----------|-------------|
| xSmall | 14pt | `.extraSmall` |
| Small | 15pt | `.small` |
| Medium | 16pt | `.medium` |
| **Large (Default)** | **17pt** | `.large` |
| xLarge | 19pt | `.extraLarge` |
| xxLarge | 21pt | `.extraExtraLarge` |
| xxxLarge | 23pt | `.extraExtraExtraLarge` |
| **AX1** | **28pt** | `.accessibilityMedium` |
| **AX2** | **33pt** | `.accessibilityLarge` |
| **AX3** | **40pt** | `.accessibilityExtraLarge` |
| **AX4** | **47pt** | `.accessibilityExtraExtraLarge` |
| **AX5** | **53pt** | `.accessibilityExtraExtraExtraLarge` |

At AX5, Body text is **3x** its default size.

## What Automatically Supports Dynamic Type

| Component | Auto-scales? | Notes |
|-----------|-------------|-------|
| SwiftUI `Text` with `.font(.body)` | ✅ | All semantic font styles scale |
| SwiftUI `Text` with `.font(.system(size: 17))` | ❌ | Fixed size — does NOT scale |
| SwiftUI `Text` with `.font(.custom("X", size: 17, relativeTo: .body))` | ✅ | Scales via `relativeTo:` |
| SwiftUI `Text` with `.font(.custom("X", fixedSize: 17))` | ❌ | Fixed — does NOT scale |
| `UILabel` with `preferredFont(forTextStyle:)` | ✅ if `adjustsFontForContentSizeCategory = true` |
| `UILabel` with `UIFont.systemFont(ofSize: 17)` | ❌ | Fixed size |
| `UITextView` with `preferredFont(forTextStyle:)` | ✅ if `adjustsFontForContentSizeCategory = true` |
| `NSAttributedString` with fixed font | ❌ | Must re-apply fonts on size change |
| `NSTextView` | Partial | macOS Dynamic Type is limited |

## UIKit: Making Text Scale

### System Fonts

```swift
label.font = UIFont.preferredFont(forTextStyle: .body)
label.adjustsFontForContentSizeCategory = true  // Auto-update on change
```

**Without `adjustsFontForContentSizeCategory`:** The font is a snapshot — it doesn't update when the user changes their size preference.

### Custom Fonts with UIFontMetrics

```swift
let customFont = UIFont(name: "Avenir-Medium", size: 17)!
let metrics = UIFontMetrics(forTextStyle: .body)

// Scale with no upper bound
label.font = metrics.scaledFont(for: customFont)

// Scale with maximum
label.font = metrics.scaledFont(for: customFont, maximumPointSize: 28)

// Scale non-font values (padding, spacing, icon sizes)
let scaledPadding = metrics.scaledValue(for: 16.0)

label.adjustsFontForContentSizeCategory = true
```

The base size (17 in this example) should be the **default (Large)** size.

### UITextView

```swift
textView.font = UIFont.preferredFont(forTextStyle: .body)
textView.adjustsFontForContentSizeCategory = true
```

**With attributed text:** `adjustsFontForContentSizeCategory` does NOT re-scale attributed string fonts. You must listen for size changes and re-apply fonts:

```swift
NotificationCenter.default.addObserver(
    forName: UIContentSizeCategory.didChangeNotification,
    object: nil, queue: .main
) { _ in
    self.reapplyDynamicFonts()
}
```

### Limiting Scale Range (iOS 15+)

```swift
// Prevent text from getting too small or too large
view.minimumContentSizeCategory = .medium
view.maximumContentSizeCategory = .accessibilityLarge
```

Works on any UIView. Caps the effective content size category for that view and its children.

## SwiftUI: Making Text Scale

### Semantic Fonts (Always Scale)

```swift
Text("Scales").font(.body)        // ✅ Scales
Text("Scales").font(.headline)    // ✅ Scales
Text("Scales").font(.largeTitle)  // ✅ Scales
```

### Custom Fonts

```swift
// ✅ Scales with Dynamic Type
Text("Custom").font(.custom("Avenir", size: 17, relativeTo: .body))

// ❌ Does NOT scale
Text("Fixed").font(.custom("Avenir", fixedSize: 17))
Text("Fixed").font(.system(size: 17))
```

### @ScaledMetric for Non-Font Values

```swift
@ScaledMetric(relativeTo: .body) var iconSize: CGFloat = 24
@ScaledMetric var padding: CGFloat = 16  // Uses .body curve by default

Image(systemName: "star")
    .frame(width: iconSize, height: iconSize)
    .padding(padding)
```

### Limiting Scale Range (iOS 15+)

```swift
Text("Limited")
    .dynamicTypeSize(.medium ... .accessibility3)
```

## macOS

`NSFont.preferredFont(forTextStyle:)` exists but macOS Dynamic Type is more limited:
- Only available on macOS 11+
- macOS doesn't have the same accessibility size categories
- Users change text size via System Settings → Accessibility → Display → Text Size (macOS 14+)
- SwiftUI on macOS uses the same `.font(.body)` API and it scales

## Non-Latin Script Line Height (iOS 17+)

iOS 17 introduced automatic dynamic line-height adjustment for scripts that are taller than Latin (Thai, Arabic, Devanagari, Tibetan). Previously, fixed `minimumLineHeight`/`maximumLineHeight` values could clip ascenders and descenders on these scripts. The system now adjusts line height per-line based on the actual glyphs rendered.

**If you set explicit `minimumLineHeight`/`maximumLineHeight` on NSParagraphStyle**, the system respects your values and may still clip. For multilingual content, prefer `lineHeightMultiple` over fixed heights, or avoid constraining line height entirely.

## What Breaks at Large Accessibility Sizes

| Issue | Solution |
|-------|---------|
| Text clips in fixed-height containers | Use `adjustsFontSizeToFitWidth` or flexible layouts |
| Horizontal layouts overflow | Switch to vertical at accessibility sizes |
| Icons too small relative to text | Use `@ScaledMetric` / `UIFontMetrics.scaledValue(for:)` |
| Table cells too short | Use self-sizing cells with Auto Layout |
| Navigation bar titles truncate | System handles, but custom title views need attention |
| Buttons with text overflow | Allow multi-line button labels |

### Large Content Viewer (iOS 13+)

For UI elements that can't grow (tab bars, toolbars, segmented controls):

```swift
// UIKit
button.showsLargeContentViewer = true
button.largeContentTitle = "Settings"
button.largeContentImage = UIImage(systemName: "gear")

// SwiftUI
Button("Settings") { }
    .accessibilityShowsLargeContentViewer {
        Label("Settings", systemImage: "gear")
    }
```

Long-press shows a HUD with the enlarged content.

## Testing Dynamic Type

1. **Xcode Environment Overrides:** Run app → Debug bar → Environment Overrides → Text Size slider
2. **Control Center:** Settings → Control Center → Add "Text Size" → Adjust while app runs
3. **Accessibility Inspector:** Xcode → Open Developer Tool → Accessibility Inspector → Settings → Font Size
4. **SwiftUI Preview:** `.environment(\.sizeCategory, .accessibilityExtraExtraExtraLarge)`

## Common Pitfalls

1. **Fixed font sizes don't scale** — `.system(size: 17)` and `UIFont.systemFont(ofSize: 17)` are permanently 17pt. Use semantic styles.
2. **Attributed strings don't auto-scale** — `adjustsFontForContentSizeCategory` only works with plain `font` property. For attributed text, listen for `UIContentSizeCategory.didChangeNotification`.
3. **Forgetting `adjustsFontForContentSizeCategory`** — Without it, UIKit text views get a snapshot font that never updates.
4. **Not testing accessibility sizes** — AX3-AX5 are where most layout bugs appear. Always test.
5. **Icons not scaling** — SF Symbols auto-scale with Dynamic Type. Custom icons need `@ScaledMetric` or `UIFontMetrics.scaledValue`.

## Related Skills

- Use `/skill txt-views` when sizing depends on which control you chose.
- Use `/skill txt-colors` for contrast and semantic color pairing.
- Use `/skill txt-writing-tools` when accessibility sizing affects editor integrations.
