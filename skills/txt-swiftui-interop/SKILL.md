---
name: txt-swiftui-interop
description: Determine which AttributedString attributes survive the SwiftUI/TextKit boundary, what SwiftUI Text actually renders vs silently ignores, and how AttributedString converts to and from NSAttributedString. Covers attribute scopes (FoundationAttributes, SwiftUIAttributes, UIKitAttributes, AppKitAttributes), the SwiftUI.Font vs UIFont mismatch, presentationIntent rendering gaps, scope-aware conversion, and inline image strategies. Use when an attribute set on AttributedString doesn't render in SwiftUI Text, when conversion to UITextView loses styling, when Markdown headings or lists don't appear, or when bridging shared text content between SwiftUI and a wrapped UITextView. Do NOT use for wrapping UITextView mechanics (txt-wrap-textview) or for the iOS 26 SwiftUI TextEditor APIs (txt-swiftui-texteditor).
license: MIT
---

# SwiftUI Text Bridging

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

The boundary between SwiftUI's text rendering and TextKit's is opinionated and often quiet about what it drops. The behaviors described here are the recurring rendering gaps; before concluding that an attribute is "broken," verify the actual `AttributedString` content (print it, or inspect the runs) and confirm the attribute is set in the scope you expect. Apple's autocomplete shows many attributes that look like they ought to work in SwiftUI `Text` but in fact do nothing at all — the question is always "which scope is this attribute in," not "is the API right."

A bridging bug usually traces to one of three things: the attribute is in `UIKitAttributes` and won't render in SwiftUI, the conversion to `NSAttributedString` was called without an explicit scope so custom attributes were dropped, or the content uses `presentationIntent` for block-level Markdown which neither SwiftUI `Text` nor `UITextView` renders automatically. Check the scope before changing the rendering layer.

## Contents

