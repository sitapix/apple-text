---
name: platform-reference
description: Look up SwiftUI bridging, UIViewRepresentable wrappers, TextEditor iOS 26+, AppKit vs UIKit differences, TextKit 1 vs 2 selection, Core Text, Foundation text utilities, and parsing.
model: sonnet
tools:
  - Glob
  - Grep
  - Read
---

# Platform Reference Agent

You answer specific questions about platform choices, SwiftUI bridging, and low-level text utilities.

## Instructions

1. Read the user's question carefully.
2. Find the relevant section in the reference material below.
3. Return ONLY the information that answers their question — maximum 40 lines.
4. Include exact API signatures, code examples, and gotchas when relevant.
5. Do NOT dump all reference material — extract what is relevant.
6. For "which view should I use" questions, start with the view selection guidance.

---

# UIViewRepresentable / NSViewRepresentable for Text Views

Use this skill when the main question is how to wrap UIKit/AppKit text views inside SwiftUI without breaking editing behavior.

## When to Use

- You are building `UIViewRepresentable` or `NSViewRepresentable` wrappers around text views.
- You need coordinator, focus, sizing, or cursor-preservation patterns.
- The problem is wrapper mechanics, not whether SwiftUI `Text` renders a type.

## Quick Decision

- Plain SwiftUI editing is enough -> avoid wrapping and stay native
- Need TextKit APIs, rich text, syntax highlighting, or attachments -> wrap `UITextView` / `NSTextView`
- Need cross-framework type/rendering limits instead of wrapper mechanics -> the swiftui bridging section in this reference

## Core Guidance

## When You Need This

```
Need rich text editing in SwiftUI?
    iOS 26+ → TextEditor with AttributedString (try this first)
    iOS 14-25 → UIViewRepresentable wrapping UITextView

Need syntax highlighting?
    → UIViewRepresentable wrapping UITextView with TextKit 2

Need TextKit API access (layout queries, custom rendering)?
    → UIViewRepresentable wrapping UITextView

Need paragraph styles, text attachments, inline images?
    → UIViewRepresentable wrapping UITextView

Just need plain multi-line text editing?
    → SwiftUI TextEditor (no bridge needed)

Just need an expanding text input?
    → TextField(axis: .vertical) with .lineLimit (iOS 16+)
```

## UIViewRepresentable Pattern (iOS)

### Complete Working Example

```swift
struct RichTextView: UIViewRepresentable {
    @Binding var text: NSAttributedString
    var uiFont: UIFont = .preferredFont(forTextStyle: .body)
    var textColor: UIColor = .label

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    func makeUIView(context: Context) -> UITextView {
        let textView = UITextView()
        textView.delegate = context.coordinator
        textView.isEditable = true
        textView.isSelectable = true
        textView.font = uiFont
        textView.textColor = textColor
        textView.backgroundColor = .clear  // Let SwiftUI backgrounds show
        textView.textContainerInset = UIEdgeInsets(top: 8, left: 4, bottom: 8, right: 4)
        return textView
    }

    func updateUIView(_ uiView: UITextView, context: Context) {
        // CRITICAL: Update coordinator's parent reference for fresh bindings
        context.coordinator.parent = self

        // Only update if text actually changed (prevents cursor jump + infinite loop)
        if uiView.attributedText != text {
            let savedRange = uiView.selectedRange
            uiView.attributedText = text
            // Restore selection if still valid
            let maxLoc = (uiView.text as NSString).length
            if savedRange.location <= maxLoc {
                uiView.selectedRange = NSRange(
                    location: min(savedRange.location, maxLoc),
                    length: min(savedRange.length, maxLoc - min(savedRange.location, maxLoc))
                )
            }
        }

        // React to environment changes
        uiView.isEditable = context.environment.isEnabled
    }

    // iOS 16+: Proper auto-sizing
    @available(iOS 16.0, *)
    func sizeThatFits(_ proposal: ProposedViewSize, uiView: UITextView, context: Context) -> CGSize? {
        guard let width = proposal.width else { return nil }
        uiView.isScrollEnabled = false
        let size = uiView.sizeThatFits(CGSize(width: width, height: .greatestFiniteMagnitude))
        return CGSize(width: width, height: size.height)
    }

    class Coordinator: NSObject, UITextViewDelegate {
        var parent: RichTextView

        init(_ parent: RichTextView) {
            self.parent = parent
        }

        func textViewDidChange(_ textView: UITextView) {
            DispatchQueue.main.async {
                self.parent.text = textView.attributedText
            }
        }
    }
}
```

### Key Rules

1. **Always update `context.coordinator.parent = self`** at the top of `updateUIView`. The coordinator stores a copy of the struct — without this, delegate callbacks use stale bindings.

2. **Guard against unnecessary updates** in `updateUIView`. Check `uiView.text != text` before setting. Otherwise: infinite loop (user types → binding updates → updateUIView sets text → triggers textViewDidChange → repeat).

3. **Use `DispatchQueue.main.async`** in delegate callbacks to avoid "Modifying state during view update" warnings. If you async one state update, async ALL related updates to maintain ordering.

4. **Save/restore `selectedRange`** when setting text programmatically — UIKit resets cursor to end.

5. **Accept `UIFont`/`UIColor`, not `Font`/`Color`** — SwiftUI types have no public conversion to UIKit types.

## NSViewRepresentable Pattern (macOS)

### Key Difference: NSScrollView Wrapping

```swift
struct MacTextView: NSViewRepresentable {
    @Binding var text: NSAttributedString

    func makeNSView(context: Context) -> NSScrollView {
        let scrollView = NSTextView.scrollableTextView()
        let textView = scrollView.documentView as! NSTextView

        textView.delegate = context.coordinator
        textView.isEditable = true
        textView.isRichText = true
        textView.allowsUndo = true
        textView.isVerticallyResizable = true
        textView.isHorizontallyResizable = false
        textView.autoresizingMask = [.width]
        textView.textContainer?.widthTracksTextView = true

        return scrollView
    }

    func updateNSView(_ nsView: NSScrollView, context: Context) {
        guard let textView = nsView.documentView as? NSTextView else { return }
        context.coordinator.parent = self

        if textView.attributedString() != text {
            let savedRanges = textView.selectedRanges
            textView.textStorage?.setAttributedString(text)
            textView.selectedRanges = savedRanges
        }
    }

    class Coordinator: NSObject, NSTextViewDelegate {
        var parent: MacTextView
        init(_ parent: MacTextView) { self.parent = parent }

        func textDidChange(_ notification: Notification) {
            guard let textView = notification.object as? NSTextView else { return }
            DispatchQueue.main.async {
                self.parent.text = textView.attributedString()
            }
        }
    }
}
```

### iOS vs macOS Differences

| Aspect | UIViewRepresentable | NSViewRepresentable |
|--------|-------------------|-------------------|
| **NSViewType** | `UITextView` directly | `NSScrollView` (NSTextView inside) |
| **Scrolling** | Built-in (UITextView IS UIScrollView) | Must wrap in NSScrollView |
| **Attributed text** | `.attributedText` property | `.attributedString()` method |
| **Set text** | `.attributedText = x` | `.textStorage?.setAttributedString(x)` |
| **Selection** | `.selectedRange` (NSRange) | `.selectedRanges` ([NSValue]) |
| **Delegate** | `UITextViewDelegate` | `NSTextViewDelegate` |
| **Text change** | `textViewDidChange(_:)` | `textDidChange(_:)` (Notification) |
| **intrinsicContentSize** | ❌ Invalidation ignored (FB8499811) | ✅ Re-queried correctly |

## Auto-Sizing (Expanding Text View)

### iOS 16+: `sizeThatFits` (Recommended)

```swift
func sizeThatFits(_ proposal: ProposedViewSize, uiView: UITextView, context: Context) -> CGSize? {
    guard let width = proposal.width else { return nil }
    uiView.isScrollEnabled = false
    return uiView.sizeThatFits(CGSize(width: width, height: .greatestFiniteMagnitude))
}
```

### iOS 13-15: Height Tracking

```swift
@State private var height: CGFloat = 40

WrappedTextView(text: $text, height: $height)
    .frame(height: height)

// In Coordinator:
func textViewDidChange(_ textView: UITextView) {
    DispatchQueue.main.async {
        let newHeight = max(textView.contentSize.height, 40)
        if self.parent.height != newHeight {
            self.parent.height = newHeight
        }
    }
}
```

### The `isScrollEnabled = false` Problem

Setting `isScrollEnabled = false` should make UITextView report `intrinsicContentSize`. **However:**
- `UIViewRepresentable` ignores `invalidateIntrinsicContentSize()` (Apple-confirmed bug: FB8499811)
- The intrinsic size may not account for line wrapping
- Use `sizeThatFits` (iOS 16+) or explicit height tracking instead

## Focus / First Responder Bridging

`@FocusState` does not bridge to `UIViewRepresentable`. Manual bridging required:

```swift
struct FocusableTextView: UIViewRepresentable {
    @Binding var isFocused: Bool

    func updateUIView(_ uiView: UITextView, context: Context) {
        if isFocused && !uiView.isFirstResponder {
            DispatchQueue.main.async { uiView.becomeFirstResponder() }
        } else if !isFocused && uiView.isFirstResponder {
            DispatchQueue.main.async { uiView.resignFirstResponder() }
        }
    }

    // In Coordinator:
    func textViewDidBeginEditing(_ textView: UITextView) {
        DispatchQueue.main.async { self.parent.isFocused = true }
    }
    func textViewDidEndEditing(_ textView: UITextView) {
        DispatchQueue.main.async { self.parent.isFocused = false }
    }
}
```

**Use `DispatchQueue.main.async` for `becomeFirstResponder()`** — calling synchronously in `updateUIView` can fail if the view isn't in the window hierarchy yet.

## Rendering Layer

### Where UITextView Renders

```
SwiftUI render tree
    → _UIHostingView (root UIView)
        → ... (SwiftUI internal views)
            → Container UIView (created by UIViewRepresentable)
                → UITextView (your view)
                    → CALayer (backed by Core Animation)
                        → TextKit renders glyphs into layer
```

- **No extra compositing layer** for the bridge — UITextView's CALayer is in the normal layer tree
- **Minimal overhead** from UIViewRepresentable — main cost is `updateUIView` calls on state changes
- TextKit renders through Core Text → Core Graphics → CALayer backing store

### SwiftUI Integration

- `.overlay()` and `.background()` work normally on the representable
- Set `textView.backgroundColor = .clear` for SwiftUI backgrounds to show through
- Z-ordering follows normal SwiftUI rules (declaration order, `.zIndex()`)
- `.clipped()` prevents UIKit content from bleeding outside the SwiftUI frame

## Toolbar Integration

### Pattern A: SwiftUI Keyboard Toolbar (iOS 15+)

