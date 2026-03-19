---
name: apple-text-attachments-ref
description: Use when embedding images, custom views, Genmoji, or any non-text content inline in text — covers NSTextAttachment, NSTextAttachmentViewProvider (TextKit 2), NSAdaptiveImageGlyph (iOS 18+), NSTextAttachmentContainer, NSTextAttachmentLayout, NSTextAttachmentCellProtocol (legacy AppKit), bounds/baseline alignment, and attachment lifecycle
license: MIT
---

# Text Attachments Reference

Use this skill when the main question is how inline non-text content should behave inside Apple text views.

## When to Use

- You are working with `NSTextAttachment`.
- You need attachment view providers, Genmoji, or baseline/bounds behavior.
- You need compatibility rules across TextKit 1, TextKit 2, UIKit, and AppKit.

## Quick Decision

- Static inline image attachment -> `NSTextAttachment`
- Interactive inline view in TextKit 2 -> `NSTextAttachmentViewProvider`
- Adaptive inline glyph on supported systems -> `NSAdaptiveImageGlyph`

## Core Guidance

Keep this file for the attachment model, view-provider lifecycle, and adaptive glyph choice. For protocol signatures, insertion patterns, copy-paste rules, and support matrices, use [protocols-and-patterns.md](protocols-and-patterns.md).

## NSTextAttachment

### What It Is

The core class for inline non-text content in attributed strings. Lives in UIFoundation (shared UIKit/AppKit).

### Initializers

```swift
// From image (iOS 13+) — most common
let attachment = NSTextAttachment(image: myImage)

// From data + UTI
let attachment = NSTextAttachment(data: pngData, ofType: UTType.png.identifier)

// From file wrapper (macOS-oriented)
let attachment = NSTextAttachment(fileWrapper: fileWrapper)
```

**macOS gotcha:** When using `init(data:ofType:)`, you must manually set `attachmentCell` or the image won't display. Use `init(fileWrapper:)` or set `image` directly.

### The Attachment Character (U+FFFC)

Attachments are represented in attributed strings by:
1. Unicode Object Replacement Character (U+FFFC) as placeholder
2. `.attachment` attribute holding the NSTextAttachment instance

```swift
let attachmentString = NSAttributedString(attachment: attachment)
// Creates: 1 character (U+FFFC) with .attachment attribute

let full = NSMutableAttributedString(string: "Hello ")
full.append(attachmentString)
full.append(NSAttributedString(string: " World"))
// Result: "Hello \u{FFFC} World" — attachment renders at position 6
```

### Bounds (Size + Baseline Alignment)

```swift
attachment.bounds = CGRect(x: 0, y: yOffset, width: width, height: height)
```

**The y-axis origin is at the text baseline.** Negative y moves the attachment below the baseline:

```swift
// Centered on text line (common pattern)
let font = UIFont.preferredFont(forTextStyle: .body)
let ratio = image.size.width / image.size.height
let height = font.capHeight
attachment.bounds = CGRect(
    x: 0,
    y: (font.capHeight - height) / 2,  // Center vertically
    width: height * ratio,
    height: height
)

// Baseline-aligned (sits on baseline)
attachment.bounds = CGRect(x: 0, y: 0, width: 20, height: 20)

// Descender-aligned (extends below baseline)
attachment.bounds = CGRect(x: 0, y: font.descender, width: 20, height: 20)
```

**`CGRect.zero` (default):** Uses the image's natural size. If image is nil, renders as missing-image placeholder.

### Properties (iOS 15+)

```swift
attachment.lineLayoutPadding = 4.0        // Horizontal padding around attachment
attachment.allowsTextAttachmentView = true // Allow view-based rendering (default: true)
attachment.usesTextAttachmentView         // Read-only: is view-based rendering active?
```

## NSTextAttachmentViewProvider (TextKit 2)

### What It Is

Provides a live `UIView`/`NSView` for rendering an attachment. Unlike image-based attachments, view providers can have interactive controls, animations, and dynamic content.

### Registration

```swift
// Register a view provider for a file type
NSTextAttachment.registerViewProviderClass(
    CheckboxAttachmentViewProvider.self,
    forFileType: "com.myapp.checkbox"
)
```

### Implementation

