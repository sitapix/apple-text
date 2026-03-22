---
name: editor-reference
description: Look up editor feature APIs — Writing Tools, text interaction, text input, undo/redo, find/replace, pasteboard, spelling, drag-and-drop, accessibility, and Dynamic Type.
model: sonnet
tools:
  - Glob
  - Grep
  - Read
---

# Editor Reference Agent

You answer specific questions about text editor features and interaction APIs.

## Instructions

1. Read the user's question carefully.
2. Find the relevant section in the reference material below.
3. Return ONLY the information that answers their question — maximum 40 lines.
4. Include exact API signatures, code examples, and gotchas when relevant.
5. Do NOT dump all reference material — extract what is relevant.

---

# Writing Tools Integration

Use this skill when the main question is how Writing Tools should integrate with a native or custom editor.

## When to Use

- You are integrating Writing Tools into `UITextView`, `NSTextView`, or a custom text engine.
- You need protected ranges, activity lifecycle hooks, or coordinator APIs.
- Writing Tools appears in the wrong mode or not at all.

## Quick Decision

- Native TextKit text view with standard behavior -> stay with native integration
- Custom `UITextInput`-based editor -> use the custom view path
- Fully custom text engine on current systems -> use `UIWritingToolsCoordinator`

## Core Guidance

## Native Text View Integration

UITextView and NSTextView get Writing Tools automatically. Configure behavior:

### Behavior Modes

```swift
// Full inline experience (default) — proofreading marks, inline rewrites
textView.writingToolsBehavior = .default

// Panel-only — results shown in popover, no inline marks
textView.writingToolsBehavior = .limited

// Disable completely
textView.writingToolsBehavior = .none
```

### Allowed Input Options

```swift
// What content types Writing Tools can process
textView.writingToolsAllowedInputOptions = [.plainText]           // Plain text only
textView.writingToolsAllowedInputOptions = [.plainText, .richText] // Rich text
textView.writingToolsAllowedInputOptions = [.plainText, .richText, .table] // Including tables
```

### TextKit 2 Requirement

**Writing Tools requires TextKit 2 for the full inline experience.** TextKit 1 views only get the limited panel-based experience (no inline proofreading marks).

```swift
// ✅ Gets full inline Writing Tools
let textView = UITextView(usingTextLayoutManager: true)

// ❌ Only gets panel-based Writing Tools
let textView = UITextView(usingTextLayoutManager: false)
```

**Check:** If Writing Tools appears only in a popover (no inline marks), verify the view is using TextKit 2.

## Delegate Methods (UITextView)

### Activity Notifications

```swift
func textViewWritingToolsWillBegin(_ textView: UITextView) {
    // Pause operations that could conflict:
    // - Undo coalescing
    // - Syncing to server
    // - Collaborative editing updates
}

func textViewWritingToolsDidEnd(_ textView: UITextView) {
    // Resume normal operations
}
```

### Checking Active State

```swift
if textView.isWritingToolsActive {
    // Writing Tools is running — don't modify text
} else {
    // Safe to manipulate text
}
```

### Protected Ranges

Exclude ranges from Writing Tools rewriting (code blocks, quotes, citations):

```swift
func textView(_ textView: UITextView,
              writingToolsIgnoredRangesIn enclosingRange: NSRange) -> [NSRange] {
    // Return ranges that should NOT be rewritten
    var protectedRanges: [NSRange] = []

    // Find code blocks
    let codePattern = try! NSRegularExpression(pattern: "```[\\s\\S]*?```")
    let matches = codePattern.matches(in: textView.text, range: enclosingRange)
    protectedRanges.append(contentsOf: matches.map(\.range))

    return protectedRanges
}
```

### NSTextView Equivalents (macOS)

```swift
func textViewWritingToolsWillBegin(_ notification: Notification)
func textViewWritingToolsDidEnd(_ notification: Notification)

// Protected ranges
func textView(_ textView: NSTextView,
              writingToolsIgnoredRangesIn range: NSRange) -> [NSRange]
```

## Custom Text View Integration (iOS 18)

For views using `UITextInput` (not UITextView), Writing Tools is available through the callout bar if the view adopts `UITextInteraction`:

```swift
class CustomTextView: UIView, UITextInput {
    let textInteraction = UITextInteraction(for: .editable)

    override init(frame: CGRect) {
        super.init(frame: frame)
        textInteraction.textInput = self
        addInteraction(textInteraction)
        // Writing Tools appears in callout bar automatically
    }
}
```

**Alternative:** Adopt `UITextSelectionDisplayInteraction` + `UIEditMenuInteraction` separately.

## UIWritingToolsCoordinator (iOS 26+)

For fully custom text engines (not using UITextInput), the coordinator provides direct Writing Tools integration with animation support.

### Setup

```swift
class CustomEditorView: UIView {
    var coordinator: UIWritingToolsCoordinator!

    override init(frame: CGRect) {
        super.init(frame: frame)
        coordinator = UIWritingToolsCoordinator(delegate: self)
        addInteraction(coordinator)
    }
}
```

### Delegate Protocol

All methods are **async**:

```swift
extension CustomEditorView: UIWritingToolsCoordinatorDelegate {
    // Provide text content for Writing Tools to process
    func writingToolsCoordinator(
        _ coordinator: UIWritingToolsCoordinator,
        requestsContextFor ranges: [UIWritingToolsCoordinator.TextRange]
    ) async -> UIWritingToolsCoordinator.Context {
        let attributedString = getAttributedString(for: ranges)
        return UIWritingToolsCoordinator.Context(
            attributedString: attributedString,
            range: NSRange(location: 0, length: attributedString.length)
        )
    }

    // Handle text replacement
    func writingToolsCoordinator(
        _ coordinator: UIWritingToolsCoordinator,
        replaceRange range: UIWritingToolsCoordinator.TextRange,
        with attributedString: NSAttributedString,
        reason: UIWritingToolsCoordinator.TextReplacementReason
    ) async {
        applyReplacement(attributedString, in: range)
    }

    // State changes
    func writingToolsCoordinator(
        _ coordinator: UIWritingToolsCoordinator,
        didChangeState newState: UIWritingToolsCoordinator.State
    ) {
        switch newState {
        case .idle:
            resumeNormalEditing()
        case .nonInteractive:
            pauseEditing()
        case .interactiveStreaming:
            showStreamingUI()
        @unknown default:
            break
        }
    }
}
```

### Animation Support

The coordinator supports animated text transitions:

```swift
// Provide preview for animation (text snapshot before change)
func writingToolsCoordinator(
    _ coordinator: UIWritingToolsCoordinator,
    requestsPreviewFor range: UIWritingToolsCoordinator.TextRange
) async -> UIWritingToolsCoordinator.TextPreview {
    let rect = getRect(for: range)
    return UIWritingToolsCoordinator.TextPreview(
        textView: self,
        rect: rect
    )
}

// Provide proofreading mark paths (underline positions)
func writingToolsCoordinator(
    _ coordinator: UIWritingToolsCoordinator,
    requestsUnderlinePathFor range: UIWritingToolsCoordinator.TextRange
) async -> UIBezierPath {
    return getUnderlinePath(for: range)
}
```

### NSWritingToolsCoordinator (macOS 26+)

macOS equivalent with the same delegate pattern:

```swift
let coordinator = NSWritingToolsCoordinator(delegate: self)
view.addInteraction(coordinator)
```

## macOS Custom Views (Pre-Coordinator)

For macOS views without UITextInput-equivalent, implement `NSServicesMenuRequestor`:

```swift
// In NSView or NSViewController
override func validRequestor(forSendType sendType: NSPasteboard.PasteboardType?,
                              returnType: NSPasteboard.PasteboardType?) -> Any? {
    if sendType == .string || sendType == .rtf {
        return self
    }
    return super.validRequestor(forSendType: sendType, returnType: returnType)
}

func writeSelection(to pboard: NSPasteboard, types: [NSPasteboard.PasteboardType]) -> Bool {
    pboard.writeObjects([selectedText as NSString])
    return true
}

func readSelection(from pboard: NSPasteboard) -> Bool {
    guard let string = pboard.string(forType: .string) else { return false }
    replaceSelection(with: string)
    return true
}
```

## PresentationIntent (iOS 26+)

Mark text structure for better Writing Tools understanding:

```swift
var str = AttributedString("My Document")

// Mark as heading
str.presentationIntent = .header(level: 1)

// Mark as code block (Writing Tools will protect this)
codeBlock.presentationIntent = .codeBlock(languageHint: "swift")

// Mark as block quote
quote.presentationIntent = .blockQuote
```

## Writing Tools Decision Tree

```
Is your view UITextView or NSTextView?
    YES → Set writingToolsBehavior + delegate methods. Done.
    NO → Does it conform to UITextInput?
        YES → Add UITextInteraction. Writing Tools in callout bar.
        NO → iOS 26+?
            YES → Use UIWritingToolsCoordinator
            NO → Not directly supported. Consider wrapping in UITextView.
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Writing Tools not in menu | `writingToolsBehavior = .none` or Apple Intelligence not enabled | Set `.default`; user must enable Apple Intelligence in Settings |
| Only panel mode, no inline | TextKit 1 mode or fallback | Ensure TextKit 2; check for `layoutManager` access triggering fallback |
| Writing Tools rewrites code | No protected ranges | Implement `writingToolsIgnoredRangesIn` delegate |
| Inline marks not animating | Missing coordinator | Use UIWritingToolsCoordinator (iOS 26+) |
| Text corrupted after rewrite | Editing during active session | Check `isWritingToolsActive` before modifications |

## Common Pitfalls

1. **TextKit 1 fallback kills inline Writing Tools** — Any access to `layoutManager` triggers fallback. Use TextKit 2.
2. **Not pausing operations during Writing Tools** — Server syncs, undo coalescing, etc. can conflict. Use `willBegin`/`didEnd`.
3. **Editing text while Writing Tools is active** — Check `isWritingToolsActive` before programmatic text changes.
4. **Forgetting protected ranges** — Code blocks, quotes, and citations should be excluded from rewriting.
5. **Assuming Writing Tools is always available** — It requires Apple Intelligence enabled. Check availability gracefully.

## Related Skills

- Use the **textkit-reference** agent when Writing Tools behavior depends on TextKit 2 capabilities.
- Use the **textkit-reference** agent when inline Writing Tools drops into limited mode.
- Use the input ref section in this reference for lower-level custom text input requirements.

---

# Text Interaction Customization

Use this skill when the main question is how to customize text interaction behavior beyond the default text view experience.

## When to Use

- Adding custom context menu actions to a text editor
- Handling link taps in a custom way
- Customizing text cursor appearance
- Overriding default selection or editing gestures
- Adding `UITextInteraction` to a custom view

## Quick Decision

- Need text view selection and wrapping -> `/skill apple-text-views`
- Need text input protocol details -> the input ref section in this reference
- Need Writing Tools coordinator -> the writing tools section in this reference
- Need copy/paste behavior -> the pasteboard section in this reference

## Core Guidance

## UIEditMenuInteraction (iOS 16+)

### Overview

`UIEditMenuInteraction` replaces the deprecated `UIMenuController`. It provides the standard edit menu (copy, cut, paste, etc.) and supports custom actions.

`UITextView` uses `UIEditMenuInteraction` automatically. To add custom items, override `canPerformAction` and implement selectors:

```swift
class CustomTextView: UITextView {
    override func canPerformAction(_ action: Selector, withSender sender: Any?) -> Bool {
        if action == #selector(defineWord(_:)) {
            return selectedRange.length > 0
        }
        return super.canPerformAction(action, withSender: sender)
    }

    @objc func defineWord(_ sender: Any?) {
        let word = (text as NSString).substring(with: selectedRange)
        // Present definition
    }
}
```

### Adding Menu Items via UIEditMenuInteraction Delegate

For richer control, add a `UIEditMenuInteraction` directly:

```swift
class EditorView: UIView {
    override func viewDidLoad() {
        let editMenu = UIEditMenuInteraction(delegate: self)
        addInteraction(editMenu)
    }
}

