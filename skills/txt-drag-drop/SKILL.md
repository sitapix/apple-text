---
name: txt-drag-drop
description: Customize text drag and drop in editors — UITextDraggable and UITextDroppable on UITextView and UITextField, UITextDragDelegate items and previews, UITextDropProposal actions, UITextDragPreviewRenderer for multi-line previews, falling back to UIDragInteraction/UIDropInteraction for custom UITextInput views, and the NSDraggingSource/NSDraggingDestination architecture on macOS. Use when text drag fails on iPhone, non-editable views need to accept drops, custom drag items or previews are needed, or a custom editor needs drag/drop wired up by hand. Trigger on 'drag a selection out of my editor', 'drop an image into my text view', 'reorder by dragging' even without UITextDraggable / UITextDroppable named. Do NOT use for clipboard operations (see txt-pasteboard).
license: MIT
---

# Text Drag and Drop

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill covers drag and drop *inside* text editors — both the iOS-specific `UITextDraggable`/`UITextDroppable` protocols (and the delegates that customize them) and the macOS `NSDraggingSource`/`NSDraggingDestination` architecture. Before relying on a specific delegate signature, fetch via Sosumi (`sosumi.ai/documentation/uikit/uitextdraggable`) — the drop proposal types and same-view operation flags have shifted across iOS versions.

The shared substrate is `NSItemProvider` type negotiation, identical to the modern paste path. Most drop bugs are gesture priorities (drag wins over selection) or a missing protocol on iPhone (text drag is off by default there). On macOS the architecture is genuinely different — the iOS-style delegates do not exist.

## Contents

