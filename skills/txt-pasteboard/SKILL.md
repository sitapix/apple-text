---
name: txt-pasteboard
description: Customize copy, cut, and paste in text editors — UIPasteboard and NSPasteboard reads and writes, NSItemProvider type negotiation, format stripping and rich-text sanitization on paste, NSTextAttachment handling for pasted images, custom UTType identifiers for round-tripping app-specific formats. Use when paste brings unwanted fonts and colors, copies should write multiple representations, custom formats need to round-trip, pasted images should land as inline attachments, or programmatic paste is bypassing typing attributes. Trigger on 'paste brings in fonts/styles I don't want', 'copy with formatting', 'cmd-c isn't doing the right thing', or any clipboard-related editor question even without UIPasteboard mentioned. Do NOT use for drag-and-drop (see txt-drag-drop).
license: MIT
---

# Pasteboard Operations

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill covers the read and write side of the system pasteboard for text editors — `UIPasteboard` on iOS, `NSPasteboard` on macOS, and the `NSItemProvider` type-negotiation pattern that's used in modern paste paths and shared with drag-and-drop. Before claiming a specific UTType identifier or pasteboard read API signature, fetch via Sosumi (`sosumi.ai/documentation/uikit/uipasteboard`) — UTType-based APIs gradually replaced legacy string identifiers across iOS 14-17.

The most common bug is that pasted rich text picks up fonts and colors from the source app. The text view doesn't know which attributes are "presentation" vs "structure," so it preserves everything by default. Stripping is opt-in via a paste override.

## Contents

