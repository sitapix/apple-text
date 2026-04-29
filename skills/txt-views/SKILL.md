---
name: txt-views
description: Use when choosing between SwiftUI Text/TextField/TextEditor, UITextView, or NSTextView — capabilities and tradeoffs
license: MIT
---

# Apple Text Views

Use this skill when the main question is "which text view should I use?" or when behavior depends on the capabilities of a specific view class.

## When to Use

- You are choosing among SwiftUI, UIKit, and AppKit text views.
- The question is mostly about capability tradeoffs, not low-level TextKit APIs.
- You need to know whether the problem belongs in `Text`, `TextField`, `TextEditor`, `UITextView`, or `NSTextView`.

## Quick Decision

**Read-only text in SwiftUI** -> `Text`

**Single-line input in SwiftUI** -> `TextField`

**Multi-line plain-text editing in SwiftUI** -> `TextEditor`

**Rich text, TextKit access, syntax highlighting, attachments, or custom layout on iOS** -> `UITextView`

**Rich text, field editor behavior, text tables, rulers, printing, or advanced desktop editing on macOS** -> `NSTextView`

**Static UIKit label** -> `UILabel`

**Simple UIKit/AppKit form input** -> `UITextField` / `NSTextField`

## Core Guidance

## Decision Guide

### 1. Are you editing text?

**No** -> Prefer `Text` or `UILabel`.

**Yes** -> Go to step 2.

### 2. Is plain-text SwiftUI editing enough?

Use `TextField` or `TextEditor` when all of these are true:

- You only need plain `String` editing
- You do not need TextKit APIs
- You do not need inline attachments or rich attributed editing
- You can accept SwiftUI's editing limitations

If any of those are false, move to `UITextView` or `NSTextView`.

### 3. Do you need TextKit or attributed text control?

Use `UITextView` / `NSTextView` when you need:

- `NSAttributedString` or advanced `AttributedString` bridging
- Layout inspection or fragment-level queries
- Syntax highlighting or custom rendering
- Inline attachments or custom attachment views
- Rich editing commands, menus, or selection behavior
- Writing Tools coordination beyond basic defaults

### 4. Do you need TextKit 2 specifically?

**Use TextKit 1** (`NSLayoutManager`) when you need:

- Glyph-level access (custom glyph drawing, glyph metrics, `shouldGenerateGlyphs`)
- Multi-page or multi-column layout (multiple text containers)
- Syntax highlighting via temporary attributes (proven, reliable)
- Text tables (`NSTextTable`, macOS)
- Printing with full pagination control

**Use TextKit 2** (`NSTextLayoutManager`) when you need:

- Viewport-based layout for large documents
- Writing Tools full inline experience
- Correct complex-script rendering by default (Arabic, Devanagari, CJK)
- Modern rendering and layout APIs

Neither is "legacy" or "modern" — they solve different problems. TextKit 1 is the right choice for glyph-level work even in a brand-new app.

For the actual TextKit 1 vs 2 choice, use `/skill txt-textkit-choice`.

## Common Decisions

**Chat composer that grows vertically** -> `TextField(axis: .vertical)` first, `UITextView` if you need richer editing behavior.

**Notes editor with rich text** -> `UITextView` on iOS, `NSTextView` on macOS.

**Syntax-highlighted code editor** -> `UITextView` / `NSTextView`. TextKit 1 if you need temporary attributes (proven) or glyph metrics; TextKit 2 if you need viewport performance on very large files.

**Simple settings field** -> `TextField`, `UITextField`, or `NSTextField`.

**Markdown display only** -> `Text` if the supported inline subset is enough; otherwise use TextKit-backed rendering.

**Need AppKit-only document editor features** -> `NSTextView`.

## Quick Code Patterns

### Read-only styled text in SwiftUI

```swift
// Inline Markdown (literal only — runtime strings need AttributedString)
Text("Visit **[example.com](https://example.com)** today.")

// AttributedString with selective styling (iOS 15+)
var attr = AttributedString("Important note")
attr.foregroundColor = .red
attr.font = .body.bold()
Text(attr).textSelection(.enabled)
```

### Single-line input with formatting (TextField)

```swift
@State private var price: Double = 0

TextField("Price", value: $price, format: .currency(code: "USD"))
    .textFieldStyle(.roundedBorder)
    .keyboardType(.decimalPad)
    .submitLabel(.done)
```

### Multi-line plain editor (TextEditor / TextField axis: .vertical)

```swift
// Pre-iOS 16: TextEditor (always multi-line, no prompt)
TextEditor(text: $body)
    .scrollContentBackground(.hidden)
    .background(Color(.systemGray6))

// iOS 16+: TextField with vertical axis (better placeholder support)
TextField("Compose…", text: $body, axis: .vertical)
    .lineLimit(2...8)
```

### Rich text editor (UIViewRepresentable wrapping UITextView)

```swift
struct RichTextEditor: UIViewRepresentable {
    @Binding var attributedText: NSAttributedString

    func makeUIView(context: Context) -> UITextView {
        let tv = UITextView()
        tv.delegate = context.coordinator
        tv.backgroundColor = .clear  // avoid painting over SwiftUI bg
        return tv
    }

    func updateUIView(_ tv: UITextView, context: Context) {
        guard tv.attributedText != attributedText else { return }  // prevent loop
        tv.attributedText = attributedText
    }

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    final class Coordinator: NSObject, UITextViewDelegate {
        var parent: RichTextEditor
        init(_ p: RichTextEditor) { parent = p }
        func textViewDidChange(_ tv: UITextView) {
            parent.attributedText = tv.attributedText
        }
    }
}
```

For wrapper details (focus, sizing, cursor preservation), see `/skill txt-representable`.

## Common Mistakes

1. **Reaching for `UITextView` when `TextField(axis: .vertical)` would work** — iOS 16+ vertical TextField handles the chat-composer case natively. Drop down only when you need attributed editing or TextKit access.
2. **Expecting full Markdown in SwiftUI `Text`** — only inline (bold/italic/code/links). Headings, lists, and blockquotes are silently dropped from the rendered output but preserved in `presentationIntent`.
3. **Setting `attributedText` in `updateUIView` without an equality check** — causes infinite update loops. Always guard the assignment.
4. **Relying on `Text.textSelection(.enabled)` for range selection on iOS** — iOS only supports select-all; range selection is macOS-only.
5. **Wrapping `UITextView` without `backgroundColor = .clear`** — UIKit's default white background paints over SwiftUI styling.
6. **Using `TextEditor` when you actually need a placeholder** — `TextEditor` has no `prompt` parameter. Either overlay a `Text` view manually or use `TextField(axis: .vertical)`.

## Related Skills

- For the full catalog, capabilities tables, and platform-by-platform reference, see [reference.md](references/reference.md).
- For usage-oriented examples, see [examples.md](references/examples.md).
- For wrapping `UITextView` or `NSTextView` in SwiftUI, use `/skill txt-representable`.
- For the TextKit 1 vs 2 decision, use `/skill txt-textkit-choice`.
- For TextKit 1 architecture, use `/skill txt-textkit1`. For TextKit 2, use `/skill txt-textkit2`.
- For SwiftUI bridging tradeoffs, use `/skill txt-swiftui-bridging`.
- For debugging weird editor behavior, use `/skill txt-textkit-debug`.