```swift
WrappedTextView(text: $text)
    .toolbar {
        ToolbarItemGroup(placement: .keyboard) {
            Button(action: toggleBold) {
                Image(systemName: "bold")
            }
            Button(action: toggleItalic) {
                Image(systemName: "italic")
            }
            Spacer()
            Button("Done") { focusedField = nil }
        }
    }
```

### Pattern B: UIKit inputAccessoryView

```swift
func makeUIView(context: Context) -> UITextView {
    let tv = UITextView()
    let toolbar = UIToolbar()
    toolbar.items = [
        UIBarButtonItem(image: UIImage(systemName: "bold"), style: .plain,
                       target: context.coordinator, action: #selector(Coordinator.toggleBold)),
    ]
    toolbar.sizeToFit()
    tv.inputAccessoryView = toolbar
    return tv
}
```

### Pattern C: ObservableObject Shared State

```swift
class TextFormatContext: ObservableObject {
    @Published var isBold = false
    @Published var isItalic = false
}

// SwiftUI toolbar reads/writes to context
// Coordinator observes context via Combine and applies to textStorage
```

## Environment Value Bridging

SwiftUI tracks which environment values you access in `updateUIView` and re-calls it when they change:

```swift
func updateUIView(_ uiView: UITextView, context: Context) {
    // Auto-reactive to Dark Mode changes
    let scheme = context.environment.colorScheme

    // Auto-reactive to Dynamic Type
    uiView.font = UIFont.preferredFont(forTextStyle: .body)

    // Auto-reactive to .disabled() modifier
    uiView.isEditable = context.environment.isEnabled
}
```

**Only access values you need** — unused accesses trigger unnecessary `updateUIView` calls.

## Limitations

### What You Cannot Do

1. **No `@FocusState` bridging** — must manually manage becomeFirstResponder/resignFirstResponder
2. **No SwiftUI selection UI** — selection handles are UIKit's, not SwiftUI's
3. **No animated text reflow** — SwiftUI can animate the frame, but text inside won't animate its reflow
4. **No `SwiftUI.Font` → `UIFont` conversion** — accept UIFont in your wrapper API
5. **No `SwiftUI.Color` → `UIColor` conversion** (public API) — accept UIColor
6. **Delegate is locked** — the Coordinator owns the delegate. External code cannot set `textView.delegate`
7. **No preference system** — UITextView can't propagate values up through SwiftUI preferences naturally

### Known Bugs

- **`intrinsicContentSize` invalidation ignored** (FB8499811) — use `sizeThatFits` or height tracking
- **Cursor jump** — setting `attributedText` resets selection. Always save/restore.
- **"Modifying state during view update"** — use `DispatchQueue.main.async` in delegate callbacks
- **Keyboard double-offset** — SwiftUI keyboard avoidance + UIScrollView contentInset can conflict. Use `.ignoresSafeArea(.keyboard)` to fix.

## Third-Party Alternatives

| Library | Platform | TextKit | Rich Text | License | Best For |
|---------|----------|---------|-----------|---------|----------|
| **STTextView** | macOS (+ iOS) | TextKit 2 | Yes | GPL/Commercial | Code editors, custom text engines |
| **RichTextKit** | iOS + macOS | TextKit 1 | Yes | MIT | Cross-platform rich text editing in SwiftUI |
| **Textual** | iOS + macOS | N/A | Display only | MIT | Markdown/rich text DISPLAY (not editing) |
| **HighlightedTextEditor** | iOS + macOS | TextKit 1 | Regex-based | MIT | Simple syntax highlighting |
| **CodeEditor** | iOS + macOS | Highlight.js | Code only | MIT | Code display with 180+ languages |

### When to Use a Library vs DIY

- **Simple rich text editing** → iOS 26+ TextEditor, or RichTextKit
- **Code editor** → STTextView or UITextView with custom TextKit 2 fragments
- **Rich text display (read-only)** → Textual or SwiftUI Text with AttributedString
- **Full control needed** → DIY UIViewRepresentable (this skill)

## Common Pitfalls

1. **Not updating `context.coordinator.parent`** — stale bindings cause wrong values in delegate callbacks
2. **Setting text without equality check** — infinite update loop
3. **Synchronous state updates in delegates** — "Modifying state during view update" crash
4. **Mixing async and sync updates** — ordering bugs. If one update is async, make them all async.
5. **Forgetting `.backgroundColor = .clear`** — UITextView paints over SwiftUI backgrounds
6. **Using ScrollView around representable with keyboard** — double-offset. Use `.ignoresSafeArea(.keyboard)`.
7. **Not setting `isScrollEnabled = false` for auto-sizing** — UITextView reports wrong intrinsic size

## Related Skills

- Use `/skill apple-text-views` when you still need to choose the view class.
- Use the swiftui bridging section in this reference for type-scope and rendering-boundary questions.
- Use the layout manager selection section in this reference when wrapper behavior depends on TextKit 1 vs 2.

---

# SwiftUI Text Bridging

Use this skill when the main question is what SwiftUI text can render, what converts cleanly, and where framework boundaries drop information.

## When to Use

- You are asking whether a Foundation text type or attribute works in SwiftUI.
- You need to know what `AttributedString` loses when bridged.
- The problem is rendering/type boundaries, not wrapper lifecycle.

## Quick Decision

- Need wrapper mechanics around `UITextView` / `NSTextView` -> the representable section in this reference
- Need to know what SwiftUI `Text` renders or ignores -> stay here
- Need attributed-text type choice itself -> the **rich-text-reference** agent

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

- Use the representable section in this reference for wrapper mechanics and coordinator issues.
- Use the **rich-text-reference** agent for type-model and conversion strategy.
- Use the **rich-text-reference** agent when `PresentationIntent` and Markdown parsing are the real drivers.

---

# SwiftUI TextEditor Rich Text Editing (iOS 26+)

Use this skill when the main question is whether SwiftUI's native TextEditor can handle a rich text editing need, or when implementing the iOS 26 rich text APIs.

## When to Use

- Building a rich text editor in SwiftUI targeting iOS 26+
- Evaluating whether TextEditor is enough or UIViewRepresentable is still needed
- Implementing formatting toolbars with AttributedTextSelection
- Constraining allowed formatting with AttributedTextFormattingDefinition

## Quick Decision

```
Need rich text editing in SwiftUI?
    Target iOS 26+?
        YES → Can TextEditor handle your needs? (see Limitations below)
            YES → Use TextEditor with AttributedString
            NO → UIViewRepresentable wrapping UITextView
        NO → UIViewRepresentable wrapping UITextView (only option)
```

**Default assumption: UIViewRepresentable is still the safer, more capable choice.** TextEditor with AttributedString is new (iOS 26), less battle-tested, and has real limitations. Use it when your needs fit within its capabilities and you don't need backward compatibility.

## Core Guidance

## What's New in iOS 26

TextEditor gained first-class `AttributedString` support, transforming it from plain-text-only to a genuine rich text editor for common formatting needs.

### Basic Rich Text Editing

```swift
struct RichEditor: View {
    @State private var text = AttributedString("Edit this text...")

    var body: some View {
        TextEditor(text: $text)
    }
}
```

Just changing the binding from `String` to `AttributedString` enables:
- Bold/italic/underline keyboard shortcuts (Cmd+B, Cmd+I, Cmd+U)
- Format menu items
- Genmoji insertion from the emoji keyboard

### Selection-Aware Formatting

```swift
struct FormattedEditor: View {
    @State private var text = AttributedString("Select text to format")
    @State private var selection = AttributedTextSelection()

    @Environment(\.fontResolutionContext) private var fontResolutionContext

    var body: some View {
        VStack {
            TextEditor(text: $text, selection: $selection)

            HStack {
                Button(action: toggleBold) {
                    Image(systemName: "bold")
                }
                Button(action: toggleItalic) {
                    Image(systemName: "italic")
                }
                Button(action: toggleUnderline) {
                    Image(systemName: "underline")
                }
            }
        }
    }

    private func toggleBold() {
        text.transformAttributes(in: &selection) {
            let font = $0.font ?? .default
            let resolved = font.resolve(in: fontResolutionContext)
            $0.font = font.bold(!resolved.isBold)
        }
    }

    private func toggleItalic() {
        text.transformAttributes(in: &selection) {
            let font = $0.font ?? .default
            let resolved = font.resolve(in: fontResolutionContext)
            $0.font = font.italic(!resolved.isItalic)
        }
    }

    private func toggleUnderline() {
        text.transformAttributes(in: &selection) {
            if $0.underlineStyle != nil {
                $0.underlineStyle = nil
            } else {
                $0.underlineStyle = .single
            }
        }
    }
}
```

### Key New Types

| Type | Purpose |
|------|---------|
| `AttributedTextSelection` | Two-way binding to user's text selection |
| `AttributedTextFormattingDefinition` | Define allowed formatting scope |
| `AttributedTextValueConstraint` | Constrain which attribute values are permitted |
| `FontResolutionContext` | Resolve semantic `Font` to concrete typographic attributes |
| `DiscontiguousAttributedSubstring` | Non-contiguous selections via `RangeSet` |

### Formatting Constraints

Restrict which formatting users can apply:

```swift
struct MyFormatting: AttributedTextFormattingDefinition {
    typealias Scope = AttributeScopes.SwiftUIAttributes

    // TextEditor probes constraints to determine valid changes
    static let fontWeight = ValueConstraint(
        \.font,
        constraint: { font in
            guard let font else { return nil }
            let weight = font.resolve().weight
            return font.weight(weight == .bold ? .regular : .bold)
        }
    )
}

TextEditor(text: $text, selection: $selection)
    .textFormattingDefinition(MyFormatting.self)
```

### Programmatic Selection Manipulation

```swift
// Replace selected text
text.replaceSelection(&selection, withCharacters: "replacement")

// Replace with attributed content
let styled = AttributedString("styled replacement")
text.replaceSelection(&selection, with: styled)

// Read selection indices
let indices = selection.indices(in: text)
```

### New AttributedString Properties

```swift
// Text alignment (new in iOS 26)
text.alignment = .center

// Line height control
text.lineHeight = .exact(points: 32)
text.lineHeight = .multiple(factor: 1.5)
text.lineHeight = .loose

// Writing direction
text.writingDirection = .rightToLeft
```

## What TextEditor Supports

| Capability | Supported? |
|------------|-----------|
| Bold / italic / underline / strikethrough | Yes |
| Custom fonts and sizes | Yes |
| Foreground and background colors | Yes |
| Text alignment | Yes |
| Line height | Yes |
| Writing direction | Yes |
| Keyboard shortcuts (Cmd+B, etc.) | Yes, automatic |
| Format menu items | Yes, automatic |
| Genmoji | Yes |
| Custom formatting toolbars | Yes, via `AttributedTextSelection` |
| Formatting constraints | Yes, via `AttributedTextFormattingDefinition` |
| Dynamic Type / Dark Mode | Yes, automatic with `Font` |

