---
name: apple-text-swiftui-bridging
description: Use when wondering if a Foundation text type works with SwiftUI Text, whether UITextView can use SwiftUI-oriented types, how to bridge AttributedString between SwiftUI and TextKit, what attributes SwiftUI Text supports vs ignores, or deciding between SwiftUI Text and TextKit for rich text display
license: MIT
---

# SwiftUI Text Bridging

Use this skill when the main question is what SwiftUI text can render, what converts cleanly, and where framework boundaries drop information.

## When to Use

- You are asking whether a Foundation text type or attribute works in SwiftUI.
- You need to know what `AttributedString` loses when bridged.
- The problem is rendering/type boundaries, not wrapper lifecycle.

## Quick Decision

- Need wrapper mechanics around `UITextView` / `NSTextView` -> `/skill apple-text-representable`
- Need to know what SwiftUI `Text` renders or ignores -> stay here
- Need attributed-text type choice itself -> `/skill apple-text-attributed-string`

## Core Guidance

## What SwiftUI Text Actually Renders

SwiftUI `Text` renders these `AttributedString` attributes:

| Attribute | Works in SwiftUI Text? |
|-----------|----------------------|
| `font` | ✅ |
| `foregroundColor` | ✅ |
| `backgroundColor` | ✅ |
| `strikethroughStyle` | ✅ |
| `underlineStyle` | ✅ |
| `kern` | ✅ |
| `tracking` | ✅ |
| `baselineOffset` | ✅ |
| `link` | ✅ (tappable, uses accent color) |

### What SwiftUI Text Silently Ignores

These attributes exist on `AttributedString` but Text **does nothing** with them:

| Attribute | Ignored? | Where It Works Instead |
|-----------|----------|----------------------|
| `paragraphStyle` | ❌ Ignored | UITextView / NSTextView |
| `shadow` | ❌ Ignored | UIKit/AppKit labels, TextKit |
| `strokeColor` / `strokeWidth` | ❌ Ignored | UIKit/AppKit |
| `textEffect` | ❌ Ignored | UIKit/AppKit |
| `attachment` (NSTextAttachment) | ❌ Ignored | TextKit only |
| `writingDirection` | ❌ Ignored | TextKit |
| `ligature` | ❌ Ignored | TextKit |
| `obliqueness` | ❌ Ignored | UIKit/AppKit |
| `expansion` | ❌ Ignored | UIKit/AppKit |
| `presentationIntent` | ❌ Ignored | Must interpret manually |

**Key insight:** Xcode autocomplete shows many attributes that "look like they ought to work but in fact do nothing at all" in SwiftUI Text.

## How to Know If Something Is "For SwiftUI"

### Attribute Scopes Tell You

Apple defines separate attribute scopes:

| Scope | Contains | Used By |
|-------|----------|---------|
| `FoundationAttributes` | `link`, `presentationIntent`, `morphology`, `inlinePresentationIntent` | Both SwiftUI and UIKit/AppKit |
| `SwiftUIAttributes` | SwiftUI-specific styling + Foundation | SwiftUI Text |
| `UIKitAttributes` | UIKit-specific (`UIFont`, paragraph styles) | UITextView, UILabel |
| `AppKitAttributes` | AppKit-specific (`NSFont`, etc.) | NSTextView |

**Rule of thumb:**
- If it's in `FoundationAttributes` → works everywhere (but may render differently)
- If it's in `SwiftUIAttributes` → primarily for SwiftUI Text
- If it's in `UIKitAttributes` / `AppKitAttributes` → for TextKit views

### SwiftUI.Font Is NOT UIFont/NSFont

This is the biggest gotcha:

```swift
var str = AttributedString("Hello")
str.font = .body           // This is SwiftUI.Font
str.uiKit.font = UIFont.systemFont(ofSize: 16)  // This is UIFont

// SwiftUI Text uses SwiftUI.Font
// UITextView needs UIFont
// They are DIFFERENT types
```

## Can UITextView Use SwiftUI-Oriented Things?

**Yes — with conversion.** The key bridge is `AttributedString` ↔ `NSAttributedString`.

### What Converts Cleanly

```swift
// Create with Foundation/inline Markdown
var attrStr = try AttributedString(markdown: "**Bold** and *italic* and `code`")

// Convert for UITextView
let nsAttrStr = NSAttributedString(attrStr)
textView.attributedText = nsAttrStr
```

Inline presentation intents (bold, italic, code, strikethrough) convert to their NSAttributedString equivalents:
- `**bold**` → bold font trait
- `*italic*` → italic font trait
- `` `code` `` → monospaced font
- `~~strike~~` → strikethrough attribute
- `[link](url)` → link attribute

### What Gets Lost in Conversion

