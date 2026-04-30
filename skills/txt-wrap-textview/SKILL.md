---
name: txt-wrap-textview
description: Wrap UITextView (UIViewRepresentable) and NSTextView (NSViewRepresentable) inside SwiftUI without breaking editing. Covers binding sync, infinite-update-loop guards, cursor preservation across programmatic mutations, focus / first-responder bridging, auto-sizing strategies, environment value propagation, toolbar integration, and the iOS vs macOS scroll-view differences. Use when building or debugging a SwiftUI text-view wrapper, when cursor jumps after typing, when binding updates don't propagate, when @FocusState seems ignored, or when a wrapped editor won't size to its content. Do NOT use for picking which view class (txt-view-picker) or for which AttributedString attributes survive the SwiftUI boundary (txt-swiftui-interop).
license: MIT
---

# Wrapping UITextView and NSTextView in SwiftUI

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

The patterns here are the recurring failure modes in `UIViewRepresentable` and `NSViewRepresentable` wrappers around text views. They are not a template to copy — every wrapper has to handle binding equality, cursor preservation, and focus bridging, but the right shape depends on what binding type you carry, whether the editor is single- or multi-line, and what the surrounding SwiftUI layout proposes. Read your existing wrapper (or write a small one) before quoting fixes from this document.

A bug in a wrapped text view is almost always one of three things: an infinite update loop because `updateUIView` writes without checking equality, a cursor jump because programmatic mutations reset `selectedRange`, or stale bindings because the coordinator's parent reference wasn't refreshed. If symptoms don't match one of those, the bug is probably in the surrounding SwiftUI hierarchy (keyboard avoidance, parent layout, environment churn) rather than the wrapper itself.

## Contents