## What TextEditor Cannot Do

This is where UIViewRepresentable wrapping UITextView is still required:

| Capability | TextEditor | UITextView |
|------------|-----------|------------|
| **Inline image attachments** | No | Yes (NSTextAttachment) |
| **Text tables** | No | Yes (AppKit) |
| **Lists** (bulleted, numbered) | No | Yes (NSTextList, iOS 17+) |
| **Exclusion paths** | No | Yes |
| **TextKit 2 API access** | No | Yes (NSTextLayoutManager) |
| **Custom text layout** | No | Yes (layout fragments) |
| **Syntax highlighting** | Limited | Full (rendering attributes) |
| **First responder control** | Limited | Full (becomeFirstResponder) |
| **Custom context menus on text** | Limited | Full (UITextItemInteraction) |
| **Spell check customization** | No | Yes (UITextInputTraits) |
| **Custom input accessories** | No | Yes (inputAccessoryView) |
| **Writing Tools coordination** | Default only | Full delegate control |
| **iOS 25 and earlier** | No | Yes |
| **Battle-tested in production** | New (iOS 26) | Mature (iOS 2+) |

### The Maturity Gap

TextEditor's rich text support shipped in iOS 26. It is a **first-generation API**:

- Edge cases in formatting interaction are likely
- SwiftData persistence of AttributedString requires manual encoding workarounds
- The constraint system (`AttributedTextValueConstraint`) is sparsely documented
- Complex formatting combinations may not round-trip perfectly
- Third-party library support (RichTextKit, etc.) targets UITextView, not TextEditor

**If your app ships to production and rich text is critical, UIViewRepresentable wrapping UITextView remains the safer choice.** TextEditor is excellent for simpler formatting needs (notes, comments, basic rich text) where the reduced complexity of staying in SwiftUI outweighs the maturity tradeoff.

## Decision Framework

```
Is iOS 26 your minimum deployment target?
    NO → UIViewRepresentable. Stop here.
    YES → Do you need ANY of these?
        - Inline images / attachments
        - TextKit API access
        - Syntax highlighting with custom rendering
        - Complex list or table structures
        - Custom input accessories
        - Full first responder control
        YES to any → UIViewRepresentable
        NO to all → Is rich text mission-critical to your app?
            YES → Consider UIViewRepresentable for maturity
            NO → TextEditor with AttributedString is a good fit
```

## Migrating from UIViewRepresentable

If you have an existing UIViewRepresentable text editor wrapper and want to evaluate migration:

1. **List your formatting requirements** — check against the "Cannot Do" table above
2. **Check your deployment target** — iOS 26+ required
3. **Audit TextKit usage** — any `textLayoutManager`, `textStorage`, or `layoutManager` access means UIViewRepresentable stays
4. **Test edge cases** — undo behavior, paste formatting, VoiceOver, Dynamic Type at accessibility sizes
5. **Keep the wrapper as fallback** — don't delete it until the TextEditor path is fully validated

## Common Pitfalls

1. **Assuming TextEditor replaces UITextView** — It handles common formatting but lacks the full TextKit stack. For anything beyond basic rich text, UITextView is still needed.
2. **Forgetting `fontResolutionContext`** — Without it, you can't check whether the current selection is bold/italic. The resolved font tells you the concrete traits.
3. **SwiftData persistence** — `AttributedString` requires custom `Codable` handling with `@CodableConfiguration` or manual encoding. Not plug-and-play.
4. **No inline images** — There is no SwiftUI equivalent of `NSTextAttachment`. Genmoji works, but arbitrary image embedding does not.
5. **First responder management** — Programmatically focusing the editor or dismissing the keyboard is less controllable than UITextView.

## Related Skills

- Use the representable section in this reference for UIViewRepresentable wrapping when TextEditor's limitations apply.
- Use the apple docs section in this reference for Apple-authored docs access on styled text editing and nearby SwiftUI APIs.
- Use `/skill apple-text-views` for the full view selection decision tree (which this skill updates for iOS 26).
- Use the **rich-text-reference** agent for AttributedString model and conversion patterns.
- Use the swiftui bridging section in this reference for what SwiftUI Text renders vs ignores.

---

# AppKit vs UIKit Text Capabilities

Use this skill when the main question is which platform text stack can support a capability or editor behavior.

## When to Use

- You are comparing `NSTextView` and `UITextView` capabilities.
- You are porting text code between macOS and iOS.
- You need to know whether a feature gap is architectural or just an API difference.

## Quick Decision

- Desktop document-editor features, text tables, rulers, or services -> AppKit
- Touch-first editing, modular interactions, or iOS-specific selection UI -> UIKit
- Unsure whether the feature is platform-only or text-view-only -> keep reading

## Core Guidance

## NSTextView Can Do — UITextView Cannot

### Rich Text Editing Panels (AppKit Only)

NSTextView provides built-in formatting panels with no UIKit equivalent:

| Panel | API | Purpose |
|-------|-----|---------|
| Font Panel | `usesFontPanel` | System Fonts window syncs with selection |
| Ruler | `usesRuler` / `isRulerVisible` | Interactive paragraph formatting (margins, tabs) |
| Link Panel | `orderFrontLinkPanel:` | Insert/edit hyperlinks |
| List Panel | `orderFrontListPanel:` | Configure list formatting |
| Table Panel | `orderFrontTablePanel:` | Insert/manipulate text tables |
| Spacing Panel | `orderFrontSpacingPanel:` | Paragraph spacing configuration |
| Substitutions Panel | `orderFrontSubstitutionsPanel:` | Smart quotes, dashes, text replacement config |

### Text Tables (NSTextTable / NSTextTableBlock)

**AppKit-only classes.** No UIKit equivalent exists.

```swift
let table = NSTextTable()
table.numberOfColumns = 3

let cell = NSTextTableBlock(table: table, startingRow: 0,
                             rowSpan: 1, startingColumn: 0, columnSpan: 1)
cell.backgroundColor = .lightGray
cell.setWidth(1.0, type: .absoluteValueType, for: .border)

let style = NSMutableParagraphStyle()
style.textBlocks = [cell]
```

Features: row/column spanning, per-cell borders/background, padding/margin control, automatic or fixed layout. **Triggers TextKit 1 fallback.**

### Grammar Checking

```swift
// AppKit
textView.isGrammarCheckingEnabled = true
textView.toggleGrammarChecking(nil)

// UIKit — NO equivalent API
// Grammar checking is system-level only, not exposed to developers
```

### Text Completion System

```swift
// AppKit — full completion infrastructure
textView.complete(nil)  // Invoke completion popup
textView.isAutomaticTextCompletionEnabled = true

// Override for custom completions:
override func completions(forPartialWordRange charRange: NSRange,
                           indexOfSelectedItem index: UnsafeMutablePointer<Int>) -> [String]? {
    return ["completion1", "completion2"]
}

// UIKit — NO built-in completion API
// Must build custom using UITextInput + overlay views
```

### Spell Checking (Granular Control)

| Feature | AppKit | UIKit |
|---------|--------|-------|
| Toggle continuous spell checking | `isContinuousSpellCheckingEnabled` | `spellCheckingType` (.yes/.no) |
| Mark specific range as misspelled | `setSpellingState(_:range:)` | Not available |
| Document tag management | `spellCheckerDocumentTag()` | Not available |
| Grammar checking | `isGrammarCheckingEnabled` | Not available |

### Smart Substitutions (Individual Toggle APIs)

| Feature | AppKit API | UIKit Equivalent |
|---------|-----------|-----------------|
| Smart quotes | `isAutomaticQuoteSubstitutionEnabled` | `smartQuotesType` (similar) |
| Smart dashes | `isAutomaticDashSubstitutionEnabled` | `smartDashesType` (similar) |
| Text replacement | `isAutomaticTextReplacementEnabled` | System-level only |
| Auto-correction | `isAutomaticSpellingCorrectionEnabled` | `autocorrectionType` (similar) |
| Link detection | `isAutomaticLinkDetectionEnabled` | `dataDetectorTypes` (different API) |
| Data detection | `isAutomaticDataDetectionEnabled` | `dataDetectorTypes` (different API) |

AppKit provides individual toggle actions and a Substitutions Panel for user configuration. UIKit has simpler enum properties.

### Services Menu Integration

NSTextView automatically participates in the macOS Services menu (send selected text to other apps):

```swift
// Automatic for NSTextView — implements NSServicesMenuRequestor
// Services like "Look Up in Dictionary", "Send via Mail" appear in Services menu

// For custom views:
override func validRequestor(forSendType sendType: NSPasteboard.PasteboardType?,
                              returnType: NSPasteboard.PasteboardType?) -> Any? {
    if sendType == .string { return self }
    return super.validRequestor(forSendType: sendType, returnType: returnType)
}
```

**iOS has no Services concept.**

### Field Editor Architecture

Unique to AppKit. One shared NSTextView per window handles all NSTextField editing:

```swift
// Get the field editor
let fieldEditor = window.fieldEditor(true, for: textField) as? NSTextView

// Custom field editor
func windowWillReturnFieldEditor(_ sender: NSWindow, to client: Any?) -> Any? {
    if client is MySpecialTextField { return myCustomFieldEditor }
    return nil
}
```

**Key implications:**
- Memory efficient (one editor for all fields)
- One TK1 fallback in ANY field editor affects ALL fields in the window
- Custom field editors can provide per-field customization

**UIKit has no field editor.** Each UITextField manages its own editing.

### NSText Heritage (Direct RTF/RTFD)

NSTextView inherits from NSText, providing:

```swift
// Direct RTF/RTFD I/O
let rtfData = textView.rtf(from: range)
let rtfdData = textView.rtfd(from: range)
textView.replaceCharacters(in: range, withRTF: rtfData)
textView.replaceCharacters(in: range, withRTFD: rtfdData)
textView.writeRTFD(toFile: path, atomically: true)
textView.readRTFD(fromFile: path)

// Font/ruler pasteboard
textView.copyFont(nil)     // Copy font attributes
textView.pasteFont(nil)    // Apply font from pasteboard
textView.copyRuler(nil)    // Copy paragraph attributes
textView.pasteRuler(nil)   // Apply paragraph attributes

// Speech
textView.startSpeaking(nil)
textView.stopSpeaking(nil)
```

**UIKit has none of these.** You'd need to manually create RTF data, manage font pasteboards, or use AVSpeechSynthesizer.

### Print Support

```swift
// AppKit — native print support via NSView
textView.printView(nil)  // Opens print dialog

// UIKit — separate print system
let formatter = UISimpleTextPrintFormatter(attributedText: textView.attributedText)
let controller = UIPrintInteractionController.shared
controller.printFormatter = formatter
controller.present(animated: true)
```