| Lost/Changed | Why | Workaround |
|-------------|-----|-----------|
| `SwiftUI.Font` → nothing | Not a UIFont. Different type system | Set `.uiKit.font` explicitly |
| `presentationIntent` → preserved but not rendered | UITextView doesn't interpret it | Parse PresentationIntent manually and apply paragraph styles |
| Custom attributes without scope | Dropped silently | Always use `including: \.myScope` |
| SwiftUI-scope-only attributes | No UIKit equivalent | Map manually |

### Conversion Pattern

```swift
// ✅ Best practice: Use UIKit scope for content destined for UITextView
var str = AttributedString("Hello World")
str.uiKit.font = UIFont.systemFont(ofSize: 16)     // UIFont, not SwiftUI.Font
str.uiKit.foregroundColor = UIColor.label           // UIColor, not SwiftUI.Color
str.uiKit.paragraphStyle = myParagraphStyle         // Works in UITextView

let nsStr = try NSAttributedString(str, including: \.uiKit)
textView.attributedText = nsStr
```

```swift
// ❌ Problematic: Using SwiftUI scope for UITextView content
var str = AttributedString("Hello World")
str.font = .body                          // SwiftUI.Font — lost in conversion
str.foregroundColor = .primary             // SwiftUI.Color — may not convert
```

## Bridging Pros and Cons

### Pros of Using AttributedString → NSAttributedString Bridge

- **Apple's Markdown parser** — Built-in, well-tested, type-safe
- **Codable** — AttributedString serializes to JSON/plist
- **Type-safe attributes** — Compile-time checking with key paths
- **Custom Markdown attributes** — `MarkdownDecodableAttributedStringKey` for extensibility
- **Single parsing, multiple rendering** — Parse once, convert for SwiftUI or UIKit as needed

### Cons of Bridging

- **Font type mismatch** — `SwiftUI.Font` ≠ `UIFont`/`NSFont`, requires manual mapping
- **PresentationIntent is data, not rendering** — Block-level Markdown (headings, lists, quotes) parsed into `presentationIntent` but no view renders it automatically
- **Two mental models** — AttributedString (value type, key paths) vs NSAttributedString (reference type, string keys)
- **Scope management** — Easy to silently lose attributes if you forget `including:`
- **Layout coordination** — UIViewRepresentable/NSViewRepresentable wrapping adds complexity
- **Performance** — Conversion has overhead; avoid in tight loops

## PresentationIntent: The Block-Level Gap

When Markdown is parsed with `.full` syntax, block-level structure lands in `presentationIntent`:

```swift
let str = try AttributedString(
    markdown: "# Heading\n\n- Item 1\n- Item 2\n\n> Quote",
    options: .init(interpretedSyntax: .full)
)

for run in str.runs {
    if let intent = run.presentationIntent {
        // intent.components contains:
        // .header(level: 1), .unorderedList, .listItem(ordinal:), .blockQuote
    }
}
```

**SwiftUI Text ignores `presentationIntent` entirely.** To render block-level Markdown visually:

1. **Third-party library** — MarkdownUI by gonzalezreal renders full Markdown in SwiftUI
2. **Manual interpretation** — Iterate runs, apply paragraph styles for headings/lists/quotes
3. **TextKit rendering** — Use UITextView/NSTextView with manually-applied NSParagraphStyle

## Decision: SwiftUI Text vs TextKit View

```
Need editable text?
    YES → UITextView / NSTextView (TextKit)
    NO → How rich is the formatting?
        Inline only (bold, italic, links)?
            → SwiftUI Text with AttributedString or Markdown literals
        Block-level (headings, lists, tables, code blocks)?
            → TextKit view or MarkdownUI library
        Paragraph styles (line spacing, indentation)?
            → TextKit view (SwiftUI Text ignores paragraphStyle)
        Custom rendering (syntax highlighting, chat bubbles)?
            → TextKit view with custom layout fragments
        Simple styled text?
            → SwiftUI Text
```

## Cross-Framework AttributedString Usage Pattern

```swift
// Shared model layer — use Foundation scope
struct Message {
    var content: AttributedString  // Foundation AttributedString
}

// SwiftUI rendering
struct MessageView: View {
    let message: Message
    var body: some View {
        Text(message.content)  // Renders supported attributes
    }
}

// UIKit rendering (e.g., in UITextView)
class MessageCell: UITableViewCell {
    func configure(with message: Message) {
        // Convert with UIKit scope
        let nsStr = NSAttributedString(message.content)
        textView.attributedText = nsStr
    }
}
```

## Inline Images: Workarounds

SwiftUI `Text` ignores `NSTextAttachment` and has no native inline image support. SwiftUI `TextEditor` only binds to plain `String`. Two workarounds exist depending on whether editing is needed.

### Display-Only: Placeholder-Overlay Technique (iOS 18+)

Pure SwiftUI approach — no UIKit bridging for rendering. Works with `Text`, not `TextEditor`.

**How it works:**

1. For each image in the attributed string, insert a transparent, correctly-sized `SwiftUI.Image` placeholder that reserves space in the text flow:

```swift
// Create an invisible image that takes up the right amount of space
Text(Image(size: CGSize(width: 80, height: 80)) { _ in })
```

