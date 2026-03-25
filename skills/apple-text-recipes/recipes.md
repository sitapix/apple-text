# Text Recipes

## Platform Note

Most recipes below show UIKit (iOS) code. For macOS/AppKit equivalents:

| UIKit | AppKit |
|-------|--------|
| `UITextView` | `NSTextView` |
| `UIFont` | `NSFont` |
| `UIColor` | `NSColor` |
| `UIBezierPath` | `NSBezierPath` |
| `UIFontMetrics` | Not available — use `NSFont.systemFont(ofSize:)` with manual scaling |
| `tintColor` (cursor) | `insertionPointColor` |
| `dataDetectorTypes` | `isAutomaticDataDetectionEnabled` + `checkTextInDocument(_:)` |
| `textView.isEditable = false` | `textView.isEditable = false` (same) |

NSTextStorage, NSLayoutManager, NSTextContainer, NSAttributedString, and NSParagraphStyle are shared across both platforms. Recipes using only these types work on macOS without changes.

---

## 1. Background Color Behind a Paragraph

### Using `.backgroundColor` attribute (simple)

```swift
let attrs: [NSAttributedString.Key: Any] = [
    .backgroundColor: UIColor.systemYellow.withAlphaComponent(0.3),
    .font: UIFont.systemFont(ofSize: 15)
]
let highlighted = NSAttributedString(string: "This paragraph has a background", attributes: attrs)
```

**Limitation:** Only colors the area directly behind glyphs, not full-width.

### Full-width paragraph background (TextKit 1 subclass)

```swift
class ParagraphBackgroundLayoutManager: NSLayoutManager {
    override func drawBackground(forGlyphRange glyphsToShow: NSRange, at origin: CGPoint) {
        super.drawBackground(forGlyphRange: glyphsToShow, at: origin)

        guard let textStorage = textStorage else { return }

        textStorage.enumerateAttribute(.paragraphBackgroundColor,
                                        in: characterRange(forGlyphRange: glyphsToShow,
                                                           actualGlyphRange: nil)) { value, charRange, _ in
            guard let color = value as? UIColor else { return }
            let glyphRange = self.glyphRange(forCharacterRange: charRange, actualCharacterRange: nil)

            enumerateLineFragments(forGlyphRange: glyphRange) { rect, _, container, _, _ in
                guard let context = UIGraphicsGetCurrentContext() else { return }
                let fullWidthRect = CGRect(
                    x: 0,
                    y: rect.origin.y + origin.y,
                    width: container.size.width,
                    height: rect.height
                )
                context.setFillColor(color.cgColor)
                context.fill(fullWidthRect)
            }
        }
    }
}

// Register custom attribute
extension NSAttributedString.Key {
    static let paragraphBackgroundColor = NSAttributedString.Key("paragraphBackgroundColor")
}
```

## 2. Line Numbers in a Text View

```swift
class LineNumberGutter: UIView {
    weak var textView: UITextView?

    func updateLineNumbers() {
        guard let textView = textView,
              let layoutManager = textView.layoutManager else { return }

        setNeedsDisplay()
    }

    override func draw(_ rect: CGRect) {
        guard let textView = textView,
              let layoutManager = textView.layoutManager else { return }

        let font = UIFont.monospacedDigitSystemFont(ofSize: 12, weight: .regular)
        let attrs: [NSAttributedString.Key: Any] = [
            .font: font,
            .foregroundColor: UIColor.secondaryLabel
        ]

        let visibleGlyphRange = layoutManager.glyphRange(
            forBoundingRect: textView.bounds,
            in: textView.textContainer
        )

        var lineNumber = 1
        var previousLineY: CGFloat = -1
        let inset = textView.textContainerInset

        // Count lines before visible range
        let textBeforeVisible = (textView.text as NSString)
            .substring(to: layoutManager.characterRange(
                forGlyphRange: NSRange(location: visibleGlyphRange.location, length: 0),
                actualGlyphRange: nil).location)
        lineNumber = textBeforeVisible.components(separatedBy: "\n").count

        layoutManager.enumerateLineFragments(forGlyphRange: visibleGlyphRange) {
            rect, _, _, glyphRange, _ in

            let charRange = layoutManager.characterRange(forGlyphRange: glyphRange,
                                                          actualGlyphRange: nil)
            let lineY = rect.origin.y + inset.top - textView.contentOffset.y

            // Only number paragraph-starting lines
            if charRange.location == 0 ||
               (textView.text as NSString).character(at: charRange.location - 1) == 0x0A {
                let numStr = "\(lineNumber)" as NSString
                let size = numStr.size(withAttributes: attrs)
                numStr.draw(at: CGPoint(
                    x: self.bounds.width - size.width - 4,
                    y: lineY + (rect.height - size.height) / 2
                ), withAttributes: attrs)
                lineNumber += 1
            }
        }
    }
}
```

## 3. Character/Word Limit