**macOS Dark Mode gotcha:** `printView(nil)` renders with the current appearance. In Dark Mode, this produces white text on white paper. Fix: create an off-screen text view sharing the same `NSTextStorage` with `.appearance = NSAppearance(named: .aqua)`, and print from that.

**iOS printing tiers:** `UISimpleTextPrintFormatter` handles most cases. For custom headers/footers or multi-section documents, subclass `UIPrintPageRenderer` and compose formatters per page range.

### Find and Replace

| Feature | AppKit | UIKit |
|---------|--------|-------|
| API | `NSTextFinder` (since OS X 10.7) | `UIFindInteraction` (since iOS 16) |
| Properties | `usesFindBar`, `usesFindPanel` | `findInteraction`, `isFindInteractionEnabled` |
| Incremental search | ✅ Built-in | ✅ Built-in |
| Custom providers | `NSTextFinderClient` protocol | `UITextSearching` protocol |

Both platforms now support find, but AppKit's has existed much longer with more customization.

## UITextView Can Do — NSTextView Cannot

### Data Detector Types (Declarative)

```swift
// UIKit — single property, granular type selection
textView.dataDetectorTypes = [.link, .phoneNumber, .address, .calendarEvent,
                               .shipmentTrackingNumber, .flightNumber]
// Detected items become tappable automatically
// Only works when isEditable = false

// AppKit — Boolean toggles, less granular
textView.isAutomaticLinkDetectionEnabled = true
textView.isAutomaticDataDetectionEnabled = true
// Requires explicit checkTextInDocument: call
```

### UITextInteraction (Modular Gestures)

```swift
// UIKit — add system text gestures to ANY UIView
let interaction = UITextInteraction(for: .editable)
interaction.textInput = customView  // Any UITextInput conformer
customView.addInteraction(interaction)

// AppKit — no equivalent modular component
// NSTextView has built-in gestures, but they can't be extracted
```

### Text Item Interactions (iOS 17+)

```swift
// UIKit — rich interaction with links, attachments, tagged ranges
func textView(_ textView: UITextView,
              primaryActionFor textItem: UITextItem,
              defaultAction: UIAction) -> UIAction? {
    // Customize tap behavior
}

func textView(_ textView: UITextView,
              menuConfigurationFor textItem: UITextItem,
              defaultMenu: UIMenu) -> UITextItem.MenuConfiguration? {
    // Custom context menu
}

// Tag arbitrary ranges for interaction
let attrs: [NSAttributedString.Key: Any] = [
    .uiTextItemTag: "myCustomTag"
]

// AppKit — only has textView(_:clickedOnLink:at:)
```

### UITextSelectionDisplayInteraction (iOS 17+)

System selection UI for custom views — cursor, handles, highlights:

```swift
let selectionDisplay = UITextSelectionDisplayInteraction(textInput: myView)
myView.addInteraction(selectionDisplay)
selectionDisplay.setNeedsSelectionUpdate()
```

AppKit gained `NSTextInsertionIndicator` (macOS Sonoma) for the cursor only, but nothing as comprehensive.

### UITextLoupeSession (iOS 17+)

```swift
let session = UITextLoupeSession.begin(at: point, from: cursorView, in: self)
session.move(to: newPoint)
session.invalidate()
```

No AppKit equivalent — macOS doesn't use a loupe for text selection.

## Architecture Differences

### Inheritance

```
AppKit:  NSObject → NSResponder → NSView → NSText → NSTextView
         (Rich NSText base: RTF, font panel, ruler, field editor, speech)

UIKit:   NSObject → UIResponder → UIView → UIScrollView → UITextView
         (Scrolling built-in, but no text-specific base class)
```

### Scrolling

| | AppKit | UIKit |
|-|--------|-------|
| Built-in scroll | ❌ Must embed in NSScrollView | ✅ IS a UIScrollView |
| Convenience | `NSTextView.scrollableTextView()` | Always scrollable |
| Non-scrolling | NSTextView is non-scrolling by default | Set `isScrollEnabled = false` |

### Text Storage Access

| | AppKit | UIKit |
|-|--------|-------|
| Property | `textStorage: NSTextStorage?` (optional) | `textStorage: NSTextStorage` (non-optional) |
| Full content | `attributedString()` method | `attributedText` property |

### Delegate Richness

NSTextViewDelegate is significantly richer than UITextViewDelegate:
- Modify selection during changes
- Intercept link clicks
- Customize drag operations
- Control tooltip display
- Completion handling

UITextViewDelegate is minimal, though iOS 17 text item interactions narrowed the gap.

### Writing Tools (Mostly Equivalent, Key Differences)

Both platforms support Writing Tools as of iOS 18 / macOS 15. The system view API is parallel (`writingToolsBehavior`, `writingToolsAllowedInputOptions`, `isWritingToolsActive`, matching delegate methods). Both require TextKit 2 for full inline experience.

**Differences for custom text engines:**

| Aspect | UIKit | AppKit |
|--------|-------|--------|
| Coordinator class | `UIWritingToolsCoordinator` | `NSWritingToolsCoordinator` |
| Attachment | `view.addInteraction(coordinator)` | `view.writingToolsCoordinator = coordinator` |
| Preview type | `UITargetedPreview` | `NSTextPreview` |
| Path type | `[UIBezierPath]` | `[NSBezierPath]` |
| Menu integration | Automatic via `UITextInteraction` | Requires `NSServicesMenuRequestor` (`validRequestor(forSendType:returnType:)`, `writeSelection(to:types:)`, `readSelection(from:)`) |

**macOS 26 additions:** `automaticallyInsertsWritingToolsItems` (default: true), `.writingToolsItems` for standard menu items, stock `NSToolbarItem` for toolbar integration.

### Fallback Detection (Different Per Platform)

| Aspect | UIKit | AppKit |
|--------|-------|--------|
| Detection | Check `textView.textLayoutManager == nil` | Same check + notifications |
| Breakpoint | `_UITextViewEnablingCompatibilityMode` | Not available |
| Notifications | None | `NSTextView.willSwitchToNSLayoutManagerNotification`, `NSTextView.didSwitchToNSLayoutManagerNotification` |
| Console log | Yes (system logs the switch) | Yes |

## Quick Decision Guide

| Need | Platform |
|------|----------|
| Text tables | AppKit only (NSTextTable) |
| Grammar checking API | AppKit only |
| Text completion API | AppKit only |
| Services menu | AppKit only (macOS concept) |
| Font panel integration | AppKit only |
| Interactive ruler | AppKit only |
| Direct RTF file I/O | AppKit only (NSText heritage) |
| Declarative data detectors | UIKit better (dataDetectorTypes) |
| Modular text interaction | UIKit only (UITextInteraction) |
| Text item context menus | UIKit only (iOS 17+) |
| Selection display component | UIKit only (UITextSelectionDisplayInteraction) |
| Multi-page/multi-column | AppKit better (historically) |
| Built-in scrolling | UIKit (IS a scroll view) |

## Related Skills

- Use `/skill apple-text-views` when the real question is which view class to adopt.
- Use the representable section in this reference when SwiftUI wrapping is part of the platform decision.
- Use the **editor-reference** agent for Apple Intelligence editor differences.

---

# Layout Manager Selection Guide

Use this skill when the main question is whether the editor should use TextKit 1 or TextKit 2.

## When to Use

- You are choosing between `NSLayoutManager` and `NSTextLayoutManager`.
- You are evaluating migration risk or performance tradeoffs.
- You need a recommendation tied to feature requirements.

## Quick Decision

```
Need glyph-level access?
    YES → NSLayoutManager (TextKit 1)

Need multi-page/multi-column layout?
    YES → NSLayoutManager (TextKit 1)

Need text tables (NSTextTable)?
    YES → NSLayoutManager (TextKit 1)

Need Writing Tools inline experience?
    YES → NSTextLayoutManager (TextKit 2)

Document > 10K lines and performance-critical?
    → Read the Performance Evidence section carefully

Reliable syntax highlighting via temporary attributes?
    → NSLayoutManager (TextKit 1) — TK2 renderingAttributes have known bugs

Targeting iOS 15?
    → NSLayoutManager (TextKit 1) — UITextView defaults to TK1 on iOS 15

Building new app, iOS 16+, none of the above?
    → TextKit 2 is the default and a good starting point.
```

## Core Guidance

## The Two Layout Managers

| Aspect | NSLayoutManager (TK1) | NSTextLayoutManager (TK2) |
|--------|----------------------|--------------------------|
| **Available** | iOS 7+ / macOS 10.0+ | iOS 15+ / macOS 12+ |
| **Layout model** | Contiguous (optional non-contiguous) | Always non-contiguous (viewport) |
| **Abstraction** | Glyph-based | Element/fragment-based |
| **Text containers** | Multiple | Single only |
| **Performance model** | O(document) or O(visible) | O(viewport) theoretical |
| **International text** | Manual glyph handling | Correct by design |
| **Writing Tools** | Panel only | Full inline |
| **Custom rendering** | Subclass + drawGlyphs | Subclass NSTextLayoutFragment |
| **Overlay styling** | Temporary attributes | Rendering attributes |
| **Printing** | Full support | Limited (iOS 18+) |

## Performance Evidence

### Apple's Claims (WWDC21)

> *"TextKit 2 is extremely fast for an incredibly wide range of scenarios, from quickly rendering labels that are only a few lines each to laying out documents that are hundreds of megabytes being scrolled through at interactive rates."*

### Developer Experience (Real-World)

**ChimeHQ TextViewBenchmark (macOS 14 beta):**
> *"TextKit 1 is extremely fast and TextKit 2 actually even a small amount faster."*

For comparable document sizes on recent macOS, TextKit 2 has reached parity or slightly better.

**Large document scrolling (Apple Developer Forums, multiple reports):**
- TextKit 2 scrolling performance degrades above ~3,000 lines
- 10K+ lines described as "an absolute nightmare" with TextKit 2
- Switching to TextKit 1 restored smooth scrolling with 1 million characters
- These reports are primarily from iOS 16/17 era; improvements in each release

**Memory usage (developer measurement):**
- ~0.5 GB with TextKit 1 custom labels
- ~1.2 GB with TextKit 2 for same content
- TextKit 2's immutable object model (NSTextLayoutFragment, NSTextLineFragment) has overhead

**Apple's own apps:**
- Pages, Xcode, Notes: still use TextKit 1 (as of reports through 2025)
- TextEdit: uses TextKit 2 but falls back for tables, page layout, printing

### Short Text (Labels, Chat Bubbles)

TextKit 2 wins here:
- No performance penalty for viewport management on short text
- Correctness benefits for international text
- Modern API with rendering attributes

### Large Documents (10K+ lines)

