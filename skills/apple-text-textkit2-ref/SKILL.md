---
name: apple-text-textkit2-ref
description: TextKit 2 complete reference — NSTextLayoutManager, NSTextContentManager, NSTextContentStorage, viewport layout, text elements, layout fragments, rendering attributes, custom rendering, and TextKit 1 migration
license: MIT
---

# TextKit 2 Reference

Use this skill when you already know the editor is on TextKit 2 and need exact APIs, object roles, or migration details.

## When to Use

- You are working with `NSTextLayoutManager`, `NSTextContentManager`, or fragments.
- You need viewport-layout or migration details.
- You are writing TextKit 2 code directly rather than choosing between stacks.

## Quick Decision

- Need to choose between TextKit 1 and 2 -> `/skill apple-text-layout-manager-selection`
- Already committed to TextKit 2 and need exact APIs -> stay here
- Need fragment/rendering behavior specifically -> `/skill apple-text-viewport-rendering`

## Core Guidance

Complete reference for TextKit 2 (iOS 15+ / macOS 12+). Replaces glyph-based TextKit 1 with element-based layout optimized for correctness, safety, and performance.

Keep this file for the object model, editing rules, and layout-manager behavior. For fragment internals, object-based range mechanics, and the TextKit 1 to 2 mapping table, use [fragments-and-migration.md](fragments-and-migration.md).

## Architecture

```
NSTextContentManager        NSTextLayoutManager         NSTextContainer
(content model)        →    (layout controller)    →    (geometry)
       │                           │                         │
NSTextContentStorage        NSTextLayoutFragment         UITextView
(wraps NSTextStorage)       NSTextLineFragment           NSTextView
       │                           │
NSTextElement               NSTextViewportLayoutController
NSTextParagraph             (viewport management)
```

### Design Principles

1. **Correctness** — No glyph APIs. International text (Arabic, Devanagari, CJK) handled correctly without character-glyph mapping assumptions.
2. **Safety** — Immutable value semantics for elements and fragments. Thread-safe reads.
3. **Performance** — Always non-contiguous. Only viewport text is laid out. O(viewport) not O(document).

## NSTextContentManager (Abstract)

Base class for content management. Manages document content as a tree of `NSTextElement` objects.

### Key Properties

```swift
var textLayoutManagers: [NSTextLayoutManager] { get }
var primaryTextLayoutManager: NSTextLayoutManager? { get set }
var automaticallySynchronizesTextLayoutManagers: Bool  // default: true
var automaticallySynchronizesToBackingStore: Bool       // default: true
```

### Editing Transaction

All text storage modifications must be wrapped:

```swift
textContentManager.performEditingTransaction {
    // Modify the backing store (NSTextStorage) here
    textStorage.replaceCharacters(in: range, with: newText)
}
// Layout invalidation happens automatically after the transaction
```

**Without the transaction wrapper:** Element regeneration and layout invalidation may not occur correctly.

### Element Enumeration

```swift
textContentManager.enumerateTextElements(from: location, options: []) { element in
    if let paragraph = element as? NSTextParagraph {
        print(paragraph.attributedString)
    }
    return true  // continue enumeration
}
```

### Delegate

```swift
// Filter elements from layout (e.g., hide comments in a code editor)
func textContentManager(_ manager: NSTextContentManager,
                        shouldEnumerate textElement: NSTextElement,
                        options: NSTextContentManager.EnumerationOptions) -> Bool
```

## NSTextContentStorage (Concrete)

Default `NSTextContentManager` subclass. Wraps `NSTextStorage` and automatically divides content into `NSTextParagraph` elements.

### Relationship to NSTextStorage

```swift
let textContentStorage = NSTextContentStorage()
textContentStorage.textStorage = myTextStorage  // Set backing store

// Access text storage from content storage
let storage = textContentStorage.textStorage
```

**NSTextContentStorage observes NSTextStorage edits** and regenerates paragraph elements automatically.

### NSTextContentStorage vs NSTextStorage

| Aspect | NSTextStorage | NSTextContentStorage |
|--------|--------------|---------------------|
| **Role** | Backing store (attributed string) | Content manager wrapping backing store |
| **Addressing** | NSRange (integer-based) | NSTextRange / NSTextLocation (object-based) |
| **Output** | Raw attributed string | NSTextElement tree (paragraphs) |
| **Editing** | Direct mutations | `performEditingTransaction` wrapper |
| **Notifications** | `processEditing()` | Element change tracking |
| **When to subclass** | Custom backing store format | Custom content model (not attributed string based) |

**Decision:** Use NSTextContentStorage (default) unless you need a fundamentally different backing store (e.g., database-backed, DOM-based, piece table). In that case, subclass NSTextContentManager directly.

### Delegate

```swift
// Create custom paragraph elements with modified display attributes
// WITHOUT changing the underlying text storage
func textContentStorage(_ storage: NSTextContentStorage,
                        textParagraphWith range: NSRange) -> NSTextParagraph? {
    // Return nil for default behavior
    // Return custom NSTextParagraph to override display
    let originalText = storage.textStorage!.attributedSubstring(from: range)
    let modified = NSMutableAttributedString(attributedString: originalText)
    modified.addAttribute(.foregroundColor, value: UIColor.gray, range: NSRange(location: 0, length: modified.length))
    return NSTextParagraph(attributedString: modified)
}
```