```swift
// Character limit
func textView(_ textView: UITextView, shouldChangeTextIn range: NSRange,
              replacementText text: String) -> Bool {
    let currentLength = textView.text.count
    let replacementLength = text.count
    let rangeLength = range.length
    let newLength = currentLength - rangeLength + replacementLength
    return newLength <= 280  // Twitter-style limit
}

// Word limit
func textView(_ textView: UITextView, shouldChangeTextIn range: NSRange,
              replacementText text: String) -> Bool {
    let currentText = (textView.text as NSString).replacingCharacters(in: range, with: text)
    let wordCount = currentText.split(separator: " ").count
    return wordCount <= 500
}
```

## 4. Text Wrapping Around an Image

```swift
// Add image view as subview of text view
let imageView = UIImageView(image: myImage)
imageView.frame = CGRect(x: 16, y: 16, width: 120, height: 120)
textView.addSubview(imageView)

// Create exclusion path in text container coordinates
let inset = textView.textContainerInset
let exclusionRect = CGRect(
    x: imageView.frame.origin.x - inset.left + imageView.frame.width,
    y: imageView.frame.origin.y - inset.top,
    width: imageView.frame.width + 8,
    height: imageView.frame.height + 8
)

// Set right-aligned exclusion (text wraps on left side)
textView.textContainer.exclusionPaths = [UIBezierPath(rect: CGRect(
    x: textView.textContainer.size.width - 120 - 8,
    y: 0,
    width: 120 + 8,
    height: 120 + 8
))]
```

## 5. Clickable Links (Non-Editable)

```swift
textView.isEditable = false
textView.isSelectable = true
textView.dataDetectorTypes = [.link]  // Auto-detect URLs

// Or manual links via attributed string:
let text = NSMutableAttributedString(string: "Visit our website for details.")
text.addAttribute(.link, value: URL(string: "https://example.com")!,
                  range: NSRange(location: 10, length: 7))
textView.attributedText = text

// Handle taps:
func textView(_ textView: UITextView, shouldInteractWith URL: URL,
              in characterRange: NSRange,
              interaction: UITextItemInteraction) -> Bool {
    // Return true for default behavior, false to handle yourself
    return true
}
```

## 6. Clickable Links (Editable Text View)

```swift
// Links in editable text views don't respond to taps by default.
// Use UITextViewDelegate to detect taps on link-attributed ranges:
func textView(_ textView: UITextView, shouldInteractWith URL: URL,
              in characterRange: NSRange,
              interaction: UITextItemInteraction) -> Bool {
    if interaction == .invokeDefaultAction {
        UIApplication.shared.open(URL)
        return false
    }
    return true
}
```

## 7. Placeholder Text in UITextView

```swift
class PlaceholderTextView: UITextView {
    var placeholder: String = "" {
        didSet { setNeedsDisplay() }
    }

    var placeholderColor: UIColor = .placeholderText

    override var text: String! {
        didSet { setNeedsDisplay() }
    }

    override func draw(_ rect: CGRect) {
        super.draw(rect)
        guard text.isEmpty else { return }

        let attrs: [NSAttributedString.Key: Any] = [
            .font: font ?? .systemFont(ofSize: 17),
            .foregroundColor: placeholderColor
        ]
        let inset = textContainerInset
        let padding = textContainer.lineFragmentPadding
        let placeholderRect = CGRect(
            x: inset.left + padding,
            y: inset.top,
            width: bounds.width - inset.left - inset.right - 2 * padding,
            height: bounds.height - inset.top - inset.bottom
        )
        placeholder.draw(in: placeholderRect, withAttributes: attrs)
    }

    // Call setNeedsDisplay in textDidChange notification
}
```

## 8. Auto-Growing Text View

```swift
// The simplest approach: disable scrolling
textView.isScrollEnabled = false
// Auto Layout now uses intrinsicContentSize to grow the text view

// With a maximum height:
textView.isScrollEnabled = false

// In your constraint setup:
let heightConstraint = textView.heightAnchor.constraint(lessThanOrEqualToConstant: 200)
heightConstraint.isActive = true

// When content exceeds max height, enable scrolling:
func textViewDidChange(_ textView: UITextView) {
    let fittingSize = textView.sizeThatFits(
        CGSize(width: textView.bounds.width, height: .greatestFiniteMagnitude)
    )
    textView.isScrollEnabled = fittingSize.height > 200
}
```

## 9. Highlight Search Results

```swift
// TextKit 1 — temporary attributes (don't modify the model)
func highlightOccurrences(of searchText: String, in textView: UITextView) {
    guard let layoutManager = textView.layoutManager,
          let text = textView.text else { return }

    // Clear previous highlights
    let fullRange = NSRange(location: 0, length: (text as NSString).length)
    layoutManager.removeTemporaryAttribute(.backgroundColor, forCharacterRange: fullRange)

    // Add new highlights
    var searchRange = text.startIndex..<text.endIndex
    while let range = text.range(of: searchText, options: .caseInsensitive, range: searchRange) {
        let nsRange = NSRange(range, in: text)
        layoutManager.addTemporaryAttribute(.backgroundColor,
                                             value: UIColor.systemYellow,
                                             forCharacterRange: nsRange)
        searchRange = range.upperBound..<text.endIndex
    }
}
```