Mixed results:
- **Theoretical advantage:** Viewport layout should scale to any document size
- **Practical issues:** Scroll bar jiggle (estimated heights), jump-to-position inaccuracy, height estimation instability
- **Improving per OS release:** macOS 14+ shows near-parity in benchmarks
- **Recommendation:** Test on your target OS version with your actual content

### Line Counting

Both systems struggle with this:
- **TextKit 1:** `numberOfGlyphs` + enumeration. Requires full layout with `allowsNonContiguousLayout = false`, or approximate with non-contiguous.
- **TextKit 2:** Must enumerate ALL layout fragments with `.ensuresLayout`. Defeats viewport optimization.

**For either system:** Consider maintaining a separate line count (incremental update on edit) rather than querying the layout system.

## TextKit 1 Is Not Deprecated

**`NSLayoutManager` is a fully supported, non-deprecated API.** Apple has not deprecated the class or its core methods. Apple's own apps (Pages, Xcode, Notes) still use TextKit 1 as of 2025. TextEdit uses TextKit 2 but falls back to TextKit 1 for tables, page layout, and printing.

TextKit 1 is not "legacy mode to maintain until you can migrate." It is the correct choice when your requirements include features that TextKit 2 does not support.

## When TextKit 1 Is the Right Choice

1. **Glyph-level access** — Custom glyph substitution, glyph inspection, typography tools. TextKit 2 has zero glyph APIs; you'd need to drop to Core Text.
2. **Multi-page/multi-column layout** — NSTextLayoutManager supports only one container. No workaround exists.
3. **Text tables** — NSTextTable/NSTextTableBlock are TextKit 1 only (macOS). Text tables in content trigger automatic fallback.
4. **Syntax highlighting via temporary attributes** — `addTemporaryAttribute` is rendering-only and well-tested. TextKit 2's `setRenderingAttributes` has known drawing bugs (FB9692714) and requires custom `NSTextLayoutFragment` subclasses as a workaround.
5. **Printing** — TextKit 2 has limited printing support (iOS 18+/macOS 15+) but still falls back for multi-page pagination.
6. **Custom NSLayoutManager subclass** — Significant investment in `drawGlyphs`, `drawBackground`, delegate methods
7. **`shouldGenerateGlyphs` delegate** — No TextKit 2 equivalent
8. **Exact document height required** — TextKit 1 contiguous layout gives exact height; TextKit 2 estimates
9. **Scroll bar accuracy critical** — TextKit 2's estimated heights cause scroll bar instability
10. **Targeting iOS 15** — UITextView defaults to TextKit 1 on iOS 15. ~2-3% of devices as of early 2026, but significant for apps with broad reach.

## When TextKit 2 Is the Right Choice

1. **New iOS 16+ app** — It's the default; fighting it adds complexity
2. **Writing Tools (full inline)** — Requires TextKit 2
3. **International text correctness** — Arabic, Devanagari, CJK handled correctly without glyph assumptions
4. **Custom rendering via fragments** — Cleaner API than drawGlyphs subclassing
5. **Short text (labels, chat bubbles)** — No downside, cleaner API
6. **Viewport-based display of large content** — When you don't need exact document metrics
7. **Custom text elements** — NSTextContentManager subclass for non-attributed-string backends

## Migration Decision Framework

### Don't Migrate If:

- App works well with TextKit 1
- You rely on glyph APIs extensively
- You need multi-container layout
- No specific TextKit 2 feature is required
- Target OS includes iOS 15 or earlier

### Consider Migrating If:

- Users need Writing Tools inline experience
- International text rendering issues in TextKit 1
- Building new text features from scratch
- Want viewport performance for very large documents
- Need rendering attributes (cleaner than temporary attributes)

### Migration Strategy

1. **Check `textLayoutManager` first** — write all new code to check TextKit 2 availability
2. **Dual code paths** — support both TK1 and TK2 during transition
3. **Test fallback** — ensure your app handles fallback gracefully
4. **Migrate incrementally** — one feature at a time, not big bang

```swift
// Dual code path pattern
if let textLayoutManager = textView.textLayoutManager {
    // TextKit 2 path
    textLayoutManager.enumerateTextLayoutFragments(from: nil, options: [.ensuresLayout]) { fragment in
        // ...
        return true
    }
} else {
    // TextKit 1 fallback
    let layoutManager = textView.layoutManager!
    layoutManager.ensureLayout(for: textView.textContainer)
    // ...
}
```

## Common Pitfalls

1. **Migrating without a reason** — TextKit 1 works. Don't fix what isn't broken.
2. **Assuming TextKit 2 is always faster** — Real-world performance depends on document size, OS version, and use case.
3. **Not testing on target OS** — TextKit 2 performance improves each release. Test on YOUR minimum deployment target.
4. **Full-document `ensureLayout` in TextKit 2** — Defeats viewport optimization. O(document_size).
5. **Expecting exact scroll metrics from TextKit 2** — Estimated heights cause scroll bar instability. If exact metrics matter, use TextKit 1.

## Related Skills

- Use the **textkit-reference** agent or the **textkit-reference** agent after you know which stack you need.
- Use the **textkit-reference** agent when compatibility mode is driving the decision.
- Use `/skill apple-text-views` when the real question is control choice, not layout-manager internals.

---

# Apple Documentation Access

Router skill providing direct access to Apple's official for-LLM markdown documentation bundled inside Xcode.

Use this skill when you want Apple-authored guidance from the Xcode-bundled Apple docs that MCP can expose at runtime, rather than only repo-authored summaries.

## When to Use

- You need the exact API signature or behavior from Apple.
- A Swift compiler diagnostic needs explanation with examples.
- Another Apple Text skill references an Apple framework and you want the official source.
- You want authoritative code examples for `AttributedString`, styled `TextEditor`, toolbar behavior, or related text-system changes that ship in Xcode docs.

Priority: Apple Text skills provide opinionated guidance and project-specific tradeoffs. Apple docs provide authoritative API detail. Use both together.

## Quick Decision

- Need opinionated guidance, not Apple's exact wording -> use the relevant Apple Text skill directly
- Need symptom-first debugging -> `/skill apple-text-textkit-diag`
- Need Apple-authored API detail or Swift diagnostic explanation -> stay here

## Example Prompts

- "What does Apple's AttributedString update doc say about the newest Foundation text changes?"
- "Show me Apple's official guidance for styled TextEditor editing."
- "What does the Swift diagnostic `actor-isolated-call` mean?"
- "What Apple-authored docs ship in Xcode for text and editor-adjacent APIs?"

## What's Covered

### Apple Guide Topics

- `AttributedString` updates and Foundation text changes.
- SwiftUI styled text editing behavior.
- Toolbar features near editing and text-centric UI.
- The checked-in sidecar index at [xcode-docs-index.md](xcode-docs-index.md) listing the local Apple-text subset and the bundled Swift diagnostics catalog.

### Swift Compiler Diagnostics

- Official explanations with examples for Swift diagnostics bundled in the Xcode toolchain.
- Especially useful when concurrency or type-system diagnostics intersect with text code and editor integrations.

## How It Works

Apple bundles for-LLM markdown documentation inside Xcode at two locations:

- `AdditionalDocumentation` for framework guides and implementation patterns.
- Swift diagnostics for compiler error and warning explanations with examples.

Apple Text can read these files at runtime from the local Xcode installation when `APPLE_TEXT_APPLE_DOCS=true`.

When runtime Apple docs are enabled in the current client, use them first. Treat the checked-in sidecars in this skill as the repo-backed fallback and the fastest local subset for Apple text questions.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `APPLE_TEXT_XCODE_PATH` | `/Applications/Xcode.app` | Custom Xcode path, such as `Xcode-beta.app` |
| `APPLE_TEXT_APPLE_DOCS` | `false` | Set to `true` to enable runtime loading of Apple-authored markdown docs from the local Xcode install |

## Related Skills

- Use the texteditor 26 section in this reference for project-specific `TextEditor` guidance after reading Apple’s docs results.
- Use the **rich-text-reference** agent for AttributedString vs NSAttributedString decisions and conversion strategy.
- Use the **editor-reference** agent when the real problem is Writing Tools integration, not Apple-doc lookup.
- Use the foundation ref section in this reference for broader Foundation text utilities beyond the Xcode-bundled subset.

---

# Core Text for TextKit Developers

Use this skill when you need glyph-level control — either because TextKit 2 has no glyph APIs, or because your use case (custom typesetting, font tables, per-glyph rendering) requires the Core Text layer directly.

## When to Use

- You need glyph positions, advances, or bounding boxes that TextKit 2 hides
- You are doing custom typesetting or non-standard line breaking
- You need font table access or OpenType feature control
- You are rendering text with custom Core Graphics effects per glyph
- You need hit testing or caret positioning outside of a TextKit text container

## Quick Decision

```
Need glyph-level access?
    TextKit 1 available? → Use NSLayoutManager glyph APIs
    TextKit 2 only? → Drop to Core Text (this skill)

Need custom line breaking?
    → CTTypesetter

Need to draw text into a CGContext directly?
    → CTLine or CTFrame

Need font metrics, tables, or OpenType features?
    → CTFont

Need inline non-text elements with custom metrics?
    → CTRunDelegate
```

## Core Guidance

## Architecture

```
CTFramesetter (factory)
    → CTTypesetter (line breaking)
        → CTFrame (laid-out region)
            → CTLine (one visual line)
                → CTRun (contiguous glyphs, same attributes)
                    → CGGlyph[] (actual glyph IDs)
                    → CGPoint[] (positions)
                    → CGSize[]  (advances)
```

Core Text sits directly above Core Graphics. It is a C API using Core Foundation types. Available since iOS 3.2 / macOS 10.5. Both TextKit 1 and TextKit 2 render through Core Text internally — it is the foundation under both, not part of either.

**Thread safety:** Font objects (CTFont, CTFontDescriptor, CTFontCollection) are thread-safe and can be shared across threads. Layout objects (CTTypesetter, CTFramesetter, CTRun, CTLine, CTFrame) are **NOT thread-safe** — use them on a single thread only.

## CTLine — The Most Common Escape Hatch

For most TextKit developers, `CTLine` is the entry point. Create one from an attributed string to get glyph information:

```swift
let attributedString = NSAttributedString(string: "Hello 👋🏽",
    attributes: [.font: UIFont.systemFont(ofSize: 16)])
let line = CTLineCreateWithAttributedString(attributedString)

// Typographic bounds
var ascent: CGFloat = 0, descent: CGFloat = 0, leading: CGFloat = 0
let width = CTLineGetTypographicBounds(line, &ascent, &descent, &leading)
let height = ascent + descent + leading

// Hit testing: point → string index
let index = CTLineGetStringIndexForPosition(line, CGPoint(x: 50, y: 0))

// Caret positioning: string index → x offset
let offset = CTLineGetOffsetForStringIndex(line, 3, nil)

// Image bounds (actual rendered pixels, not typographic)
let ctx = UIGraphicsGetCurrentContext()!
let imageBounds = CTLineGetImageBounds(line, ctx)
```

