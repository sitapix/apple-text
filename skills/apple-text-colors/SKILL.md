---
name: apple-text-colors
description: Use when choosing text colors, implementing dark mode for text, understanding semantic colors (UIColor.label, NSColor.textColor, Color.primary), wide color / Display P3 for text, HDR/EDR text, making attributed string colors dynamic, or understanding which colors auto-adapt and which don't — complete color catalog for UIKit, AppKit, and SwiftUI text
license: MIT
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
- Need advanced formatting attributes -> `/skill apple-text-formatting-ref`

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

- Use `/skill apple-text-formatting-ref` for broader attributed-text formatting rules.
- Use `/skill apple-text-dynamic-type` when color decisions interact with accessibility text sizing.
- Use `/skill apple-text-attributed-string` when the color question is really about attribute storage and conversion.