### Range Conversion

```swift
// NSRange → NSTextRange
let textRange = textContentStorage.textRange(for: nsRange)

// NSTextRange → NSRange
let nsRange = textContentStorage.offset(from: textContentStorage.documentRange.location,
                                         to: textRange.location)
```

## NSTextElement

Abstract base class for document building blocks. Immutable (value semantics).

### Properties

```swift
var elementRange: NSTextRange? { get set }  // Range within document
var textContentManager: NSTextContentManager? { get }
var childElements: [NSTextElement] { get }    // For nested structures
var parentElement: NSTextElement? { get }
var isRepresentedElement: Bool { get }
```

## NSTextParagraph

Default element type. One per paragraph of text.

```swift
let paragraph: NSTextParagraph
paragraph.attributedString     // The paragraph's attributed content
paragraph.paragraphContentRange // Range excluding paragraph separator
paragraph.paragraphSeparators   // The paragraph separator characters
```

## NSTextLayoutManager

Replaces NSLayoutManager. **No glyph APIs.** Operates on elements and fragments.

### Key Properties

```swift
var textContentManager: NSTextContentManager? { get }
var textContainer: NSTextContainer? { get set }
var textViewportLayoutController: NSTextViewportLayoutController { get }
var textSelectionNavigation: NSTextSelectionNavigation { get }
var textSelections: [NSTextSelection] { get set }
var usageBoundsForTextContainer: CGRect { get }
var documentRange: NSTextRange { get }
```

### Layout Fragment Enumeration

```swift
// Enumerate visible layout fragments
textLayoutManager.enumerateTextLayoutFragments(
    from: textLayoutManager.documentRange.location,
    options: [.ensuresLayout, .ensuresExtraLineFragment]
) { fragment in
    print("Frame: \(fragment.layoutFragmentFrame)")
    for lineFragment in fragment.textLineFragments {
        print("  Line: \(lineFragment.typographicBounds)")
    }
    return true  // continue
}
```

**Options:**
- `.ensuresLayout` — Forces layout computation (expensive for large ranges)
- `.ensuresExtraLineFragment` — Includes empty trailing line fragment
- `.estimatesSize` — Use estimated sizes (faster, less accurate)
- `.reverse` — Enumerate backwards

### Rendering Attributes

Replace TextKit 1's temporary attributes. Overlay visual styling without modifying text storage:

```swift
// Set rendering attributes (replaces any existing)
textLayoutManager.setRenderingAttributes(
    [.foregroundColor: UIColor.red],
    forTextRange: range
)

// Add rendering attributes (merges)
textLayoutManager.addRenderingAttribute(.backgroundColor,
                                        value: UIColor.yellow,
                                        forTextRange: range)

// Remove rendering attributes
textLayoutManager.removeRenderingAttribute(.backgroundColor, forTextRange: range)

// Enumerate rendering attributes
textLayoutManager.enumerateRenderingAttributes(
    from: location, reverse: false
) { manager, attributes, range in
    return true
}
```

**Key difference from text storage attributes:** Rendering attributes don't persist, don't modify the model, and don't trigger element regeneration.

### Invalidating Layout

```swift
// Invalidate specific range
textLayoutManager.invalidateLayout(for: range)

// TextKit 2 re-lays out affected fragments on next viewport update
```

### Delegate

```swift
// Custom layout fragments (e.g., chat bubble backgrounds)
func textLayoutManager(_ manager: NSTextLayoutManager,
                       textLayoutFragmentFor location: NSTextLocation,
                       in textElement: NSTextElement) -> NSTextLayoutFragment {
    return BubbleLayoutFragment(textElement: textElement, range: textElement.elementRange)
}
```

## Common Pitfalls

1. **Using `ensuresLayout` for the full document** — O(document_size). Only ensure layout for visible ranges.
2. **NSTextLineFragment.characterRange is local** — It's relative to the line's attributed string, NOT the document. Convert through the parent element.
3. **`renderingSurfaceBounds` differs from `layoutFragmentFrame`** — Drawing can extend beyond the layout frame (diacritics, large descenders). Override `renderingSurfaceBounds` in custom fragments.
4. **Forgetting `performEditingTransaction`** — Direct NSTextStorage edits may not trigger proper element regeneration.
5. **Assuming layout exists outside viewport** — TextKit 2 may only have estimated layout for off-screen content. Use `.estimatesSize` option when precision isn't needed.

## Related Skills

- For fragment APIs, viewport controller hooks, range conversion, and migration tables, see [fragments-and-migration.md](fragments-and-migration.md).
- Use `/skill apple-text-layout-manager-selection` for migration and stack choice.
- Use `/skill apple-text-viewport-rendering` for fragment and rendering-pipeline behavior.
- Use `/skill apple-text-storage` for backing-store and editing-transaction background.