extension EditorView: UIEditMenuInteractionDelegate {
    func editMenuInteraction(
        _ interaction: UIEditMenuInteraction,
        menuFor configuration: UIEditMenuConfiguration,
        suggestedActions: [UIMenuElement]
    ) -> UIMenu? {
        let customAction = UIAction(title: "Format Bold", image: UIImage(systemName: "bold")) { _ in
            self.toggleBold()
        }
        var actions = suggestedActions
        actions.append(customAction)
        return UIMenu(children: actions)
    }
}
```

## Link and Text Item Handling

### UITextItem Interactions (iOS 17+) — Preferred

The modern API for handling taps and long-presses on links, attachments, and custom tagged ranges:

```swift
// Customize tap action for any text item
func textView(_ textView: UITextView,
              primaryActionFor textItem: UITextItem,
              defaultAction: UIAction) -> UIAction? {
    switch textItem.content {
    case .link(let url):
        return UIAction { _ in self.handleLink(url) }
    case .textAttachment(let attachment):
        return UIAction { _ in self.handleAttachment(attachment) }
    case .tag(let tag):
        return UIAction { _ in self.handleTag(tag) }
    @unknown default:
        return defaultAction
    }
}

// Customize long-press context menu for any text item
func textView(_ textView: UITextView,
              menuConfigurationFor textItem: UITextItem,
              defaultMenu: UIMenu) -> UITextItem.MenuConfiguration? {
    switch textItem.content {
    case .tag(let tag):
        let customAction = UIAction(title: "View Profile") { _ in
            self.showProfile(for: tag)
        }
        let menu = UIMenu(children: [customAction] + defaultMenu.children)
        return UITextItem.MenuConfiguration(menu: menu)
    default:
        return UITextItem.MenuConfiguration(menu: defaultMenu)
    }
}
```

### Tagging Custom Interactive Ranges

Make arbitrary text ranges tappable without using `.link` (which forces link styling):

```swift
let attrString = NSMutableAttributedString(string: "@username is here")
attrString.addAttribute(
    .uiTextItemTag,
    value: "user:123",
    range: NSRange(location: 0, length: 9)
)
// The range is now interactive — tap/long-press triggers the delegate methods above
// Unlike .link, it does NOT change the text color to tintColor
```

### Legacy Link Delegate (Pre-iOS 17)

The older API only handles `.link`-attributed ranges. Deprecated in iOS 17:

```swift
func textView(_ textView: UITextView,
              shouldInteractWith URL: URL,
              in characterRange: NSRange,
              interaction: UITextItemInteraction) -> Bool {
    switch interaction {
    case .invokeDefaultAction:
        handleLinkTap(URL)
        return false
    case .presentActions:
        return true
    case .preview:
        return true
    @unknown default:
        return true
    }
}
```

### Making Non-Link Text Tappable

Apply `.link` attribute for simple cases (text gets tintColor styling):

```swift
let attrString = NSMutableAttributedString(string: "@username")
attrString.addAttribute(.link, value: "myapp://user/123", range: NSRange(location: 0, length: 9))
textStorage.append(attrString)
```

For custom styling without tintColor override, use `.uiTextItemTag` instead (iOS 17+).

The text view renders link-attributed text in `tintColor` and makes it tappable. Customize link appearance:

```swift
textView.linkTextAttributes = [
    .foregroundColor: UIColor.systemBlue,
    .underlineStyle: NSUnderlineStyle.single.rawValue
]
```

## UITextInteraction

### Adding Text Interaction to a Custom View

`UITextInteraction` provides selection handles, loupe, and cursor to any view that adopts `UITextInput`:

```swift
class CustomEditorView: UIView, UITextInput {
    let textInteraction = UITextInteraction(for: .editable)

    override init(frame: CGRect) {
        super.init(frame: frame)
        textInteraction.textInput = self
        addInteraction(textInteraction)
    }

    // UITextInput protocol implementation required
    // (see apple-text-input-ref for the full protocol)
}
```

For read-only text, use `.nonEditable`:

```swift
let readOnlyInteraction = UITextInteraction(for: .nonEditable)
```

### Interaction Delegate

```swift
extension CustomEditorView: UITextInteractionDelegate {
    func interactionShouldBegin(
        _ interaction: UITextInteraction,
        at point: CGPoint
    ) -> Bool {
        // Return false to block interaction at certain positions
        // (e.g., over inline buttons or non-text elements)
        return isTextLocation(point)
    }

    func interactionWillBegin(_ interaction: UITextInteraction) {
        // Prepare for interaction (e.g., show cursor)
    }

    func interactionDidEnd(_ interaction: UITextInteraction) {
        // Clean up after interaction
    }
}
```

## Text Cursor Customization

### Cursor Color

```swift
textView.tintColor = .systemRed  // Changes cursor and selection color
```

### Cursor Width (iOS 17+)

```swift
// Use UITextSelectionDisplayInteraction for custom cursor rendering
// The cursor is rendered by the text interaction system
// Custom width requires subclassing or private API (not recommended)
```

### Hiding the Cursor

For presentation-mode or non-editable states where you want text selection without a blinking cursor:

```swift
class NoCursorTextView: UITextView {
    override var caretRect: CGRect {
        // Override caretRect(for:) in UITextInput to return .zero
        return .zero
    }

    override func caretRect(for position: UITextPosition) -> CGRect {
        return .zero  // Hides cursor
    }
}
```

## Selection Customization

### Disabling Selection of Certain Ranges

```swift
func textViewDidChangeSelection(_ textView: UITextView) {
    let selected = textView.selectedRange
    if let protectedRange = protectedRange, NSIntersectionRange(selected, protectedRange).length > 0 {
        // Push selection outside protected range
        textView.selectedRange = NSRange(location: NSMaxRange(protectedRange), length: 0)
    }
}
```

### Custom Selection Granularity

Override selection gestures by intercepting touch handling in a `UITextView` subclass:

```swift
class WordSelectTextView: UITextView {
    override func selectionRects(for range: UITextRange) -> [UITextSelectionRect] {
        // Customize selection rect appearance
        return super.selectionRects(for: range)
    }
}
```

## Gesture Handling

### Intercepting Gestures on UITextView

`UITextView` installs many gesture recognizers for selection, link taps, and editing. Override at the gesture level:

```swift
class CustomGestureTextView: UITextView {
    override func gestureRecognizerShouldBegin(_ gestureRecognizer: UIGestureRecognizer) -> Bool {
        // Block specific system gestures if needed
        if gestureRecognizer is UILongPressGestureRecognizer {
            let point = gestureRecognizer.location(in: self)
            if isOverCustomElement(point) {
                return false  // Let your custom handler take over
            }
        }
        return super.gestureRecognizerShouldBegin(gestureRecognizer)
    }
}
```

### Adding Custom Tap Actions

```swift
let tap = UITapGestureRecognizer(target: self, action: #selector(handleTap(_:)))
tap.delegate = self
textView.addGestureRecognizer(tap)

// In UIGestureRecognizerDelegate:
func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer,
                       shouldRecognizeSimultaneouslyWith other: UIGestureRecognizer) -> Bool {
    return true  // Allow both your tap and text view's taps
}
```

## Common Pitfalls

1. **UIMenuController is deprecated.** Use `UIEditMenuInteraction` on iOS 16+. `UIMenuController` calls still work but will eventually stop.
2. **Link delegate not called for non-editable text views.** `isEditable = false` and `isSelectable = true` is required for link taps to reach the delegate. If `isSelectable` is false, links do not work.
3. **Gesture conflicts with text view.** Adding tap or long-press recognizers to a text view can conflict with the system's text interaction gestures. Use `shouldRecognizeSimultaneously` or check touch location to resolve.
4. **tintColor affects both cursor and links.** There is no separate cursor color API. Both are driven by `tintColor`. To have different colors for cursor and links, customize `linkTextAttributes` separately.

## Related Skills

- Use the input ref section in this reference for the full `UITextInput` protocol.
- Use the writing tools section in this reference for Writing Tools interaction with menus.
- Use the pasteboard section in this reference for copy/paste customization.
- Use `/skill apple-text-views` for view selection decisions.

---

# Text Input Reference

Use this skill when the main question is how custom text input should satisfy UIKit or AppKit input contracts.

## When to Use

- You are implementing `UIKeyInput`, `UITextInput`, or `NSTextInputClient`.
- You need marked-text, selection, or geometry rules for custom editors.
- The problem is lower-level input behavior, not general view selection.

## Quick Decision

- Simple Latin-only input -> `UIKeyInput`
- Full IME, selection, autocorrection, or geometry -> `UITextInput`
- macOS custom input view -> `NSTextInputClient`

## Core Guidance

## Protocol Hierarchy (UIKit)

```
UIResponder
    └── UIKeyInput              (minimal: insert, delete, hasText)
            └── UITextInput     (full: positions, ranges, marked text, geometry)
```

## UIKeyInput (Minimal Input)

Three methods for basic text entry:

```swift
class SimpleInputView: UIView, UIKeyInput {
    var text = ""

    var hasText: Bool { !text.isEmpty }

    func insertText(_ text: String) {
        self.text += text
        setNeedsDisplay()
    }

    func deleteBackward() {
        guard !text.isEmpty else { return }
        text.removeLast()
        setNeedsDisplay()
    }

    override var canBecomeFirstResponder: Bool { true }
}
```

**Sufficient for:** Simple single-stage input (Latin keyboard). Does NOT support:
- CJK multistage input (marked text)
- Autocorrection / spell checking
- Selection / cursor positioning
- Copy/paste

## UITextInput (Full Input)

### Required Custom Types

```swift
// Custom position
class MyTextPosition: UITextPosition {
    let offset: Int
    init(_ offset: Int) { self.offset = offset }
}

// Custom range
class MyTextRange: UITextRange {
    let start: MyTextPosition
    let end: MyTextPosition

    override var start: UITextPosition { _start }
    override var end: UITextPosition { _end }
    override var isEmpty: Bool { _start.offset == _end.offset }

    init(start: Int, end: Int) {
        _start = MyTextPosition(start)
        _end = MyTextPosition(end)
    }
}
```

### Required Protocol Methods (Grouped by Purpose)

#### Text Access

```swift
// Read text in range
func text(in range: UITextRange) -> String?

// Replace text (main edit entry point from system)
func replace(_ range: UITextRange, withText text: String)
```

#### Position Arithmetic

```swift
// Offset from a position
func position(from position: UITextPosition, offset: Int) -> UITextPosition?

// Offset in a direction
func position(from position: UITextPosition, in direction: UITextLayoutDirection,
              offset: Int) -> UITextPosition?

// Distance between positions
func offset(from: UITextPosition, to: UITextPosition) -> Int

// Compare positions
func compare(_ position: UITextPosition, to other: UITextPosition) -> ComparisonResult
```

#### Range Creation

```swift
func textRange(from: UITextPosition, to: UITextPosition) -> UITextRange?
```

#### Selection

```swift
// Current selection (cursor = zero-length range)
var selectedTextRange: UITextRange? { get set }
```

#### Marked Text (CJK/IME)

Marked text is provisionally inserted text during multistage input. Visually distinct (underlined).

```swift
// Current marked text range (nil = no marked text)
var markedTextRange: UITextRange? { get }

// Style dictionary for marked text
var markedTextStyle: [NSAttributedString.Key: Any]? { get set }

// Set marked text with internal selection
func setMarkedText(_ markedText: String?, selectedRange: NSRange)

// Commit marked text
func unmarkText()
```

**Lifecycle:**
1. User starts CJK input → `setMarkedText("拼", selectedRange: NSRange(1, 0))`
2. User continues → `setMarkedText("拼音", selectedRange: NSRange(2, 0))`
3. User confirms → `unmarkText()` (marked text becomes regular text)
4. User cancels → `setMarkedText(nil, selectedRange: NSRange(0, 0))`

#### Geometry (For System UI)

```swift
// Rect for caret at position
func caretRect(for position: UITextPosition) -> CGRect