## 10. Strikethrough Text

```swift
// Single strikethrough
let attrs: [NSAttributedString.Key: Any] = [
    .strikethroughStyle: NSUnderlineStyle.single.rawValue,
    .strikethroughColor: UIColor.red
]

// Double strikethrough
let attrs: [NSAttributedString.Key: Any] = [
    .strikethroughStyle: NSUnderlineStyle.double.rawValue
]

// Thick strikethrough
let attrs: [NSAttributedString.Key: Any] = [
    .strikethroughStyle: NSUnderlineStyle.thick.rawValue
]
```

## 11. Letter Spacing

```swift
// Kern — fixed spacing in points (doesn't scale with font size)
let attrs: [NSAttributedString.Key: Any] = [
    .kern: 2.0  // 2pt between characters
]

// Tracking (iOS 14+) — scales with font size
let attrs: [NSAttributedString.Key: Any] = [
    .tracking: 0.5  // Proportional to font size
]
```

**Use `.tracking` when possible** — it produces consistent results across font sizes.

## 12. Different Line Heights Per Paragraph

For full line-height mechanics (the stack, `lineHeightMultiple`, `baselineOffset`), see `/skill apple-text-line-breaking`.

```swift
func styledParagraph(_ text: String, lineHeight: CGFloat, font: UIFont) -> NSAttributedString {
    let style = NSMutableParagraphStyle()
    style.minimumLineHeight = lineHeight
    style.maximumLineHeight = lineHeight

    let baselineOffset = (lineHeight - font.lineHeight) / 2

    return NSAttributedString(string: text + "\n", attributes: [
        .font: font,
        .paragraphStyle: style,
        .baselineOffset: baselineOffset
    ])
}

let result = NSMutableAttributedString()
result.append(styledParagraph("Title", lineHeight: 36,
              font: .boldSystemFont(ofSize: 28)))
result.append(styledParagraph("Body text here...", lineHeight: 24,
              font: .systemFont(ofSize: 17)))
```

## 13. Indent First Line

```swift
let style = NSMutableParagraphStyle()
style.firstLineHeadIndent = 24  // Only first line indented
```

## 14. Bullet Lists (Manual, Cross-Platform)

```swift
func bulletList(_ items: [String], font: UIFont) -> NSAttributedString {
    let bullet = "\u{2022}"  // bullet character
    let indentWidth: CGFloat = 20

    let style = NSMutableParagraphStyle()
    style.headIndent = indentWidth
    style.tabStops = [NSTextTab(textAlignment: .left, location: indentWidth)]
    style.firstLineHeadIndent = 0

    let result = NSMutableAttributedString()
    for item in items {
        let line = "\(bullet)\t\(item)\n"
        result.append(NSAttributedString(string: line, attributes: [
            .font: font,
            .paragraphStyle: style
        ]))
    }
    return result
}
```

## 15. Read-Only Styled Text

```swift
textView.isEditable = false
textView.isSelectable = true  // Allow copy
textView.textContainerInset = UIEdgeInsets(top: 16, left: 16, bottom: 16, right: 16)
textView.attributedText = styledContent
textView.backgroundColor = .systemBackground
```

## 16. Auto-Detect Data

```swift
textView.isEditable = false
textView.dataDetectorTypes = [.link, .phoneNumber, .address, .calendarEvent]
// Text view automatically makes detected data tappable
```

**Must be non-editable.** Data detection is disabled when `isEditable = true`.

## 17. Custom Cursor Color

```swift
textView.tintColor = .systemPurple  // Changes cursor AND selection handles
```

## 18. Disable Text Selection

```swift
// Option 1: Subclass
class NonSelectableTextView: UITextView {
    override var canBecomeFirstResponder: Bool { false }
}

// Option 2: Disable interaction
textView.isSelectable = false
textView.isEditable = false
```

## 19. Scroll to Range

```swift
// Scroll to make a character range visible
let range = NSRange(location: 500, length: 0)
textView.scrollRangeToVisible(range)

// Scroll to bottom
let bottom = NSRange(location: textView.text.count - 1, length: 1)
textView.scrollRangeToVisible(bottom)
```

## 20. Get Current Line Number

```swift
func currentLineNumber(in textView: UITextView) -> Int {
    guard let layoutManager = textView.layoutManager else { return 1 }

    let cursorPosition = textView.selectedRange.location
    var lineNumber = 1
    let glyphIndex = layoutManager.glyphIndexForCharacter(at: cursorPosition)

    layoutManager.enumerateLineFragments(
        forGlyphRange: NSRange(location: 0, length: glyphIndex)
    ) { _, _, _, _, _ in
        lineNumber += 1
    }

    return lineNumber
}
```
