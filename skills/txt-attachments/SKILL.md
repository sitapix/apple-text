---
name: txt-attachments
description: Embed images, custom interactive views, or Genmoji inline in attributed text via NSTextAttachment, NSTextAttachmentViewProvider, and NSAdaptiveImageGlyph. Use when an attachment renders at the wrong size or position, baseline alignment is off, a view-based attachment vanishes, Genmoji insertion fails, or copy/paste loses the image. Covers attachment bounds and baseline math, view-provider lifecycle, registration timing, and the TextKit 1 fallback that kills view providers. Read the actual storage and view-provider implementation before reciting causes; the patterns here are clues, not answers.
license: MIT
---

# Text Attachments

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill covers the three inline-attachment systems in Apple's text stack: `NSTextAttachment` for static images and file wrappers, `NSTextAttachmentViewProvider` for live `UIView`/`NSView` content (TextKit 2 only), and `NSAdaptiveImageGlyph` for Genmoji and stickers (iOS 18+). The patterns here describe how the systems usually fail; before quoting any cause, open the storage that builds the attributed string, the view provider class, and the text view configuration — the sizing math and the TextKit 1 fallback transition are where most bugs live, and they don't show up in a stack trace.

A symptom often points away from the attachment itself. A view-based attachment that disappears is almost always TextKit 1 fallback, not the provider. An attachment that renders at the wrong y-position is almost always confusion about Core Text's baseline-origin coordinate system. A Genmoji that fails to insert is usually the text view missing `supportsAdaptiveImageGlyph = true`.

## Contents