// Rect covering a text range (for selection highlight)
func firstRect(for range: UITextRange) -> CGRect

// All selection rects for a range (multi-line)
func selectionRects(for range: UITextRange) -> [UITextSelectionRect]
```

#### Hit Testing

```swift
// Position nearest to point
func closestPosition(to point: CGPoint) -> UITextPosition?

// Position nearest to point within range
func closestPosition(to point: CGPoint, within range: UITextRange) -> UITextPosition?

// Character range at point
func characterRange(at point: CGPoint) -> UITextRange?
```

#### Document Bounds

```swift
var beginningOfDocument: UITextPosition { get }
var endOfDocument: UITextPosition { get }
```

#### Tokenizer

```swift
// For word/sentence/paragraph boundaries
var tokenizer: UITextInputTokenizer { get }
// Default: return UITextInputStringTokenizer(textInput: self)
```

### Notifying the System of Changes

```swift
var inputDelegate: UITextInputDelegate? { get set }

// MUST call these when modifying text/selection externally
inputDelegate?.textWillChange(self)
// ... modify text ...
inputDelegate?.textDidChange(self)

inputDelegate?.selectionWillChange(self)
// ... modify selection ...
inputDelegate?.selectionDidChange(self)
```

**Failure to call these** causes the input system to desync — autocorrect stops working, marked text corrupts, keyboard misbehaves.

## NSTextInputClient (AppKit)

The macOS equivalent for custom text input.

### Key Methods

```swift
protocol NSTextInputClient {
    // Insert confirmed text
    func insertText(_ string: Any, replacementRange: NSRange)

    // Set/update marked text
    func setMarkedText(_ string: Any, selectedRange: NSRange, replacementRange: NSRange)

    // Commit marked text
    func unmarkText()

    // Query selection
    func selectedRange() -> NSRange

    // Query marked text
    func markedRange() -> NSRange

    // Check if has marked text
    func hasMarkedText() -> Bool

    // Geometry
    func firstRect(forCharacterRange range: NSRange, actualRange: NSRangePointer?) -> NSRect

    // Hit testing
    func characterIndex(for point: NSPoint) -> Int

    // Content access
    func attributedSubstring(forProposedRange range: NSRange,
                             actualRange: NSRangePointer?) -> NSAttributedString?
    func attributedString() -> NSAttributedString

    // Valid attributes
    func validAttributesForMarkedText() -> [NSAttributedString.Key]
}
```

### NSTextInputContext

Manages the input context (keyboard layout, input method) for a view:

```swift
// Get current input context
let context = NSTextInputContext.current

// Invalidate character coordinates (after layout change)
context?.invalidateCharacterCoordinates()

// Discard marked text
context?.discardMarkedText()
```

## iOS Selection UI (iOS 17+)

### UITextSelectionDisplayInteraction

Provides system selection UI (cursor, handles, highlights) for custom text views:

```swift
class CustomTextView: UIView, UITextInput {
    lazy var selectionDisplay = UITextSelectionDisplayInteraction(textInput: self, isAccessibilityElement: false)

    override init(frame: CGRect) {
        super.init(frame: frame)
        addInteraction(selectionDisplay)
    }

    // Call when selection changes
    func updateSelection() {
        selectionDisplay.setNeedsSelectionUpdate()
    }
}
```

### UITextLoupeSession

Magnifier loupe for precise cursor positioning:

```swift
// Begin loupe at point
let session = UITextLoupeSession.begin(at: point, from: selectionWidget, in: self)

// Move during drag
session.move(to: newPoint)

// End
session.invalidate()
```

## macOS Cursor (macOS Sonoma+)

### NSTextInsertionIndicator

System text cursor for custom AppKit views:

```swift
let indicator = NSTextInsertionIndicator(frame: .zero)
documentView.addSubview(indicator)

// Required: set up effects view (for animation effects)
indicator.effectsViewInserter = { effectView in
    self.documentView.addSubview(effectView, positioned: .above, relativeTo: nil)
}

// Show/hide
indicator.displayMode = .automatic  // or .hidden
```

## Text Interactions

### UITextInteraction (iOS 13+)

Adds system text interactions to a view (selection gestures, menu):

```swift
let interaction = UITextInteraction(for: .editable)  // or .nonEditable
interaction.textInput = self  // Must conform to UITextInput
view.addInteraction(interaction)
```

### UIEditMenuInteraction (iOS 16+)

The modern replacement for UIMenuController:

```swift
let editMenu = UIEditMenuInteraction(delegate: self)
view.addInteraction(editMenu)

// Show menu
let config = UIEditMenuConfiguration(identifier: nil, sourcePoint: point)
editMenu.presentEditMenu(with: config)
```

## Quick Reference

| Need | UIKit | AppKit |
|------|-------|--------|
| Minimal text input | UIKeyInput | NSTextInputClient |
| Full text input | UITextInput | NSTextInputClient |
| System cursor | UITextSelectionDisplayInteraction | NSTextInsertionIndicator |
| Magnifier | UITextLoupeSession | N/A (system-provided) |
| Selection gestures | UITextInteraction | N/A (NSTextView built-in) |
| Edit menu | UIEditMenuInteraction | NSMenu (right-click) |
| Input context | N/A (automatic) | NSTextInputContext |

## Scribble / Apple Pencil Handwriting (iPadOS 14+)

UITextView and UITextField get Scribble for free. Custom `UITextInput` views also get automatic support if the implementation is complete.

For customization (`UIScribbleInteraction`) and non-text-input views that should accept handwriting (`UIIndirectScribbleInteraction`), see [scribble-patterns.md](scribble-patterns.md).

## Common Pitfalls

1. **Not calling `inputDelegate` methods** — System desyncs. Autocorrect and marked text break.
2. **Wrong `caretRect` / `firstRect`** — System UI (keyboard, autocorrect, selection handles) positioned incorrectly.
3. **Ignoring marked text** — CJK input stops working. Always implement `setMarkedText`/`unmarkText`.
4. **Forgetting `canBecomeFirstResponder`** — View never receives keyboard input.
5. **Using UITextInput without UITextSelectionDisplayInteraction** — No cursor or selection handles shown.
6. **Not invalidating character coordinates (macOS)** — After layout changes, call `NSTextInputContext.current?.invalidateCharacterCoordinates()`.

## Related Skills

- Use the **platform-reference** agent when custom input lives inside a SwiftUI wrapper.
- Use the writing tools section in this reference when text input requirements intersect with Apple Intelligence editing.
- Use `/skill apple-text-textkit-diag` when the problem is symptom-first rather than protocol-first.

---

# Text Editor Undo/Redo

Use this skill when the main question is how undo and redo work in Apple text editors.

## When to Use

- Implementing undo in a custom text editor
- Debugging undo that groups too many or too few changes
- Programmatic edits that should or should not be undoable
- Custom NSTextStorage subclass undo integration

## Quick Decision

- Need storage editing lifecycle -> the **textkit-reference** agent
- Need layout invalidation after undo -> the **textkit-reference** agent
- Need general debugging -> `/skill apple-text-textkit-diag`

## Core Guidance

## How Undo Works in UITextView / NSTextView

### Built-In Behavior

`UITextView` and `NSTextView` both ship with undo support out of the box. The text view's `undoManager` automatically records character insertions, deletions, and attribute changes made through the text input system (typing, paste, cut, dictation).

The system records undo actions at the `NSTextStorage` level by observing `processEditing` notifications. Each editing cycle (between `beginEditing` and `endEditing`) becomes one undo group.

### Undo Grouping

The undo manager groups user typing into runs. A new undo group is created when:

- The user pauses typing (after a system-defined delay)
- The user moves the insertion point
- A non-typing edit occurs (paste, cut, delete key vs character key)
- `beginUndoGrouping()` / `endUndoGrouping()` are called explicitly

This means "undo" after typing "Hello World" typically undoes the whole phrase if typed without pause, not individual characters.

### Coalescing

TextKit coalesces adjacent character insertions into a single undo operation. This is handled automatically by the text view. If you subclass `NSTextStorage`, coalescing still works as long as you follow the editing lifecycle correctly (`beginEditing` / `edited` / `endEditing`).

## Programmatic Edits and Undo

### Making Programmatic Edits Undoable

Programmatic edits via `textStorage.replaceCharacters(in:with:)` are undoable by default when:

1. The text storage is attached to a text view
2. The text view has an undo manager
3. The edit flows through the normal `processEditing` path

```swift
// This is undoable automatically
textView.textStorage.beginEditing()
textView.textStorage.replaceCharacters(in: range, with: newText)
textView.textStorage.endEditing()
```

### Making Programmatic Edits NOT Undoable

Sometimes programmatic edits should not be undoable (e.g., loading initial content, applying server-provided text). Disable undo registration:

```swift
textView.undoManager?.disableUndoRegistration()
textView.textStorage.beginEditing()
textView.textStorage.replaceCharacters(in: range, with: newText)
textView.textStorage.endEditing()
textView.undoManager?.enableUndoRegistration()
```

Call `disableUndoRegistration()` before the edit and `enableUndoRegistration()` after. These calls nest — if you call disable twice, you must call enable twice.

### Grouping Programmatic Edits

If a programmatic operation involves multiple storage mutations that should undo as a single unit:

```swift
textView.undoManager?.beginUndoGrouping()

textView.textStorage.beginEditing()
textView.textStorage.replaceCharacters(in: range1, with: text1)
textView.textStorage.replaceCharacters(in: range2, with: text2)
textView.textStorage.endEditing()

textView.undoManager?.endUndoGrouping()
```

Without explicit grouping, each `endEditing()` call creates a separate undo group.

## Custom NSTextStorage Subclass

### Undo Registration in Subclasses

If you subclass `NSTextStorage` with a custom backing store, undo registration happens automatically at the text view level — the text view observes `processEditing` and records the inverse operation. Your subclass does not need to register undo actions itself, as long as:

1. `edited(_:range:changeInLength:)` is called with correct parameters
2. `processEditing()` fires normally
3. The text storage is attached to a text view with an undo manager

### The Trap: Wrong changeInLength Breaks Undo

If `edited()` receives a wrong `changeInLength` delta, the undo manager records the wrong inverse operation. Undo will then apply an incorrect replacement range, causing crashes or text corruption. This is one of the most common undo bugs in custom text storage subclasses.

### Standalone Undo (No Text View)

If your `NSTextStorage` is used without a text view (e.g., in a document model layer), you must register undo actions yourself:

```swift
class UndoableTextStorage: NSTextStorage {
    var externalUndoManager: UndoManager?

    override func replaceCharacters(in range: NSRange, with str: String) {
        let oldText = (string as NSString).substring(with: range)

        if let undoManager = externalUndoManager, undoManager.isUndoRegistrationEnabled {
            let inverseRange = NSRange(location: range.location, length: (str as NSString).length)
            undoManager.registerUndo(withTarget: self) { storage in
                storage.replaceCharacters(in: inverseRange, with: oldText)
            }
        }

        beginEditing()
        backingStore.replaceCharacters(in: range, with: str)
        edited(.editedCharacters, range: range, changeInLength: (str as NSString).length - range.length)
        endEditing()
    }
}
```

## TextKit 2 Undo Patterns

### performEditingTransaction and Undo

In TextKit 2, edits should be wrapped in `performEditingTransaction`. Undo still operates at the text storage level:

```swift
textContentStorage.performEditingTransaction {
    textStorage.replaceCharacters(in: range, with: newText)
}
// Undo reverses the text storage change, which triggers
// element regeneration through the content storage automatically
```

The undo manager does not need to know about `performEditingTransaction` — it records the inverse at the storage level, and when undo replays the inverse, the content storage observes the storage change and regenerates elements.

### Custom NSTextContentManager and Undo

If you subclass `NSTextContentManager` directly (no text storage), undo is entirely your responsibility. The system has no attributed string to diff against.

```swift
class DatabaseContentManager: NSTextContentManager {
    var undoManager: UndoManager?

