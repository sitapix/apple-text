---
name: txt-undo
description: Implement and debug undo and redo in text editors — NSUndoManager grouping with beginUndoGrouping/endUndoGrouping, automatic typing coalescing on UITextView and NSTextView, disabling registration around programmatic edits, the changeInLength bug that breaks undo on custom NSTextStorage subclasses, registering manual inverses on NSTextContentManager, and avoiding cross-talk with Writing Tools revert. Trigger on 'undo isn't working right', 'too many undo steps for one paste', 'undo lost my work after Writing Tools', 'cmd-z behaves wrong' even without NSUndoManager named. Use when undo collapses too many changesUse when undo collapses too many changes, splits one operation into many groups, applies wrong inverse ranges, or stops working entirely after a paste, replace-all, or document load.
license: MIT
---

# Undo and Redo

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill covers undo behavior in Apple text editors — what `UITextView` and `NSTextView` give you for free, how `NSUndoManager` groups work, how to make programmatic edits undoable (or not), and the registration patterns for custom storage and content managers. Before claiming a specific `NSUndoManager` method signature, fetch via Sosumi (`sosumi.ai/documentation/foundation/undomanager`) — registration semantics around closures and `withTarget:` overloads have shifted.

The recurring failure mode is undo registering the wrong inverse because storage edits were emitted with a wrong `changeInLength`. The undo manager records what it was told; if the bookkeeping is off by one, the inverse replaces the wrong range and either crashes or corrupts text on undo.

## Contents

