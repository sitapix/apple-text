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
if let url = URL(string: "https://example.com") {
    text.addAttribute(.link, value: url,
                      range: NSRange(location: 10, length: 7))
}
textView.attributedText = text

// Handle taps with the modern API (iOS 17+):
func textView(_ textView: UITextView,
              primaryActionFor textItem: UITextItem,
              defaultAction: UIAction) -> UIAction? {
    if case .link(let url) = textItem.content {
        return UIAction { _ in /* custom handling */ }
    }
    return defaultAction  // Fall back to system behavior
}
```

> Use `primaryActionFor textItem:` on iOS 17+. The older `shouldInteractWith URL:in:interaction:` delegate is deprecated.

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

For full line-height mechanics (the stack, `lineHeightMultiple`, `baselineOffset`), see `/skill txt-line-breaking`.

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

## 21. Strip Formatting on Paste (Rich-Paste Sanitization)

Override `paste(_:)` to convert pasteboard content to plain text using the view's current default attributes — preserves font/color/size while dropping inline styling, links, and images.

```swift
final class SanitizingTextView: UITextView {
    override func paste(_ sender: Any?) {
        let pasteboard = UIPasteboard.general
        guard let plain = pasteboard.string else { return }

        let defaults = typingAttributes
        let sanitized = NSAttributedString(string: plain, attributes: defaults)

        guard let range = selectedTextRange else { return }
        let nsRange = NSRange(location: offset(from: beginningOfDocument, to: range.start),
                              length: offset(from: range.start, to: range.end))
        textStorage.replaceCharacters(in: nsRange, with: sanitized)
    }

    override func canPerformAction(_ action: Selector, withSender sender: Any?) -> Bool {
        if action == #selector(paste(_:)) { return UIPasteboard.general.hasStrings }
        return super.canPerformAction(action, withSender: sender)
    }
}
```

For finer-grained sanitization (keep bold/italic, drop colors and links), filter `NSAttributedString` attributes through an allow-list — see `/skill txt-pasteboard`.

## 22. Convert AttributedString ↔ NSAttributedString Safely

Cross-scope round trips can silently drop custom attributes. Use the right initializer for the destination scope, and guard the inverse conversion.

```swift
import SwiftUI

// SwiftUI -> UIKit (for NSTextStorage)
let swiftAttr: AttributedString = ...
let nsAttr = NSAttributedString(swiftAttr)  // SwiftUI scope -> Foundation scope

// UIKit -> SwiftUI (lossy if custom attributes use non-Codable scopes)
do {
    let roundTrip = try AttributedString(nsAttr, including: \.uiKit)
    // Use \.swiftUI, \.appKit, or a custom AttributeScope as needed
} catch {
    // Falls back to plain string if scope keys are unrepresentable
    let plain = AttributedString(nsAttr.string)
}
```

> Custom `AttributedStringKey` types must be in a scope (`AttributeScope`) for either direction to preserve them. Foundation-only attributes (e.g., `.link`) round-trip without a scope argument.

## 23. Export NSAttributedString to RTF / HTML

```swift
let attr: NSAttributedString = ...
let fullRange = NSRange(location: 0, length: attr.length)

// RTF (UIKit and AppKit)
if let rtfData = try? attr.data(
    from: fullRange,
    documentAttributes: [.documentType: NSAttributedString.DocumentType.rtf]
) {
    try? rtfData.write(to: URL(fileURLWithPath: "/tmp/out.rtf"))
}

// HTML (returns UTF-8 encoded HTML)
if let htmlData = try? attr.data(
    from: fullRange,
    documentAttributes: [
        .documentType: NSAttributedString.DocumentType.html,
        .characterEncoding: String.Encoding.utf8.rawValue
    ]
) {
    let html = String(data: htmlData, encoding: .utf8) ?? ""
}
```

> HTML import (`init(data:options:documentAttributes:)` with `.html`) must run on the main thread on iOS — it spins up a hidden WebKit parser.

## 24. Suppress Autocorrect / Smart Punctuation On a Single Field

```swift
// UITextView / UITextField (UIKit)
field.autocorrectionType = .no
field.autocapitalizationType = .none
field.smartQuotesType = .no
field.smartDashesType = .no
field.smartInsertDeleteType = .no
field.spellCheckingType = .no
field.inlinePredictionType = .no   // iOS 17+

// SwiftUI (iOS 17+ / macOS 14+)
TextField("Code", text: $code)
    .autocorrectionDisabled()
    .textInputAutocapitalization(.never)
    .keyboardType(.asciiCapable)        // iOS only
```

Use this for code editors, identifiers, and password-like fields. Setting `autocorrectionType` alone leaves smart punctuation enabled — disable each trait you actually want off.

## 25. Auto-Resizing UITextView in SwiftUI Without Update Loops

`TextEditor` resizes implicitly, but for custom UITextView wrapping you must compute height in `updateUIView` and write back through a non-`text` binding. Comparing the new height before assigning prevents the SwiftUI re-render → text-set → height-recompute cycle.

```swift
struct GrowingTextEditor: UIViewRepresentable {
    @Binding var text: String
    @Binding var height: CGFloat

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIView(context: Context) -> UITextView {
        let view = UITextView()
        view.delegate = context.coordinator
        view.isScrollEnabled = false  // Activates intrinsicContentSize
        view.textContainerInset = .zero
        return view
    }

