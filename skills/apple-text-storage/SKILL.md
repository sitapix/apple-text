---
name: apple-text-storage
description: Use when working with NSTextStorage, NSTextContentStorage, or NSTextContentManager — subclassing, processEditing, or delegate hooks
license: MIT
---

# Text Storage Architecture

Use this skill when the main question is how text content is stored, mutated, and synchronized with layout.

Keep this file for the storage architecture, editing lifecycle, and common pitfalls. For custom backing stores (piece table, rope, CRDT), thread-safety patterns, and performance profiling, use [advanced-patterns.md](advanced-patterns.md).

## When to Use

- You are editing or subclassing `NSTextStorage`.
- You need to understand `NSTextContentStorage` or `NSTextContentManager`.
- You are debugging storage-layer behavior beneath layout or rendering symptoms.

## Quick Decision

- Need invalidation behavior after edits -> `/skill apple-text-layout-invalidation`
- Need storage architecture and editing lifecycle -> stay here
- Need TextKit 1 or 2 API detail after choosing a stack -> jump to the matching `*-ref` skill

## Core Guidance

## Architecture Overview

### TextKit 1 Storage

```
NSTextStorage (IS-A NSMutableAttributedString)
    │
    ├── stores characters + attributes
    ├── processEditing() lifecycle
    └── notifies → NSLayoutManager(s)
```

### TextKit 2 Storage

```
NSTextContentManager (abstract)
    │
    └── NSTextContentStorage (concrete)
            │
            ├── wraps → NSTextStorage
            ├── generates → NSTextParagraph elements
            └── notifies → NSTextLayoutManager(s)
```

### The Key Difference

- **TextKit 1:** NSTextStorage is the ONLY model layer. Layout managers read directly from it.
- **TextKit 2:** NSTextContentStorage adds an **element layer** on top of NSTextStorage. Layout managers work with elements (NSTextParagraph), not raw attributed strings.

## NSTextStorage

### What It Is

`NSTextStorage` is a subclass of `NSMutableAttributedString`. It IS an attributed string with additional change-tracking and notification machinery.

```swift
class NSTextStorage: NSMutableAttributedString {
    var layoutManagers: [NSLayoutManager] { get }
    var editedMask: EditActions { get }
    var editedRange: NSRange { get }
    var changeInLength: Int { get }

    func addLayoutManager(_ aLayoutManager: NSLayoutManager)
    func removeLayoutManager(_ aLayoutManager: NSLayoutManager)

    func edited(_ editedMask: EditActions, range editedRange: NSRange, changeInLength delta: Int)
    func processEditing()

    var delegate: NSTextStorageDelegate?
}
```

### Editing Lifecycle (Complete)

```
                    ┌─────────────────────────────┐
                    │      External mutation       │
                    │  (replaceCharacters, etc.)   │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │     edited(_:range:delta:)   │
                    │  Accumulates edit tracking:  │
                    │  - editedMask |= mask        │
                    │  - editedRange = union(old,  │
                    │    new, adjusted for delta)   │
                    │  - changeInLength += delta    │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │      endEditing() called     │
                    │      (or auto if no batch)   │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │       processEditing()       │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
   ┌──────────▼──────────┐  ┌─────▼─────┐  ┌──────────▼──────────┐
   │ willProcessEditing   │  │ fixAttrs  │  │ didProcessEditing   │
   │ delegate callback    │  │ (system)  │  │ delegate callback   │
   │                      │  │           │  │                     │
   │ Can modify:          │  │ Font sub, │  │ Can modify:         │
   │ - Characters ✅      │  │ paragraph │  │ - Attributes ✅     │
   │ - Attributes ✅      │  │ fixing    │  │ - Characters ❌     │
   └──────────────────────┘  └───────────┘  └─────────┬───────────┘
                                                       │
                                          ┌────────────▼────────────┐
                                          │ Notify layout managers  │
                                          │ processEditing(for:     │
                                          │   edited:range:         │
                                          │   changeInLength:       │
                                          │   invalidatedRange:)    │
                                          └─────────────────────────┘
```

