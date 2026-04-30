---
name: txt-view-picker
description: Choose between SwiftUI Text/TextField/TextEditor, UIKit UITextView, and AppKit NSTextView. Capability comparison, tradeoffs, and decision criteria for read-only display vs single-line input vs multi-line editing vs rich attributed editing vs TextKit access. Use when the user asks "which text view should I use," "should I use TextField or TextEditor," "do I need UITextView for this," or describes a feature without naming a view class. Do NOT use for wrapping UITextView in SwiftUI — see txt-wrap-textview. Do NOT use for SwiftUI/TextKit attribute compatibility rules — see txt-swiftui-interop. Do NOT use for the iOS 26 SwiftUI TextEditor rich-text APIs themselves — see txt-swiftui-texteditor.
license: MIT
---

# Apple Text View Picker

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill is a capability comparison across the Apple text views. The capability matrix below is a starting point; before committing a view choice, open the actual feature requirements list and confirm each line item against the matrix — view selection mistakes propagate into wrapper code, performance work, and Writing Tools integration that are expensive to undo. If you are deciding based on a single requirement, you have not surveyed the full requirement set yet.

A view class isn't picked from the framework alone. SwiftUI `Text` displays attributed strings but ignores `paragraphStyle`. SwiftUI `TextField` accepts a vertical axis since iOS 16 and handles many cases that previously required `UITextView`. SwiftUI `TextEditor` gained real rich-text editing on iOS 26 but still cannot do inline images, lists, or TextKit access. The right answer depends on the *combination* of features you need, the deployment floor, and whether the view will be wrapped, embedded, or composed.

## Contents