- [The minimal correct wrapper](#the-minimal-correct-wrapper)
- [Update-loop and cursor-jump guards](#update-loop-and-cursor-jump-guards)
- [Production wrapping rules](#production-wrapping-rules)
- [Auto-sizing](#auto-sizing)
- [Focus / first responder](#focus--first-responder)
- [NSViewRepresentable on macOS](#nsviewrepresentable-on-macos)
- [Environment values](#environment-values)
- [Toolbar integration](#toolbar-integration)
- [Common mistakes](#common-mistakes)
- [References](#references)

## The minimal correct wrapper

A wrapper that handles binding sync, equality guards, cursor preservation, and coordinator parent refresh:

```swift
struct RichTextView: UIViewRepresentable {
    @Binding var text: NSAttributedString
    var uiFont: UIFont = .preferredFont(forTextStyle: .body)
    var textColor: UIColor = .label

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIView(context: Context) -> UITextView {
        let tv = UITextView()
        tv.delegate = context.coordinator
        tv.font = uiFont
        tv.textColor = textColor
        tv.backgroundColor = .clear            // let SwiftUI bg show
        tv.textContainerInset = UIEdgeInsets(top: 8, left: 4, bottom: 8, right: 4)
        return tv
    }

    func updateUIView(_ tv: UITextView, context: Context) {
        // 1. Refresh coordinator's parent so delegate callbacks see fresh bindings.
        context.coordinator.parent = self

        // 2. Equality guard — the only way to avoid the update loop.
        if tv.attributedText != text {
            let saved = tv.selectedRange
            tv.attributedText = text
            // Clamp selection to the new length.
            let len = (tv.text as NSString).length
            let loc = min(saved.location, len)
            let lengthCap = max(0, len - loc)
            tv.selectedRange = NSRange(location: loc,
                                       length: min(saved.length, lengthCap))
        }

        // 3. React to environment changes.
        tv.isEditable = context.environment.isEnabled
    }

    final class Coordinator: NSObject, UITextViewDelegate {
        var parent: RichTextView
        init(_ parent: RichTextView) { self.parent = parent }

        func textViewDidChange(_ tv: UITextView) {
            // Async to avoid "Modifying state during view update" warnings.
            DispatchQueue.main.async { self.parent.text = tv.attributedText }
        }
    }
}
```

Three lines deserve attention. `context.coordinator.parent = self` refreshes the captured wrapper struct so the delegate writes to the current binding, not a stale copy. `if tv.attributedText != text` is the equality guard that breaks the otherwise infinite write/notify/update cycle. The save/restore around `selectedRange` keeps the cursor where the user left it instead of jumping to the end.

The wrapper accepts `UIFont` and `UIColor`, not SwiftUI `Font` and `Color`. There is no public conversion from SwiftUI types to UIKit types — accept the UIKit versions in your wrapper API and let callers translate, or wire to `Font.preferredFont(forTextStyle:)` for Dynamic Type.

## Update-loop and cursor-jump guards

The infinite-update problem is structural. SwiftUI re-runs `updateUIView` whenever the surrounding state changes; if `updateUIView` always writes to `attributedText`, every write triggers the delegate, which writes back to the binding, which triggers `updateUIView` again. The equality guard breaks the cycle. It is not optional and not "an optimization" — without it, typing produces dropped characters or hard hangs, and programmatic edits produce visible flicker.

Use `!=` on the actual content. `NSAttributedString.isEqual(_:)` does deep comparison including attributes; that's what `!=` calls. For `String` bindings, plain `!=` works. For `AttributedString` bindings, `!=` works but is more expensive than the NS equivalent on long strings — only pay that cost when needed.

The cursor-jump problem is separate: assigning `attributedText` resets `selectedRange` to the end of the new text. After every programmatic assignment, save the old range, do the assignment, then clamp the saved range to the new length and re-assign. The clamp step matters — if the new text is shorter than `saved.location + saved.length`, restoring the raw range raises an exception.

A subtler trap: don't save the cursor before the equality guard. Save it after the guard fires (so you only do the work when you're actually mutating), and do the save *before* the assignment. The order is read range → assign text → write range.

Delegate callbacks have to dispatch their state writes to the next runloop tick:

```swift
func textViewDidChange(_ tv: UITextView) {
    DispatchQueue.main.async { self.parent.text = tv.attributedText }
}
```

Synchronous writes during `textViewDidChange` produce "Modifying state during view update" warnings and, on some configurations, crashes. If one delegate callback is async, make all related callbacks async to preserve relative ordering — mixed sync/async produces ordering races.

## Production wrapping rules

Two rules generalize the wrapping work into something an editor wrapper can be checked against (popularised by Chris Eidhof in his SwiftUI/UIKit interop writing): bidirectional equality guards on every cross-boundary write, and async dispatch for any UIKit-triggered SwiftUI mutation. The first prevents the update loop, the second keeps state writes out of the SwiftUI update cycle. Together they're sufficient — almost every reproducible "wrapper feels broken" report violates one or both.

Under Swift 6, the `Coordinator` should be `@MainActor`. `UIView` and `NSView` are `@MainActor`-isolated as of Swift 6's UIKit/AppKit annotations, so a coordinator that holds a reference to the wrapped view inherits the same isolation. Making the coordinator explicitly `@MainActor` keeps the compiler honest about the actor context of delegate callbacks, which all run on the main actor anyway:

```swift
@MainActor
final class Coordinator: NSObject, UITextViewDelegate {
    var parent: RichTextView
    init(_ p: RichTextView) { parent = p }
    // …
}
```

If the wrapper is a struct held across actor boundaries (it shouldn't be in normal usage, but `Sendable` checks may flag it), the binding-mutation closures inside delegate methods are the natural seams to resolve isolation warnings.

A useful alternative to the raw `@Binding` shape, attributed to Malcolm Hall: store a *closure* in the wrapper instead of a binding, and refresh state from `updateUIView`. The wrapper takes `var onTextChange: (NSAttributedString) -> Void` instead of `@Binding var text: NSAttributedString`. The coordinator calls `parent.onTextChange(tv.attributedText)` from `textViewDidChange`; the calling SwiftUI view passes a closure that updates whatever model it owns. This pattern is well-suited to editor wrappers where the "current text" lives in an `ObservableObject` document model rather than a SwiftUI `@State` — the wrapper stays untangled from the binding's update mechanics, and the document model controls when/how to mutate. RichTextKit and STTextView use a similar context-object architecture rather than threading bindings through every wrapper layer.

The combined trap to avoid: declaring `intrinsicContentSize` on the wrapped view *plus* writing height back into a SwiftUI `@State` from `textViewDidChange`. Both mechanisms try to drive the wrapper's layout, and they don't agree on timing — the result is an infinite-pass layout loop that compiles, runs, and burns CPU. Pick one: `sizeThatFits(_:uiView:context:)` on iOS 16+ (the right answer when available), or external height tracking — never both at once.

## Auto-sizing

The "expanding text view" problem has two reasonable answers depending on iOS version.

**iOS 16+:** override `sizeThatFits(_:uiView:context:)` on the representable. This is the right answer when available:

```swift
@available(iOS 16.0, *)
func sizeThatFits(_ proposal: ProposedViewSize, uiView: UITextView, context: Context) -> CGSize? {
    guard let width = proposal.width else { return nil }
    uiView.isScrollEnabled = false
    let size = uiView.sizeThatFits(CGSize(width: width, height: .greatestFiniteMagnitude))
    return CGSize(width: width, height: size.height)
}
```

`isScrollEnabled = false` is required — a scrolling `UITextView` reports its frame size, not its content size. With it disabled, `sizeThatFits` returns the height needed to render all content at the proposed width.

**iOS 13-15:** track height via a state binding driven from `textViewDidChange`. Update only when the height actually changes, otherwise SwiftUI re-runs layout on every keystroke even when nothing moved.

`UIViewRepresentable` is known to ignore `invalidateIntrinsicContentSize()` (FB8499811). Don't try to use intrinsic content size as an auto-sizing strategy — `sizeThatFits` or external height tracking are the working paths.

## Focus / first responder

`@FocusState` does not bridge into `UIViewRepresentable`. A wrapped `UITextView` neither participates in `@FocusState` nor honors `.focused()`. Bridge manually:

```swift
struct FocusableTextView: UIViewRepresentable {
    @Binding var isFocused: Bool

    func updateUIView(_ tv: UITextView, context: Context) {
        // Async — UIKit may not have placed the view in a window yet.
        if isFocused && !tv.isFirstResponder {
            DispatchQueue.main.async { tv.becomeFirstResponder() }
        } else if !isFocused && tv.isFirstResponder {
            DispatchQueue.main.async { tv.resignFirstResponder() }
        }
    }

    final class Coordinator: NSObject, UITextViewDelegate {
        var parent: FocusableTextView
        init(_ p: FocusableTextView) { parent = p }

        func textViewDidBeginEditing(_ tv: UITextView) {
            DispatchQueue.main.async { self.parent.isFocused = true }
        }
        func textViewDidEndEditing(_ tv: UITextView) {
            DispatchQueue.main.async { self.parent.isFocused = false }
        }
    }
}
```

`becomeFirstResponder()` called synchronously inside `updateUIView` can fail silently when the view hasn't entered the window hierarchy yet. The async dispatch defers it to a runloop turn where the view is attached.

If the wrapper is inside a `ScrollView` and `becomeFirstResponder()` produces a double-offset on keyboard appearance, the SwiftUI keyboard avoidance is fighting `UIScrollView.contentInset`. `.ignoresSafeArea(.keyboard)` on the scroll view is the usual fix.

## NSViewRepresentable on macOS

The macOS shape is similar but with structural differences worth knowing:

```swift
struct MacTextView: NSViewRepresentable {
    @Binding var text: NSAttributedString

    func makeNSView(context: Context) -> NSScrollView {
        let scroll = NSTextView.scrollableTextView()
        let tv = scroll.documentView as! NSTextView
        tv.delegate = context.coordinator
        tv.isEditable = true
        tv.isRichText = true
        tv.allowsUndo = true
        tv.autoresizingMask = [.width]
        tv.textContainer?.widthTracksTextView = true
        return scroll
    }

    func updateNSView(_ nsView: NSScrollView, context: Context) {
        guard let tv = nsView.documentView as? NSTextView else { return }
        context.coordinator.parent = self

        if tv.attributedString() != text {
            let saved = tv.selectedRanges
            tv.textStorage?.setAttributedString(text)
            tv.selectedRanges = saved
        }
    }

    final class Coordinator: NSObject, NSTextViewDelegate {
        var parent: MacTextView
        init(_ p: MacTextView) { parent = p }

        func textDidChange(_ note: Notification) {
            guard let tv = note.object as? NSTextView else { return }
            DispatchQueue.main.async { self.parent.text = tv.attributedString() }
        }
    }
}
```

Key differences from UIKit:

- `NSTextView` is **not** a scroll view. The `NSViewRepresentable` returns an `NSScrollView` with the text view as its `documentView`. `NSTextView.scrollableTextView()` constructs the pair correctly.
- Read attributed text via `attributedString()` (a method, not a property) and write via `textStorage?.setAttributedString(_:)` for proper undo registration.
- Selection is `selectedRanges` (`[NSValue]`), not `selectedRange` (`NSRange`).
- The delegate is `NSTextViewDelegate`. The change notification is `textDidChange(_:)`, a `Notification`-based callback.
- Unlike UIKit, `NSViewRepresentable` does honor `intrinsicContentSize` invalidation correctly.

## Environment values

SwiftUI tracks which `context.environment` keys you read inside `updateUIView` and re-runs the closure only when those keys change:

```swift
func updateUIView(_ tv: UITextView, context: Context) {
    tv.font = .preferredFont(forTextStyle: .body)         // Dynamic Type
    tv.isEditable = context.environment.isEnabled         // .disabled() modifier
    if context.environment.colorScheme == .dark { … }     // Dark Mode
}
```

Reading an environment value subscribes the wrapper to changes; not reading it leaves the wrapper untouched on those changes. Don't read environment values defensively — only the ones you actually use.

## Toolbar integration

Three patterns work for adding format buttons to a wrapped editor:

- **SwiftUI keyboard toolbar.** Apply `.toolbar { ToolbarItemGroup(placement: .keyboard) { … } }` to the representable. Pure SwiftUI, but each button needs a way to reach the underlying text view — usually via a coordinator-held `weak` reference or a shared formatting model.
- **UIKit `inputAccessoryView`.** Construct a `UIToolbar`, set its actions to coordinator selectors, and assign to `tv.inputAccessoryView`. Lives entirely below the SwiftUI surface, so it doesn't interact with SwiftUI's keyboard avoidance.
- **Shared formatting model.** Define an `ObservableObject` carrying `isBold`, `isItalic`, etc. SwiftUI buttons mutate it; the coordinator observes and applies attributes to `textStorage`. Cleanest separation when the toolbar lives elsewhere in the SwiftUI tree.

The third pattern scales best in real apps because the toolbar can live anywhere — a custom view above the editor, a `Menu` button, a separate panel — without the editor needing to know.

## Common mistakes

1. **Forgetting `context.coordinator.parent = self` at the top of `updateUIView`.** The coordinator captured a snapshot of the wrapper struct at init. Without this refresh, delegate callbacks write to the binding the wrapper had when the coordinator was created, which is often the wrong one after re-renders. Symptom: typing in the editor doesn't update the binding, or updates a stale binding tree, or works on first render but breaks after a parent state change.

2. **Setting `attributedText` without an equality check.** Every assignment triggers `textViewDidChange`, which writes the binding, which calls `updateUIView`, which assigns again. Either an infinite loop or a flicker plus dropped characters. Always guard:

   ```swift
   // WRONG — drops characters or loops
   func updateUIView(_ tv: UITextView, context: Context) {
       tv.attributedText = text
   }

   // CORRECT — guarded
   func updateUIView(_ tv: UITextView, context: Context) {
       context.coordinator.parent = self
       if tv.attributedText != text {
           tv.attributedText = text
       }
   }
   ```

3. **Synchronous state writes in delegate callbacks.** Writing to a SwiftUI `@Binding` synchronously from `textViewDidChange` runs inside SwiftUI's view update cycle and produces "Modifying state during view update" warnings, occasional crashes, and ordering bugs. Wrap state writes in `DispatchQueue.main.async`. If you make one delegate callback async, make all related ones async to preserve ordering.

4. **Not preserving `selectedRange` across programmatic edits.** Assigning `attributedText` resets the selection to the end. The user perceives this as the cursor jumping every time the wrapper updates. Save before the assignment, clamp to new length, restore after.

5. **Forgetting `backgroundColor = .clear` on the wrapped view.** UIKit's default `systemBackground` paints a solid color over the SwiftUI background, list-row separator, or material effect. The wrapper appears to ignore SwiftUI styling. Set the background to clear unless you specifically want UIKit's color.

6. **Using `ScrollView` around the representable on iOS without `.ignoresSafeArea(.keyboard)`.** SwiftUI's keyboard avoidance and `UITextView`'s own contentInset both adjust for the keyboard, producing a double offset. Either use `.ignoresSafeArea(.keyboard)` on the scroll view or remove the SwiftUI scroll view entirely and let the text view scroll itself.

7. **Trying to use `intrinsicContentSize` for auto-sizing.** `UIViewRepresentable` ignores `invalidateIntrinsicContentSize()` calls (FB8499811). The intrinsic size path doesn't reliably trigger SwiftUI re-layout. Use `sizeThatFits(_:uiView:context:)` on iOS 16+ or external height tracking on older versions.

## References

- `/skill txt-view-picker` — choosing whether you need a wrapper at all
- `/skill txt-swiftui-interop` — which AttributedString attributes survive the SwiftUI/TextKit boundary
- `/skill txt-textkit-debug` — diagnosing editor behavior bugs that aren't wrapper-mechanic issues
- [UIViewRepresentable](https://sosumi.ai/documentation/swiftui/uiviewrepresentable)
- [NSViewRepresentable](https://sosumi.ai/documentation/swiftui/nsviewrepresentable)
- [UITextView](https://sosumi.ai/documentation/uikit/uitextview)
- [NSTextView](https://sosumi.ai/documentation/appkit/nstextview)