- [How undo works in stock text views](#how-undo-works-in-stock-text-views)
- [Grouping and coalescing](#grouping-and-coalescing)
- [Programmatic edits — undoable and not](#programmatic-edits--undoable-and-not)
- [Custom NSTextStorage subclasses](#custom-nstextstorage-subclasses)
- [Standalone storage without a text view](#standalone-storage-without-a-text-view)
- [TextKit 2 transactions and content managers](#textkit-2-transactions-and-content-managers)
- [Writing Tools and undo](#writing-tools-and-undo)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## How undo works in stock text views

Both `UITextView` and `NSTextView` ship with a working `undoManager`. Typing, paste, cut, dictation, and selected-text replacement all register themselves automatically. The mechanism is observation of `processEditing` on `NSTextStorage` — when the storage commits an edit, the text view records the inverse on its undo manager.

This is why making a programmatic edit "undoable" is usually free: write through `textStorage.replaceCharacters(in:with:)` and the recording happens on the next `processEditing` cycle, as long as the storage is attached to the text view and the text view has an undo manager.

## Grouping and coalescing

A single tap on Undo doesn't reverse one keystroke — it reverses one *group*, where the group is roughly "what the user did in one continuous editing run." The system creates a new group when:

- Typing pauses past an internal threshold.
- The insertion point moves.
- A non-typing edit happens (paste, cut, delete).
- `beginUndoGrouping()` / `endUndoGrouping()` are called explicitly.

Within a group, adjacent character insertions are coalesced — typing "Hello world" produces one undo group, not eleven. As long as your custom storage subclass calls `beginEditing/edited/endEditing` correctly, the same coalescing works there.

To force a single undo group around a multi-step operation, wrap explicitly:

```swift
textView.undoManager?.beginUndoGrouping()
defer { textView.undoManager?.endUndoGrouping() }

textView.textStorage.beginEditing()
textView.textStorage.replaceCharacters(in: r1, with: t1)
textView.textStorage.replaceCharacters(in: r2, with: t2)
textView.textStorage.endEditing()
```

Without the outer grouping, each `endEditing()` call ends up in its own undo group and the user has to undo three times to revert the operation.

## Programmatic edits — undoable and not

Sometimes a programmatic edit is part of the user's authored content and should be undoable. Sometimes it's a system update (loading a document, applying a server pull, restoring state) and it must NOT pollute the undo stack.

```swift
// Undoable — just write through storage; the text view records automatically
textView.textStorage.beginEditing()
textView.textStorage.replaceCharacters(in: range, with: newText)
textView.textStorage.endEditing()

// Not undoable — bracket with disable/enable registration
textView.undoManager?.disableUndoRegistration()
defer { textView.undoManager?.enableUndoRegistration() }

textView.textStorage.beginEditing()
textView.textStorage.replaceCharacters(in: range, with: newText)
textView.textStorage.endEditing()
```

`disableUndoRegistration()` and `enableUndoRegistration()` are reference-counted. Calling disable twice requires two enables. The `defer` is the safe pattern — every early return still re-enables registration.

Setting `textView.text = "..."` or `textView.attributedText = ...` replaces the entire `NSTextStorage` and clears the undo stack. This is how to load a fresh document, but it's also how undo "mysteriously stops working" if you ever set those properties during editing.

## Custom NSTextStorage subclasses

A subclass of `NSTextStorage` does not need to register undo actions itself — the text view does that — provided the subclass calls `edited(_:range:changeInLength:)` with accurate values.

```swift
override func replaceCharacters(in range: NSRange, with str: String) {
    backingStore.replaceCharacters(in: range, with: str)
    let delta = (str as NSString).length - range.length
    edited(.editedCharacters, range: range, changeInLength: delta)
}
```

The trap: `delta` must be in NSString units (UTF-16). Swift `String.count` is wrong on emoji and combining marks. If `delta` is wrong by even one, the undo manager records an inverse range that doesn't match the actual edit, and the next undo either crashes (`NSRangeException`) or replaces the wrong characters silently.

Attribute-only edits should pass `.editedAttributes` rather than `.editedCharacters`. Mismatching the mask isn't a crash, but the undo recorded for an attribute change might end up structured as a character change and replay incorrectly.

## Standalone storage without a text view

If your `NSTextStorage` lives in a model layer with no attached text view, there's no observer to record undo. You register inverses yourself in the override:

```swift
final class UndoableTextStorage: NSTextStorage {
    var externalUndoManager: UndoManager?

    override func replaceCharacters(in range: NSRange, with str: String) {
        let oldText = (string as NSString).substring(with: range)

        if let um = externalUndoManager, um.isUndoRegistrationEnabled {
            let inverseRange = NSRange(location: range.location,
                                       length: (str as NSString).length)
            um.registerUndo(withTarget: self) { storage in
                storage.replaceCharacters(in: inverseRange, with: oldText)
            }
        }

        beginEditing()
        backingStore.replaceCharacters(in: range, with: str)
        edited(.editedCharacters,
               range: range,
               changeInLength: (str as NSString).length - range.length)
        endEditing()
    }
}
```

Capture the data needed to compute the inverse *before* applying the forward edit, otherwise the captured `oldText` is whatever the storage looks like after the change.

## TextKit 2 transactions and content managers

In TextKit 2, edits to `NSTextContentStorage` should be wrapped in `performEditingTransaction`. Undo recording still happens at the text storage level — the content storage observes the storage edit and regenerates elements on replay.

```swift
textContentStorage.performEditingTransaction {
    textStorage.replaceCharacters(in: range, with: newText)
}
```

When you subclass `NSTextContentManager` *without* a backing `NSTextStorage` (database-backed editor, programmatic content), there is no attributed string for the system to diff. Undo is entirely your responsibility:

```swift
final class DatabaseContentManager: NSTextContentManager {
    var undoManager: UndoManager?

    func insertRow(_ row: Row, at index: Int) {
        undoManager?.registerUndo(withTarget: self) { cm in
            cm.deleteRow(at: index)
        }
        performEditingTransaction { database.insert(row, at: index) }
    }

    func deleteRow(at index: Int) {
        let row = database.row(at: index)
        undoManager?.registerUndo(withTarget: self) { cm in
            cm.insertRow(row, at: index)
        }
        performEditingTransaction { database.deleteRow(at: index) }
    }
}
```

Register the inverse before or after the mutation, but consistently. Inside the transaction is allowed but harder to reason about — observers receive the transaction's change, see your registration mid-flight, and the resulting interleaving is fragile.

## Writing Tools and undo

Writing Tools uses the host's undo manager to offer its own revert ("undo Writing Tools change"). If your code registers custom undo actions while a Writing Tools session is active, the revert can apply your inverse against text Writing Tools rewrote, leaving the document in a corrupted state.

Guard programmatic registration during active sessions:

```swift
guard !textView.isWritingToolsActive else { return }
undoManager?.registerUndo(withTarget: self) { /* ... */ }
```

## Common Mistakes

1. **Wrong `changeInLength` in a custom NSTextStorage subclass.** The undo manager records an inverse against the wrong range. Subsequent undos either crash with `NSRangeException` or silently corrupt text. Always compute `delta` in NSString (UTF-16) units, not Swift `String.count`.

2. **`disableUndoRegistration()` without a matching `enableUndoRegistration()`.** Future edits silently aren't undoable. Use `defer { undoManager?.enableUndoRegistration() }` to guarantee balance.

3. **`beginUndoGrouping()` without `endUndoGrouping()`.** Edits accumulate into one giant group until the run loop ends. Use `defer` on the matching `endUndoGrouping()`.

4. **Setting `textView.text` or `textView.attributedText` during editing.** Replaces the storage and clears the undo stack. For undoable replacement of large content, write through `textStorage.replaceCharacters` instead.

5. **Syntax highlighting through `textStorage.addAttribute` polluting undo.** Attribute changes register undo entries. The user undoes their typing and gets "undo highlight color" first. Apply display-only styling via temporary attributes (TextKit 1) or rendering attributes (TextKit 2). See `txt-find-replace` for the highlighting paths and `txt-textkit-debug` for the broader pattern.

6. **Replace All firing one undo per match.** Without an outer grouping, each `endEditing()` ends a group. Wrap the whole loop in `beginUndoGrouping/endUndoGrouping` so the whole replace-all is one undo.

7. **Custom UndoManager registration during an active Writing Tools session.** Writing Tools owns the revert behavior; your registration corrupts its state. Check `isWritingToolsActive` before registering.

8. **Standalone storage with no text view, expecting automatic undo.** No text view means no observer means no recording. Register inverses yourself in `replaceCharacters(in:with:)`.

9. **Capturing the wrong `oldText` in the inverse closure.** Reading the value *after* the forward edit gives you the new text, not the original. Capture before mutating.

## References

- `txt-nstextstorage` — `NSTextStorage` editing lifecycle (`beginEditing`/`edited`/`endEditing`) that undo recording observes
- `txt-textkit-debug` — symptom-driven debugging when undo causes stale layout, crashes, or content loss
- `txt-find-replace` — highlight paths that don't pollute undo, and replace-all single-undo grouping
- `txt-writing-tools` — Writing Tools session lifecycle and the revert that shares the undo manager
- [UndoManager](https://sosumi.ai/documentation/foundation/undomanager)