### Batching Edits

```swift
textStorage.beginEditing()

// Multiple mutations — each calls edited() internally
textStorage.replaceCharacters(in: range1, with: "new text")
textStorage.addAttribute(.font, value: UIFont.boldSystemFont(ofSize: 16), range: range2)
textStorage.deleteCharacters(in: range3)

textStorage.endEditing()
// processEditing() called ONCE with accumulated edits
```

**Without batching:** Each mutation triggers `processEditing()` separately = multiple layout invalidation passes.

### Subclassing NSTextStorage

Required when you want a custom backing store (e.g., rope data structure, gap buffer, piece table).

**Four required primitives:**

```swift
class RopeTextStorage: NSTextStorage {
    private var rope = Rope()  // Your custom backing store

    // 1. Read string content
    override var string: String {
        rope.string
    }

    // 2. Read attributes at location
    override func attributes(at location: Int,
                             effectiveRange range: NSRangePointer?) -> [NSAttributedString.Key: Any] {
        rope.attributes(at: location, effectiveRange: range)
    }

    // 3. Replace characters (MUST call edited())
    override func replaceCharacters(in range: NSRange, with str: String) {
        beginEditing()
        rope.replaceCharacters(in: range, with: str)
        edited(.editedCharacters, range: range, changeInLength: (str as NSString).length - range.length)
        endEditing()
    }

    // 4. Set attributes (MUST call edited())
    override func setAttributes(_ attrs: [NSAttributedString.Key: Any]?, range: NSRange) {
        beginEditing()
        rope.setAttributes(attrs, range: range)
        edited(.editedAttributes, range: range, changeInLength: 0)
        endEditing()
    }
}
```

**Critical rules for subclasses:**
- `replaceCharacters` and `setAttributes` MUST call `edited(_:range:changeInLength:)` with correct mask
- `edited()` with `.editedCharacters` must include accurate `changeInLength`
- The `string` property must always reflect current content
- `attributes(at:effectiveRange:)` must handle the full range correctly

### Delegate Protocol

```swift
protocol NSTextStorageDelegate: NSObjectProtocol {
    // Called BEFORE fixAttributes — can modify characters AND attributes
    func textStorage(_ textStorage: NSTextStorage,
                     willProcessEditing editedMask: NSTextStorage.EditActions,
                     range editedRange: NSRange,
                     changeInLength delta: Int)

    // Called AFTER fixAttributes — can modify ONLY attributes
    func textStorage(_ textStorage: NSTextStorage,
                     didProcessEditing editedMask: NSTextStorage.EditActions,
                     range editedRange: NSRange,
                     changeInLength delta: Int)
}
```

**Common use cases:**
- `willProcessEditing`: Auto-correct, text transforms, syntax detection
- `didProcessEditing`: Syntax highlighting (apply color attributes based on content)

## NSTextContentStorage (TextKit 2)

### What It Is

Concrete subclass of `NSTextContentManager` that bridges NSTextStorage to the TextKit 2 element model.

```swift
class NSTextContentStorage: NSTextContentManager {
    var textStorage: NSTextStorage? { get set }
    var attributedString: NSAttributedString? { get set }

    func textRange(for range: NSRange) -> NSTextRange?
    func offset(from: NSTextLocation, to: NSTextLocation) -> Int

    var delegate: NSTextContentStorageDelegate?
}
```

### How It Works

1. NSTextContentStorage **observes** NSTextStorage edit notifications
2. When text storage changes, it **regenerates** affected `NSTextParagraph` elements
3. Paragraph boundaries are determined by paragraph separators (`\n`, `\r\n`, `\r`, `\u{2029}`)
4. Each paragraph becomes one `NSTextParagraph` with the paragraph's attributed text

### Editing Pattern

