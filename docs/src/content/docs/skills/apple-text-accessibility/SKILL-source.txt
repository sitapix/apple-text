---
name: apple-text-accessibility
description: Use when implementing VoiceOver, Dynamic Type, or accessibility traits in custom Apple text editors
license: MIT
---

# Accessibility in Custom Text Editors

Use this skill when the main question is how to make a custom text editor work with VoiceOver, Dynamic Type, or other assistive technologies.

## When to Use

- Making a wrapped UITextView accessible in SwiftUI
- VoiceOver not reading text or announcing changes in a custom editor
- Dynamic Type not scaling in a custom text view
- Custom view needs text editing accessibility traits
- Accessibility Inspector shows missing or wrong information

## Quick Decision

- Need Dynamic Type font scaling -> `/skill apple-text-dynamic-type`
- Need color contrast for text -> `/skill apple-text-colors`
- Need UIViewRepresentable wrapping -> `/skill apple-text-representable`
- Need general iOS accessibility beyond text editors -> see platform accessibility documentation

## Core Guidance

## UITextView Accessibility (Built-In)

`UITextView` is accessible by default. It:

- Reports as static text or editable text field depending on `isEditable`
- Exposes text content to VoiceOver
- Supports text navigation gestures (swipe up/down for character/word/line granularity)
- Announces text changes automatically

If your `UITextView` is not accessible, check that it is not hidden behind another view, that `isAccessibilityElement` has not been set to `false`, and that it is within the accessibility hierarchy.

## UIViewRepresentable Text View Accessibility

### The Problem

When wrapping `UITextView` in SwiftUI via `UIViewRepresentable`, the accessibility tree can break. SwiftUI may create its own accessibility element that shadows the UITextView's built-in accessibility.

### The Fix

Ensure the SwiftUI wrapper does not override the UITextView's accessibility:

```swift
struct EditorView: UIViewRepresentable {
    func makeUIView(context: Context) -> UITextView {
        let textView = UITextView()
        textView.isEditable = true
        textView.isSelectable = true
        // Do NOT set accessibilityLabel or accessibilityValue on the wrapper
        // Let UITextView handle its own accessibility
        return textView
    }

    func updateUIView(_ uiView: UITextView, context: Context) {
        // Update text content only
    }
}
```

If you need to add accessibility hints:

```swift
func makeUIView(context: Context) -> UITextView {
    let textView = UITextView()
    textView.accessibilityHint = "Double tap to edit"
    // accessibilityLabel and accessibilityValue are managed by UITextView
    return textView
}
```

### SwiftUI Accessibility Modifiers vs UIKit

Do NOT apply SwiftUI accessibility modifiers to the wrapper — they replace the UITextView's accessibility subtree:

```swift
// ❌ WRONG — shadows UITextView's built-in accessibility
EditorView()
    .accessibilityLabel("Editor")  // Replaces UITextView's dynamic label

// ✅ CORRECT — set on the UITextView itself
func makeUIView(context: Context) -> UITextView {
    let textView = UITextView()
    textView.accessibilityLabel = "Editor"  // Supplements, doesn't replace
    return textView
}
```

## Custom View Accessibility

If you build a text view from scratch (not using UITextView), you must implement accessibility yourself.

### Minimum Requirements

```swift
class CustomTextView: UIView {
    override var isAccessibilityElement: Bool {
        get { true }
        set { }
    }

    override var accessibilityTraits: UIAccessibilityTraits {
        get { isEditable ? .none : .staticText }
        set { }
    }

    override var accessibilityValue: String? {
        get { textContent }
        set { }
    }

    override var accessibilityLabel: String? {
        get { placeholder ?? "Text editor" }
        set { }
    }
}
```

### Text Editing Accessibility

For VoiceOver text navigation (character-by-character, word-by-word), adopt `UIAccessibilityReadingContent`:

```swift
extension CustomTextView: UIAccessibilityReadingContent {
    func accessibilityLineNumber(for point: CGPoint) -> Int {
        lineNumber(at: point)
    }

    func accessibilityContent(forLineNumber lineNumber: Int) -> String? {
        textContent(forLine: lineNumber)
    }

    func accessibilityFrame(forLineNumber lineNumber: Int) -> CGRect {
        frameForLine(lineNumber)
    }

    func accessibilityPageContent() -> String? {
        textContent
    }
}
```

### UIAccessibilityTextualContext

Set the textual context so the system optimizes VoiceOver behavior:

```swift
textView.accessibilityTextualContext = .plain          // Default prose
textView.accessibilityTextualContext = .sourceCode     // Code editor
textView.accessibilityTextualContext = .messaging      // Chat messages
textView.accessibilityTextualContext = .spreadsheet    // Tabular data
textView.accessibilityTextualContext = .wordProcessing // Rich text editor
```