    func insertRow(_ row: Row, at index: Int) {
        undoManager?.registerUndo(withTarget: self) { cm in
            cm.deleteRow(at: index)
        }

        performEditingTransaction {
            database.insert(row, at: index)
        }
    }

    func deleteRow(at index: Int) {
        let row = database.row(at: index)
        undoManager?.registerUndo(withTarget: self) { cm in
            cm.insertRow(row, at: index)
        }

        performEditingTransaction {
            database.deleteRow(at: index)
        }
    }
}
```

Register the undo action before or after the mutation, but always outside the `performEditingTransaction` block — registration inside the transaction still works but is confusing to reason about.

## Common Pitfalls

1. **Undo after `disableUndoRegistration` without re-enabling.** Forgetting to call `enableUndoRegistration()` silently breaks all future undo. Use `defer` to ensure balance:

```swift
textView.undoManager?.disableUndoRegistration()
defer { textView.undoManager?.enableUndoRegistration() }
```

2. **Attribute-only changes creating undo entries.** Syntax highlighting that applies attributes through text storage creates undo entries. Users undo their typing and get "undo highlight color" instead. Apply display-only styling via rendering attributes (TextKit 2) or temporary attributes (TextKit 1) to avoid this.

3. **Undo groups left open.** If `beginUndoGrouping()` is called without `endUndoGrouping()`, the undo manager accumulates everything into one giant undo group until the run loop ends. Use `defer`:

```swift
undoManager.beginUndoGrouping()
defer { undoManager.endUndoGrouping() }
```

4. **Setting `text` or `attributedText` clears undo.** Assigning to `textView.text` or `textView.attributedText` replaces the entire text storage and clears the undo stack. Use `textStorage.replaceCharacters(in:with:)` for undoable edits.

5. **Undo during Writing Tools.** Writing Tools uses the undo manager to offer its own revert. Mixing programmatic undo registration during an active Writing Tools session can corrupt the revert state. Check `isWritingToolsActive` before registering custom undo actions.

## Related Skills

- Use the **textkit-reference** agent for the editing lifecycle behind undo recording.
- Use `/skill apple-text-textkit-diag` when undo causes stale layout or crashes.
- Use the writing tools section in this reference for Writing Tools interaction with undo.

---

# Find and Replace in Text Editors

Use this skill when the main question is how to add find and replace to a text editor on Apple platforms.

## When to Use

- Adding find/replace to a custom text editor
- Wiring `UIFindInteraction` into a `UITextView` wrapper
- Implementing find in a custom view that is not a text view
- Highlighting search results without affecting layout
- Implementing replace-all efficiently in large documents

## Quick Decision

- Need text view selection or wrapping -> `/skill apple-text-views` or the **platform-reference** agent
- Need rendering overlays for highlighting -> the **textkit-reference** agent
- Need attributed string patterns -> the **rich-text-reference** agent

## Core Guidance

## UIFindInteraction (iOS 16+)

### Overview

`UIFindInteraction` is the modern find and replace system for iOS. It provides the standard find bar UI and drives find/replace through the `UITextSearching` protocol.

`UITextView` supports `UIFindInteraction` out of the box. Set `isFindInteractionEnabled = true`:

```swift
textView.isFindInteractionEnabled = true

// Present find bar programmatically
textView.findInteraction?.presentFindNavigator(showingReplace: false)
```

### UITextSearching Protocol

If you have a custom view (not `UITextView`) that needs find, adopt `UITextSearching`:

```swift
class CustomEditorView: UIView, UITextSearching {
    var supportsTextReplacement: Bool { true }

    func decorateFound(
        _ foundRange: UITextRange,
        in document: UITextSearchDocumentIdentifier,
        usingStyle style: UITextSearchFoundTextStyle
    ) {
        // Highlight the found range
        switch style {
        case .found:
            addHighlight(for: foundRange, color: .systemYellow.withAlphaComponent(0.3))
        case .highlighted:
            addHighlight(for: foundRange, color: .systemYellow)
        case .normal:
            removeHighlight(for: foundRange)
        @unknown default:
            break
        }
    }

    func clearAllDecoratedFoundText() {
        removeAllHighlights()
    }

    func performTextSearch(
        queryString: String,
        options: UITextSearchOptions,
        resultAggregator aggregator: UITextSearchAggregator
    ) {
        // Search your text content
        let text = contentString
        var searchRange = text.startIndex..<text.endIndex

        while let range = text.range(of: queryString, options: searchOptions(from: options), range: searchRange) {
            let textRange = convertToUITextRange(range)
            aggregator.foundRange(textRange, searchString: queryString, document: nil)
            searchRange = range.upperBound..<text.endIndex
        }
        aggregator.finishedSearching()
    }

    func replaceFound(
        _ foundRange: UITextRange,
        in document: UITextSearchDocumentIdentifier,
        with replacementText: String
    ) {
        replaceText(in: foundRange, with: replacementText)
    }

    func replaceAllOccurrences(
        ofQueryString queryString: String,
        using options: UITextSearchOptions,
        with replacementText: String
    ) {
        // Replace all — work backward to preserve ranges
        let ranges = findAllRanges(of: queryString, options: options)
        for range in ranges.reversed() {
            replaceText(in: range, with: replacementText)
        }
    }

    func shouldReplaceFound(
        _ foundRange: UITextRange,
        in document: UITextSearchDocumentIdentifier,
        with replacementText: String
    ) -> Bool {
        return true  // Return false to skip protected ranges
    }
}
```

### Adding UIFindInteraction to a Custom View

```swift
class CustomEditorView: UIView, UITextSearching {
    lazy var findInteraction = UIFindInteraction(sessionDelegate: self)

    override var interactions: [any UIInteraction] {
        [findInteraction]
    }

    // ... UITextSearching implementation
}

extension CustomEditorView: UIFindInteractionDelegate {
    func findInteraction(
        _ interaction: UIFindInteraction,
        sessionFor view: UIView
    ) -> UIFindSession? {
        return UITextSearchingFindSession(searchableObject: self)
    }
}
```

## NSTextFinder (macOS)

### Overview

`NSTextFinder` provides the macOS find bar. It works with any view that adopts `NSTextFinderClient`.

```swift
class EditorView: NSView, NSTextFinderClient {
    let textFinder = NSTextFinder()

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        textFinder.client = self
        textFinder.findBarContainer = enclosingScrollView
        textFinder.isIncrementalSearchingEnabled = true
    }

    // NSTextFinderClient required methods
    var string: String { textStorage.string }
    var isEditable: Bool { true }

    func stringLength() -> Int { (string as NSString).length }

    func string(at characterIndex: Int, effectiveRange: NSRangePointer, endsWithSearchBoundary: UnsafeMutablePointer<ObjCBool>) -> String {
        effectiveRange.pointee = NSRange(location: 0, length: stringLength())
        endsWithSearchBoundary.pointee = true
        return string
    }

    func shouldReplaceCharacters(in ranges: [NSValue], with strings: [String]) -> Bool {
        return true
    }

    func replaceCharacters(in range: NSRange, with string: String) {
        textStorage.replaceCharacters(in: range, with: string)
    }

    func scrollRangeToVisible(_ range: NSRange) {
        // Scroll the text view to show the range
    }

    var firstSelectedRange: NSRange {
        // Return current selection
    }

    var selectedRanges: [NSValue] {
        get { /* current selections */ }
        set { /* update selections */ }
    }
}
```

`NSTextView` has built-in `NSTextFinder` support via `usesFindBar = true`.

## Highlighting Search Results

### TextKit 1: Temporary Attributes

Use temporary attributes to highlight search results without affecting the document or undo:

```swift
func highlightSearchResults(_ ranges: [NSRange], in layoutManager: NSLayoutManager) {
    // Clear previous highlights
    let fullRange = NSRange(location: 0, length: layoutManager.textStorage!.length)
    layoutManager.removeTemporaryAttribute(.backgroundColor, forCharacterRange: fullRange)

    // Apply new highlights
    for range in ranges {
        layoutManager.addTemporaryAttribute(.backgroundColor,
                                            value: UIColor.systemYellow.withAlphaComponent(0.3),
                                            forCharacterRange: range)
    }
}
```

Temporary attributes do not trigger layout invalidation, do not affect undo, and do not persist to the document.

### TextKit 2: Rendering Attributes

```swift
func highlightSearchResults(_ ranges: [NSTextRange], in textLayoutManager: NSTextLayoutManager) {
    // Clear previous highlights
    textLayoutManager.removeRenderingAttribute(.backgroundColor,
                                               forTextRange: textLayoutManager.documentRange)

    // Apply new highlights
    for range in ranges {
        textLayoutManager.addRenderingAttribute(.backgroundColor,
                                                value: UIColor.systemYellow.withAlphaComponent(0.3),
                                                forTextRange: range)
    }
}
```

### Performance: Large Result Sets

For documents with thousands of matches, avoid applying highlights to all results at once. Instead, highlight only results near the viewport:

```swift
func highlightVisibleResults(near viewportRange: NSTextRange) {
    let extendedRange = extendRange(viewportRange, by: 2000)  // characters of overdraw
    let visibleResults = allResults.filter { extendedRange.contains($0) }
    for result in visibleResults {
        textLayoutManager.addRenderingAttribute(.backgroundColor,
                                                value: highlightColor,
                                                forTextRange: result)
    }
}
```

## Replace-All Performance

Replace-all in large documents must work backward to preserve range validity:

```swift
func replaceAll(matching query: String, with replacement: String) {
    let ranges = findAllRanges(of: query)

    textStorage.beginEditing()
    for range in ranges.reversed() {  // MUST be reversed
        textStorage.replaceCharacters(in: range, with: replacement)
    }
    textStorage.endEditing()
    // Single processEditing pass for all replacements
}
```

Working forward invalidates subsequent ranges because each replacement changes character offsets. Working backward keeps earlier ranges valid.

## Common Pitfalls

1. **Highlighting via text storage attributes creates undo entries.** Use temporary attributes (TextKit 1) or rendering attributes (TextKit 2) for search highlights.
2. **Replace-all forward corrupts ranges.** Always work backward (highest range first).
3. **Not calling `finishedSearching()` on the aggregator.** `UIFindInteraction` waits for this signal. Without it, the find bar spins forever.
4. **Regex search without escaping.** `UITextSearchOptions` may or may not indicate regex mode. Check `wordMatch` and `caseInsensitive` options and apply them correctly.
5. **Find bar not appearing.** `UIFindInteraction` needs a `UIFindSession`. Make sure the delegate returns a session and the view is in the responder chain.

## Related Skills

- Use the **textkit-reference** agent for custom rendering overlay patterns.
- Use the **rich-text-reference** agent for attribute-based highlighting choices.
- Use the undo section in this reference when find-replace undo grouping is wrong.

---

# Copy, Cut, and Paste in Text Editors

Use this skill when the main question is how paste, copy, or cut works in Apple text editors, or when you need to customize pasteboard behavior.

## When to Use

- Sanitizing pasted rich text (stripping fonts, colors, or styles)
- Implementing custom pasteboard types for your editor
- Handling pasted images as `NSTextAttachment` objects
- Controlling what gets copied from your editor
- Bridging `NSItemProvider` content into attributed strings

## Quick Decision

- Need attachment rendering -> the **rich-text-reference** agent
- Need attributed string conversion -> the **rich-text-reference** agent
- Need UIViewRepresentable bridging -> the **platform-reference** agent

## Core Guidance

## Built-In Paste Behavior

`UITextView` and `NSTextView` handle paste automatically. By default:

- **Plain text paste:** Inserts text with the text view's `typingAttributes`
- **Rich text paste:** Inserts the attributed string preserving source formatting (fonts, colors, paragraph styles)
- **Image paste:** Creates an `NSTextAttachment` with the image data

### Controlling Paste via UITextViewDelegate

```swift
func textView(_ textView: UITextView,
              shouldChangeTextIn range: NSRange,
              replacementText text: String) -> Bool {
    // This fires for typed text and paste
    // Return false to reject the edit
    return true
}
```

This delegate is limited — it only receives plain text, not the rich attributed string. For full paste control, override at the text view or responder level.

## Stripping Formatting on Paste

### UITextView: Override paste(_:)

```swift
class PlainPasteTextView: UITextView {
    override func paste(_ sender: Any?) {
        // Read plain text from pasteboard, ignoring rich content
        guard let plainText = UIPasteboard.general.string else { return }

        // Insert with current typing attributes
        let range = selectedRange
        textStorage.beginEditing()
        textStorage.replaceCharacters(in: range, with: plainText)

        let insertedRange = NSRange(location: range.location, length: (plainText as NSString).length)
        textStorage.setAttributes(typingAttributes, range: insertedRange)
        textStorage.endEditing()

        // Move cursor to end of insertion
        selectedRange = NSRange(location: insertedRange.location + insertedRange.length, length: 0)
    }
}
```

### Selective Sanitization

Keep some attributes (bold, italic) but strip others (font name, colors):

```swift
func sanitizePastedAttributedString(_ source: NSAttributedString) -> NSAttributedString {
    let result = NSMutableAttributedString(string: source.string)
    let fullRange = NSRange(location: 0, length: result.length)

    // Start with default attributes
    result.setAttributes(defaultAttributes, range: fullRange)

    // Preserve only bold/italic from source
    source.enumerateAttributes(in: fullRange, options: []) { attrs, range, _ in
        if let font = attrs[.font] as? UIFont {
            let traits = font.fontDescriptor.symbolicTraits
            if traits.contains(.traitBold) {
                result.addAttribute(.font, value: boldFont, range: range)
            }
            if traits.contains(.traitItalic) {
                result.addAttribute(.font, value: italicFont, range: range)
            }
        }
        // Preserve links
        if let link = attrs[.link] {
            result.addAttribute(.link, value: link, range: range)
        }
    }
    return result
}
```

## Handling Pasted Images

### Reading Images from Pasteboard

```swift
override func paste(_ sender: Any?) {
    let pasteboard = UIPasteboard.general

    if pasteboard.hasImages, let image = pasteboard.image {
        insertImageAttachment(image)
    } else {
        super.paste(sender)  // Default text paste
    }
}