```swift
// ✅ CORRECT: Wrap edits in transaction
textContentStorage.performEditingTransaction {
    textStorage.replaceCharacters(in: range, with: newText)
}

// ❌ WRONG: Direct edit without transaction
textStorage.replaceCharacters(in: range, with: newText)
// May not trigger proper element regeneration
```

### Delegate

```swift
protocol NSTextContentStorageDelegate: NSTextContentManagerDelegate {
    // Create custom paragraph elements with display-only modifications
    func textContentStorage(_ textContentStorage: NSTextContentStorage,
                            textParagraphWith range: NSRange) -> NSTextParagraph?
}
```

**Use case:** Return modified paragraph for display without changing the underlying storage (e.g., show line numbers, fold code, render Markdown preview).

## NSTextContentManager (Abstract)

### When to Subclass Directly

Subclass `NSTextContentManager` (instead of using `NSTextContentStorage`) when your backing store is NOT an attributed string:

- Database-backed document model
- HTML DOM
- AST (abstract syntax tree)
- Collaborative editing CRDT

### Required Overrides

```swift
class DOMContentManager: NSTextContentManager {
    override var documentRange: NSTextRange { ... }

    override func enumerateTextElements(
        from textLocation: NSTextLocation?,
        options: NSTextContentManager.EnumerationOptions,
        using block: (NSTextElement) -> Bool
    ) { ... }

    override func replaceContents(
        in range: NSTextRange,
        with textElements: [NSTextElement]?
    ) { ... }

    override func location(
        _ location: NSTextLocation,
        offsetBy offset: Int
    ) -> NSTextLocation? { ... }

    override func offset(
        from: NSTextLocation,
        to: NSTextLocation
    ) -> Int { ... }
}
```

## Storage Layer Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                      TextKit 1 Only                         │
│                                                             │
│  NSTextStorage ──────────────────────→ NSLayoutManager(s)   │
│  (attributed string = backing store)                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      TextKit 2                              │
│                                                             │
│  NSTextStorage ──→ NSTextContentStorage ──→ NSTextLayout-   │
│  (backing store)   (element generator)      Manager(s)      │
│                           │                                 │
│                    NSTextParagraph(s)                        │
│                    (element tree)                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 Custom TextKit 2                             │
│                                                             │
│  Custom Store ──→ NSTextContentManager ──→ NSTextLayout-    │
│  (any format)     (custom subclass)        Manager(s)       │
│                           │                                 │
│                    Custom NSTextElement(s)                   │
└─────────────────────────────────────────────────────────────┘
```

## Common Pitfalls

1. **Not calling `edited()` in NSTextStorage subclass** — Layout managers never learn about changes. The most common subclassing bug.
2. **Wrong `changeInLength` value** — Causes range calculation errors, crashes, or corrupted layout.
3. **Modifying characters in `didProcessEditing`** — Characters are already committed. Attribute-only modifications allowed here.
4. **Direct NSTextStorage edit without `performEditingTransaction` (TextKit 2)** — Element tree may not update correctly.
5. **Accessing `textStorage.string` during processEditing** — The string is valid, but indices from before the edit are invalid if characters changed.
6. **Not batching edits** — `beginEditing()`/`endEditing()` exists for a reason. Use it for multi-mutation operations.

## Going Deeper

Read `advanced-patterns.md` in this skill directory for:

- Custom backing stores (piece table, rope, CRDT) with subclassing examples
- Thread-safety patterns for background processing with version guards
- NSTextContentManager subclassing for non-attributed-string document models
- Performance measurement with `os_signpost` instrumentation

## Related Skills

- Use `/skill apple-text-layout-invalidation` for what re-renders or recomputes after storage edits.
- Use `/skill apple-text-textkit1-ref` and `/skill apple-text-textkit2-ref` for stack-specific APIs.
- Use `/skill apple-text-textkit-diag` when the symptom matters more than the storage model.
