---
name: txt-uitextinput
description: Implement UITextInput, UIKeyInput, or NSTextInputClient in custom views — marked text for CJK input, position and range arithmetic, geometry for system UI, inputDelegate notifications, UITextInteraction adoption. Use when building a text-editing view that does not derive from UITextView or NSTextView and the keyboard, autocorrect, selection handles, magnifier, or IME input is wrong or missing. Do NOT use for selection or edit-menu customization on stock UITextView/NSTextView (see txt-selection-menus) or for find/replace UI (see txt-find-replace).
license: MIT
---

# UITextInput / NSTextInputClient

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill is for implementing the input contracts that UIKit and AppKit require of any view that wants real text editing — keyboard, IME, selection handles, magnifier, autocorrect. The contract is large and most of it has to be right at the same time before the system stops misbehaving. Before claiming any specific API signature, fetch the current Apple docs via Sosumi (`sosumi.ai/documentation/uikit/uitextinput`) — protocol surface and inputDelegate timing have shifted across iOS versions.

If the question is how to customize a stock `UITextView` or `NSTextView`, this is the wrong skill. The protocol implementation here exists *underneath* those views; touching it on a stock view is fighting the framework. This skill applies when you genuinely have no UIKit text view to lean on.

## Contents

- [Protocol layering](#protocol-layering)
- [UIKeyInput minimum](#uikeyinput-minimum)
- [UITextInput — required surface](#uitextinput--required-surface)
- [Marked text and IME input](#marked-text-and-ime-input)
- [Geometry methods](#geometry-methods)
- [inputDelegate notifications](#inputdelegate-notifications)
- [Selection display and loupe](#selection-display-and-loupe)
- [NSTextInputClient on macOS](#nstextinputclient-on-macos)
- [UITextInteraction wiring](#uitextinteraction-wiring)
- [Key commands and multi-scene focus](#key-commands-and-multi-scene-focus)
- [Edge cases and regressions](#edge-cases-and-regressions)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Protocol layering

UIKit splits text input into two protocols. `UIKeyInput` is the floor: `insertText(_:)`, `deleteBackward()`, `hasText`. It produces a keyboard, accepts Latin keys, and nothing else. CJK input methods, autocorrect, selection handles, and copy/paste require the larger `UITextInput` protocol, which extends `UIKeyInput`.

A view that adopts `UITextInput` must also be a `UIResponder` with `canBecomeFirstResponder` returning `true`, and must instantiate concrete subclasses of `UITextPosition` and `UITextRange` to represent positions in its content. Those classes are abstract; instantiate `UITextPosition` directly and the system silently rejects every position you return.

```swift
final class MyPosition: UITextPosition {
    let offset: Int
    init(_ offset: Int) { self.offset = offset; super.init() }
}

final class MyRange: UITextRange {
    let _start: MyPosition
    let _end: MyPosition
    init(start: MyPosition, end: MyPosition) {
        self._start = start; self._end = end; super.init()
    }
    override var start: UITextPosition { _start }
    override var end: UITextPosition { _end }
    override var isEmpty: Bool { _start.offset == _end.offset }
}
```

## UIKeyInput minimum

A pure `UIKeyInput` view is fine for password fields, PIN entry, and other single-stage Latin input. The system gives you a keyboard the moment the view becomes first responder.

```swift
final class PinEntryView: UIView, UIKeyInput {
    private(set) var text = ""
    var hasText: Bool { !text.isEmpty }
    func insertText(_ s: String) { text += s; setNeedsDisplay() }
    func deleteBackward() { _ = text.popLast(); setNeedsDisplay() }
    override var canBecomeFirstResponder: Bool { true }
}
```

`UIKeyInput` cannot satisfy CJK input methods. Multi-stage composition needs marked text, which only exists on `UITextInput`. If users will type Chinese, Japanese, Korean, or use Apple Pencil Scribble for handwriting, the floor is too low.

## UITextInput — required surface

The system calls into the protocol in roughly four groups: text access, position arithmetic, range construction, and selection. Every one of these has to round-trip correctly with your storage representation, or the keyboard, autocorrect, and selection state get into a bad state that doesn't recover until the view is rebuilt.

```swift
// Text access — main edit entry point from the system
func text(in range: UITextRange) -> String?
func replace(_ range: UITextRange, withText text: String)

// Position arithmetic
func position(from p: UITextPosition, offset: Int) -> UITextPosition?
func position(from p: UITextPosition, in dir: UITextLayoutDirection, offset: Int) -> UITextPosition?
func offset(from a: UITextPosition, to b: UITextPosition) -> Int
func compare(_ a: UITextPosition, to b: UITextPosition) -> ComparisonResult

// Range construction
func textRange(from a: UITextPosition, to b: UITextPosition) -> UITextRange?

// Selection (cursor is a zero-length range)
var selectedTextRange: UITextRange? { get set }

// Document bounds
var beginningOfDocument: UITextPosition { get }
var endOfDocument: UITextPosition { get }

// Word/sentence/paragraph boundaries
var tokenizer: UITextInputTokenizer { get }   // typically UITextInputStringTokenizer(textInput: self)
```

Position arithmetic is unforgiving. `offset(from:to:)` and `position(from:offset:)` must agree: `position(from: a, offset: offset(from: a, to: b))` must compare equal to `b`. If your offset counts UTF-16 code units in one method and Swift `Character`s in another, the system computes selection positions that don't exist in your storage and you get either silently wrong selection or `EXC_BAD_ACCESS` in the gesture pipeline.

## Marked text and IME input

Marked text is the provisional, underlined string an IME presents while a user is composing. The system installs it via `setMarkedText(_:selectedRange:)`, mutates it across keystrokes, and resolves it via `unmarkText()` (commit) or another `setMarkedText(nil, ...)` (cancel).

```swift
var markedTextRange: UITextRange? { get }       // nil ⇒ no composition
var markedTextStyle: [NSAttributedString.Key: Any]? { get set }
func setMarkedText(_ text: String?, selectedRange: NSRange)
func unmarkText()
```

The `selectedRange` argument is *relative to the marked text*, not the document. To get the document-level cursor while composing, add `markedTextRange.location`. The composition cursor is what positions the IME candidate window; computing it in the wrong frame leaves the candidate UI floating in the corner.

Two tricky cases recur. First, on iOS the system can call `setMarkedText` twice for what looks like a single composition step; treat each call idempotently and don't accumulate state across them. Second, when the surrounding code is a reactive binding (Combine, SwiftUI `@Binding`, RxSwift), echoing every text change back into the view destroys composition: the IME ends up reading the committed text mid-stroke. Suppress outbound bindings while `markedTextRange != nil`.

```swift
func textChanged() {
    guard markedTextRange == nil else { return }   // skip during composition
    binding.wrappedValue = currentText
}
```

## Geometry methods

The system uses your geometry methods to position the caret, the selection handles, the magnifier loupe, autocorrect bubbles, and the IME candidate window. Wrong rects don't crash — they put system UI in the wrong place.

```swift
func caretRect(for position: UITextPosition) -> CGRect
func firstRect(for range: UITextRange) -> CGRect
func selectionRects(for range: UITextRange) -> [UITextSelectionRect]
func closestPosition(to point: CGPoint) -> UITextPosition?
func closestPosition(to point: CGPoint, within range: UITextRange) -> UITextPosition?
func characterRange(at point: CGPoint) -> UITextRange?
```

`selectionRects(for:)` must return one rect per visual line, not one rect for the whole range. A single rect on multi-line text produces a selection that covers the bounding box of all lines including blank space outside the actual selection. The returned `UITextSelectionRect` subclasses also carry direction and continuation flags the system reads to draw handles correctly.

All geometry must be in the view's own coordinate space. Forgetting to convert from a scroll-view content offset is a typical source of "the cursor is 200 points off when scrolled."

## inputDelegate notifications

When your code mutates text or selection from outside the system call sites (network update, undo, your own gesture), the system needs to be told. If the IME or autocorrect cache thinks the text is one thing and your storage says another, the next system mutation lands in the wrong place.

```swift
weak var inputDelegate: UITextInputDelegate?

func applyExternalEdit() {
    inputDelegate?.textWillChange(self)
    storage.applyEdit()
    inputDelegate?.textDidChange(self)
}

func moveCursorProgrammatically() {
    inputDelegate?.selectionWillChange(self)
    selectedTextRange = newRange
    inputDelegate?.selectionDidChange(self)
}
```

The will/did pair must wrap the actual mutation. Calling `textDidChange` without `textWillChange` first is worse than not calling either — the system invalidates caches based on assumptions that a will/did pair is balanced.

## Selection display and loupe

Adopting `UITextInput` does not by itself draw a caret or selection handles. On modern iOS, the selection UI comes from `UITextSelectionDisplayInteraction`, added as a `UIInteraction`:

```swift
lazy var selectionDisplay = UITextSelectionDisplayInteraction(
    textInput: self,
    delegate: nil
)

override init(frame: CGRect) {
    super.init(frame: frame)
    addInteraction(selectionDisplay)
}

func selectionChanged() {
    selectionDisplay.setNeedsSelectionUpdate()
}
```

For drag-to-position cursor work, `UITextLoupeSession` handles the magnifier:

```swift
let session = UITextLoupeSession.begin(at: point, fromSelectionWidgetView: nil, in: self)
// during drag:
session.move(to: newPoint)
// at end:
session.invalidate()
```

The macOS equivalent of `UITextSelectionDisplayInteraction` is `NSTextInsertionIndicator`, an `NSView` subclass you add to your document view and update as the cursor moves.

## NSTextInputClient on macOS

`NSTextInputClient` is AppKit's analog to `UITextInput`. Same idea, slightly different surface: methods take `NSRange` instead of `UITextRange`, and `setMarkedText` carries an extra `replacementRange` parameter that some Japanese IMEs use to reconvert already-committed text.

```swift
protocol NSTextInputClient {
    func insertText(_ s: Any, replacementRange: NSRange)
    func setMarkedText(_ s: Any, selectedRange: NSRange, replacementRange: NSRange)
    func unmarkText()
    func selectedRange() -> NSRange
    func markedRange() -> NSRange
    func hasMarkedText() -> Bool
    func attributedSubstring(forProposedRange r: NSRange,
                             actualRange: NSRangePointer?) -> NSAttributedString?
    func attributedString() -> NSAttributedString
    func validAttributesForMarkedText() -> [NSAttributedString.Key]
    func firstRect(forCharacterRange r: NSRange,
                   actualRange: NSRangePointer?) -> NSRect
    func characterIndex(for point: NSPoint) -> Int
}
```

After any layout change that moves character coordinates, call `NSTextInputContext.current?.invalidateCharacterCoordinates()` so the IME re-queries `firstRect(forCharacterRange:)`. To force-cancel composition (e.g. on focus change), call `NSTextInputContext.current?.discardMarkedText()`.

## UITextInteraction wiring

`UITextInput` describes the contract; `UITextInteraction` provides the gesture recognizers — tap-to-position, double-tap to select word, long-press for the loupe, the link tap pipeline. Without it the protocol implementation gets typed input but no pointer/touch interaction.

```swift
let interaction = UITextInteraction(for: .editable)   // or .nonEditable
interaction.textInput = self
addInteraction(interaction)
```

Writing Tools, Scribble (Apple Pencil handwriting on iPad), and the Edit menu all rely on a complete `UITextInput` plus `UITextInteraction`. Half-implemented protocols fail these features quietly: Writing Tools shows the panel but skips inline rewrites; Scribble accepts strokes but the inserted text lands at offset zero; the edit menu appears with placeholder items.

## Key commands and multi-scene focus

`UIKeyCommand` registered via `keyCommands` competes with system bindings. For an editor that wants to override Cmd-Left/Right for word navigation or Cmd-Shift-Up for selection extension, set `wantsPriorityOverSystemBehavior = true` on the command. Without it the system handler wins and your routing never runs. This single property is the most commonly missed reason a custom editor's key commands appear to do nothing.

```swift
let cmd = UIKeyCommand(input: UIKeyCommand.inputLeftArrow,
                       modifierFlags: .command,
                       action: #selector(moveToBeginningOfLine))
cmd.wantsPriorityOverSystemBehavior = true
```

Stage Manager and external displays make first-responder scope per-scene. Each `UIWindowScene` has its own first-responder chain, so `keyCommands` registered on a view in the iPad scene do not fire on a window connected to an external display. Use `UIFocusSystem` for cross-window focus reasoning, and restore selection on the active scene in `sceneWillEnterForeground(_:)` so the user's caret position survives a scene swap. If a user resizes a Stage Manager window such that the editor moves between scenes, expect first-responder loss and re-establish it deliberately.

## Edge cases and regressions

iOS 18 introduced a content collector for Apple Intelligence that calls `_intelligenceCollectContent` on text views. A `UITextView` subclass — or any custom `UITextInput` view — that returns an out-of-bounds `NSRange` from `selectedRange` crashes the collector deep in private framework code, with a stack trace that does not mention the editor. Bounds-check the range before returning it, and return the documented sentinel when there is no selection:

```swift
override var selectedRange: NSRange {
    guard hasSelection else {
        return NSRange(location: NSNotFound, length: 0)
    }
    let len = (text as NSString).length
    let loc = max(0, min(_selectedRange.location, len))
    let end = max(loc, min(_selectedRange.location + _selectedRange.length, len))
    return NSRange(location: loc, length: end - loc)
}
```

Mutating text from outside the system while marked text is active breaks IME composition. Setting `text` or `attributedText` in the middle of a Japanese, Korean, or Chinese composition silently commits half-typed characters and leaves the IME's candidate cache pointing at content that no longer exists. React Native explicitly avoids `setAttributedString:` while typing for this reason. Check `markedTextRange == nil` before any external mutation; queue the mutation for after `unmarkText()` resolves the composition if marked text is active:

```swift
func applyExternalEdit(_ edit: () -> Void) {
    guard markedTextRange == nil else {
        pendingEdits.append(edit)
        return
    }
    inputDelegate?.textWillChange(self)
    edit()
    inputDelegate?.textDidChange(self)
}

func unmarkText() {
    super.unmarkText()
    pendingEdits.forEach { applyExternalEdit($0) }
    pendingEdits.removeAll()
}
```

iOS 17 regressed the relationship between `inputView` and `becomeFirstResponder`. Setting `inputView` and immediately calling `becomeFirstResponder` shows the default keyboard, not the custom view. Workaround: call `reloadInputViews()` once the responder chain has settled. The same pattern fixes a custom `inputAccessoryView` that fails to appear on first focus.

```swift
view.inputView = customKeyboard
view.becomeFirstResponder()
view.reloadInputViews()   // forces the custom inputView to actually show
```

## Common Mistakes

1. **Returning `UITextPosition` directly instead of a subclass.** The base class has no usable representation. Subclass it once, hold an `Int` (or whatever your storage indexes by), and return that. Symptom: every selection method silently fails and the keyboard appears to type into nothing.

2. **Mismatching units between offset arithmetic methods.** If `offset(from:to:)` returns Swift `String.distance` and `position(from:offset:)` interprets the offset as UTF-16, multi-byte characters drift on every keystroke. Pick one unit (UTF-16 is the path of least resistance because the system already speaks `NSRange`) and apply it everywhere.

3. **Skipping `inputDelegate` calls around external mutations.** Autocorrect "stops working" with no error. The cache the system keeps about your text is stale; it computes correction ranges against text that's no longer there.

4. **`selectedRange` in `setMarkedText` interpreted as document-relative.** The IME hands you a position inside the marked string. Document position = `markedTextRange.location + selectedRange.location`. Mixing these breaks CJK candidate placement.

5. **Single rect from `selectionRects(for:)` on multi-line ranges.** Selection handles end up inside blank rows. Return one `UITextSelectionRect` per visual line.

6. **Reactive bindings echoing during composition.** A `@Binding<String>` updated on every change writes the in-progress marked text back into the view, which the IME reads as committed text mid-stroke. Guard with `markedTextRange == nil`.

7. **Forgetting `canBecomeFirstResponder`.** The view never gets focus, and so never gets the keyboard. The default returns `false` on `UIView`.

8. **Adopting `UITextInput` without `UITextInteraction`.** The protocol is silent; the interaction makes it audible. Without the interaction there are no selection handles, no loupe, no edit menu.

9. **Stale character coordinates on macOS.** After a layout pass that moved text on screen, the IME's candidate window stays where the old text was. Call `invalidateCharacterCoordinates()` on the input context.

## References

- `txt-selection-menus` — selection UI, edit menus, link taps, gestures on stock text views
- `txt-find-replace` — find/replace UI for editors
- `txt-spell-autocorrect` — spell check and autocorrect, including the UITextInteraction correction trap on custom views
- `txt-writing-tools` — Writing Tools requirements when text input is custom
- [UITextInput](https://sosumi.ai/documentation/uikit/uitextinput)
- [UIKeyInput](https://sosumi.ai/documentation/uikit/uikeyinput)
- [UITextInteraction](https://sosumi.ai/documentation/uikit/uitextinteraction)
- [UITextSelectionDisplayInteraction](https://sosumi.ai/documentation/uikit/uitextselectiondisplayinteraction)
- [UITextLoupeSession](https://sosumi.ai/documentation/uikit/uitextloupesession)
- [NSTextInputClient](https://sosumi.ai/documentation/appkit/nstextinputclient)
- [NSTextInsertionIndicator](https://sosumi.ai/documentation/appkit/nstextinsertionindicator)
