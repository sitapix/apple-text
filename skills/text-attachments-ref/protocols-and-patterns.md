# Attachment Protocols and Patterns

Use this sidecar when `text-attachments-ref` needs the lower-level protocols, insertion recipes, or compatibility matrix without loading them into every attachment question.

## CTAdaptiveImageProviding

The Core Text protocol underlying `NSAdaptiveImageGlyph`:

```swift
protocol CTAdaptiveImageProviding {
    func image(forProposedSize: CGSize,
               scaleFactor: CGFloat,
               imageOffset: UnsafeMutablePointer<CGPoint>,
               imageSize: UnsafeMutablePointer<CGSize>) -> CGImage
}
```

Returns the best image for the requested size and scale factor.

## NSTextAttachmentContainer

The TextKit 1 protocol for attachment rendering. `NSTextAttachment` conforms to this.

```swift
protocol NSTextAttachmentContainer {
    func image(forBounds imageBounds: CGRect,
               textContainer: NSTextContainer?,
               characterIndex charIndex: Int) -> UIImage?

    func attachmentBounds(for textContainer: NSTextContainer?,
                          proposedLineFragment lineFrag: CGRect,
                          glyphPosition position: CGPoint,
                          characterIndex charIndex: Int) -> CGRect
}
```

This is TextKit 1 only. Its `glyphPosition` and `characterIndex` parameters reflect the older glyph-oriented model.

## NSTextAttachmentLayout

The modern attachment-layout protocol. `NSTextAttachment` conforms to this and uses `NSTextLocation`.

```swift
protocol NSTextAttachmentLayout {
    func image(for bounds: CGRect,
               attributes: [NSAttributedString.Key: Any],
               location: NSTextLocation,
               textContainer: NSTextContainer?) -> UIImage?

    func attachmentBounds(for attributes: [NSAttributedString.Key: Any],
                          location: NSTextLocation,
                          textContainer: NSTextContainer?,
                          proposedLineFragment: CGRect,
                          position: CGPoint) -> CGRect

    func viewProvider(for parentView: UIView?,
                      location: NSTextLocation,
                      textContainer: NSTextContainer?) -> NSTextAttachmentViewProvider?
}
```

## NSTextAttachmentCellProtocol

The legacy AppKit cell protocol. It is TextKit 1 only and conflicts with TextKit 2 view providers.

```swift
protocol NSTextAttachmentCellProtocol {
    var attachment: NSTextAttachment? { get set }

    func cellSize() -> NSSize
    func cellBaselineOffset() -> NSPoint
    func cellFrame(for textContainer: NSTextContainer,
                   proposedLineFragment lineFrag: NSRect,
                   glyphPosition position: NSPoint,
                   characterIndex charIndex: Int) -> NSRect

    func draw(withFrame cellFrame: NSRect, in controlView: NSView?)
    func draw(withFrame cellFrame: NSRect, in controlView: NSView?,
              characterIndex charIndex: Int, layoutManager: NSLayoutManager)

    func wantsToTrackMouse() -> Bool
    func trackMouse(with event: NSEvent, in cellFrame: NSRect,
                    of controlView: NSView?, untilMouseUp flag: Bool) -> Bool

    func highlight(_ flag: Bool, withFrame cellFrame: NSRect, in controlView: NSView?)
}
```

Using `attachmentCell` or cell-based rendering forces TextKit 1 fallback. The migration path is `NSTextAttachmentViewProvider`.

## Practical Patterns

### Inline Image

```swift
func insertInlineImage(_ image: UIImage, in textView: UITextView) {
    let attachment = NSTextAttachment(image: image)
    let font = textView.font ?? .systemFont(ofSize: 16)
    let ratio = image.size.width / image.size.height
    attachment.bounds = CGRect(
        x: 0,
        y: font.descender,
        width: font.lineHeight * ratio,
        height: font.lineHeight
    )

    let mutable = NSMutableAttributedString(attributedString: textView.attributedText)
    mutable.insert(NSAttributedString(attachment: attachment), at: textView.selectedRange.location)
    textView.attributedText = mutable
}
```

### Custom Interactive View

```swift
let checkboxType = "com.myapp.checkbox"

NSTextAttachment.registerViewProviderClass(
    CheckboxProvider.self,
    forFileType: checkboxType
)

let attachment = NSTextAttachment(data: Data([0]), ofType: checkboxType)
let str = NSAttributedString(attachment: attachment)
textStorage.insert(str, at: position)
```

### Async Image Loading

```swift
class AsyncImageProvider: NSTextAttachmentViewProvider {
    override func loadView() {
        let imageView = UIImageView()
        imageView.contentMode = .scaleAspectFit
        imageView.backgroundColor = .secondarySystemBackground
        view = imageView

        Task {
            let image = try await loadImage(url: imageURL)
            await MainActor.run {
                (view as? UIImageView)?.image = image
            }
        }
    }
}
```

### Copy and Paste

Attachments only survive paste when `contents` is non-nil.

```swift
let attachment = NSTextAttachment(data: imageData, ofType: UTType.png.identifier)
```

If you only set `attachment.image`, the attachment can render but still be lost on paste.

### Accessibility

```swift
let attachment = NSTextAttachment(image: starImage)
let str = NSMutableAttributedString(attachment: attachment)
str.addAttribute(.accessibilityTextCustom, value: "5-star rating",
                 range: NSRange(location: 0, length: 1))
```

For adaptive image glyphs, populate `glyph.contentDescription`.

## Support Matrix

| View | Image Attachment | View Provider | Adaptive Image Glyph |
|------|-----------------|---------------|---------------------|
| UITextView (TK2) | Yes | Yes | Yes (iOS 18+) |
| UITextView (TK1) | Yes | No | No |
| NSTextView (TK2) | Yes | Yes | Yes (macOS 15+) |
| NSTextView (TK1) | Yes (via cell) | No | No |
| UILabel | Yes (display only) | No | No |
| SwiftUI Text | No | No | No |
| SwiftUI TextEditor (iOS 26+) | No | No | Yes (Genmoji) |