- [The view classes](#the-view-classes)
- [Display vs editing](#display-vs-editing)
- [SwiftUI plain-text editing](#swiftui-plain-text-editing)
- [When you need TextKit access](#when-you-need-textkit-access)
- [Common decisions](#common-decisions)
- [Quick code patterns](#quick-code-patterns)
- [Common mistakes](#common-mistakes)
- [References](#references)

## The view classes

Five views cover almost every case:

- **`Text`** (SwiftUI) — read-only display. Renders `String`, `LocalizedStringKey`, and a defined subset of `AttributedString` attributes. No editing, no cursor.
- **`TextField`** (SwiftUI) — single-line editing by default; multi-line via `axis: .vertical` since iOS 16. Plain `String` binding, with `format:` for typed values.
- **`TextEditor`** (SwiftUI) — multi-line editing. Plain `String` on iOS 14-25; `AttributedString` rich-text editing on iOS 26+.
- **`UITextView`** (UIKit) — full TextKit-backed editor. Attributed text, attachments, layout managers, custom rendering, Writing Tools.
- **`NSTextView`** (AppKit) — desktop counterpart with field-editor architecture, text tables, rulers, Services menu, NSText heritage (RTF/RTFD I/O).

`UILabel` / `NSTextField` exist for the cases where a view doesn't wrap into the SwiftUI hierarchy. They're rarely the answer in a SwiftUI app — `Text` and `TextField` cover the same ground.

## Display vs editing

If the text is read-only, the choice collapses fast. SwiftUI `Text` is the right answer for nearly all read-only display, including styled `AttributedString`, inline Markdown literals, and dynamic text composition via the `+` operator. The exceptions are narrow:

- Need range-select-and-copy on iOS — `Text.textSelection(.enabled)` only supports select-all on iOS; range selection works on macOS but not iOS.
- Need TextKit-rendered features the SwiftUI subset omits (paragraph styles, attachments, exclusion paths, custom rendering attributes) — drop to a `UITextView` or `NSTextView` configured non-editable.
- Need to render block-level Markdown (headings, lists, blockquotes) — `Text` only renders inline Markdown; block structure ends up in `presentationIntent` and is silently ignored. Either preprocess into a SwiftUI view tree or render via TextKit.

For editing, the question is what kind of input.

## SwiftUI plain-text editing

If the binding can stay as `String`, SwiftUI is usually the right call. `TextField` covers single-line and (since iOS 16) modest multi-line growth. `TextEditor` covers always-multi-line editing.

`TextField(axis: .vertical)` is underused — it grows to fit content, accepts `lineLimit(2...8)` for bounded growth, supports a placeholder via the `prompt` parameter, and behaves correctly inside forms and lists. For chat composers and comment fields it is almost always the right answer over `TextEditor` or a wrapped `UITextView`.

`TextEditor` is the right choice when the editor must always be multi-line, when there is no placeholder requirement, or when you need iOS 26 rich-text editing. On iOS 25 and earlier, `TextEditor` is plain-text only and has no `prompt` — overlay a `Text` view manually if a placeholder is needed, or use `TextField(axis: .vertical)`.

The iOS 26 rich-text variant (`TextEditor` with `AttributedString` binding) handles bold/italic/underline, foreground/background colors, alignment, line height, and writing direction. Genmoji insertion works. What it can't do — inline images, lists, tables, exclusion paths, TextKit access, custom layout — is a real ceiling, so check requirements before picking it for anything beyond simple rich text.

## When you need TextKit access

The boundary at which SwiftUI stops working is well-defined. Drop to `UITextView` (or `NSTextView`) when any of these are true:

- You need to inspect or manipulate `textStorage`, `layoutManager` (TK1), or `textLayoutManager` (TK2).
- You need temporary attributes for syntax highlighting (TextKit 1) or rendering attributes (TextKit 2).
- You need inline `NSTextAttachment` views.
- You need exclusion paths, multi-column layout, or `NSTextTable`.
- You need full Writing Tools delegate control beyond the default behavior.
- You need a custom input accessory view, custom keyboard, or marked-text handling.
- You need spellcheck customization beyond `UITextInputTraits`.

Once any of these is on the requirement list, SwiftUI text views become a poor fit and a `UIViewRepresentable` wrapping `UITextView` (or `NSViewRepresentable` wrapping `NSTextView` inside an `NSScrollView`) is the path. The wrapping mechanics are non-trivial — that is its own skill.

`UITextView` and `NSTextView` are not interchangeable. `UITextView` *is* a `UIScrollView`, has `UITextInteraction` for modular gestures, and gained `UITextItem` interactions in iOS 17. `NSTextView` lives inside an `NSScrollView`, owns text tables, ruler, font panel, Services menu, and NSText's RTF I/O. Cross-platform code typically wraps each in its own representable.

## Common decisions

A few cases come up often enough to spell out:

- **Chat composer that grows vertically.** `TextField(axis: .vertical)` first. Drop to a wrapped `UITextView` only if you need attributed editing, attachments, or TextKit features. Don't reach for `TextEditor` here — it always takes its full proposed height and has no placeholder.

- **Notes editor with rich text on iOS 26+.** Try `TextEditor` with `AttributedString` first. Drop to a wrapped `UITextView` if you need attachments, lists, or TextKit access.

- **Notes editor with rich text on iOS 25 or earlier.** Wrapped `UITextView`. Plain `TextEditor` doesn't accept `AttributedString` on those versions.

- **Syntax-highlighted code editor.** Wrapped `UITextView` / `NSTextView`. TextKit 1 if you need temporary attributes (proven, fast) or glyph metrics; TextKit 2 if viewport performance on huge files is critical. Neither is "legacy" or "modern" — they solve different problems.

- **Static styled label.** `Text` with an `AttributedString` or inline Markdown literal. `UILabel` only when you can't be in SwiftUI.

- **Settings-style form input.** `TextField`. Use `format:` for typed values (currency, integers, dates).

- **Markdown rendering, display only.** If only inline Markdown (bold, italic, links, code) — `Text` with `AttributedString(markdown:)`. If block-level (headings, lists, quotes) — TextKit-backed view or a third-party SwiftUI Markdown renderer.

- **Document editor with text tables, rulers, or printing.** `NSTextView` on macOS. UIKit has no equivalent for text tables or rulers.

## Quick code patterns

Read-only styled text in SwiftUI:

```swift
// Inline Markdown literal — interpreted at compile time
Text("Visit **[example.com](https://example.com)** today.")

// Runtime AttributedString
var attr = AttributedString("Important note")
attr.foregroundColor = .red
attr.font = .body.bold()
Text(attr).textSelection(.enabled)
```

Single-line input with a typed value:

```swift
@State private var price: Double = 0

TextField("Price", value: $price, format: .currency(code: "USD"))
    .textFieldStyle(.roundedBorder)
    .keyboardType(.decimalPad)
    .submitLabel(.done)
```

Vertical-axis chat composer:

```swift
TextField("Compose…", text: $body, axis: .vertical)
    .lineLimit(2...8)
```

iOS 26 rich-text editing:

```swift
@State private var text = AttributedString("Edit this text")

var body: some View {
    TextEditor(text: $text)
}
```

Wrapped UITextView for rich editing on older iOS or when TextKit access is needed:

```swift
struct RichTextEditor: UIViewRepresentable {
    @Binding var attributedText: NSAttributedString

    func makeUIView(context: Context) -> UITextView {
        let tv = UITextView()
        tv.delegate = context.coordinator
        tv.backgroundColor = .clear  // let SwiftUI background show
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

The wrapper above is a starting sketch. Real-world wrappers have to handle focus, sizing, cursor preservation, and update-loop guards correctly — see the wrap-textview skill.

## Common mistakes

1. **Reaching for `UITextView` when `TextField(axis: .vertical)` would work.** The vertical-axis `TextField` covers the chat-composer case natively since iOS 16, including placeholder, line-limit growth, and form integration. A wrapped `UITextView` is the right answer only when attributed editing, attachments, or TextKit access is on the requirement list. Defaulting to a wrapper to "be safe" buys complexity you'll pay for in update-loop bugs and focus management.

2. **Expecting full Markdown to render in SwiftUI `Text`.** Inline Markdown (bold, italic, code, links) renders. Block-level Markdown (headings, lists, blockquotes, code blocks) is parsed into `presentationIntent` and silently dropped from the rendered output. The text appears unformatted. If block-level rendering matters, use TextKit, a third-party SwiftUI Markdown view, or render the parsed structure into a SwiftUI view tree manually.

3. **Setting `attributedText` in `updateUIView` without an equality check.** Each set triggers `textViewDidChange`, which writes back to the binding, which calls `updateUIView`, which sets `attributedText` again. Infinite loop, or at minimum cursor jumps every keystroke. Guard with `guard tv.attributedText != attributedText else { return }`.

4. **Relying on `Text.textSelection(.enabled)` for range selection on iOS.** On iOS, the modifier enables select-all only. Range selection works on macOS but not iOS. If users need to copy a substring on iOS, use a non-editable `UITextView` instead.

5. **Wrapping `UITextView` without `backgroundColor = .clear`.** UIKit's default `systemBackground` color paints over any SwiftUI background, list separator styling, or material effect behind the wrapped view. Always clear the background and let SwiftUI's chrome show through.

6. **Using `TextEditor` when you actually need a placeholder.** `TextEditor` has no `prompt` parameter on any iOS version. Either overlay a `Text` view manually (showing/hiding based on the binding being empty) or switch to `TextField(axis: .vertical)`, which has `prompt` and similar growth behavior.

7. **Picking `TextEditor` with `AttributedString` for production rich-text on iOS 26.** It works for simple cases. It cannot do inline images, lists, tables, exclusion paths, or TextKit access. If rich text is mission-critical or the app needs iOS 25 support, a wrapped `UITextView` remains the safer choice. Treat the iOS 26 path as additive, not a replacement.

## References

- `references/reference.md` — capability matrix and platform-by-platform reference, loaded only when needed
- `references/examples.md` — usage-oriented examples, loaded only when needed
- `/skill txt-wrap-textview` — wrapping `UITextView` / `NSTextView` in SwiftUI
- `/skill txt-swiftui-interop` — which AttributedString attributes survive the SwiftUI/TextKit boundary
- `/skill txt-swiftui-texteditor` — iOS 26 SwiftUI TextEditor rich-text APIs
- `/skill txt-textkit-choice` — TextKit 1 vs TextKit 2 decision
- `/skill txt-appkit-vs-uikit` — NSTextView vs UITextView capability comparison
- [SwiftUI Text](https://sosumi.ai/documentation/swiftui/text)
- [SwiftUI TextField](https://sosumi.ai/documentation/swiftui/textfield)
- [SwiftUI TextEditor](https://sosumi.ai/documentation/swiftui/texteditor)
- [UITextView](https://sosumi.ai/documentation/uikit/uitextview)
- [NSTextView](https://sosumi.ai/documentation/appkit/nstextview)