func insertImageAttachment(_ image: UIImage) {
    let attachment = NSTextAttachment()
    attachment.image = image

    // Scale to fit text container width
    let maxWidth = textContainer.size.width - textContainer.lineFragmentPadding * 2
    if image.size.width > maxWidth {
        let scale = maxWidth / image.size.width
        attachment.bounds = CGRect(origin: .zero,
                                   size: CGSize(width: image.size.width * scale,
                                                height: image.size.height * scale))
    }

    let attrString = NSAttributedString(attachment: attachment)
    textStorage.insert(attrString, at: selectedRange.location)
}
```

### NSItemProvider (Drag, Drop, and Modern Paste)

For iOS 16+ and modern drag-and-drop, content arrives via `NSItemProvider`:

```swift
func handleItemProviders(_ providers: [NSItemProvider]) {
    for provider in providers {
        if provider.hasItemConformingToTypeIdentifier(UTType.image.identifier) {
            provider.loadDataRepresentation(forTypeIdentifier: UTType.image.identifier) { data, error in
                guard let data, let image = UIImage(data: data) else { return }
                DispatchQueue.main.async {
                    self.insertImageAttachment(image)
                }
            }
        } else if provider.hasItemConformingToTypeIdentifier(UTType.attributedString.identifier) {
            provider.loadObject(ofClass: NSAttributedString.self) { object, error in
                guard let attrString = object as? NSAttributedString else { return }
                DispatchQueue.main.async {
                    let sanitized = self.sanitizePastedAttributedString(attrString)
                    self.insertAttributedString(sanitized)
                }
            }
        } else if provider.hasItemConformingToTypeIdentifier(UTType.plainText.identifier) {
            provider.loadObject(ofClass: String.self) { object, error in
                guard let text = object as? String else { return }
                DispatchQueue.main.async {
                    self.insertPlainText(text)
                }
            }
        }
    }
}
```

## Custom Copy Behavior

### Copying Rich Content

Override `copy(_:)` to write custom formats to the pasteboard:

```swift
override func copy(_ sender: Any?) {
    guard selectedRange.length > 0 else { return }
    let selectedAttrString = textStorage.attributedSubstring(from: selectedRange)

    let pasteboard = UIPasteboard.general
    pasteboard.items = []

    // Write multiple representations: rich, plain, and custom
    var items: [String: Any] = [:]

    // Plain text
    items[UTType.plainText.identifier] = selectedAttrString.string

    // Rich text (RTF)
    if let rtfData = try? selectedAttrString.data(from: NSRange(location: 0, length: selectedAttrString.length),
                                                   documentAttributes: [.documentType: NSAttributedString.DocumentType.rtf]) {
        items[UTType.rtf.identifier] = rtfData
    }

    // Custom format (e.g., your app's internal representation)
    if let customData = encodeCustomFormat(selectedAttrString) {
        items["com.yourapp.richtext"] = customData
    }

    pasteboard.addItems([items])
}
```

### Reading Custom Formats on Paste

```swift
override func paste(_ sender: Any?) {
    let pasteboard = UIPasteboard.general

    // Prefer your custom format first
    if let customData = pasteboard.data(forPasteboardType: "com.yourapp.richtext") {
        let attrString = decodeCustomFormat(customData)
        insertAttributedString(attrString)
    } else if let rtfData = pasteboard.data(forPasteboardType: UTType.rtf.identifier) {
        let attrString = try? NSAttributedString(data: rtfData, options: [.documentType: NSAttributedString.DocumentType.rtf], documentAttributes: nil)
        if let attrString {
            insertAttributedString(sanitizePastedAttributedString(attrString))
        }
    } else {
        super.paste(sender)
    }
}
```

## Common Pitfalls

1. **Rich paste brings unwanted fonts.** Source app fonts may not exist on the device. The system substitutes, but the result looks wrong. Always sanitize or remap fonts on paste.
2. **Pasted text loses typing attributes.** When inserting plain text programmatically, apply `typingAttributes` to the inserted range. The text view does this automatically for user paste but not for programmatic insertions.
3. **NSItemProvider callbacks on background thread.** `loadObject` and `loadDataRepresentation` call back on arbitrary threads. Dispatch to main before touching text storage.
4. **`shouldChangeTextIn` does not fire for programmatic paste.** If you override `paste(_:)` and modify text storage directly, the delegate method is not called. Apply your own validation.
5. **Undo after paste.** Custom paste implementations must go through the normal editing lifecycle (`beginEditing`/`endEditing`) to get proper undo registration. See the undo section in this reference.

## Related Skills

- Use the **rich-text-reference** agent for attachment sizing, baseline, and view providers.
- Use the **rich-text-reference** agent for attribute conversion between paste formats.
- Use the undo section in this reference for undo registration around paste operations.

---

# Spell Checking & Autocorrect

Use this skill when the main question is how spell checking, autocorrect, or text completion works in Apple text editors, or when custom views need these features.

## When to Use

- Configuring spell checking or autocorrect on text views
- Building a custom UITextInput view that needs spell checking
- Implementing custom word completion with UITextChecker
- Debugging autocorrect not working in a custom editor
- Comparing spell checking capabilities between iOS and macOS

## Quick Decision

```
Using UITextView or NSTextView?
    → Spell checking works automatically. Configure via properties.

Building a custom UITextInput view?
    → READ THE TRAP SECTION BELOW before enabling spell checking.

Need custom word suggestions or spell checking logic?
    → UITextChecker (iOS) or NSSpellChecker (macOS)

Need to disable spell checking for a code editor?
    → Set spellCheckingType = .no and autocorrectionType = .no
```

## Core Guidance

## UITextView / NSTextView (Built-In)

Standard text views handle spell checking automatically. Configure with properties:

### UITextView (iOS)

```swift
textView.spellCheckingType = .yes       // .default, .no, .yes
textView.autocorrectionType = .yes      // .default, .no, .yes
textView.autocapitalizationType = .sentences
textView.smartQuotesType = .yes
textView.smartDashesType = .yes
textView.smartInsertDeleteType = .yes
textView.inlinePredictionType = .yes    // iOS 17+
```

### NSTextView (macOS)

```swift
textView.isContinuousSpellCheckingEnabled = true
textView.isGrammarCheckingEnabled = true           // macOS only — no iOS equivalent
textView.isAutomaticSpellingCorrectionEnabled = true
textView.isAutomaticQuoteSubstitutionEnabled = true
textView.isAutomaticDashSubstitutionEnabled = true
textView.isAutomaticTextReplacementEnabled = true
textView.isAutomaticTextCompletionEnabled = true
textView.isAutomaticLinkDetectionEnabled = true
textView.isAutomaticDataDetectionEnabled = true
```

### Disabling for Code Editors

```swift
// iOS
textView.spellCheckingType = .no
textView.autocorrectionType = .no
textView.autocapitalizationType = .none
textView.smartQuotesType = .no
textView.smartDashesType = .no

// macOS
textView.isContinuousSpellCheckingEnabled = false
textView.isGrammarCheckingEnabled = false
textView.isAutomaticSpellingCorrectionEnabled = false
textView.isAutomaticTextCompletionEnabled = false
```

## The UITextInteraction Trap (Custom Views)

**This is the single most important thing in this skill.**

If you build a custom `UITextInput` view and add `UITextInteraction`, spell checking underlines appear correctly. The system detects misspelled words, draws red underlines, and shows a correction popover when the user taps.

**But tapping a correction invokes a private API (`UITextReplacement`).** Your custom view cannot apply the correction without accessing private symbols. This means:

- Spell check underlines appear ✅
- Correction popover appears ✅
- Tapping a correction **does nothing or crashes** ❌
- Using the private API gets **rejected from the App Store** ❌

### Workarounds

**Option A: Disable system spell checking, build your own**

```swift
// Disable system spell checking on your custom view
var spellCheckingType: UITextSpellCheckingType { .no }
var autocorrectionType: UITextAutocorrectionType { .no }

// Use UITextChecker for your own spell check logic
let checker = UITextChecker()
let misspelledRange = checker.rangeOfMisspelledWord(
    in: text, range: NSRange(location: 0, length: (text as NSString).length),
    startingAt: 0, wrap: false, language: "en"
)

if misspelledRange.location != NSNotFound {
    let guesses = checker.guesses(forWordRange: misspelledRange, in: text, language: "en")
    // Show your own correction UI (popover, menu, etc.)
}
```

**Option B: Accept panel-only corrections**

Leave `spellCheckingType = .yes` but accept that inline corrections won't apply. Users can still use the system spell check panel (Edit menu → Spelling) on macOS.

**Option C: Use UITextView instead**

If spell checking is important, consider using UITextView (which handles corrections correctly) rather than a fully custom UITextInput view.

## UITextChecker

Standalone spell checking class. Not tied to any view. Works on iOS and macOS.

### Basic Spell Checking

```swift
let checker = UITextChecker()
let text = "Ths is a tset"
let range = NSRange(location: 0, length: (text as NSString).length)

var offset = 0
while offset < (text as NSString).length {
    let misspelled = checker.rangeOfMisspelledWord(
        in: text, range: range, startingAt: offset,
        wrap: false, language: "en"
    )

    if misspelled.location == NSNotFound { break }

    let word = (text as NSString).substring(with: misspelled)
    let guesses = checker.guesses(forWordRange: misspelled, in: text, language: "en") ?? []
    print("'\(word)' → suggestions: \(guesses)")

    offset = misspelled.location + misspelled.length
}
```

### Word Completion

```swift
let partial = "prog"
let completions = checker.completions(
    forPartialWordRange: NSRange(location: 0, length: (partial as NSString).length),
    in: partial, language: "en"
) ?? []
// Returns: ["program", "programming", "progress", ...]
// NOTE: sorted alphabetically despite docs saying "by probability"
```

### Custom Dictionary

```swift
// Teach a word (persists across app launches)
UITextChecker.learnWord("SwiftUI")

