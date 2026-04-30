---
name: txt-snippets
description: Look up working code snippets for common text-view features — placeholder text, character/word limits, auto-growing height, search highlighting, link/data detection, line numbers, custom cursor color, scroll-to-range. Use when the user asks "how do I…" about a small, well-scoped UITextView/NSTextView or NSAttributedString task and you need a copy-paste recipe rather than architecture guidance. Trigger on casual 'how do I add line numbers / a placeholder / a character limit / a custom cursor color' phrasings even when no API name appears. Do NOT use for picking between TextKit 1 and TextKit 2 (txt-textkit-choice), choosing a text view (txt-view-picker), or paragraph-style internals (txt-line-breaking).
license: MIT
---

# Text Recipes

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill is a catalog of working snippets for the small, recurring "how do I add X to a text view" tasks. Each recipe is intended to drop into a project with minimal adjustment. The patterns here are starting points, not final code — verify the integration in the actual project before claiming the recipe matches what's needed, and confirm any API used here against current Apple docs via Sosumi if the snippet is a few releases old.

The five most-asked recipes are inlined below. The full catalog of twenty recipes lives in [references/recipes.md](references/recipes.md), grouped by topic.

## Contents

- [Placeholder text in UITextView](#placeholder-text-in-uitextview)
- [Character or word limit](#character-or-word-limit)
- [Auto-growing text view](#auto-growing-text-view)
- [Highlight search results](#highlight-search-results)
- [Auto-detect links and data](#auto-detect-links-and-data)
- [Full recipe index](#full-recipe-index)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Placeholder text in UITextView

`UITextView` has no built-in placeholder. Subclass and draw the placeholder when the text is empty, then invalidate display whenever text or placeholder changes.

```swift
class PlaceholderTextView: UITextView {
    var placeholder: String = "" { didSet { setNeedsDisplay() } }
    override var text: String! { didSet { setNeedsDisplay() } }

    override func draw(_ rect: CGRect) {
        super.draw(rect)
        guard text.isEmpty else { return }
        let inset = textContainerInset
        let pad = textContainer.lineFragmentPadding
        let drawRect = CGRect(
            x: inset.left + pad,
            y: inset.top,
            width: bounds.width - inset.left - inset.right - 2 * pad,
            height: bounds.height - inset.top - inset.bottom
        )
        placeholder.draw(in: drawRect, withAttributes: [
            .font: font ?? .systemFont(ofSize: 17),
            .foregroundColor: UIColor.placeholderText
        ])
    }
}
```

Hook the host's `textViewDidChange(_:)` (or `NSText.didChangeNotification`) to call `setNeedsDisplay()` on every keystroke so the placeholder appears as soon as the text becomes empty again.

## Character or word limit

Enforce a limit in `shouldChangeTextIn:replacementText:`. Compute the would-be length first; reject the edit if it exceeds the cap.

```swift
func textView(_ textView: UITextView,
              shouldChangeTextIn range: NSRange,
              replacementText text: String) -> Bool {
    let current = (textView.text as NSString).length
    let newLength = current - range.length + (text as NSString).length
    return newLength <= 280
}
```

Use NSString length for the math — Swift `String.count` returns grapheme clusters, which diverges from NSRange units on emoji and combining marks. For word limits, count `text.split(separator: " ", omittingEmptySubsequences: true).count` against the projected text after the edit.

## Auto-growing text view

A `UITextView` reports a non-trivial `intrinsicContentSize` only when scrolling is disabled. Disable scrolling, let Auto Layout drive the height, and re-enable scrolling once a maximum height is reached.

```swift
textView.isScrollEnabled = false   // intrinsicContentSize now drives layout
textView.heightAnchor.constraint(lessThanOrEqualToConstant: 200).isActive = true

func textViewDidChange(_ textView: UITextView) {
    let fits = textView.sizeThatFits(
        CGSize(width: textView.bounds.width, height: .greatestFiniteMagnitude)
    )
    textView.isScrollEnabled = fits.height > 200
}
```

If the view is inside a stack or scroll view, ensure the parent honors the changed intrinsic size — a sibling with `lowest` content-hugging priority can absorb the growth instead of the editor.

## Highlight search results

Mutating `attributedText` to highlight matches invalidates layout and disturbs typing attributes. Use the layout manager's *temporary attributes* on TextKit 1 — they live above the storage and don't enter the editing lifecycle.

```swift
func highlight(_ query: String, in textView: UITextView) {
    guard let lm = textView.layoutManager, let text = textView.text else { return }
    let full = NSRange(location: 0, length: (text as NSString).length)
    lm.removeTemporaryAttribute(.backgroundColor, forCharacterRange: full)

    var search = text.startIndex..<text.endIndex
    while let r = text.range(of: query, options: .caseInsensitive, range: search) {
        lm.addTemporaryAttribute(.backgroundColor,
                                 value: UIColor.systemYellow,
                                 forCharacterRange: NSRange(r, in: text))
        search = r.upperBound..<text.endIndex
    }
}
```

Note: accessing `layoutManager` flips a TextKit 2 `UITextView` to TextKit 1 permanently. On TextKit 2, use `setRenderingAttributes(_:for:)` on the layout manager instead — same effect, no fallback. See `txt-fallback-triggers`.

## Auto-detect links and data

Built-in detection in `UITextView` requires a non-editable view. The data-detector property is silently ignored when editing is enabled.

```swift
textView.isEditable = false
textView.dataDetectorTypes = [.link, .phoneNumber, .address, .calendarEvent]
```

For editable text views, run `NSDataDetector` over the content and apply `.link` attributes to the matched ranges manually. See `txt-detectors-tagger` for the detector setup.

## Full recipe index

The complete catalog lives in [references/recipes.md](references/recipes.md):

| # | Recipe |
|---|--------|
| 1 | Background color behind a paragraph |
| 2 | Line numbers in a text view |
| 3 | Character or word limit on input |
| 4 | Text wrapping around an image |
| 5 | Clickable links (read-only) |
| 6 | Clickable links (editable) |
| 7 | Placeholder text in UITextView |
| 8 | Auto-growing text view |
| 9 | Highlight search results |
| 10 | Strikethrough text |
| 11 | Letter spacing (tracking and kern) |
| 12 | Different line heights per paragraph |
| 13 | First-line indent on paragraphs |
| 14 | Bullet or numbered lists |
| 15 | Read-only styled text |
| 16 | Auto-detect data (phones, URLs, dates) |
| 17 | Custom cursor color |
| 18 | Disable text selection |
| 19 | Programmatically scroll to range |
| 20 | Get current line number |
| 21 | Strip formatting on paste |
| 22 | Convert AttributedString ↔ NSAttributedString |
| 23 | Export NSAttributedString to RTF / HTML |
| 24 | Suppress autocorrect / smart punctuation |
| 25 | Auto-resizing UITextView in SwiftUI |
| 26 | Smart pairs and auto-indent (cursor-stable) |
| 27 | Tree-sitter concurrent reparse |
| 28 | Modern keyboard avoidance with `keyboardLayoutGuide` |

Recipes show UIKit code by default. Recipes that touch only `NSTextStorage`, `NSAttributedString`, or `NSParagraphStyle` work on AppKit unchanged. UIKit-specific surfaces (`UITextView`, content-size category, `dataDetectorTypes`) need the AppKit equivalent — see the platform-translation table at the top of `references/recipes.md`.

## Common Mistakes

1. **`dataDetectorTypes` on an editable text view.** Silently ignored. Detection only runs on `isEditable = false` views; for editable views, run `NSDataDetector` and apply attributes yourself.

2. **`String.count` for `NSRange` math.** Counts graphemes, not UTF-16 code units. Wrong on emoji and combining marks. Use `(text as NSString).length` or `NSRange(swiftRange, in: text)`.

3. **Mutating `attributedText` to highlight matches.** Invalidates layout, disturbs typing attributes, and on TextKit 2 forces a full re-render. Use temporary attributes (TK1) or rendering attributes (TK2) instead.

4. **Auto-grow with `isScrollEnabled = true`.** UIKit reports `UIView.noIntrinsicMetric` for the height while scrolling is enabled. Disable scrolling first, then conditionally re-enable past a maximum height.

5. **Forgetting to invalidate display on placeholder change.** The placeholder is drawn in `draw(_:)`. Without `setNeedsDisplay()`, the previous placeholder lingers until the next layout pass.

## References

- [references/recipes.md](references/recipes.md) — full catalog of 20 recipes with code
- `/skill txt-view-picker` — picking a text view in the first place
- `/skill txt-line-breaking` — paragraph style internals (line height, spacing, tab stops)
- `/skill txt-attribute-keys` — formatting attribute catalog
- `/skill txt-measurement` — sizing text and views to fit content
- `/skill txt-detectors-tagger` — `NSDataDetector` for editable views
- `/skill txt-fallback-triggers` — TextKit 2 → 1 fallback when accessing `layoutManager`