- [Default behavior on stock text views](#default-behavior-on-stock-text-views)
- [UITextDragDelegate](#uitextdragdelegate)
- [UITextDropDelegate and UITextDropProposal](#uitextdropdelegate-and-uitextdropproposal)
- [Multi-line drag previews](#multi-line-drag-previews)
- [Non-editable drops](#non-editable-drops)
- [Custom UITextInput views](#custom-uitextinput-views)
- [macOS drag and drop](#macos-drag-and-drop)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Default behavior on stock text views

`UITextView` and `UITextField` adopt `UITextDraggable` and `UITextDroppable` automatically on iPad. The user lifts a selection with a long-press, the system makes drag items from the selected text, and drops insert at the caret position. Same-view drops behave as moves (the source range is removed); cross-view or cross-app drops behave as copies.

iPhone is the exception: text drag is *disabled* by default. The drop side is enabled. To turn drag on:

```swift
textView.textDragInteraction?.isEnabled = true
```

If users on iPhone can't initiate a drag, this is almost always the cause. The interaction is installed but switched off.

## UITextDragDelegate

Set `textView.textDragDelegate = self`. All methods are optional; you implement only the seams you care about.

```swift
func textDraggableView(_ view: UIView & UITextDraggable,
                       itemsForDrag req: UITextDragRequest) -> [UIDragItem] {
    let plain = req.suggestedItems.first?.localObject as? String ?? ""
    let textItem = UIDragItem(itemProvider: NSItemProvider(object: plain as NSString))

    // Add an app-specific representation
    let custom = encodeRichFormat(for: req.dragRange)
    let customItem = UIDragItem(itemProvider: NSItemProvider(
        item: custom as NSData,
        typeIdentifier: "com.example.myapp.richtext"
    ))
    return [textItem, customItem]
}
```

Returning an empty array disables drag for that selection. To disable globally, switch off `textDragInteraction.isEnabled` instead — it's clearer and avoids running the delegate per gesture.

To strip text colors from the drag preview (useful when the document has high-contrast styling that looks bad lifted on the screen background):

```swift
textView.textDragOptions = .stripTextColorFromPreviews
```

Lifecycle hooks:

```swift
func textDraggableView(_ v: UIView & UITextDraggable,
                       dragSessionWillBegin s: UIDragSession) {
    // pause autosave, hide cursor, etc.
}
func textDraggableView(_ v: UIView & UITextDraggable,
                       dragSessionDidEnd s: UIDragSession) {
    // resume normal state
}
```

## UITextDropDelegate and UITextDropProposal

The drop side returns a proposal describing what the drop will do at this position:

```swift
func textDroppableView(_ v: UIView & UITextDroppable,
                       proposalForDrop drop: UITextDropRequest) -> UITextDropProposal {
    let proposal = drop.isSameView
        ? UITextDropProposal(dropAction: .insert)   // moves within view
        : UITextDropProposal(dropAction: .insert)
    proposal.useFastSameViewOperations = true
    return proposal
}
```

The actions are `.insert` (insert at drop position, the usual case), `.replaceSelection` (replace whatever is currently selected), and `.replaceAll` (replace the whole document — used for "open this file" style drops). `useFastSameViewOperations` lets the system optimize the move case by avoiding a full round-trip through serialization.

`willPerformDrop` runs just before the drop applies, useful for validation, undo grouping, or telemetry:

```swift
func textDroppableView(_ v: UIView & UITextDroppable,
                       willPerformDrop drop: UITextDropRequest) {
    // last chance to log or fail
}
```

## Multi-line drag previews

Default drag previews work for single-line selections. Multi-line text needs `UITextDragPreviewRenderer`, which produces previews that follow the actual line geometry:

```swift
let renderer = UITextDragPreviewRenderer(
    layoutManager: textView.layoutManager,
    range: textView.selectedRange
)

renderer.adjust(firstLineRect: &firstLineRect,
                bodyRect: &bodyRect,
                lastLineRect: &lastLineRect,
                textOrigin: origin)
```

The renderer doesn't return a `UITargetedDragPreview` directly; you compose one using the rects it adjusts. For the lifting preview, return a `UITargetedDragPreview` from `dragPreviewForLiftingItem`; for the drop animation, return one from `previewForDroppingAllItemsWithDefault`.

## Non-editable drops

Read-only text views reject drops by default — same flag controls both editing and dropping. Override to accept drops on a non-editable view:

```swift
func textDroppableView(_ v: UIView & UITextDroppable,
                       willBecomeEditableForDrop drop: UITextDropRequest) -> UITextDropEditability {
    .temporary    // editable for this drop only
    // .yes — permanently editable
    // .no — reject drop (default)
}
```

`.temporary` is the typical answer when the document is conceptually read-only but specific commands (like "drop here to import") should write through.

## Custom UITextInput views

`UITextDraggable` and `UITextDroppable` are NOT auto-adopted by custom views. Only `UITextField` and `UITextView` get them. A custom view needs the general drag/drop interactions and translates positions into `UITextPosition` values manually.

```swift
final class CustomEditor: UIView, UITextInput {
    override init(frame: CGRect) {
        super.init(frame: frame)
        addInteraction(UIDragInteraction(delegate: self))
        addInteraction(UIDropInteraction(delegate: self))
    }
}

extension CustomEditor: UIDragInteractionDelegate {
    func dragInteraction(_ i: UIDragInteraction,
                         itemsForBeginning session: any UIDragSession) -> [UIDragItem] {
        guard let s = textInSelectedRange() else { return [] }
        return [UIDragItem(itemProvider: NSItemProvider(object: s as NSString))]
    }
}

extension CustomEditor: UIDropInteractionDelegate {
    func dropInteraction(_ i: UIDropInteraction,
                         performDrop session: any UIDropSession) {
        let point = session.location(in: self)
        guard let pos = closestPosition(to: point) else { return }
        for item in session.items {
            _ = item.itemProvider.loadObject(ofClass: NSString.self) { obj, _ in
                guard let s = obj as? String else { return }
                Task { @MainActor in self.insert(s, at: pos) }
            }
        }
    }
}
```

The drop point is in the view's coordinate space, and `closestPosition(to:)` is the same `UITextInput` method system gestures use — see `txt-uitextinput` for the position arithmetic that backs it.

## macOS drag and drop

AppKit has no analog to `UITextDragDelegate`. Drag is initiated by `NSDraggingSource`, drops are received by `NSDraggingDestination` — both protocols are adopted by `NSView`, so any text view inherits a baseline.

```swift
final class CustomTextView: NSTextView {
    override var acceptableDragTypes: [NSPasteboard.PasteboardType] {
        var types = super.acceptableDragTypes
        types.append(.init("com.example.myapp.richtext"))
        return types
    }

    override func performDragOperation(_ info: NSDraggingInfo) -> Bool {
        let pb = info.draggingPasteboard
        if let data = pb.data(forType: .init("com.example.myapp.richtext")) {
            insertCustomContent(data)
            return true
        }
        return super.performDragOperation(info)
    }
}
```

Two macOS-specific gotchas. First, file drops onto `NSTextView` only work if both `isRichText` and `importsGraphics` are `true`; either alone won't do it. Second, when the user drags onto an `NSTextField` *while it's being edited*, the drop hits the shared field editor (an `NSTextView` instance), not the text field itself. To intercept, supply a custom field editor:

```swift
func windowWillReturnFieldEditor(_ sender: NSWindow, to client: Any?) -> Any? {
    client is MyTextField ? customFieldEditor : nil
}
```

## Common Mistakes

1. **Drag doesn't work on iPhone.** `textDragInteraction.isEnabled` defaults to `false` on iPhone. Set it to `true` if you want users to lift selections.

2. **Non-editable view rejects drops silently.** Read-only views reject drops by default. Implement `willBecomeEditableForDrop` returning `.temporary` to opt in for specific drops while keeping the document read-only otherwise.

3. **Custom UITextInput view assumed to inherit text drag/drop.** Only `UITextView` and `UITextField` get the text-specific protocols. A custom view needs `UIDragInteraction` and `UIDropInteraction` added by hand and translates drop points to `UITextPosition` itself.

4. **Multi-line drag preview looks like a single rectangle.** Default preview composes one rect for the bounding box. Use `UITextDragPreviewRenderer` to follow per-line geometry; otherwise multi-line lifts look glued together.

5. **Drag delegate returning empty array but interaction still installed.** Wastes a delegate round-trip per gesture. Toggle `textDragInteraction.isEnabled = false` instead.

6. **Move vs copy confusion.** Same-view drop = move (source removed); cross-view or cross-app = copy. Inspect `drop.isSameView` if behavior depends on the source.

7. **NSTextView refusing file drops.** Both `isRichText` and `importsGraphics` must be `true` for file drops to land on macOS text views.

8. **Drops landing on the field editor instead of the NSTextField.** While editing, the field editor handles the drop. Provide a custom field editor through `windowWillReturnFieldEditor(_:to:)` to intercept.

9. **`loadObject`/`loadDataRepresentation` callbacks touching text storage on the wrong thread.** They fire on arbitrary threads. Hop to main before mutating storage, just like the paste path.

## References

- `txt-pasteboard` — clipboard operations and the shared `NSItemProvider` type-negotiation pattern
- `txt-uitextinput` — `UITextInput` implementation for custom views, including `closestPosition(to:)` and position arithmetic used by drop handlers
- `txt-attachments` — when dropped images become inline `NSTextAttachment` content
- `txt-selection-menus` — gesture coordination, useful when drag conflicts with selection or long-press
- [UITextDraggable](https://sosumi.ai/documentation/uikit/uitextdraggable)
- [UITextDroppable](https://sosumi.ai/documentation/uikit/uitextdroppable)
- [UITextDropProposal](https://sosumi.ai/documentation/uikit/uitextdropproposal)
- [UITextDragPreviewRenderer](https://sosumi.ai/documentation/uikit/uitextdragpreviewrenderer)
- [UIDragInteraction](https://sosumi.ai/documentation/uikit/uidraginteraction)
- [UIDropInteraction](https://sosumi.ai/documentation/uikit/uidropinteraction)
