---
name: txt-recipes
description: Use when building common text features or looking up quick recipes — background colors, line numbers, character limits, links, placeholders
license: MIT
---

# Text Recipes Cookbook

Quick, working solutions to the most common "how do I..." questions about Apple text views.

## When to Use

- User asks "how do I [specific text thing]?" and you need a direct answer.
- You need a working code snippet, not architecture guidance.
- The question maps to a common text task that doesn't need a full skill.

## Top Recipes Inline

The 5 most-asked recipes — copy/paste ready. Full catalog of 20 recipes in [recipes.md](references/recipes.md).

### Placeholder text in UITextView

```swift
class PlaceholderTextView: UITextView {
    var placeholder: String = "" { didSet { setNeedsDisplay() } }
    override var text: String! { didSet { setNeedsDisplay() } }

    override func draw(_ rect: CGRect) {
        super.draw(rect)
        guard text.isEmpty else { return }
        let inset = textContainerInset
        let pad = textContainer.lineFragmentPadding
        let drawRect = CGRect(x: inset.left + pad, y: inset.top,
                              width: bounds.width - inset.left - inset.right - 2 * pad,
                              height: bounds.height - inset.top - inset.bottom)
        placeholder.draw(in: drawRect, withAttributes: [
            .font: font ?? .systemFont(ofSize: 17),
            .foregroundColor: UIColor.placeholderText
        ])
    }
}
// Hook to NSText.didChangeNotification or textViewDidChange to refresh.
```

### Character limit on input

```swift
func textView(_ textView: UITextView, shouldChangeTextIn range: NSRange,
              replacementText text: String) -> Bool {
    let newLength = textView.text.count - range.length + text.count
    return newLength <= 280
}
```

### Auto-growing text view (no scroll)

```swift
textView.isScrollEnabled = false  // intrinsicContentSize now drives layout

// Optional: cap at 200pt then enable scrolling
textView.heightAnchor.constraint(lessThanOrEqualToConstant: 200).isActive = true
func textViewDidChange(_ textView: UITextView) {
    let fits = textView.sizeThatFits(CGSize(width: textView.bounds.width,
                                            height: .greatestFiniteMagnitude))
    textView.isScrollEnabled = fits.height > 200
}
```

### Highlight search results (TextKit 1, no model mutation)

```swift
func highlight(_ query: String, in textView: UITextView) {
    guard let lm = textView.layoutManager, let text = textView.text else { return }
    let full = NSRange(location: 0, length: (text as NSString).length)
    lm.removeTemporaryAttribute(.backgroundColor, forCharacterRange: full)

    var search = text.startIndex..<text.endIndex
    while let r = text.range(of: query, options: .caseInsensitive, range: search) {
        lm.addTemporaryAttribute(.backgroundColor, value: UIColor.systemYellow,
                                  forCharacterRange: NSRange(r, in: text))
        search = r.upperBound..<text.endIndex
    }
}
```

### Auto-detect links / phones / addresses (read-only)

```swift
textView.isEditable = false
textView.dataDetectorTypes = [.link, .phoneNumber, .address, .calendarEvent]
// Required: must be non-editable. Detection is disabled when isEditable = true.
```

## Full Recipe Index

Find the recipe number below, then see [recipes.md](references/recipes.md) for the code.

| # | Recipe | Framework |
|---|--------|-----------|
| 1 | Background color behind a paragraph | TextKit 1 / TextKit 2 |
| 2 | Line numbers in a text view | TextKit 1 |
| 3 | Character/word limit on input | UITextView delegate |
| 4 | Text wrapping around an image | NSTextContainer |
| 5 | Clickable links (not editable) | UITextView |
| 6 | Clickable links (editable) | UITextView delegate |
| 7 | Placeholder text in UITextView | UITextView |
| 8 | Auto-growing text view (no scroll) | Auto Layout |
| 9 | Highlight search results | Temporary attributes |
| 10 | Strikethrough text | NSAttributedString |
| 11 | Letter spacing (tracking/kern) | NSAttributedString |
| 12 | Different line heights per paragraph | NSParagraphStyle |
| 13 | Indent first line of paragraphs | NSParagraphStyle |
| 14 | Bullet/numbered lists | NSTextList / manual |
| 15 | Read-only styled text | UITextView |
| 16 | Detect data (phones, URLs, dates) | UITextView |
| 17 | Custom cursor color | UITextView |
| 18 | Disable text selection | UITextView |
| 19 | Programmatically scroll to range | UITextView |
| 20 | Get current line number | TextKit 1 |

## Platform Coverage

Recipes show UIKit (iOS) code by default. See the **Platform Note** at the top of [recipes.md](references/recipes.md) for a UIKit → AppKit translation table. Recipes that use only NSTextStorage, NSAttributedString, and NSParagraphStyle work on both platforms without changes.

## Quick Decision

- Need architecture guidance, not a snippet -> `/skill txt-views` or `/skill txt-textkit-choice`
- Need paragraph style details (line height, spacing) -> `/skill txt-line-breaking`
- Need formatting attribute catalog -> `/skill txt-formatting`
- Need measurement or sizing -> `/skill txt-measurement`

## Common Mistakes

1. **Setting `dataDetectorTypes` on an editable text view** — silently does nothing. Detection requires `isEditable = false`.
2. **Using `String.count` for `NSRange` math** — `String.count` is grapheme clusters; `NSRange` is UTF-16 units. Use `(text as NSString).length` or `NSRange(swiftRange, in: text)`.
3. **Modifying `attributedText` to highlight search results** — invalidates layout and loses attribute identity. Use `addTemporaryAttribute` on the layout manager (TextKit 1) or rendering attributes (TextKit 2).
4. **Forgetting to call `setNeedsDisplay` on placeholder change** — the placeholder draw path runs in `draw(_:)`. Without invalidation, the old placeholder lingers.
5. **Auto-grow without `isScrollEnabled = false`** — UIKit reports `intrinsicContentSize.height = UIView.noIntrinsicMetric` while scrolling is enabled.

## Related Skills

- For measurement -> `/skill txt-measurement`
- For exclusion paths or layout -> `/skill txt-exclusion-paths`, `/skill txt-layout-invalidation`
- For paragraph style and line breaking -> `/skill txt-line-breaking`
- For formatting attributes -> `/skill txt-formatting`
- For attachment views -> `/skill txt-attachments`
- For find/replace -> `/skill txt-find-replace`
- For editor interaction details -> `/skill txt-interaction`
