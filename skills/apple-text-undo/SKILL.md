---
name: apple-text-undo
description: Use when implementing undo/redo in text editors, debugging undo grouping issues, integrating NSUndoManager with NSTextStorage or NSTextContentManager, handling undo for programmatic edits, or understanding undo coalescing behavior — covers TextKit 1 and TextKit 2 undo patterns
license: MIT
---

# Text Editor Undo/Redo

Use this skill when the main question is how undo and redo work in Apple text editors.

## When to Use

- Implementing undo in a custom text editor
- Debugging undo that groups too many or too few changes
- Programmatic edits that should or should not be undoable
- Custom NSTextStorage subclass undo integration

## Quick Decision

- Need storage editing lifecycle -> `/skill apple-text-storage`
- Need layout invalidation after undo -> `/skill apple-text-layout-invalidation`
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

- Use `/skill apple-text-storage` for the editing lifecycle behind undo recording.
- Use `/skill apple-text-textkit-diag` when undo causes stale layout or crashes.
- Use `/skill apple-text-writing-tools` for Writing Tools interaction with undo.