2. Tag each placeholder with a custom `TextAttribute` carrying the attachment identity:

```swift
struct InlineImageAttribute: TextAttribute {
    let image: UIImage  // or URL, or any identifier
}

// Apply to the placeholder run
text = text.customAttribute(InlineImageAttribute(image: loadedImage))
```

3. After SwiftUI performs layout, read the resolved `Text.Layout` via the `Text.LayoutKey` preference to discover where each placeholder landed:

```swift
content.overlayPreferenceValue(Text.LayoutKey.self) { layouts in
    if let layout = layouts.first {
        GeometryReader { geometry in
            ImageOverlayView(layout: layout.layout, origin: geometry[layout.origin])
        }
    }
}
```

4. Draw the real images at those positions using a `Canvas` overlay with resolved symbols:

```swift
Canvas { context, _ in
    for line in layout {
        for run in line {
            guard let attr = run[InlineImageAttribute.self],
                  let symbol = context.resolveSymbol(id: attr.image)
            else { continue }
            context.draw(symbol, in: run.typographicBounds.rect)
        }
    }
} symbols: {
    ForEach(images, id: \.self) { img in
        Image(uiImage: img).resizable().tag(img)
    }
}
```

**Requirements:** iOS 18+ / macOS 15+ for `Text.LayoutKey`, `Text.Layout.Run` custom attribute subscripts, and `Image(size:)`.

**Tradeoffs:**
- Pure SwiftUI — works with native text layout, accessibility, animation
- Read-only — no editing, cursor, or text input
- Pair with a write/preview split for editing workflows (TextEditor for raw markdown, this technique for rendered preview)

### Editable: UITextView + NSTextAttachment (via UIViewRepresentable)

For true inline images in an editable text view, bridge to UIKit.

```swift
struct RichTextEditor: UIViewRepresentable {
    @Binding var attributedText: NSAttributedString

    func makeUIView(context: Context) -> UITextView {
        let textView = UITextView()
        textView.delegate = context.coordinator
        textView.allowsEditingTextAttributes = true
        return textView
    }

    func updateUIView(_ uiView: UITextView, context: Context) {
        if uiView.attributedText != attributedText {
            let selection = uiView.selectedRange
            uiView.attributedText = attributedText
            if selection.location + selection.length <= uiView.attributedText.length {
                uiView.selectedRange = selection
            }
        }
    }

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    class Coordinator: NSObject, UITextViewDelegate {
        var parent: RichTextEditor
        init(_ parent: RichTextEditor) { self.parent = parent }
        func textViewDidChange(_ textView: UITextView) {
            parent.attributedText = textView.attributedText
        }
    }
}
```

Insert an image at the cursor:

```swift
func insertImage(_ image: UIImage, in textView: UITextView) {
    let attachment = NSTextAttachment()
    attachment.image = image

    // Size to fit text line height, or a fixed size
    let lineHeight = textView.font?.lineHeight ?? 20
    let ratio = image.size.width / image.size.height
    attachment.bounds = CGRect(x: 0, y: -4, width: lineHeight * ratio, height: lineHeight)

    let attachmentString = NSAttributedString(attachment: attachment)
    let mutable = NSMutableAttributedString(attributedString: textView.attributedText)
    mutable.insert(attachmentString, at: textView.selectedRange.location)
    textView.attributedText = mutable
}
```

**Tradeoffs:**
- Full editing support — cursor, selection, typing around images
- Requires UIKit bridging and `NSAttributedString` (not Foundation `AttributedString`)
- No native SwiftUI state management — must sync via coordinator
- macOS equivalent uses `NSTextView` + `NSViewRepresentable`

### Which to Use

```
Need the user to type/edit around the images?
    YES → UITextView + NSTextAttachment (UIViewRepresentable)
    NO  → Is iOS 18+ acceptable?
        YES → Placeholder-overlay with Text + Text.LayoutKey
        NO  → UITextView + NSTextAttachment (read-only mode), or
              WebView rendering as fallback
```

## Common Pitfalls

1. **Assuming SwiftUI Text renders all AttributedString attributes** — It renders about 10. Most are ignored silently.
2. **Using SwiftUI.Font in content for UITextView** — Wrong font type. Use `.uiKit.font` with UIFont.
3. **Expecting PresentationIntent to render** — No view renders it automatically. Parse and apply styles manually.
4. **Forgetting scope in conversion** — `NSAttributedString(attrStr)` without `including:` drops custom attributes.
5. **Using `.full` Markdown syntax and expecting visual rendering** — Only inline formatting renders. Block-level is stored in `presentationIntent` and ignored by both SwiftUI Text and UITextView.

## Related Skills

- Use `/skill apple-text-representable` for wrapper mechanics and coordinator issues.
- Use `/skill apple-text-attributed-string` for type-model and conversion strategy.
- Use `/skill apple-text-markdown` when `PresentationIntent` and Markdown parsing are the real drivers.