// Check if learned
UITextChecker.hasLearnedWord("SwiftUI")  // true

// Forget a word
UITextChecker.unlearnWord("SwiftUI")
```

### Per-Session Ignore List

```swift
let tag = UITextChecker.uniqueSpellDocumentTag()
checker.ignoreWord("xyzzy", inSpellDocumentWithTag: tag)
let ignored = checker.ignoredWords(inSpellDocumentWithTag: tag)
// Don't forget to close when done (macOS pattern, good practice on iOS too)
```

### Available Languages

```swift
let languages = UITextChecker.availableLanguages
// ["en", "fr", "de", "es", "it", "pt", "nl", "sv", "da", ...]
```

## NSSpellChecker (macOS)

The macOS spell checker is significantly more capable. It's a singleton service.

### Basic Usage

```swift
let spellChecker = NSSpellChecker.shared

// Simple check
let text = "Ths is a tset"
let misspelled = spellChecker.checkSpelling(of: text, startingAt: 0)

// Unified checking (spelling + grammar + data detection)
let results = spellChecker.check(
    text, range: NSRange(location: 0, length: (text as NSString).length),
    types: NSTextCheckingAllTypes, options: nil,
    inSpellDocumentWithTag: 0, orthography: nil, wordCount: nil
)
```

### Async Checking (Large Documents)

```swift
let tag = NSSpellChecker.uniqueSpellDocumentTag()
spellChecker.requestChecking(
    of: text,
    range: NSRange(location: 0, length: (text as NSString).length),
    types: .correctionIndicator,
    options: nil,
    inSpellDocumentWithTag: tag
) { sequenceNumber, results, orthography, wordCount in
    // Apply results on main thread
    DispatchQueue.main.async {
        self.applySpellCheckResults(results)
    }
}
```

### Spell Document Tags

Isolate ignore lists per document:

```swift
let tag = NSSpellChecker.uniqueSpellDocumentTag()
// ... use tag for all checking in this document ...

// When document closes:
NSSpellChecker.shared.closeSpellDocument(withTag: tag)
```

### Marking Misspelled Ranges (AppKit Only)

```swift
// Visually mark a range as misspelled (red underline)
textView.setSpellingState(NSSpellingStateSpellingFlag, range: misspelledRange)

// Or use the .spellingState attributed string key
let attrs: [NSAttributedString.Key: Any] = [
    .spellingState: NSSpellingStateSpellingFlag
]
```

No iOS equivalent of `setSpellingState`. On iOS, the system manages spell check underlines internally.

## Platform Comparison

| Feature | iOS (UITextView) | macOS (NSTextView) |
|---------|------------------|-------------------|
| Continuous spell checking | Yes (`spellCheckingType`) | Yes (`isContinuousSpellCheckingEnabled`) |
| Grammar checking | No API | Yes (`isGrammarCheckingEnabled`) |
| Mark specific range as misspelled | No | Yes (`setSpellingState`) |
| Spell document tags | UITextChecker only | Full support |
| Async checking | No | Yes (`requestChecking`) |
| Text completion popup | No built-in | Yes (`complete(_:)`) |
| System Spelling panel | No | Yes (`orderFrontSpellingPanel:`) |
| Substitutions panel | No | Yes (`orderFrontSubstitutionsPanel:`) |
| Individual toggle APIs | Enum properties | Boolean properties per feature |
| Spell check pre-existing text | Only near edits | Yes (full document) |

## How Autocorrect Works with UITextInput

For autocorrect to function in a custom `UITextInput` view, the system needs:

1. **`UITextInputTraits` properties** — `spellCheckingType` and `autocorrectionType` must be `.yes` or `.default`
2. **`inputDelegate` callbacks** — You MUST call `textWillChange`/`textDidChange` and `selectionWillChange`/`selectionDidChange` on every change. Failing to do so desyncs the autocorrect system silently.
3. **Correct geometry** — `caretRect(for:)` and `firstRect(for:)` must return accurate rects. The autocorrect bubble and spell check popover are positioned using these.
4. **`UITextInteraction` added** — The interaction provides the gesture recognizers that trigger the spell check popover.

### When Autocorrect Silently Breaks

| Symptom | Cause |
|---------|-------|
| No autocorrect suggestions appear | `inputDelegate.textDidChange` not called |
| Autocorrect bubble appears in wrong position | `caretRect(for:)` returns wrong rect |
| Changing `autocorrectionType` has no effect | Changed while view is first responder (must resign first) |
| Red underlines appear but corrections don't apply | The UITextInteraction private API trap (see above) |
| Spell check only works on new text, not pre-existing | iOS only checks near edits, not the full document |

## Common Pitfalls

1. **The UITextInteraction correction trap** — Spell check underlines work in custom UITextInput views, but applying corrections uses private API. Either disable system spell checking and use UITextChecker directly, or use UITextView.
2. **Not calling `inputDelegate` methods** — The autocorrect system desyncs silently. No error, no crash — just stops working.
3. **Changing traits while first responder** — `spellCheckingType` and `autocorrectionType` changes only take effect when the view is not first responder. Resign and re-become first responder.
4. **Expecting `completions` sorted by probability** — `UITextChecker.completions(forPartialWordRange:)` returns alphabetical order despite Apple's documentation claiming probability-based sorting.
5. **Not managing spell document tags (macOS)** — Forgetting `closeSpellDocument(withTag:)` leaks ignore lists.
6. **Code editors with spell checking on** — Set `spellCheckingType = .no` for code editors. Red underlines on variable names are distracting and wrong.
7. **NSSpellChecker on background thread** — It's main-thread only. Use `requestChecking` for async work on large documents.
8. **Expecting iOS grammar checking** — There is no grammar checking API on iOS. It's macOS only.

## Related Skills

- Use the input ref section in this reference for the full UITextInput protocol and inputDelegate requirements.
- Use the interaction section in this reference for UITextInteraction setup and gesture handling.
- Use the **platform-reference** agent for broader platform capability comparison.
- Use `/skill apple-text-views` when the real question is whether to use UITextView vs a custom view.

---

# Text Drag and Drop

Use this skill when the main question is how text-specific drag and drop works in Apple text editors, or when customizing drag/drop behavior beyond the defaults.

## When to Use

- Customizing what gets dragged from a text view
- Controlling drop behavior (insert, replace selection, replace all)
- Enabling text drag on iPhone (disabled by default)
- Building drag/drop for a custom UITextInput view
- Handling drops in non-editable text views
- Custom drag previews for multi-line text

## Quick Decision

```
Using UITextView or UITextField?
    → Drag and drop works automatically (iPad). Configure via delegates.
    → iPhone: must enable explicitly.

Building a custom UITextInput view?
    → Text drag/drop protocols are NOT automatically adopted.
    → Must add UIDragInteraction / UIDropInteraction manually.

Need copy/paste instead of drag/drop?
    → the pasteboard section in this reference

macOS?
    → Different architecture (NSDraggingSource / NSDraggingDestination)
```

## Core Guidance

## Default Behavior

UITextView and UITextField conform to `UITextDraggable` and `UITextDroppable` automatically.

**Drag:** User selects text, long-presses the selection to lift it. The system creates drag items with the selected text.

**Drop:** Text views accept dropped text, inserting at the position under the user's finger. The caret tracks the drag position.

**Move vs copy:**
- Same text view → move (dragged text removed from original position)
- Different view or app → copy

### iPhone vs iPad

```swift
// iPad: drag enabled by default
// iPhone: drag DISABLED by default
textView.textDragInteraction?.isEnabled = true  // Enable on iPhone
```

## UITextDragDelegate

All methods are optional. Set via `textView.textDragDelegate = self`.

### Providing Custom Drag Items

```swift
func textDraggableView(_ textDraggableView: UIView & UITextDraggable,
                       itemsForDrag dragRequest: UITextDragRequest) -> [UIDragItem] {
    // Return custom items (e.g., add image alongside text)
    let text = dragRequest.suggestedItems.first?.localObject as? String ?? ""
    let textItem = UIDragItem(itemProvider: NSItemProvider(object: text as NSString))

    // Add a custom representation
    let customData = encodeRichFormat(for: dragRequest.dragRange)
    let customItem = UIDragItem(itemProvider: NSItemProvider(
        item: customData as NSData,
        typeIdentifier: "com.myapp.richtext"
    ))

    return [textItem, customItem]
}
```

### Disabling Drag

```swift
// Option A: Return empty array
func textDraggableView(_ textDraggableView: UIView & UITextDraggable,
                       itemsForDrag dragRequest: UITextDragRequest) -> [UIDragItem] {
    return []  // Disables drag
}

// Option B: Disable the interaction
textView.textDragInteraction?.isEnabled = false
```

### Custom Drag Preview

```swift
func textDraggableView(_ textDraggableView: UIView & UITextDraggable,
                       dragPreviewForLiftingItem item: UIDragItem,
                       session: UIDragSession) -> UITargetedDragPreview? {
    // Return nil for default preview
    // Return custom UITargetedDragPreview for custom appearance
    return nil
}
```

### UITextDragPreviewRenderer

Text-aware preview rendering that understands multi-line text geometry:

```swift
// Create a renderer from layout manager and range
let renderer = UITextDragPreviewRenderer(
    layoutManager: textView.layoutManager,
    range: selectedRange
)

// Adjust the preview rectangles
renderer.adjust(firstLineRect: &firstRect,
                bodyRect: &bodyRect,
                lastLineRect: &lastRect,
                textOrigin: origin)

// The renderer provides proper multi-line drag previews
// that follow the text's line geometry
```

### Strip Color from Previews

```swift
textView.textDragOptions = .stripTextColorFromPreviews
// Renders drag preview in uniform color instead of preserving text colors
```

### Lifecycle Hooks

```swift
func textDraggableView(_ textDraggableView: UIView & UITextDraggable,
                       dragSessionWillBegin session: UIDragSession) {
    // Drag is starting — pause syncing, show visual feedback
}

func textDraggableView(_ textDraggableView: UIView & UITextDraggable,
                       dragSessionDidEnd session: UIDragSession) {
    // Drag ended — resume normal operations
}
```

## UITextDropDelegate

All methods are optional. Set via `textView.textDropDelegate = self`.

### Controlling Drop Behavior

```swift
func textDroppableView(_ textDroppableView: UIView & UITextDroppable,
                       proposalForDrop drop: UITextDropRequest) -> UITextDropProposal {
    // Check if this is a same-view drop (move vs copy)
    if drop.isSameView {
        return UITextDropProposal(dropAction: .insert)
    }

    // Accept external drops as insert at drop position
    return UITextDropProposal(dropAction: .insert)
}
```

### UITextDropProposal Actions

| Action | Behavior |
|--------|----------|
| `.insert` | Insert at drop position (default) |
| `.replaceSelection` | Replace the current text selection |
| `.replaceAll` | Replace all text in the view |

```swift
// Replace selection on drop
let proposal = UITextDropProposal(dropAction: .replaceSelection)