## CTRun — Glyph-Level Access

Each `CTRun` is a contiguous sequence of glyphs sharing the same attributes:

```swift
let runs = CTLineGetGlyphRuns(line) as! [CTRun]

for run in runs {
    let glyphCount = CTRunGetGlyphCount(run)

    // Get all glyphs
    var glyphs = [CGGlyph](repeating: 0, count: glyphCount)
    CTRunGetGlyphs(run, CFRange(location: 0, length: glyphCount), &glyphs)

    // Get positions (relative to line origin)
    var positions = [CGPoint](repeating: .zero, count: glyphCount)
    CTRunGetPositions(run, CFRange(location: 0, length: glyphCount), &positions)

    // Get advances (width of each glyph)
    var advances = [CGSize](repeating: .zero, count: glyphCount)
    CTRunGetAdvances(run, CFRange(location: 0, length: glyphCount), &advances)

    // Map glyph indices back to string indices (UTF-16)
    var stringIndices = [CFIndex](repeating: 0, count: glyphCount)
    CTRunGetStringIndices(run, CFRange(location: 0, length: glyphCount), &stringIndices)

    // Get the run's attributes
    let attrs = CTRunGetAttributes(run) as! [NSAttributedString.Key: Any]
    let font = attrs[.font] as! CTFont
}
```

## CTFramesetter / CTFrame — Multi-Line Layout

For laying out text into a rectangular (or custom-shaped) region:

```swift
let framesetter = CTFramesetterCreateWithAttributedString(attributedString)

// Suggest frame size for constrained width
let constraint = CGSize(width: 300, height: .greatestFiniteMagnitude)
let suggestedSize = CTFramesetterSuggestFrameSizeWithConstraints(
    framesetter, CFRange(location: 0, length: 0), nil, constraint, nil)

// Create frame in a path
let path = CGPath(rect: CGRect(origin: .zero, size: suggestedSize), transform: nil)
let frame = CTFramesetterCreateFrame(framesetter, CFRange(location: 0, length: 0), path, nil)

// Get lines and origins
let lines = CTFrameGetLines(frame) as! [CTLine]
var origins = [CGPoint](repeating: .zero, count: lines.count)
CTFrameGetLineOrigins(frame, CFRange(location: 0, length: lines.count), &origins)

// Draw the entire frame
CTFrameDraw(frame, context)
```

## CTTypesetter — Custom Line Breaking

For control over where lines break:

```swift
let typesetter = CTTypesetterCreateWithAttributedString(attributedString)

var start: CFIndex = 0
let stringLength = CFAttributedStringGetLength(attributedString)

while start < stringLength {
    // Suggest line break for a given width
    let count = CTTypesetterSuggestLineBreak(typesetter, start, 300.0)

    // Or suggest with cluster breaking (for CJK)
    // let count = CTTypesetterSuggestClusterBreak(typesetter, start, 300.0)

    let line = CTTypesetterCreateLine(typesetter, CFRange(location: start, length: count))
    // Position and draw the line
    start += count
}
```

## CTFont — Font Metrics and Features

```swift
// Create from UIFont
let uiFont = UIFont.systemFont(ofSize: 16)
let ctFont = CTFontCreateWithName(uiFont.fontName as CFString, uiFont.pointSize, nil)

// Metrics
let ascent = CTFontGetAscent(ctFont)
let descent = CTFontGetDescent(ctFont)
let leading = CTFontGetLeading(ctFont)
let unitsPerEm = CTFontGetUnitsPerEm(ctFont)

// Get glyphs for characters
var characters: [UniChar] = Array("A".utf16)
var glyphs = [CGGlyph](repeating: 0, count: characters.count)
CTFontGetGlyphsForCharacters(ctFont, &characters, &glyphs, characters.count)

// Glyph bounding boxes
var boundingRects = [CGRect](repeating: .zero, count: glyphs.count)
CTFontGetBoundingRectsForGlyphs(ctFont, .default, glyphs, &boundingRects, glyphs.count)

// Glyph path (for custom rendering)
if let path = CTFontCreatePathForGlyph(ctFont, glyphs[0], nil) {
    // Draw the glyph outline
    context.addPath(path)
    context.fillPath()
}

// OpenType features
let features = CTFontCopyFeatures(ctFont) as? [[String: Any]] ?? []
```

## CTRunDelegate — Inline Custom Elements

Reserve space in a line for non-text content (images, custom views):

```swift
var callbacks = CTRunDelegateCallbacks(version: kCTRunDelegateCurrentVersion,
    dealloc: { _ in },
    getAscent: { _ in 20 },   // Height above baseline
    getDescent: { _ in 5 },    // Depth below baseline
    getWidth: { _ in 30 }      // Width of the space
)

let delegate = CTRunDelegateCreate(&callbacks, nil)!

let attrs: [NSAttributedString.Key: Any] = [
    kCTRunDelegateAttributeName as NSAttributedString.Key: delegate
]
let placeholder = NSAttributedString(string: "\u{FFFC}", attributes: attrs)

// Insert into your attributed string
// Then draw your custom content at the run's position after layout
```

## Critical: Coordinate System

**Core Text uses bottom-left origin (Core Graphics). UIKit uses top-left origin.**

### Drawing Core Text in UIKit

```swift
override func draw(_ rect: CGRect) {
    guard let context = UIGraphicsGetCurrentContext() else { return }

    // REQUIRED: Flip coordinate system for Core Text
    context.textMatrix = .identity
    context.translateBy(x: 0, y: bounds.height)
    context.scaleBy(x: 1, y: -1)

    // Now draw
    CTLineDraw(line, context)
    // or CTFrameDraw(frame, context)
}
```

**Forgetting the flip is the #1 Core Text mistake.** Text renders upside-down or at the wrong position.

### Converting Line Origins from CTFrame

`CTFrameGetLineOrigins` returns origins in Core Text coordinates (bottom-left). To use in UIKit:

```swift
let lines = CTFrameGetLines(frame) as! [CTLine]
var origins = [CGPoint](repeating: .zero, count: lines.count)
CTFrameGetLineOrigins(frame, CFRange(location: 0, length: lines.count), &origins)

for (i, line) in lines.enumerated() {
    // Flip y: UIKit y = frameHeight - CoreText y
    let uikitY = frameRect.height - origins[i].y
    // uikitY is now the BASELINE position in UIKit coordinates
}
```

## Bridging TextKit ↔ Core Text

### TextKit 2: Getting Glyph Info from a Layout Fragment

```swift
// In a custom NSTextLayoutFragment or delegate callback:
let attributedString = textElement.attributedString
let line = CTLineCreateWithAttributedString(attributedString as CFAttributedString)
let runs = CTLineGetGlyphRuns(line) as! [CTRun]

for run in runs {
    let glyphCount = CTRunGetGlyphCount(run)
    var positions = [CGPoint](repeating: .zero, count: glyphCount)
    CTRunGetPositions(run, CFRange(location: 0, length: glyphCount), &positions)

    // positions are relative to the line origin
    // Add layoutFragmentFrame.origin to get document coordinates
    // Remember to handle the coordinate flip if drawing in UIKit
}
```

### Font Bridging

```swift
// macOS: NSFont ↔ CTFont is toll-free bridged
let ctFont = nsFont as CTFont
let nsFont = ctFont as NSFont

// iOS: UIFont ↔ CTFont is NOT toll-free bridged
// UIFont → CTFont
let ctFont = CTFontCreateWithName(uiFont.fontName as CFString, uiFont.pointSize, nil)

// CTFont → UIFont
let uiFont = UIFont(name: CTFontCopyPostScriptName(ctFont) as String,
                     size: CTFontGetSize(ctFont))!

// NSAttributedString ↔ CFAttributedString IS toll-free bridged (both platforms)
let cfAttrStr = attributedString as CFAttributedString
```

### Attribute Key Differences

Core Text uses its own attribute keys that differ from UIKit/AppKit:

| Purpose | Core Text Key | UIKit/AppKit Key |
|---------|--------------|-----------------|
| Font | `kCTFontAttributeName` (CTFont) | `.font` (UIFont/NSFont) |
| Foreground color | `kCTForegroundColorAttributeName` (CGColor) | `.foregroundColor` (UIColor/NSColor) |
| Paragraph style | `kCTParagraphStyleAttributeName` (CTParagraphStyle) | `.paragraphStyle` (NSParagraphStyle) |
| Kern | `kCTKernAttributeName` | `.kern` |

**When creating attributed strings for Core Text directly, use the `kCT*` keys.** Mixing Core Text keys and UIKit keys in the same attributed string can cause subtle rendering differences.

In practice, UIKit's `.font` attribute (UIFont) works with Core Text because UIFont wraps a CTFont internally. But `.foregroundColor` (UIColor) does NOT — Core Text needs CGColor.

## Common Pitfalls

1. **Forgetting to flip coordinates** — Core Text is bottom-left origin. UIKit is top-left. Text appears upside-down or at wrong position. Always set `context.textMatrix = .identity` and flip.
2. **Not resetting text matrix** — `CGContext.textMatrix` persists between drawing calls. If a previous operation set a non-identity matrix, your Core Text drawing will be transformed unexpectedly.
3. **String indices are UTF-16** — `CTRunGetStringIndices` returns UTF-16 code unit indices (matching NSString), not Swift Character indices. A single emoji can span 2-4 UTF-16 units.
4. **CTFont ≠ UIFont on iOS** — They are NOT toll-free bridged on iOS. Create CTFont explicitly.
5. **CTFrameGetLines returns non-retained array** — In Swift this is usually managed automatically, but be careful with the CFArray if you bridge to C.
6. **Attribute key mismatch** — `kCTForegroundColorAttributeName` expects CGColor, not UIColor. Passing UIColor silently fails (no color rendered).
7. **Character-glyph mapping is not 1:1** — Ligatures produce fewer glyphs than characters. Complex scripts (Arabic, Devanagari) can produce more glyphs than characters. Always use `CTRunGetStringIndices` for the mapping.
8. **CTParagraphStyle is not NSParagraphStyle** — They are related but not interchangeable. CTParagraphStyle uses a C struct API; NSParagraphStyle has Objective-C properties. NSParagraphStyle internally wraps CTParagraphStyle.

## Related Skills

- Use the **textkit-reference** agent for the TextKit 2 APIs that sit above Core Text.
- Use the **textkit-reference** agent when NSLayoutManager's glyph APIs are sufficient (no need to drop lower).
- Use the **textkit-reference** agent for how Core Text fits into the rendering pipeline.
- Use the **rich-text-reference** agent when CTRunDelegate is used for inline non-text content.

---

# Foundation Text Utilities Reference

Use this skill when you need the exact Foundation or NaturalLanguage tool for a text-processing problem.

## When to Use

