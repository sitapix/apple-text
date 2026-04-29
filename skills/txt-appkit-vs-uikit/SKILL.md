---
name: txt-appkit-vs-uikit
description: Use when comparing NSTextView and UITextView capabilities or porting editor behavior between macOS and iOS
license: MIT
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

## Common Pitfalls When Porting

1. **NSTextView doesn't scroll itself** — UITextView IS a UIScrollView; NSTextView is NOT. On macOS, you must wrap NSTextView in an `NSScrollView` (`NSScrollView(documentView: textView)`).

2. **`isEditable` semantics flip on field editors** — On macOS, `NSTextField` shares a single field editor (`NSTextView`) per window. Setting properties on the field editor leaks across all fields. Touch field-editor settings only via `textShouldBeginEditing(_:)`.

3. **`tintColor` is UIKit-only** — On AppKit, cursor color is `insertionPointColor`; selection color is `selectedTextAttributes[.backgroundColor]`. They are not unified.

4. **`UITextDragInteraction` has no AppKit equivalent** — AppKit drag-and-drop uses `NSDraggingSource`/`NSDraggingDestination` on the view, not on a separate interaction object.

5. **AppKit menu validation is opt-in** — `validateMenuItem(_:)` and `validateUserInterfaceItem(_:)` must be implemented for context menus to enable/disable correctly. UIKit's `UIEditMenuInteraction` infers state automatically.

6. **NSTextView delegate methods can fire on background threads** during pasteboard reading/writing — never assume main-thread context in `textView(_:writeSelectionTo:)` callbacks. UITextView always dispatches on the main thread.

7. **Field editor cascade triggers TextKit 1 fallback for the entire window** — Touching `layoutManager` on one `NSTextField`'s field editor flips all field editors in that window. Audit shared field-editor code paths carefully.

## Related Skills

- Use `/skill txt-views` when the real question is which view class to adopt.
- Use `/skill txt-representable` when SwiftUI wrapping is part of the platform decision.
- Use `/skill txt-writing-tools` for Apple Intelligence editor differences.
