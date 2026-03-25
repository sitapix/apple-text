---
name: apple-text-representable
description: Use when wrapping UITextView or NSTextView in SwiftUI — binding, focus, sizing, cursor preservation, or update loops
license: MIT
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
- Need cross-framework type/rendering limits instead of wrapper mechanics -> `/skill apple-text-swiftui-bridging`

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
- Use `/skill apple-text-swiftui-bridging` for type-scope and rendering-boundary questions.
- Use `/skill apple-text-layout-manager-selection` when wrapper behavior depends on TextKit 1 vs 2.