- You need `NSRegularExpression`, `NSDataDetector`, or NaturalLanguage APIs.
- You are measuring text or bridging `String` and `NSString`.
- The question is about utility APIs, not parser choice alone.

## Quick Decision

- Need parser choice guidance -> the parsing section in this reference
- Need the exact utility API or compatibility details -> stay here
- Need attributed-text model guidance instead of utilities -> the **rich-text-reference** agent

## Core Guidance

## NSRegularExpression

ICU-compatible regex engine. Reference type.

```swift
let pattern = "\\b[A-Z][a-z]+\\b"
let regex = try NSRegularExpression(pattern: pattern, options: [.caseInsensitive])

// Find all matches
let text = "Hello World from Swift"
let fullRange = NSRange(text.startIndex..., in: text)
let matches = regex.matches(in: text, range: fullRange)

for match in matches {
    if let range = Range(match.range, in: text) {
        print(text[range])
    }
}

// First match only
let firstMatch = regex.firstMatch(in: text, range: fullRange)

// Number of matches
let count = regex.numberOfMatches(in: text, range: fullRange)

// Replace
let replaced = regex.stringByReplacingMatches(
    in: text, range: fullRange,
    withTemplate: "[$0]"
)

// Enumerate matches
regex.enumerateMatches(in: text, range: fullRange) { result, flags, stop in
    guard let result else { return }
    // Process match
}
```

### Options

```swift
NSRegularExpression.Options:
    .caseInsensitive      // i
    .allowCommentsAndWhitespace  // x
    .ignoreMetacharacters  // literal match
    .dotMatchesLineSeparators    // s
    .anchorsMatchLines     // m
    .useUnixLineSeparators
    .useUnicodeWordBoundaries
```

### Capture Groups

```swift
let regex = try NSRegularExpression(pattern: "(\\w+)@(\\w+\\.\\w+)")
let text = "user@example.com"
if let match = regex.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)) {
    // match.range(at: 0) — full match
    // match.range(at: 1) — first group ("user")
    // match.range(at: 2) — second group ("example.com")
    let user = String(text[Range(match.range(at: 1), in: text)!])
    let domain = String(text[Range(match.range(at: 2), in: text)!])
}
```

### Modern Alternative: Swift Regex (iOS 16+)

```swift
let regex = /(?<user>\w+)@(?<domain>\w+\.\w+)/
if let match = text.firstMatch(of: regex) {
    let user = match.user
    let domain = match.domain
}

// With RegexBuilder
import RegexBuilder
let pattern = Regex {
    Capture { OneOrMore(.word) }
    "@"
    Capture { OneOrMore(.word); "."; OneOrMore(.word) }
}
```

**When to use NSRegularExpression vs Swift Regex:**
- NSRegularExpression: Dynamic patterns (user input), pre-iOS 16, NSRange-based APIs
- Swift Regex: Static patterns, type-safe captures, iOS 16+

## NSDataDetector

Detects semantic data in natural language text. Subclass of NSRegularExpression.

```swift
let types: NSTextCheckingResult.CheckingType = [.link, .phoneNumber, .address, .date]
let detector = try NSDataDetector(types: types.rawValue)

let text = "Call 555-1234 on March 15, 2025 or visit https://apple.com"
let matches = detector.matches(in: text, range: NSRange(text.startIndex..., in: text))

for match in matches {
    switch match.resultType {
    case .link:
        print("URL: \(match.url!)")
    case .phoneNumber:
        print("Phone: \(match.phoneNumber!)")
    case .address:
        print("Address: \(match.addressComponents!)")
    case .date:
        print("Date: \(match.date!)")
    case .transitInformation:
        print("Flight: \(match.components!)")
    default: break
    }
}
```

### Supported Types

| Type | Properties | Example |
|------|-----------|---------|
| `.link` | `url` | "https://apple.com" |
| `.phoneNumber` | `phoneNumber` | "555-1234" |
| `.address` | `addressComponents` | "1 Apple Park Way, Cupertino" |
| `.date` | `date`, `duration`, `timeZone` | "March 15, 2025" |
| `.transitInformation` | `components` (airline, flight) | "UA 123" |

### Modern Alternative: DataDetection (iOS 18+)

```swift
import DataDetection
// New API with structured results and better accuracy
```

## NaturalLanguage Framework (iOS 12+)

Replaces deprecated `NSLinguisticTagger`.

### NLTagger

Tag text with linguistic information:

```swift
import NaturalLanguage

let tagger = NLTagger(tagSchemes: [.lexicalClass, .nameType, .lemma])
tagger.string = "Apple released new iPhones in Cupertino"

// Enumerate tags
tagger.enumerateTags(
    in: tagger.string!.startIndex..<tagger.string!.endIndex,
    unit: .word,
    scheme: .lexicalClass
) { tag, range in
    if let tag {
        print("\(tagger.string![range]): \(tag.rawValue)")
        // "Apple": Noun, "released": Verb, etc.
    }
    return true
}
```

### Tag Schemes

| Scheme | Tags | Purpose |
|--------|------|---------|
| `.tokenType` | `.word`, `.punctuation`, `.whitespace` | Token classification |
| `.lexicalClass` | `.noun`, `.verb`, `.adjective`, `.adverb`, etc. | Part of speech |
| `.nameType` | `.personalName`, `.placeName`, `.organizationName` | Named entity recognition |
| `.lemma` | (base form string) | Word lemmatization |
| `.language` | (BCP 47 code) | Per-word language |
| `.script` | (ISO 15924 code) | Writing script |

### NLTokenizer

Segment text into tokens:

```swift
let tokenizer = NLTokenizer(unit: .word)  // .word, .sentence, .paragraph, .document
tokenizer.string = "Hello, world! How are you?"

tokenizer.enumerateTokens(in: tokenizer.string!.startIndex..<tokenizer.string!.endIndex) { range, attrs in
    print(tokenizer.string![range])
    return true
}
// Output: "Hello", "world", "How", "are", "you"
```

### NLLanguageRecognizer

Identify language of text:

```swift
let recognizer = NLLanguageRecognizer()
recognizer.processString("Bonjour le monde")
let language = recognizer.dominantLanguage  // .french

// With probabilities
let hypotheses = recognizer.languageHypotheses(withMaximum: 3)
// [.french: 0.95, .italian: 0.03, .spanish: 0.02]

// Constrain to specific languages
recognizer.languageConstraints = [.english, .french, .german]

// Language hints (prior probabilities)
recognizer.languageHints = [.french: 0.8, .english: 0.2]
```

### NLEmbedding

Word and sentence embeddings for semantic similarity:

```swift
// Built-in word embeddings
if let embedding = NLEmbedding.wordEmbedding(for: .english) {
    let distance = embedding.distance(between: "king", and: "queen")

    // Find nearest neighbors
    embedding.enumerateNeighbors(for: "swift", maximumCount: 5) { neighbor, distance in
        print("\(neighbor): \(distance)")
        return true
    }
}

// Sentence embedding (iOS 14+)
if let sentenceEmbedding = NLEmbedding.sentenceEmbedding(for: .english) {
    let distance = sentenceEmbedding.distance(
        between: "The cat sat on the mat",
        and: "A feline rested on the rug"
    )
}
```

### Custom NLModel (via Create ML)

```swift
// Load trained model
let model = try NLModel(mlModel: MyTextClassifier().model)

// Classify text
let label = model.predictedLabel(for: "This is great!")
// e.g., "positive"

// With confidence
let hypotheses = model.predictedLabelHypotheses(for: "This is great!", maximumCount: 3)
```

## NSStringDrawingContext

Controls text drawing behavior, especially scaling:

```swift
let context = NSStringDrawingContext()
context.minimumScaleFactor = 0.5  // Allow shrinking to 50%

let boundingRect = CGRect(x: 0, y: 0, width: 200, height: 50)
attributedString.draw(with: boundingRect,
                      options: [.usesLineFragmentOrigin],
                      context: context)

// Check what scale was actually used
print("Scale used: \(context.actualScaleFactor)")
// 1.0 = no shrinking needed, < 1.0 = text was shrunk
```

### Bounding Rect Calculation

```swift
// Calculate size needed for attributed string
let size = attributedString.boundingRect(
    with: CGSize(width: maxWidth, height: .greatestFiniteMagnitude),
    options: [.usesLineFragmentOrigin, .usesFontLeading],
    context: nil
).size

// Round up for pixel alignment
let ceilSize = CGSize(width: ceil(size.width), height: ceil(size.height))
```

**Options:**
- `.usesLineFragmentOrigin` — Multi-line text (ALWAYS include for multi-line)
- `.usesFontLeading` — Include font leading in height
- `.truncatesLastVisibleLine` — Truncate if exceeds bounds

## String / NSString Bridging

### Key Differences

| Aspect | String (Swift) | NSString (ObjC) |
|--------|---------------|-----------------|
| **Encoding** | UTF-8 internal | UTF-16 internal |
| **Indexing** | `String.Index` (Character) | `Int` (UTF-16 code unit) |
| **Count** | `.count` (Characters) | `.length` (UTF-16 units) |
| **Empty check** | `.isEmpty` | `.length == 0` |
| **Type** | Value type | Reference type |

### Bridging Cost

```swift
let swiftStr: String = "Hello"
let nsStr = swiftStr as NSString     // Bridge (may defer copy)
let backStr = nsStr as String         // Bridge back

// NSRange ↔ Range conversion
let nsRange = NSRange(swiftStr.startIndex..., in: swiftStr)
let swiftRange = Range(nsRange, in: swiftStr)
```

**Performance note:** Bridging is NOT zero-cost. UTF-8 ↔ UTF-16 conversion may occur. For tight loops with Foundation APIs, consider working with NSString directly.

### Common Pattern: NSRange from String

```swift
let text = "Hello 👋🏽 World"

// ✅ CORRECT: Using String for conversion
let nsRange = NSRange(text.range(of: "World")!, in: text)

// ✅ CORRECT: Full range
let fullRange = NSRange(text.startIndex..., in: text)

// ❌ WRONG: Assuming character count = NSString length
let badRange = NSRange(location: 0, length: text.count)  // WRONG for emoji/CJK
```

**Why counts differ:** `"👋🏽".count` = 1 (one Character), `("👋🏽" as NSString).length` = 4 (four UTF-16 code units).

## Quick Reference

| Need | API | Min OS |
|------|-----|--------|
| Pattern matching (dynamic) | NSRegularExpression | All |
| Pattern matching (static) | Swift Regex | iOS 16 |
| Detect links/phones/dates | NSDataDetector | All |
| Detect data (modern) | DataDetection | iOS 18 |
| Part of speech tagging | NLTagger (.lexicalClass) | iOS 12 |
| Named entity recognition | NLTagger (.nameType) | iOS 12 |
| Language detection | NLLanguageRecognizer | iOS 12 |
| Text segmentation | NLTokenizer | iOS 12 |
| Word similarity | NLEmbedding.wordEmbedding | iOS 13 |
| Sentence similarity | NLEmbedding.sentenceEmbedding | iOS 14 |
| Custom classifier | NLModel + Create ML | iOS 12 |
| Text measurement | NSAttributedString.boundingRect | All |
| Draw text with scaling | NSStringDrawingContext | All |