// Optimize same-view operations
proposal.useFastSameViewOperations = true
```

### Handling the Drop

```swift
func textDroppableView(_ textDroppableView: UIView & UITextDroppable,
                       willPerformDrop drop: UITextDropRequest) {
    // Called just before the drop executes
    // Use for validation, logging, or pre-processing
}
```

### Non-Editable Text Views

By default, non-editable text views reject drops. Override with:

```swift
func textDroppableView(_ textDroppableView: UIView & UITextDroppable,
                       willBecomeEditableForDrop drop: UITextDropRequest) -> UITextDropEditability {
    return .temporary  // Become editable just for this drop, then revert
    // .no — reject the drop (default for non-editable)
    // .yes — become permanently editable
}
```

### Custom Drop Preview

```swift
func textDroppableView(_ textDroppableView: UIView & UITextDroppable,
                       previewForDroppingAllItemsWithDefault defaultPreview: UITargetedDragPreview) -> UITargetedDragPreview? {
    // Return nil for default animation
    // Return custom preview for custom drop animation
    return nil
}
```

## macOS (AppKit)

macOS text drag/drop uses a completely different architecture — no UITextDragDelegate equivalent.

### NSTextView Default Behavior

NSTextView uses `NSDraggingSource` and `NSDraggingDestination` (which NSView conforms to). By default:
- Text can be dragged from selections
- Text drops are accepted if the view is editable
- File drops are only accepted if `isRichText` and `importsGraphics` are both enabled

### Customizing on macOS

```swift
class CustomTextView: NSTextView {
    // Accept additional pasteboard types
    override var acceptableDragTypes: [NSPasteboard.PasteboardType] {
        var types = super.acceptableDragTypes
        types.append(.init("com.myapp.richtext"))
        return types
    }

    // Handle the drop
    override func performDragOperation(_ draggingInfo: NSDraggingInfo) -> Bool {
        let pasteboard = draggingInfo.draggingPasteboard
        if let customData = pasteboard.data(forType: .init("com.myapp.richtext")) {
            insertCustomContent(customData)
            return true
        }
        return super.performDragOperation(draggingInfo)
    }
}
```

### Field Editor Gotcha

During NSTextField editing, drops go to the **field editor** (shared NSTextView), not the NSTextField itself. To intercept:

```swift
func windowWillReturnFieldEditor(_ sender: NSWindow, to client: Any?) -> Any? {
    if client is MyTextField {
        return myCustomFieldEditor  // Subclass NSTextView with custom drop handling
    }
    return nil
}
```

## Custom UITextInput Views

`UITextDraggable` and `UITextDroppable` are **NOT automatically adopted** by custom UITextInput views. Only UITextField and UITextView get them.

For custom views, use the general drag/drop APIs:

```swift
class CustomEditor: UIView, UITextInput {
    override init(frame: CGRect) {
        super.init(frame: frame)

        // Add general drag/drop interactions
        let dragInteraction = UIDragInteraction(delegate: self)
        addInteraction(dragInteraction)

        let dropInteraction = UIDropInteraction(delegate: self)
        addInteraction(dropInteraction)
    }
}

extension CustomEditor: UIDragInteractionDelegate {
    func dragInteraction(_ interaction: UIDragInteraction,
                        itemsForBeginning session: any UIDragSession) -> [UIDragItem] {
        guard let selectedText = textInSelectedRange() else { return [] }
        let provider = NSItemProvider(object: selectedText as NSString)
        return [UIDragItem(itemProvider: provider)]
    }
}

extension CustomEditor: UIDropInteractionDelegate {
    func dropInteraction(_ interaction: UIDropInteraction,
                        performDrop session: any UIDropSession) {
        // Handle the drop using UITextInput methods
        // Convert drop point to UITextPosition
        let point = session.location(in: self)
        guard let position = closestPosition(to: point) else { return }
        // Insert text at position
    }
}
```

## Platform Comparison

| Feature | iOS (UITextView) | macOS (NSTextView) |
|---------|------------------|-------------------|
| Text drag/drop protocols | UITextDraggable / UITextDroppable | NSDraggingSource / NSDraggingDestination |
| Specialized delegates | UITextDragDelegate / UITextDropDelegate | None (general dragging APIs) |
| Drop proposal system | UITextDropProposal with actions | performDragOperation override |
| Multi-line preview | UITextDragPreviewRenderer | System-provided |
| iPhone drag | Disabled by default | N/A |
| File drops on text | Supported | Only if isRichText + importsGraphics |
| Move vs copy | Automatic (same view = move) | Manual via operation mask |

## Common Pitfalls

1. **Drag not working on iPhone** — `textDragInteraction?.isEnabled` defaults to `false` on iPhone. Must enable explicitly.
2. **Non-editable views rejecting drops** — Implement `willBecomeEditableForDrop` returning `.temporary` to accept drops on read-only views.
3. **Custom UITextInput views have no text drag/drop** — Must add UIDragInteraction/UIDropInteraction manually. The text-specific protocols only apply to UITextField and UITextView.
4. **Attributed text ignored in drag previews** — Known issue (rdar://34098227). Provide custom drag items to ensure attributed text is included.
5. **macOS field editor intercepts drops** — Drops during NSTextField editing go to the field editor, not the text field. Provide a custom field editor to intercept.
6. **Move vs copy confusion** — Same-view drops default to move (source text deleted). Cross-view defaults to copy. Check `drop.isSameView` in your proposal.
7. **NSTextView not accepting file drops** — Both `isRichText` and `importsGraphics` must be enabled for file drop acceptance on macOS.

## Related Skills

- Use the pasteboard section in this reference for copy/paste (synchronous clipboard operations).
- Use the interaction section in this reference for other gesture and interaction customization.
- Use the input ref section in this reference for the UITextInput protocol that custom drag/drop builds on.
- Use the **rich-text-reference** agent when dropped content becomes inline attachments.

---

# Accessibility in Custom Text Editors

Use this skill when the main question is how to make a custom text editor work with VoiceOver, Dynamic Type, or other assistive technologies.

## When to Use

- Making a wrapped UITextView accessible in SwiftUI
- VoiceOver not reading text or announcing changes in a custom editor
- Dynamic Type not scaling in a custom text view
- Custom view needs text editing accessibility traits
- Accessibility Inspector shows missing or wrong information

## Quick Decision

- Need Dynamic Type font scaling -> the dynamic type section in this reference
- Need color contrast for text -> the **rich-text-reference** agent
- Need UIViewRepresentable wrapping -> the **platform-reference** agent
- Need general iOS accessibility beyond text editors -> see platform accessibility documentation

## Core Guidance

## UITextView Accessibility (Built-In)

`UITextView` is accessible by default. It:

- Reports as static text or editable text field depending on `isEditable`
- Exposes text content to VoiceOver
- Supports text navigation gestures (swipe up/down for character/word/line granularity)
- Announces text changes automatically

If your `UITextView` is not accessible, check that it is not hidden behind another view, that `isAccessibilityElement` has not been set to `false`, and that it is within the accessibility hierarchy.

## UIViewRepresentable Text View Accessibility

### The Problem

When wrapping `UITextView` in SwiftUI via `UIViewRepresentable`, the accessibility tree can break. SwiftUI may create its own accessibility element that shadows the UITextView's built-in accessibility.

### The Fix

Ensure the SwiftUI wrapper does not override the UITextView's accessibility:

```swift
struct EditorView: UIViewRepresentable {
    func makeUIView(context: Context) -> UITextView {
        let textView = UITextView()
        textView.isEditable = true
        textView.isSelectable = true
        // Do NOT set accessibilityLabel or accessibilityValue on the wrapper
        // Let UITextView handle its own accessibility
        return textView
    }

    func updateUIView(_ uiView: UITextView, context: Context) {
        // Update text content only
    }
}
```

If you need to add accessibility hints:

```swift
func makeUIView(context: Context) -> UITextView {
    let textView = UITextView()
    textView.accessibilityHint = "Double tap to edit"
    // accessibilityLabel and accessibilityValue are managed by UITextView
    return textView
}
```

### SwiftUI Accessibility Modifiers vs UIKit

Do NOT apply SwiftUI accessibility modifiers to the wrapper — they replace the UITextView's accessibility subtree:

```swift
// ❌ WRONG — shadows UITextView's built-in accessibility
EditorView()
    .accessibilityLabel("Editor")  // Replaces UITextView's dynamic label

// ✅ CORRECT — set on the UITextView itself
func makeUIView(context: Context) -> UITextView {
    let textView = UITextView()
    textView.accessibilityLabel = "Editor"  // Supplements, doesn't replace
    return textView
}
```

## Custom View Accessibility

If you build a text view from scratch (not using UITextView), you must implement accessibility yourself.

### Minimum Requirements

```swift
class CustomTextView: UIView {
    override var isAccessibilityElement: Bool {
        get { true }
        set { }
    }

    override var accessibilityTraits: UIAccessibilityTraits {
        get { isEditable ? .none : .staticText }
        set { }
    }

    override var accessibilityValue: String? {
        get { textContent }
        set { }
    }

    override var accessibilityLabel: String? {
        get { placeholder ?? "Text editor" }
        set { }
    }
}
```

### Text Editing Accessibility

For VoiceOver text navigation (character-by-character, word-by-word), adopt `UIAccessibilityReadingContent`:

```swift
extension CustomTextView: UIAccessibilityReadingContent {
    func accessibilityLineNumber(for point: CGPoint) -> Int {
        lineNumber(at: point)
    }

    func accessibilityContent(forLineNumber lineNumber: Int) -> String? {
        textContent(forLine: lineNumber)
    }

    func accessibilityFrame(forLineNumber lineNumber: Int) -> CGRect {
        frameForLine(lineNumber)
    }

    func accessibilityPageContent() -> String? {
        textContent
    }
}
```

### UIAccessibilityTextualContext

Set the textual context so the system optimizes VoiceOver behavior:

```swift
textView.accessibilityTextualContext = .plain          // Default prose
textView.accessibilityTextualContext = .sourceCode     // Code editor
textView.accessibilityTextualContext = .messaging      // Chat messages
textView.accessibilityTextualContext = .spreadsheet    // Tabular data
textView.accessibilityTextualContext = .wordProcessing // Rich text editor
```

This affects VoiceOver's reading behavior — for example, `.sourceCode` reads punctuation that would be skipped in `.plain`.

## Announcing Text Changes

### Automatic Behavior

`UITextView` does NOT automatically post accessibility notifications like `screenChanged` or `layoutChanged`. For incremental typing, VoiceOver reads characters directly through the text input system. For programmatic changes that the user should know about, you must post notifications yourself.

### Custom Announcements

When your editor makes programmatic changes that the user should know about:

```swift
func applyFormatting(_ style: FormatStyle) {
    // Apply the formatting
    applyStyle(style, to: selectedRange)

    // Announce to VoiceOver
    UIAccessibility.post(
        notification: .announcement,
        argument: "Applied \(style.name) formatting"
    )
}