    func updateUIView(_ view: UITextView, context: Context) {
        if view.text != text { view.text = text }            // Avoid feedback
        let target = view.sizeThatFits(CGSize(width: view.bounds.width,
                                              height: .infinity)).height
        if abs(target - height) > 0.5 {                      // Avoid feedback
            DispatchQueue.main.async { height = target }
        }
    }

    final class Coordinator: NSObject, UITextViewDelegate {
        let parent: GrowingTextEditor
        init(_ parent: GrowingTextEditor) { self.parent = parent }
        func textViewDidChange(_ textView: UITextView) { parent.text = textView.text }
    }
}
```

Two non-negotiables: `isScrollEnabled = false` (so `intrinsicContentSize` reflects content) and the height-tolerance guard (so identical layout passes don't re-publish the same value and re-enter SwiftUI's update phase).

## 26. Smart Pairs and Auto-Indent (Cursor-Stable)

Returning `true` from `textView(_:shouldChangeTextIn:replacementText:)` lets UIKit insert the user's character first, after which any follow-up mutation runs on a shifted range — the cursor lands a position too late, or a closing pair appears outside the selection. Drafts' approach: return `false` to suppress UIKit's own insertion, then drive `textStorage.replaceCharacters(in:with:)` with the full pair and place `selectedRange` between the two characters in one pass. Storage mutation routes through `textViewDidChange(_:)` for typing-attributes refresh and through the undo manager exactly once.

```swift
func textView(_ textView: UITextView,
              shouldChangeTextIn range: NSRange,
              replacementText text: String) -> Bool {
    let pairs: [String: String] = ["(": ")", "[": "]", "{": "}", "\"": "\"", "`": "`"]
    guard let close = pairs[text] else { return true }

    let inserted = "\(text)\(close)"
    textView.textStorage.replaceCharacters(in: range, with: inserted)
    textView.selectedRange = NSRange(location: range.location + (text as NSString).length, length: 0)
    textView.delegate?.textViewDidChange?(textView)
    return false
}
```

Same pattern for auto-indent on Enter: detect a newline, peek at the previous line's leading whitespace, replace with `"\n" + indent`, set `selectedRange` past the indent. Wrap multi-step storage mutations in `textStorage.beginEditing()` / `endEditing()` so the layout manager and undo manager see one transaction.

## 27. Tree-Sitter Concurrent Reparse

Tree-sitter trees are atomically refcounted, so a parse on a background thread is safe while the main thread reads the previous tree for syntax queries. The pattern: on every storage mutation, mutate the tree synchronously with the user's edit (cheap, structural), enqueue an async reparse with the old tree as a hint (incremental, O(changed_region)), and apply the new tree's highlight ranges back on the main thread. Reference: SwiftTreeSitter (<https://github.com/ChimeHQ/SwiftTreeSitter>).

```swift
final class IncrementalHighlighter {
    private let parser: Parser            // SwiftTreeSitter.Parser
    private var tree: Tree?               // last successful parse
    private let reparseQueue = DispatchQueue(label: "tree-sitter.reparse")

    func textStorage(_ storage: NSTextStorage, didEdit edit: InputEdit, fullText: String) {
        // 1. Synchronously inform the existing tree of the edit (structural shift only).
        tree?.edit(edit)
        let editedTree = tree

        // 2. Reparse off-main using the edited tree as a hint.
        reparseQueue.async { [weak self] in
            guard let self else { return }
            let newTree = self.parser.parse(tree: editedTree, string: fullText)
            DispatchQueue.main.async {
                self.tree = newTree
                self.applyHighlights(from: newTree, to: storage)
            }
        }
    }

    private func applyHighlights(from tree: Tree?, to storage: NSTextStorage) {
        // Walk the new tree, build ranges, addAttribute / setRenderingAttributes on main.
    }
}
```

The edit-then-reparse-with-hint sequence is what makes this O(changed region) instead of O(document). Skipping the `tree?.edit(edit)` step forces a full reparse every keystroke.

## 28. Modern Keyboard Avoidance with `keyboardLayoutGuide`

`view.keyboardLayoutGuide` (iOS 15.4+) tracks the on-screen keyboard's frame as a layout guide — no `keyboardWillShow`/`keyboardWillHide` notifications, no manual constraint juggling. Constrain the bottom of the editor (or its container) to the guide's top anchor; the system animates the constraint as the keyboard appears, dismisses, and resizes. `followsUndockedKeyboard = true` extends tracking to floating and split keyboards on iPad.

```swift
view.keyboardLayoutGuide.followsUndockedKeyboard = true

NSLayoutConstraint.activate([
    textView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
    textView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
    textView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
    textView.bottomAnchor.constraint(equalTo: view.keyboardLayoutGuide.topAnchor),
])
```

Don't combine this with `additionalSafeAreaInsets.bottom` adjustments from a notification observer — the two compound and the editor ends up double-inset by the keyboard height. Pick one mechanism per view controller; for new code on iOS 15.4+, the layout guide is the cleaner path.