## Common Pitfalls

1. **Assuming String.count == NSString.length** — They use different counting units (Characters vs UTF-16). Always convert ranges explicitly.
2. **Missing `.usesLineFragmentOrigin`** — Without this option, `boundingRect` calculates for single-line text.
3. **NSRegularExpression with user input** — Always `try` the constructor — invalid patterns throw.
4. **NLTagger requires enough text** — Very short strings produce unreliable linguistic analysis.
5. **Bridging in hot loops** — String ↔ NSString conversion has overhead. Keep one type in tight loops.

## Related Skills

- Use the parsing section in this reference for Swift Regex vs `NSRegularExpression` choice.
- Use the **rich-text-reference** agent when parsing feeds Markdown-rendering workflows.
- Use the **rich-text-reference** agent when utility output becomes attributed content.

---

# Text Parsing Approaches

Swift Regex vs NSRegularExpression — when to use which, performance, and TextKit integration.

## When to Use

- You are choosing between Swift Regex and `NSRegularExpression`.
- You are wiring parsing into TextKit or editor code.
- You need tradeoffs around ranges, performance, or deployment target.

## Quick Decision

```
Deployment target iOS 16+?
    YES → Need dynamic pattern (user input)?
        YES → try Regex(userPattern) or NSRegularExpression (both runtime)
        NO → Swift Regex literal (/pattern/) — compile-time validated
    NO → NSRegularExpression (only option)

Working with TextKit / NSAttributedString APIs (NSRange)?
    → NSRegularExpression gives NSRange directly
    → Swift Regex gives Range<String.Index> — needs NSRange(range, in:) bridge

Complex parsing with dates/numbers?
    → Swift Regex + Foundation parsers (.date(), .currency())

Need readable, maintainable pattern?
    → RegexBuilder DSL
```

## Core Guidance

## Swift Regex (iOS 16+)

### Three Creation Methods

```swift
// 1. Regex literal — compile-time validated, strongly typed
let emailRegex = /(?<user>\w+)@(?<domain>\w+\.\w+)/

// 2. String-based — runtime, AnyRegexOutput (loses type safety)
let dynamicRegex = try Regex(patternString)

// 3. RegexBuilder DSL — structured, self-documenting
import RegexBuilder
let emailPattern = Regex {
    Capture { OneOrMore(.word) }
    "@"
    Capture {
        OneOrMore(.word)
        "."
        OneOrMore(.word)
    }
}
```

### Pros

- **Compile-time validation** — regex literals catch syntax errors at build time
- **Type-safe captures** — output types known at compile time (`Regex<(Substring, Substring)>`)
- **Unicode-correct** — matches extended grapheme clusters, canonical equivalence by default
- **Foundation parser integration** — embed `.date()`, `.currency()`, `.localizedInteger`
- **Native String indices** — results use `Range<String.Index>`
- **RegexBuilder readability** — self-documenting, modular components
- **Backtracking control** — `Local { }` for atomic groups, `.repetitionBehavior(.reluctant)`

### Cons

- **iOS 16+ only**
- **No direct NSRange** — must bridge for TextKit APIs
- **New engine** — less battle-tested than ICU
- **`AnyRegexOutput`** — string-constructed regexes lose type safety
- **Learning curve** — RegexBuilder is a new paradigm

### String Methods

```swift
let text = "Hello World 2025"

// Check if matches
text.contains(/\d+/)

// First match
if let match = text.firstMatch(of: /(\d+)/) {
    let number = match.1  // Substring "2025"
}

// All match ranges
let ranges = text.ranges(of: /\w+/)

// Replace
let result = text.replacing(/\d+/, with: "YEAR")

// Split
let parts = text.split(separator: /\s+/)

// Trim prefix
let trimmed = text.trimmingPrefix(/Hello\s*/)
```

### Foundation Parser Integration

```swift
import RegexBuilder

let dateRegex = Regex {
    "Date: "
    Capture { .date(.numeric, locale: .current, timeZone: .current) }
}

let currencyRegex = Regex {
    "Price: "
    Capture { .localizedCurrency(code: "USD") }
}

// Parses "Date: 03/15/2025" → actual Date object
// Parses "Price: $42.99" → actual Decimal value
```

## NSRegularExpression

### Pros

- **All OS versions** — no deployment target restrictions
- **NSRange native** — works directly with TextKit, NSAttributedString APIs
- **ICU engine** — mature, well-tested, predictable performance
- **Familiar syntax** — standard POSIX/ICU regex

### Cons

- **No compile-time checking** — pattern errors are runtime exceptions
- **String-based** — no type safety, easy typos
- **NSRange/String.Index mismatch** — UTF-16 offsets vs grapheme clusters
- **Verbose API** — manual range extraction from `NSTextCheckingResult`
- **No parser integration** — must post-process captures manually

### TextKit Integration Pattern

```swift
let regex = try NSRegularExpression(pattern: "\\b(TODO|FIXME|HACK)\\b")
let text = textStorage.string
let fullRange = NSRange(location: 0, length: textStorage.length)

regex.enumerateMatches(in: text, range: fullRange) { match, flags, stop in
    guard let matchRange = match?.range else { return }
    // Direct NSRange — works immediately with NSAttributedString
    textStorage.addAttribute(.foregroundColor, value: UIColor.orange, range: matchRange)
}
```

## Bridging Swift Regex to NSRange

When using Swift Regex with TextKit/NSAttributedString APIs:

```swift
let text = textStorage.string

// Swift Regex match
if let match = text.firstMatch(of: /TODO:\s*(.+)/) {
    // Convert Range<String.Index> → NSRange
    let fullNSRange = NSRange(match.range, in: text)
    let captureNSRange = NSRange(match.1.startIndex..<match.1.endIndex, in: text)

    // Now use with NSAttributedString
    textStorage.addAttribute(.foregroundColor, value: UIColor.red, range: fullNSRange)
    textStorage.addAttribute(.font, value: UIFont.boldSystemFont(ofSize: 14), range: captureNSRange)
}

// All matches
for match in text.matches(of: /\b\w+\b/) {
    let nsRange = NSRange(match.range, in: text)
    // Use nsRange with TextKit
}
```

**Bridging cost:** `NSRange(range, in: string)` is O(1) for contiguous strings. Lightweight but adds a line per use.

## Performance Comparison

| Aspect | Swift Regex | NSRegularExpression |
|--------|-------------|---------------------|
| **Simple patterns** | Comparable | Comparable (ICU mature) |
| **Complex backtracking** | `Local { }` prevents catastrophic backtracking | ICU may catastrophically backtrack |
| **Compilation** | Regex literals: compile-time; Regex(string): runtime | Always runtime |
| **Match execution** | New engine, improving | ICU, very optimized |
| **Foundation parsers** | Single-pass date/currency extraction | Regex + manual parsing (two passes) |
| **Hot loop** | Benchmark both | May have slight edge for simple patterns |

**Practical advice:** For most text processing, the performance difference is negligible. Choose based on:
1. Deployment target (iOS 16+ required for Swift Regex)
2. Whether you need NSRange directly (TextKit) or Range<String.Index>
3. Whether type-safe captures matter for your use case

## Syntax Highlighting Pattern

### With NSRegularExpression (TextKit-native)

```swift
func highlightSyntax(in range: NSRange, textStorage: NSTextStorage) {
    let text = textStorage.string

    // Keywords
    let keywordRegex = try! NSRegularExpression(pattern: "\\b(func|var|let|class|struct|enum|if|else|for|while|return)\\b")
    keywordRegex.enumerateMatches(in: text, range: range) { match, _, _ in
        guard let r = match?.range else { return }
        textStorage.addAttribute(.foregroundColor, value: UIColor.systemPink, range: r)
    }

    // Strings
    let stringRegex = try! NSRegularExpression(pattern: "\"[^\"]*\"")
    stringRegex.enumerateMatches(in: text, range: range) { match, _, _ in
        guard let r = match?.range else { return }
        textStorage.addAttribute(.foregroundColor, value: UIColor.systemRed, range: r)
    }

    // Comments
    let commentRegex = try! NSRegularExpression(pattern: "//.*$", options: .anchorsMatchLines)
    commentRegex.enumerateMatches(in: text, range: range) { match, _, _ in
        guard let r = match?.range else { return }
        textStorage.addAttribute(.foregroundColor, value: UIColor.systemGreen, range: r)
    }
}
```

### With Swift Regex (Bridged)

```swift
func highlightSyntax(in range: NSRange, textStorage: NSTextStorage) {
    let text = textStorage.string
    guard let swiftRange = Range(range, in: text) else { return }
    let substring = text[swiftRange]

    // Keywords — type-safe, compile-time validated
    for match in substring.matches(of: /\b(func|var|let|class|struct|enum|if|else|for|while|return)\b/) {
        let nsRange = NSRange(match.range, in: text)
        textStorage.addAttribute(.foregroundColor, value: UIColor.systemPink, range: nsRange)
    }
}
```

## When to Use Which — Summary

| Scenario | Recommendation |
|----------|---------------|
| iOS 16+ app, new code | Swift Regex |
| Must support iOS 15 or earlier | NSRegularExpression |
| Heavy TextKit integration (NSRange everywhere) | NSRegularExpression or Swift Regex with bridging |
| Complex parsing with dates/numbers | Swift Regex (Foundation parsers) |
| User-supplied patterns | Either (both support runtime patterns) |
| Compile-time safety desired | Swift Regex literals |
| Syntax highlighting in NSTextStorage delegate | NSRegularExpression (NSRange native, no bridging) |
| Readable, maintainable complex patterns | RegexBuilder DSL |

## Common Pitfalls

1. **String.count ≠ NSString.length** — Swift Regex uses String.Index (grapheme clusters). NSRegularExpression uses NSRange (UTF-16). Always bridge explicitly.
2. **Compiling NSRegularExpression in a loop** — Cache the compiled regex. Construction is expensive.
3. **Forgetting `try` on Regex(string)** — Runtime-constructed regexes can throw.
4. **Using `AnyRegexOutput` when type safety matters** — Prefer regex literals for static patterns.
5. **Not using `.anchorsMatchLines` for per-line matching** — Default anchors match document start/end only.

## Related Skills

- Use the foundation ref section in this reference for the wider Foundation text utility catalog.
- Use the **rich-text-reference** agent when the parsing question is really Markdown rendering or intent handling.
- Use the **rich-text-reference** agent when parsing output feeds attributed-text pipelines.