```swift
class CheckboxAttachmentViewProvider: NSTextAttachmentViewProvider {
    override init(textAttachment: NSTextAttachment,
                  parentView: UIView?,
                  textLayoutManager: NSTextLayoutManager?,
                  location: NSTextLocation) {
        super.init(textAttachment: textAttachment,
                   parentView: parentView,
                   textLayoutManager: textLayoutManager,
                   location: location)
        // MUST set tracksTextAttachmentViewBounds HERE, not in loadView
        tracksTextAttachmentViewBounds = true
    }

    override func loadView() {
        let checkbox = UISwitch()
        checkbox.isOn = (textAttachment.contents?.first == 1)
        view = checkbox
    }

    override func attachmentBounds(
        for attributes: [NSAttributedString.Key: Any],
        location: NSTextLocation,
        textContainer: NSTextContainer?,
        proposedLineFragment: CGRect,
        position: CGPoint
    ) -> CGRect {
        return CGRect(x: 0, y: -4, width: 30, height: 30)
    }
}
```

### Lifecycle

1. **Registration** — `registerViewProviderClass` maps file type → provider class
2. **Creation** — TextKit 2 creates provider when attachment enters viewport
3. **`loadView()`** — Called to create the view. Set `self.view`.
4. **Display** — View is added to the text view's subview hierarchy
5. **Removal** — When attachment scrolls out of viewport, view may be removed
6. **Reuse** — Views are NOT reused like table cells. New provider per appearance.

### Critical Rules

- **`tracksTextAttachmentViewBounds` must be set in `init`, NOT `loadView`** — Setting it in loadView is too late and the bounds won't track correctly.
- **View-based attachments are LOST on TextKit 1 fallback** — The moment anything triggers fallback, all NSTextAttachmentViewProvider views disappear because TextKit 1 uses NSTextAttachmentCellProtocol instead.
- **Only works with TextKit 2** — `usesTextAttachmentView` returns false if TextKit 1 is active.

## NSAdaptiveImageGlyph (iOS 18+)

### What It Is

A special inline image that automatically adapts its size to match surrounding text. Used for Genmoji, stickers, and Memoji.

```swift
let glyph = NSAdaptiveImageGlyph(imageContent: imageData)

glyph.contentIdentifier   // Unique ID
glyph.contentDescription  // Accessibility description
glyph.imageContent        // Raw image data (multi-resolution)
glyph.contentType          // UTType
```

### How It Differs from NSTextAttachment

| Aspect | NSTextAttachment | NSAdaptiveImageGlyph |
|--------|-----------------|---------------------|
| Sizing | Manual (bounds property) | Automatic (matches text size) |
| Aspect ratio | Any | Always square |
| Resolutions | Single image | Multiple resolutions embedded |
| Dynamic Type | Manual handling | Automatic scaling |
| User insertion | Programmatic | Emoji keyboard |
| Available | iOS 7+ | iOS 18+ |

### Enabling in Text Views

```swift
textView.supportsAdaptiveImageGlyph = true  // UITextView
// Users can now insert Genmoji from the emoji keyboard
```

### Extracting from Attributed String

```swift
attributedString.enumerateAttribute(
    .adaptiveImageGlyph,
    in: NSRange(location: 0, length: attributedString.length)
) { value, range, _ in
    if let glyph = value as? NSAdaptiveImageGlyph {
        print("Genmoji: \(glyph.contentDescription)")
    }
}
```

## Common Pitfalls

1. **View attachments lost on TK1 fallback** — The instant anything triggers fallback, all NSTextAttachmentViewProvider views vanish.
2. **`tracksTextAttachmentViewBounds` set in loadView** — Too late. Must set in init.
3. **macOS: image not displaying** — With `init(data:ofType:)`, must set `attachmentCell` manually or use `init(fileWrapper:)`.
4. **Copy/paste loses attachment** — `contents` must be non-nil. Image-only attachments don't survive paste.
5. **Bounds y-coordinate confusion** — Negative y goes below baseline. Use `font.descender` for bottom-aligned.
6. **Not setting accessibility** — VoiceOver announces U+FFFC as "replacement character" without a description.

## Related Skills

- For protocol signatures, insertion recipes, and support matrices, see [protocols-and-patterns.md](protocols-and-patterns.md).
- Use `/skill apple-text-formatting-ref` for non-attachment attributed-text formatting.
- Use `/skill apple-text-textkit2-ref` for fragment and viewport behavior around attachments.
- Use `/skill apple-text-fallback-triggers` when attachment choices may force compatibility mode.