- [What SwiftUI Text renders](#what-swiftui-text-renders)
- [What SwiftUI Text silently ignores](#what-swiftui-text-silently-ignores)
- [Attribute scopes](#attribute-scopes)
- [SwiftUI.Font vs UIFont](#swiftuifont-vs-uifont)
- [Converting to NSAttributedString](#converting-to-nsattributedstring)
- [PresentationIntent: the block-level gap](#presentationintent-the-block-level-gap)
- [Inline images](#inline-images)
- [Common mistakes](#common-mistakes)
- [References](#references)

## What SwiftUI Text renders

These attributes on `AttributedString` render correctly in SwiftUI `Text`:

| Attribute | Notes |
|-----------|-------|
| `font` | SwiftUI.Font, not UIFont |
| `foregroundColor` | SwiftUI.Color |
| `backgroundColor` | SwiftUI.Color |
| `strikethroughStyle` | Style enum |
| `underlineStyle` | Style enum |
| `kern` | Letter spacing |
| `tracking` | Tracking |
| `baselineOffset` | Vertical offset |
| `link` | Tappable, uses accent color |

The set is intentionally small. SwiftUI `Text` is a layout primitive, not a rich-text renderer; complex paragraph-level features are not in scope.

## What SwiftUI Text silently ignores

These attributes exist on `AttributedString` (and Xcode autocompletes them on a SwiftUI binding), but `Text` does nothing with them:

| Attribute | Where it works |
|-----------|----------------|
| `paragraphStyle` | UITextView / NSTextView |
| `shadow` | UIKit/AppKit labels, TextKit |
| `strokeColor` / `strokeWidth` | UIKit/AppKit |
| `textEffect` | UIKit/AppKit |
| `attachment` (`NSTextAttachment`) | TextKit only |
| `writingDirection` | TextKit |
| `ligature` | TextKit |
| `obliqueness` | UIKit/AppKit |
| `expansion` | UIKit/AppKit |
| `presentationIntent` | Must be interpreted manually |

The compile passes. The runtime silently drops. The fix is almost always either to switch to a TextKit-backed view or to set the attribute in a scope SwiftUI does render (which usually means picking a SwiftUI-scope equivalent or restructuring the content into a SwiftUI view tree).

## Attribute scopes

Apple defines four attribute scopes:

| Scope | Contents | Used by |
|-------|----------|---------|
| `FoundationAttributes` | `link`, `presentationIntent`, `morphology`, `inlinePresentationIntent`, `languageIdentifier` | Both SwiftUI and UIKit/AppKit |
| `SwiftUIAttributes` | SwiftUI styling (Font, Color) plus Foundation | SwiftUI Text |
| `UIKitAttributes` | UIKit-specific (UIFont, paragraph styles, shadow) plus Foundation | UITextView, UILabel |
| `AppKitAttributes` | AppKit-specific (NSFont, NSParagraphStyle) plus Foundation | NSTextView |

A practical rule:

- Attributes in `FoundationAttributes` work everywhere, but the renderer decides whether to honor them.
- Attributes in `SwiftUIAttributes` are primarily for `Text`. They do not survive bridging to UITextView without translation.
- Attributes in `UIKitAttributes` / `AppKitAttributes` are for TextKit views and don't render in SwiftUI `Text`.

Attribute scope selection is more important than which attribute name you set. Set `str.foregroundColor = .red` and the type is inferred — SwiftUI scope by default. Set `str.uiKit.foregroundColor = .red` and the type is `UIColor`. Same name, different scope, different rendering paths. The scope is what determines whether your styling survives the boundary.

## SwiftUI.Font vs UIFont

The single most common bridging bug is treating `.font` as if it were `UIFont`:

```swift
var str = AttributedString("Hello")
str.font = .body                           // SwiftUI.Font
str.uiKit.font = .systemFont(ofSize: 16)   // UIFont — separate attribute

// Text(str) renders the SwiftUI font.
// UITextView reading NSAttributedString(str) sees the .uiKit.font.
// The two are independent.
```

When content is shared between a SwiftUI `Text` and a wrapped `UITextView`, set both scopes — or pick one renderer and stop trying to bridge. The runtime never converts between them.

For Dynamic Type, the SwiftUI side uses `.body`, `.title`, etc. The UIKit side uses `UIFont.preferredFont(forTextStyle: .body)`. Both update on Content Size Category change; they are not the same attribute.

## Converting to NSAttributedString

The AttributedString → NSAttributedString conversion is scope-aware and lossy by default. Use the explicit form:

```swift
// Best: pick the scope explicitly so custom attributes survive
let nsStr = try NSAttributedString(attrStr, including: \.uiKit)

// Default scope — drops custom attributes, may silently drop SwiftUI-only attributes
let nsStr = NSAttributedString(attrStr)
```

For content destined for a `UITextView`, set values in the `.uiKit` scope and convert with `including: \.uiKit`. For content destined for an `NSTextView`, use `.appKit`. For shared model layers, keep values in the Foundation scope and convert per renderer.

Inline-presentation Markdown (bold, italic, code, strikethrough, links) translates correctly:

- `**bold**` → bold font trait
- `*italic*` → italic font trait
- `` `code` `` → monospaced font
- `~~strike~~` → strikethrough
- `[label](url)` → link attribute

Block-level Markdown (headings, lists, blockquotes) goes into `presentationIntent` and is not auto-translated to paragraph styles. See the next section.

The biggest hidden cost is custom attributes. If you defined a custom `AttributedString` key without declaring a scope, it gets silently dropped during conversion. Always declare a scope on custom keys, and always pass `including:` matching that scope.

## PresentationIntent: the block-level gap

`AttributedString(markdown:options:)` with `.full` syntax parses block-level structure into `presentationIntent` runs:

```swift
let str = try AttributedString(
    markdown: "# Heading\n\n- Item 1\n\n> Quote",
    options: .init(interpretedSyntax: .full)
)

for run in str.runs {
    if let intent = run.presentationIntent {
        // intent.components: .header(level: 1), .unorderedList,
        // .listItem(ordinal:), .blockQuote, .paragraph, etc.
    }
}
```

Neither SwiftUI `Text` nor `UITextView` renders `presentationIntent` automatically. Three real options:

- **Render manually in SwiftUI.** Iterate runs, group by paragraph, emit `Text` views per heading/paragraph/list-item with the right font and spacing. A working but tedious path; gets the result fully native to SwiftUI.
- **Render via TextKit with NSParagraphStyle.** In a `UITextView`, walk the runs, translate each `presentationIntent` component to paragraph-style attributes (heading font, list indent, blockquote indent), and apply via `addAttribute(.paragraphStyle, …)`.
- **Use a third-party SwiftUI Markdown renderer.** Several libraries (MarkdownUI, swift-markdown-ui, etc.) walk the same structure and emit a SwiftUI view tree. Trade build complexity for not maintaining the renderer yourself.

For inline-only Markdown, none of this is needed — `Text(try AttributedString(markdown: "**bold**"))` works. The block-level gap matters only when content includes headings, lists, or quotes.

## Inline images

SwiftUI `Text` ignores `NSTextAttachment`. SwiftUI `TextEditor` (pre-iOS 26) only takes `String`. The iOS 26 rich-text `TextEditor` accepts `AttributedString` but still has no inline-image attribute. Two real workarounds.

**Display-only on iOS 18+:** insert transparent `Image(size:)` placeholders into the `Text`, tag each with a custom `TextAttribute`, and read the resolved layout via the `Text.LayoutKey` preference. Draw the real images at the resolved positions in a `Canvas` overlay. This stays inside SwiftUI — works with native layout, accessibility, and animations — but is read-only.

```swift
struct InlineImageAttribute: TextAttribute {
    let image: UIImage
}

// Build the text with placeholders that take the right space
var t = Text("")
for piece in pieces {
    switch piece {
    case .text(let s): t = t + Text(s)
    case .image(let img):
        let placeholder = Text(Image(size: img.size) { _ in })
            .customAttribute(InlineImageAttribute(image: img))
        t = t + placeholder
    }
}

// Read the resolved layout and draw real images on top via Canvas
content.overlayPreferenceValue(Text.LayoutKey.self) { layouts in
    Canvas { ctx, _ in
        for line in layouts {
            for run in line {
                guard let attr = run[InlineImageAttribute.self] else { continue }
                if let symbol = ctx.resolveSymbol(id: attr.image) {
                    ctx.draw(symbol, in: run.typographicBounds.rect)
                }
            }
        }
    } symbols: {
        ForEach(images, id: \.self) { Image(uiImage: $0).tag($0) }
    }
}
```

**Editable:** wrap a `UITextView` and use `NSTextAttachment`. This is the only path for editing around inline images on any iOS version. The wrapper takes care of the editing mechanics; the attachment carries the image and bounds.

```swift
func insertImage(_ image: UIImage, in tv: UITextView) {
    let att = NSTextAttachment()
    att.image = image
    let lineHeight = tv.font?.lineHeight ?? 20
    let ratio = image.size.width / max(image.size.height, 1)
    att.bounds = CGRect(x: 0, y: -4, width: lineHeight * ratio, height: lineHeight)

    let mutable = NSMutableAttributedString(attributedString: tv.attributedText)
    mutable.insert(NSAttributedString(attachment: att), at: tv.selectedRange.location)
    tv.attributedText = mutable
}
```

If editing isn't needed and iOS 18+ is acceptable, the placeholder-overlay technique is cleaner. Otherwise the wrapped `UITextView` is the path.

## Common mistakes

1. **Assuming SwiftUI Text renders all AttributedString attributes.** It renders about ten. The rest exist on the type, autocomplete in Xcode, and silently do nothing. If a `paragraphStyle`, `shadow`, or `strokeColor` doesn't appear, the code isn't broken — `Text` just doesn't honor those attributes. Either set the SwiftUI-equivalent modifier on `Text` (line spacing via `.lineSpacing`, etc.) or move the rendering to a TextKit-backed view.

2. **Setting `.font` to a SwiftUI.Font when the content goes to UITextView.** The SwiftUI scope's `font` is `SwiftUI.Font`, not `UIFont`. UITextView reads `NSAttributedString.Key.font`, which is `UIFont`. The two attributes coexist on `AttributedString` but never convert. Set `str.uiKit.font = UIFont.preferredFont(forTextStyle: .body)` for content destined for a UIKit view.

   ```swift
   // WRONG — lost in conversion to NSAttributedString
   str.font = .body
   textView.attributedText = NSAttributedString(str)

   // CORRECT — UIKit scope
   str.uiKit.font = .preferredFont(forTextStyle: .body)
   textView.attributedText = try NSAttributedString(str, including: \.uiKit)
   ```

3. **Expecting `presentationIntent` to render.** Block-level Markdown (headings, lists, blockquotes) lands in `presentationIntent` runs. Neither SwiftUI `Text` nor `UITextView` renders that automatically. Either parse the runs into a SwiftUI view tree, translate to paragraph styles for TextKit, or use a third-party Markdown renderer.

4. **Calling `NSAttributedString(attrStr)` without `including:`.** The default-scope conversion drops custom attributes that were declared in a non-default scope. Custom domain attributes — link styles, semantic markers, app-specific metadata — disappear. Always pass `including: \.myScope` (or `\.uiKit` / `\.appKit` for the framework scopes), and declare scopes on every custom attribute key.

5. **Using `.full` Markdown syntax and expecting visual rendering.** `.full` parses block-level structure but neither view auto-renders it. Either use `.inlineOnly` (the default) and don't expect blocks, or accept that you're parsing for structural data, not for ready-to-render output.

6. **Treating the attribute scope as decorative.** Scope determines which renderer honors the attribute. Setting `foregroundColor` on the SwiftUI scope and reading it in a `UITextView` produces invisible text. Pick the scope based on where the rendering happens, and when content is shared, set both scopes (or use the Foundation scope for renderer-agnostic content).

## References

- `/skill txt-wrap-textview` — wrapper mechanics around UITextView and NSTextView
- `/skill txt-attributed-string` — AttributedString vs NSAttributedString decision and conversion strategy
- `/skill txt-swiftui-texteditor` — iOS 26 SwiftUI TextEditor rich-text APIs
- `/skill txt-markdown` — Markdown rendering specifics
- [AttributedString](https://sosumi.ai/documentation/foundation/attributedstring)
- [NSAttributedString](https://sosumi.ai/documentation/foundation/nsattributedstring)
- [SwiftUI Text](https://sosumi.ai/documentation/swiftui/text)
- [NSTextAttachment](https://sosumi.ai/documentation/uikit/nstextattachment)