- [Default paste behavior](#default-paste-behavior)
- [Stripping or remapping rich-text formatting](#stripping-or-remapping-rich-text-formatting)
- [Pasted images as attachments](#pasted-images-as-attachments)
- [NSItemProvider type negotiation](#nsitemprovider-type-negotiation)
- [Custom copy with multiple representations](#custom-copy-with-multiple-representations)
- [macOS NSPasteboard differences](#macos-nspasteboard-differences)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Default paste behavior

`UITextView` and `NSTextView` already paste plaintext, rich text, and images without any code. The defaults:

- Plain text → inserted with the text view's `typingAttributes`.
- Rich text → inserted as the source attributed string, preserving fonts, colors, paragraph styles, and links.
- Images → wrapped in an `NSTextAttachment` and inserted at the caret.

Paste flows through the text view's edit pipeline, so undo, `processEditing`, and the `UITextViewDelegate` change methods all fire. The plaintext branch of `textView(_:shouldChangeTextIn:replacementText:)` is reached for the inserted string but only sees the unstyled text — the delegate has no view of the rich content. For full paste interception you override `paste(_:)` on the view or its responder.

## Stripping or remapping rich-text formatting

To force plaintext paste:

```swift
final class PlainPasteTextView: UITextView {
    override func paste(_ sender: Any?) {
        guard let s = UIPasteboard.general.string else { return }
        let r = selectedRange
        textStorage.beginEditing()
        textStorage.replaceCharacters(in: r, with: s)
        let inserted = NSRange(location: r.location, length: (s as NSString).length)
        textStorage.setAttributes(typingAttributes, range: inserted)
        textStorage.endEditing()
        selectedRange = NSRange(location: NSMaxRange(inserted), length: 0)
    }
}
```

The two non-obvious lines: applying `typingAttributes` to the inserted range, and updating `selectedRange` to land after the insertion. The user-paste path does both automatically; the programmatic path doesn't.

For selective sanitization — keep bold and italic, drop everything else — walk the source attributed string and rebuild it on top of your default attributes:

```swift
func sanitize(_ source: NSAttributedString) -> NSAttributedString {
    let result = NSMutableAttributedString(string: source.string)
    let full = NSRange(location: 0, length: result.length)
    result.setAttributes(defaultAttributes, range: full)

    source.enumerateAttributes(in: full, options: []) { attrs, range, _ in
        if let f = attrs[.font] as? UIFont {
            let traits = f.fontDescriptor.symbolicTraits
            if traits.contains(.traitBold)   { result.addAttribute(.font, value: boldFont,   range: range) }
            if traits.contains(.traitItalic) { result.addAttribute(.font, value: italicFont, range: range) }
        }
        if let link = attrs[.link] {
            result.addAttribute(.link, value: link, range: range)
        }
    }
    return result
}
```

Source fonts that don't exist on the device get substituted, and the substitution is often visually wrong (line height, weight, metrics). Always remap fonts on paste rather than passing the source font through.

## Pasted images as attachments

```swift
override func paste(_ sender: Any?) {
    let pb = UIPasteboard.general
    if pb.hasImages, let image = pb.image {
        insertImageAttachment(image)
    } else {
        super.paste(sender)
    }
}

func insertImageAttachment(_ image: UIImage) {
    let att = NSTextAttachment()
    att.image = image
    let maxW = textContainer.size.width - textContainer.lineFragmentPadding * 2
    if image.size.width > maxW {
        let scale = maxW / image.size.width
        att.bounds = CGRect(origin: .zero,
                            size: CGSize(width: image.size.width * scale,
                                         height: image.size.height * scale))
    }
    textStorage.insert(NSAttributedString(attachment: att),
                       at: selectedRange.location)
}
```

Without the explicit `bounds` setting, large images render at intrinsic size and overflow the container. `lineFragmentPadding` defaults to 5 on each side; subtract twice that from the container width.

## NSItemProvider type negotiation

Modern paste, drag, and the share sheet all flow through `NSItemProvider`. The contract is: ask the provider what types it conforms to, request the highest-fidelity one, and dispatch to main when the data arrives.

```swift
func handle(providers: [NSItemProvider]) {
    for p in providers {
        if p.hasItemConformingToTypeIdentifier(UTType.image.identifier) {
            p.loadDataRepresentation(forTypeIdentifier: UTType.image.identifier) { data, _ in
                guard let data, let img = UIImage(data: data) else { return }
                Task { @MainActor in self.insertImageAttachment(img) }
            }
        } else if p.hasItemConformingToTypeIdentifier(UTType.attributedString.identifier) {
            _ = p.loadObject(ofClass: NSAttributedString.self) { obj, _ in
                guard let attr = obj as? NSAttributedString else { return }
                Task { @MainActor in self.insert(self.sanitize(attr)) }
            }
        } else if p.hasItemConformingToTypeIdentifier(UTType.plainText.identifier) {
            _ = p.loadObject(ofClass: NSString.self) { obj, _ in
                guard let s = obj as? String else { return }
                Task { @MainActor in self.insertPlain(s) }
            }
        }
    }
}
```

Two recurring traps. The completion handlers run on arbitrary threads; touching text storage from there crashes intermittently. And the order of the type checks matters — check the highest-fidelity type your editor handles first, falling back to plaintext last. If you check plaintext first, you drop the rich content even when it was available.

## Custom copy with multiple representations

Writing one item with multiple type identifiers gives downstream apps a choice. Your own app can recognize a private UTType for lossless round-trips, while other apps fall back to RTF or plaintext.

```swift
override func copy(_ sender: Any?) {
    guard selectedRange.length > 0 else { return }
    let attr = textStorage.attributedSubstring(from: selectedRange)
    let pb = UIPasteboard.general

    var item: [String: Any] = [:]
    item[UTType.plainText.identifier] = attr.string

    if let rtf = try? attr.data(
        from: NSRange(location: 0, length: attr.length),
        documentAttributes: [.documentType: NSAttributedString.DocumentType.rtf]
    ) {
        item[UTType.rtf.identifier] = rtf
    }

    if let custom = encodeAppFormat(attr) {
        item["com.example.myapp.richtext"] = custom
    }

    pb.items = [item]
}
```

When pasting back, prefer the private format first, then RTF, then plaintext:

```swift
override func paste(_ sender: Any?) {
    let pb = UIPasteboard.general
    if let data = pb.data(forPasteboardType: "com.example.myapp.richtext") {
        insert(decodeAppFormat(data))
    } else if let rtf = pb.data(forPasteboardType: UTType.rtf.identifier),
              let attr = try? NSAttributedString(
                data: rtf,
                options: [.documentType: NSAttributedString.DocumentType.rtf],
                documentAttributes: nil) {
        insert(sanitize(attr))
    } else {
        super.paste(sender)
    }
}
```

Custom UTType identifiers that round-trip across launches or devices need a declaration in `Info.plist` under `UTExportedTypeDeclarations`. Without it, the pasteboard accepts the data but other processes can't discover what it is.

## macOS NSPasteboard differences

`NSPasteboard` is named (`general`, `find`, `font`, `ruler`, `drag`) instead of singleton. The general pasteboard mirrors `UIPasteboard.general`, but macOS apps frequently use the find pasteboard to share search strings across apps:

```swift
let pb = NSPasteboard.general
pb.clearContents()
pb.declareTypes([.string, .rtf], owner: nil)
pb.setString(plain, forType: .string)
pb.setData(rtfData, forType: .rtf)
```

Reading is symmetric:

```swift
if let attr = pb.readObjects(forClasses: [NSAttributedString.self], options: nil)?.first
   as? NSAttributedString { ... }
```

`NSTextView` exposes `readSelectionFromPasteboard(_:type:)` and `writeSelection(to:type:)` for fine-grained control over which type to read or write at a given moment.

## Common Mistakes

1. **Source-app fonts pass through paste and look wrong.** Remap fonts on paste; the source font may not be installed and the substitution is rarely correct. Build a sanitizer that derives bold/italic from symbolic traits and re-applies your own font.

2. **Programmatic paste skips `typingAttributes`.** When you bypass `paste(_:)` and write directly to text storage, you have to apply `typingAttributes` to the inserted range and move `selectedRange` past the insertion yourself. The user-paste path does both.

3. **`textView(_:shouldChangeTextIn:replacementText:)` overridden, expecting full paste control.** That delegate sees plaintext only, even when the actual paste is rich. For real paste interception override `paste(_:)`.

4. **NSItemProvider callbacks touching text storage on a background thread.** They run on arbitrary threads. Hop to main before mutating storage.

5. **Type-identifier checks in the wrong order.** Plaintext is the universal fallback — check it last. If you check it first, you drop rich content that was available.

6. **Custom UTType not declared in Info.plist.** Round-trips work in your own app but fail across processes. Declare under `UTExportedTypeDeclarations`.

7. **Paste path bypassing `beginEditing`/`endEditing`.** Each individual `replaceCharacters` triggers its own `processEditing` cycle, which fires the change delegate multiple times and breaks undo grouping. Wrap a multi-step paste in begin/end.

8. **Reading `UIPasteboard.general.string` after the user dismissed a permission prompt with "Don't Allow."** iOS 14+ prompts on first read per launch in some contexts; the property returns `nil` if denied. Either use the system Paste button (`UIPasteControl`) which doesn't prompt, or check `pb.hasStrings` before reading.

## References

- `txt-drag-drop` — the drag/drop side of the same `NSItemProvider` type negotiation
- `txt-attachments` — sizing, baseline, and view providers for `NSTextAttachment`
- `txt-attributed-string` — converting between attributed string formats
- `txt-undo` — undo registration around custom paste implementations
- [UIPasteboard](https://sosumi.ai/documentation/uikit/uipasteboard)
- [NSPasteboard](https://sosumi.ai/documentation/appkit/nspasteboard)