This affects VoiceOver's reading behavior — for example, `.sourceCode` reads punctuation that would be skipped in `.plain`.

## Announcing Text Changes

### Automatic Behavior

`UITextView` does NOT automatically post accessibility notifications like `screenChanged` or `layoutChanged`. For incremental typing, VoiceOver reads characters directly through the text input system. For programmatic changes that the user should know about, you must post notifications yourself.

### Custom Announcements

When your editor makes programmatic changes that the user should know about:

```swift
func applyFormatting(_ style: FormatStyle) {
    // Apply the formatting
    applyStyle(style, to: selectedRange)

    // Announce to VoiceOver
    UIAccessibility.post(
        notification: .announcement,
        argument: "Applied \(style.name) formatting"
    )
}

func insertAutocompletion(_ text: String) {
    insertText(text)

    // Announce what was inserted
    UIAccessibility.post(
        notification: .announcement,
        argument: "Autocompleted: \(text)"
    )
}
```

### Layout Changes

When the editor's content or layout changes significantly (e.g., content loaded, view resized):

```swift
UIAccessibility.post(notification: .layoutChanged, argument: textView)
// VoiceOver will re-read the focused element
```

## Dynamic Type in Custom Editors

### Scaling Fonts

If your editor uses custom fonts, they must scale with Dynamic Type:

```swift
let baseFont = UIFont(name: "Menlo", size: 14)!
let scaledFont = UIFontMetrics(forTextStyle: .body).scaledFont(for: baseFont)
textView.font = scaledFont
```

### Responding to Size Changes

```swift
override func traitCollectionDidChange(_ previousTraitCollection: UITraitCollection?) {
    super.traitCollectionDidChange(previousTraitCollection)
    if traitCollection.preferredContentSizeCategory != previousTraitCollection?.preferredContentSizeCategory {
        // Re-apply fonts
        updateFonts()
    }
}
```

For iOS 17+, use `UITraitChangeObservable`:

```swift
registerForTraitChanges([UITraitPreferredContentSizeCategory.self]) { (self: EditorView, _) in
    self.updateFonts()
}
```

### adjustsFontForContentSizeCategory

For `UITextView` with a single font:

```swift
textView.adjustsFontForContentSizeCategory = true
textView.font = UIFont.preferredFont(forTextStyle: .body)
```

For editors with mixed fonts (syntax highlighting), you must manually re-apply `UIFontMetrics.scaledFont(for:)` when the content size category changes.

## Accessibility Inspector Testing

### What to Check

1. **Element exists.** The text view appears in the Accessibility Inspector hierarchy.
2. **Traits correct.** Shows as editable text (not just static text) when `isEditable = true`.
3. **Value updates.** The `accessibilityValue` reflects current text content.
4. **Label present.** Either set explicitly or derived from a placeholder.
5. **Actions available.** Activate (double-tap) puts the view into editing mode.
6. **Text navigation.** Rotor gestures work for character, word, line, and heading navigation.

### Common Failures

| Symptom | Likely Cause |
|---------|-------------|
| VoiceOver skips the editor | `isAccessibilityElement = false` or view is hidden |
| VoiceOver reads stale text | `accessibilityValue` not updating after edits |
| "Dimmed" announcement | `isEnabled = false` on the text view |
| No text navigation gestures | Missing `UIAccessibilityReadingContent` on custom view |
| SwiftUI modifier shadows UIKit | `.accessibilityLabel()` applied to UIViewRepresentable wrapper |

## Common Pitfalls

1. **SwiftUI accessibility modifiers on UIViewRepresentable wrappers.** These replace the UIKit view's accessibility subtree. Set accessibility properties on the UIKit view directly, not on the SwiftUI wrapper.
2. **Not posting announcements for programmatic changes.** Users cannot see the screen — if your code changes text without user input, announce it.
3. **Custom fonts without UIFontMetrics.** Raw `UIFont(name:size:)` does not scale with Dynamic Type. Always wrap in `UIFontMetrics.scaledFont(for:)`.
4. **Forgetting to set accessibilityTextualContext.** Source code editors that don't set `.sourceCode` will have VoiceOver skip punctuation, making code incomprehensible.
5. **Testing only with VoiceOver.** Also test with Switch Control, Voice Control, and Full Keyboard Access — each has different interaction patterns.

## Related Skills

- Use `/skill apple-text-dynamic-type` for comprehensive Dynamic Type patterns.
- Use `/skill apple-text-colors` for color contrast and accessibility colors.
- Use `/skill apple-text-representable` for UIViewRepresentable wrapping patterns.
- Use `/skill apple-text-views` for choosing accessible text views.