func insertAutocompletion(_ text: String) {
    insertText(text)

    // Announce what was inserted
    UIAccessibility.post(
        notification: .announcement,
        argument: "Autocompleted: \(text)"
    )
}
```

### Layout Changes

When the editor's content or layout changes significantly (e.g., content loaded, view resized):

```swift
UIAccessibility.post(notification: .layoutChanged, argument: textView)
// VoiceOver will re-read the focused element
```

## Dynamic Type in Custom Editors

### Scaling Fonts

If your editor uses custom fonts, they must scale with Dynamic Type:

```swift
let baseFont = UIFont(name: "Menlo", size: 14)!
let scaledFont = UIFontMetrics(forTextStyle: .body).scaledFont(for: baseFont)
textView.font = scaledFont
```

### Responding to Size Changes

```swift
override func traitCollectionDidChange(_ previousTraitCollection: UITraitCollection?) {
    super.traitCollectionDidChange(previousTraitCollection)
    if traitCollection.preferredContentSizeCategory != previousTraitCollection?.preferredContentSizeCategory {
        // Re-apply fonts
        updateFonts()
    }
}
```

For iOS 17+, use `UITraitChangeObservable`:

```swift
registerForTraitChanges([UITraitPreferredContentSizeCategory.self]) { (self: EditorView, _) in
    self.updateFonts()
}
```

### adjustsFontForContentSizeCategory

For `UITextView` with a single font:

```swift
textView.adjustsFontForContentSizeCategory = true
textView.font = UIFont.preferredFont(forTextStyle: .body)
```

For editors with mixed fonts (syntax highlighting), you must manually re-apply `UIFontMetrics.scaledFont(for:)` when the content size category changes.

## Accessibility Inspector Testing

### What to Check

1. **Element exists.** The text view appears in the Accessibility Inspector hierarchy.
2. **Traits correct.** Shows as editable text (not just static text) when `isEditable = true`.
3. **Value updates.** The `accessibilityValue` reflects current text content.
4. **Label present.** Either set explicitly or derived from a placeholder.
5. **Actions available.** Activate (double-tap) puts the view into editing mode.
6. **Text navigation.** Rotor gestures work for character, word, line, and heading navigation.

### Common Failures

| Symptom | Likely Cause |
|---------|-------------|
| VoiceOver skips the editor | `isAccessibilityElement = false` or view is hidden |
| VoiceOver reads stale text | `accessibilityValue` not updating after edits |
| "Dimmed" announcement | `isEnabled = false` on the text view |
| No text navigation gestures | Missing `UIAccessibilityReadingContent` on custom view |
| SwiftUI modifier shadows UIKit | `.accessibilityLabel()` applied to UIViewRepresentable wrapper |

## Common Pitfalls

1. **SwiftUI accessibility modifiers on UIViewRepresentable wrappers.** These replace the UIKit view's accessibility subtree. Set accessibility properties on the UIKit view directly, not on the SwiftUI wrapper.
2. **Not posting announcements for programmatic changes.** Users cannot see the screen — if your code changes text without user input, announce it.
3. **Custom fonts without UIFontMetrics.** Raw `UIFont(name:size:)` does not scale with Dynamic Type. Always wrap in `UIFontMetrics.scaledFont(for:)`.
4. **Forgetting to set accessibilityTextualContext.** Source code editors that don't set `.sourceCode` will have VoiceOver skip punctuation, making code incomprehensible.
5. **Testing only with VoiceOver.** Also test with Switch Control, Voice Control, and Full Keyboard Access — each has different interaction patterns.

## Related Skills

- Use the dynamic type section in this reference for comprehensive Dynamic Type patterns.
- Use the **rich-text-reference** agent for color contrast and accessibility colors.
- Use the **platform-reference** agent for UIViewRepresentable wrapping patterns.
- Use `/skill apple-text-views` for choosing accessible text views.

---

# Dynamic Type Reference

Use this skill when the main question is how text should scale with content size category and accessibility sizes.

## When to Use

- You are implementing Dynamic Type in UIKit, AppKit, or SwiftUI.
- You are scaling custom fonts.
- You are testing layout behavior at large accessibility sizes.

## Quick Decision

- Native text styles are enough -> use semantic text styles directly
- Custom font but standard scaling -> use `UIFontMetrics`
- Rich text or attributed text does not update -> handle size-category changes explicitly

## Core Guidance

## Text Styles and Default Sizes (at Large / Default)

| Text Style | UIKit | SwiftUI | Weight | Default Size |
|------------|-------|---------|--------|-------------|
| Extra Large Title 2 | `.extraLargeTitle2` | `.extraLargeTitle2` | Bold | 28pt |
| Extra Large Title | `.extraLargeTitle` | `.extraLargeTitle` | Bold | 36pt |
| Large Title | `.largeTitle` | `.largeTitle` | Regular | 34pt |
| Title 1 | `.title1` | `.title` | Regular | 28pt |
| Title 2 | `.title2` | `.title2` | Regular | 22pt |
| Title 3 | `.title3` | `.title3` | Regular | 20pt |
| Headline | `.headline` | `.headline` | **Semibold** | 17pt |
| Body | `.body` | `.body` | Regular | 17pt |
| Callout | `.callout` | `.callout` | Regular | 16pt |
| Subheadline | `.subheadline` | `.subheadline` | Regular | 15pt |
| Footnote | `.footnote` | `.footnote` | Regular | 13pt |
| Caption 1 | `.caption1` | `.caption` | Regular | 12pt |
| Caption 2 | `.caption2` | `.caption2` | Regular | 11pt |

## Point Size Scaling Table (Body Style)

| Category | Body Size | API Constant |
|----------|----------|-------------|
| xSmall | 14pt | `.extraSmall` |
| Small | 15pt | `.small` |
| Medium | 16pt | `.medium` |
| **Large (Default)** | **17pt** | `.large` |
| xLarge | 19pt | `.extraLarge` |
| xxLarge | 21pt | `.extraExtraLarge` |
| xxxLarge | 23pt | `.extraExtraExtraLarge` |
| **AX1** | **28pt** | `.accessibilityMedium` |
| **AX2** | **33pt** | `.accessibilityLarge` |
| **AX3** | **40pt** | `.accessibilityExtraLarge` |
| **AX4** | **47pt** | `.accessibilityExtraExtraLarge` |
| **AX5** | **53pt** | `.accessibilityExtraExtraExtraLarge` |

At AX5, Body text is **3x** its default size.

## What Automatically Supports Dynamic Type

| Component | Auto-scales? | Notes |
|-----------|-------------|-------|
| SwiftUI `Text` with `.font(.body)` | ✅ | All semantic font styles scale |
| SwiftUI `Text` with `.font(.system(size: 17))` | ❌ | Fixed size — does NOT scale |
| SwiftUI `Text` with `.font(.custom("X", size: 17, relativeTo: .body))` | ✅ | Scales via `relativeTo:` |
| SwiftUI `Text` with `.font(.custom("X", fixedSize: 17))` | ❌ | Fixed — does NOT scale |
| `UILabel` with `preferredFont(forTextStyle:)` | ✅ if `adjustsFontForContentSizeCategory = true` |
| `UILabel` with `UIFont.systemFont(ofSize: 17)` | ❌ | Fixed size |
| `UITextView` with `preferredFont(forTextStyle:)` | ✅ if `adjustsFontForContentSizeCategory = true` |
| `NSAttributedString` with fixed font | ❌ | Must re-apply fonts on size change |
| `NSTextView` | Partial | macOS Dynamic Type is limited |

## UIKit: Making Text Scale

### System Fonts

```swift
label.font = UIFont.preferredFont(forTextStyle: .body)
label.adjustsFontForContentSizeCategory = true  // Auto-update on change
```

**Without `adjustsFontForContentSizeCategory`:** The font is a snapshot — it doesn't update when the user changes their size preference.

### Custom Fonts with UIFontMetrics

```swift
let customFont = UIFont(name: "Avenir-Medium", size: 17)!
let metrics = UIFontMetrics(forTextStyle: .body)

// Scale with no upper bound
label.font = metrics.scaledFont(for: customFont)

// Scale with maximum
label.font = metrics.scaledFont(for: customFont, maximumPointSize: 28)

// Scale non-font values (padding, spacing, icon sizes)
let scaledPadding = metrics.scaledValue(for: 16.0)

label.adjustsFontForContentSizeCategory = true
```

The base size (17 in this example) should be the **default (Large)** size.

### UITextView

```swift
textView.font = UIFont.preferredFont(forTextStyle: .body)
textView.adjustsFontForContentSizeCategory = true
```

**With attributed text:** `adjustsFontForContentSizeCategory` does NOT re-scale attributed string fonts. You must listen for size changes and re-apply fonts:

```swift
NotificationCenter.default.addObserver(
    forName: UIContentSizeCategory.didChangeNotification,
    object: nil, queue: .main
) { _ in
    self.reapplyDynamicFonts()
}
```

### Limiting Scale Range (iOS 15+)

```swift
// Prevent text from getting too small or too large
view.minimumContentSizeCategory = .medium
view.maximumContentSizeCategory = .accessibilityLarge
```

Works on any UIView. Caps the effective content size category for that view and its children.

## SwiftUI: Making Text Scale

### Semantic Fonts (Always Scale)

```swift
Text("Scales").font(.body)        // ✅ Scales
Text("Scales").font(.headline)    // ✅ Scales
Text("Scales").font(.largeTitle)  // ✅ Scales
```

### Custom Fonts

```swift
// ✅ Scales with Dynamic Type
Text("Custom").font(.custom("Avenir", size: 17, relativeTo: .body))

// ❌ Does NOT scale
Text("Fixed").font(.custom("Avenir", fixedSize: 17))
Text("Fixed").font(.system(size: 17))
```

### @ScaledMetric for Non-Font Values

```swift
@ScaledMetric(relativeTo: .body) var iconSize: CGFloat = 24
@ScaledMetric var padding: CGFloat = 16  // Uses .body curve by default

Image(systemName: "star")
    .frame(width: iconSize, height: iconSize)
    .padding(padding)
```

### Limiting Scale Range (iOS 15+)

```swift
Text("Limited")
    .dynamicTypeSize(.medium ... .accessibility3)
```

## macOS

`NSFont.preferredFont(forTextStyle:)` exists but macOS Dynamic Type is more limited:
- Only available on macOS 11+
- macOS doesn't have the same accessibility size categories
- Users change text size via System Settings → Accessibility → Display → Text Size (macOS 14+)
- SwiftUI on macOS uses the same `.font(.body)` API and it scales

## Non-Latin Script Line Height (iOS 17+)

iOS 17 introduced automatic dynamic line-height adjustment for scripts that are taller than Latin (Thai, Arabic, Devanagari, Tibetan). Previously, fixed `minimumLineHeight`/`maximumLineHeight` values could clip ascenders and descenders on these scripts. The system now adjusts line height per-line based on the actual glyphs rendered.

**If you set explicit `minimumLineHeight`/`maximumLineHeight` on NSParagraphStyle**, the system respects your values and may still clip. For multilingual content, prefer `lineHeightMultiple` over fixed heights, or avoid constraining line height entirely.

## What Breaks at Large Accessibility Sizes

| Issue | Solution |
|-------|---------|
| Text clips in fixed-height containers | Use `adjustsFontSizeToFitWidth` or flexible layouts |
| Horizontal layouts overflow | Switch to vertical at accessibility sizes |
| Icons too small relative to text | Use `@ScaledMetric` / `UIFontMetrics.scaledValue(for:)` |
| Table cells too short | Use self-sizing cells with Auto Layout |
| Navigation bar titles truncate | System handles, but custom title views need attention |
| Buttons with text overflow | Allow multi-line button labels |

### Large Content Viewer (iOS 13+)

For UI elements that can't grow (tab bars, toolbars, segmented controls):

```swift
// UIKit
button.showsLargeContentViewer = true
button.largeContentTitle = "Settings"
button.largeContentImage = UIImage(systemName: "gear")

// SwiftUI
Button("Settings") { }
    .accessibilityShowsLargeContentViewer {
        Label("Settings", systemImage: "gear")
    }
```

Long-press shows a HUD with the enlarged content.

## Testing Dynamic Type

1. **Xcode Environment Overrides:** Run app → Debug bar → Environment Overrides → Text Size slider
2. **Control Center:** Settings → Control Center → Add "Text Size" → Adjust while app runs
3. **Accessibility Inspector:** Xcode → Open Developer Tool → Accessibility Inspector → Settings → Font Size
4. **SwiftUI Preview:** `.environment(\.sizeCategory, .accessibilityExtraExtraExtraLarge)`

## Common Pitfalls

1. **Fixed font sizes don't scale** — `.system(size: 17)` and `UIFont.systemFont(ofSize: 17)` are permanently 17pt. Use semantic styles.
2. **Attributed strings don't auto-scale** — `adjustsFontForContentSizeCategory` only works with plain `font` property. For attributed text, listen for `UIContentSizeCategory.didChangeNotification`.
3. **Forgetting `adjustsFontForContentSizeCategory`** — Without it, UIKit text views get a snapshot font that never updates.
4. **Not testing accessibility sizes** — AX3-AX5 are where most layout bugs appear. Always test.
5. **Icons not scaling** — SF Symbols auto-scale with Dynamic Type. Custom icons need `@ScaledMetric` or `UIFontMetrics.scaledValue`.

## Related Skills

- Use `/skill apple-text-views` when sizing depends on which control you chose.
- Use the **rich-text-reference** agent for contrast and semantic color pairing.
- Use the writing tools section in this reference when accessibility sizing affects editor integrations.