- [How attachments live in attributed strings](#how-attachments-live-in-attributed-strings)
- [NSTextAttachment basics](#nstextattachment-basics)
- [Bounds and baseline alignment](#bounds-and-baseline-alignment)
- [NSTextAttachmentViewProvider](#nstextattachmentviewprovider)
- [NSAdaptiveImageGlyph for Genmoji](#nsadaptiveimageglyph-for-genmoji)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## How attachments live in attributed strings

An attachment is two things at once: a Unicode Object Replacement Character (U+FFFC) at a specific position in the string, plus an `.attachment` attribute at that single character whose value is the `NSTextAttachment` instance. The character is what the layout system advances over; the attribute is what tells it to render something other than a glyph.

```swift
let attachment = NSTextAttachment(image: image)
let attachmentString = NSAttributedString(attachment: attachment)
// 1 character (U+FFFC) carrying the .attachment attribute

let full = NSMutableAttributedString(string: "Hello ")
full.append(attachmentString)
full.append(NSAttributedString(string: " World"))
```

Removing an attachment means deleting that single character; replacing it means replacing one character with another attributed segment. Treating it as anything else (operating on the attribute alone, leaving the U+FFFC behind) leaves a stranded replacement character that VoiceOver reads as "object replacement."

## NSTextAttachment basics

```swift
// From a UIImage / NSImage
let attachment = NSTextAttachment(image: image)

// From data plus UTI
let attachment = NSTextAttachment(data: pngData, ofType: UTType.png.identifier)

// From a file wrapper (the AppKit-friendly path)
let attachment = NSTextAttachment(fileWrapper: wrapper)
```

On macOS, the `init(data:ofType:)` form leaves `attachmentCell` unset, and the image won't display until something assigns one. The reliable initializers on macOS are `init(image:)` and `init(fileWrapper:)`.

Properties worth knowing:

- `attachment.image` — the rendered image. Setting this triggers a redraw of the surrounding line.
- `attachment.bounds` — the rect used for layout (see next section).
- `attachment.lineLayoutPadding` — horizontal padding around the attachment within its line. iOS 15+.
- `attachment.allowsTextAttachmentView` — opt-out for view-provider rendering. Default `true`.
- `attachment.usesTextAttachmentView` — read-only reflection of whether view-provider rendering is live (false on TextKit 1).
- `attachment.contents` — raw data; required to be non-nil for paste fidelity. Image-only attachments without `contents` lose data on copy/paste.

## Bounds and baseline alignment

`NSTextAttachment.bounds` uses Core Text's coordinate convention: the y-origin is the text baseline, with positive y going up. This is opposite to UIKit's view-coordinate intuition and is the source of most "attachment in the wrong place" bugs.

```swift
// CGRect.zero (default) — uses the image's natural size, sitting on the baseline.
attachment.bounds = .zero

// Sit on the baseline at a fixed size.
attachment.bounds = CGRect(x: 0, y: 0, width: 20, height: 20)

// Drop below the baseline by the font's descender depth.
attachment.bounds = CGRect(x: 0, y: font.descender, width: 20, height: 20)

// Center vertically against capHeight (a common visual match for inline icons).
let height = font.capHeight
let ratio = image.size.width / image.size.height
attachment.bounds = CGRect(
    x: 0,
    y: (font.capHeight - height) / 2,
    width: height * ratio,
    height: height
)
```

The image-only `.zero` default is fine for icons whose natural size already matches the line height, and wrong everywhere else — large product photos render at full pixel size and overflow the line. For predictable inline behavior, set `bounds` explicitly using font metrics.

## NSTextAttachmentViewProvider

A view provider is the TextKit 2-only path for inline content that isn't a static image — checkboxes, pickers, animated content, anything that wants to be a real `UIView` or `NSView`. The provider class is registered against a UTI; TextKit 2 instantiates it when an attachment with that UTI enters the viewport.

```swift
// Register once, ideally at app launch.
NSTextAttachment.registerViewProviderClass(
    CheckboxAttachmentViewProvider.self,
    forFileType: "com.example.checkbox"
)

class CheckboxAttachmentViewProvider: NSTextAttachmentViewProvider {
    override init(textAttachment: NSTextAttachment,
                  parentView: UIView?,
                  textLayoutManager: NSTextLayoutManager?,
                  location: NSTextLocation) {
        super.init(textAttachment: textAttachment,
                   parentView: parentView,
                   textLayoutManager: textLayoutManager,
                   location: location)
        // tracksTextAttachmentViewBounds must be set in init, not loadView.
        tracksTextAttachmentViewBounds = true
    }

    override func loadView() {
        let toggle = UISwitch()
        toggle.isOn = (textAttachment.contents?.first == 1)
        view = toggle
    }

    override func attachmentBounds(
        for attributes: [NSAttributedString.Key: Any],
        location: NSTextLocation,
        textContainer: NSTextContainer?,
        proposedLineFragment: CGRect,
        position: CGPoint
    ) -> CGRect {
        CGRect(x: 0, y: -4, width: 30, height: 30)
    }
}
```

Lifecycle to keep in mind: TextKit 2 creates a provider when the attachment scrolls into the viewport, calls `loadView()` to build the view, parents it under the text view's subview hierarchy, and may discard it when the attachment scrolls out. New providers are instantiated on re-entry; there is no UITableViewCell-style reuse.

The two failure modes that catch people: setting `tracksTextAttachmentViewBounds` inside `loadView()` (too late — it has to be in `init`), and TextKit 1 fallback. The instant a fallback trigger fires anywhere in the text view's lifetime, view providers stop being used for *every* attachment in the view, because TextKit 1 implements attachments via `NSTextAttachmentCellProtocol` instead. The fix is to keep the view in TextKit 2 mode; see `txt-fallback-triggers`.

## NSAdaptiveImageGlyph for Genmoji

`NSAdaptiveImageGlyph` (iOS 18+) is the carrier for Apple's Genmoji and sticker system. It differs from `NSTextAttachment` in three ways: sizing is automatic to match surrounding text, the image data carries multiple resolutions for Dynamic Type scaling, and insertion is driven by the emoji keyboard rather than programmatic code.

To accept Genmoji input in a UITextView, the view opts in:

```swift
textView.supportsAdaptiveImageGlyph = true
```

The user can now insert Genmoji from the emoji keyboard. The data lives in the attributed string under the `.adaptiveImageGlyph` attribute, with an `NSAdaptiveImageGlyph` value:

```swift
let full = NSRange(location: 0, length: attributedString.length)
attributedString.enumerateAttribute(.adaptiveImageGlyph, in: full) { value, range, _ in
    if let glyph = value as? NSAdaptiveImageGlyph {
        // glyph.contentDescription — accessibility label
        // glyph.contentIdentifier  — stable ID
        // glyph.imageContent       — multi-resolution data
        // glyph.contentType        — UTType
    }
}
```

`NSAdaptiveImageGlyph` is always square. For non-square inline content, fall back to `NSTextAttachment`. Genmoji also doesn't survive plain RTF — preserve via Codable `AttributedString` or RTFD-style document writing.

## Common Mistakes

1. **View-based attachments vanish, and the bug is "fallback."** Setting up an `NSTextAttachmentViewProvider` correctly and seeing the view never appear almost always means something elsewhere in the view's lifetime triggered TextKit 1 fallback — accessing `layoutManager`, querying `textContainer.layoutManager`, an old library injecting an `NSLayoutManagerDelegate`. Check `textView.textLayoutManager != nil` to confirm TextKit 2 is still active. The view provider machinery is fine; the host view isn't running it.

2. **`tracksTextAttachmentViewBounds = true` in `loadView()`.** Setting it after the view has been built is too late — the bounds tracking infrastructure is wired during init. The fix is to set it inside the `init(textAttachment:parentView:textLayoutManager:location:)` override, before `super.init` returns control to TextKit.

3. **Bounds y-coordinate read as UIKit coordinates.** `attachment.bounds.y = 0` sits on the baseline; positive y goes *up* (above the baseline), negative y goes *down*. An attachment that "renders too high" is usually a positive y intended as "down."

   ```swift
   // WRONG — pushes the icon above the line
   attachment.bounds = CGRect(x: 0, y: 4, width: 20, height: 20)

   // CORRECT — visually drops by the descender depth
   attachment.bounds = CGRect(x: 0, y: font.descender, width: 20, height: 20)
   ```

4. **macOS attachment with no image visible.** `init(data:ofType:)` on macOS leaves `attachmentCell` unset and renders nothing until one is assigned. Use `init(fileWrapper:)` or `init(image:)` (when targeting unified Foundation), or assign a cell explicitly.

5. **Copy/paste loses the image.** `NSTextAttachment.contents` must be non-nil for the attachment to survive serialization on the pasteboard. An attachment built from a `UIImage` directly carries no `contents` data — for paste fidelity, also set `attachment.contents = imageData` and `attachment.fileType = UTType.png.identifier`.

6. **Genmoji insertion does nothing.** The text view needs `supportsAdaptiveImageGlyph = true`. Without it, the emoji keyboard's Genmoji UI silently inserts nothing. The flag is an explicit opt-in — privacy-related, since Genmoji content can carry user-generated imagery.

7. **No accessibility label on a static image attachment.** VoiceOver reads U+FFFC as "object replacement character" by default. For meaningful announcements, set `attachment.image?.accessibilityLabel` (or build the attachment from an image with one) before constructing the attributed string.

## References

- `txt-attribute-keys` — `.attachment` and `.adaptiveImageGlyph` keys, value types, view compatibility
- `txt-fallback-triggers` — the full TextKit 1 fallback catalog; the cause of most lost view providers
- `txt-textkit2` — viewport, fragments, and how view providers are scheduled
- `references/protocols-and-patterns.md` — protocol signatures, insertion recipes, support matrices
- [NSTextAttachment](https://sosumi.ai/documentation/uikit/nstextattachment)
- [NSTextAttachmentViewProvider](https://sosumi.ai/documentation/uikit/nstextattachmentviewprovider)
- [NSAdaptiveImageGlyph](https://sosumi.ai/documentation/uikit/nsadaptiveimageglyph)
