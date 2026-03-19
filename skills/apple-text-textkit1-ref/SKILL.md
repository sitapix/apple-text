---
name: apple-text-textkit1-ref
description: TextKit 1 complete reference — NSLayoutManager, NSTextStorage, NSTextContainer MVC triad, glyph generation, layout process, temporary attributes, exclusion paths, multi-column layout, and customization points
license: MIT
---

# TextKit 1 Reference

Use this skill when you already know the editor is on TextKit 1 and need the exact APIs or lifecycle details.

## When to Use

- You are working with `NSLayoutManager`.
- You need glyph-based APIs.
- You are maintaining legacy or explicitly opt-in TextKit 1 code.

## Quick Decision

- Need to choose between TextKit 1 and 2 -> `/skill apple-text-layout-manager-selection`
- Already committed to TextKit 1 and need exact APIs -> stay here
- Debugging symptoms before you know the root cause -> `/skill apple-text-textkit-diag`

## Core Guidance

Complete reference for TextKit 1 covering the NSLayoutManager-based text system available since iOS 7 / macOS 10.0.

## Architecture (MVC Triad)

```
NSTextStorage (Model) ←→ NSLayoutManager (Controller) ←→ NSTextContainer → UITextView/NSTextView (View)
       │                         │                              │
  Attributed string        Glyphs + layout              Geometric region
  Character storage        Glyph → character mapping     Exclusion paths
  Edit notifications       Line fragment rects           Size constraints
```

**One-to-many relationships:**
- One NSTextStorage → many NSLayoutManagers (same text, different layouts)
- One NSLayoutManager → many NSTextContainers (multi-page/multi-column)
- One NSTextContainer → one UITextView/NSTextView

## NSTextStorage

Subclass of `NSMutableAttributedString`. The canonical backing store for all TextKit text.

### Required Primitives (When Subclassing)

You **must** subclass NSTextStorage if you want a custom backing store. Implement these four:

```swift
class CustomTextStorage: NSTextStorage {
    private var storage = NSMutableAttributedString()

    override var string: String {
        storage.string
    }

    override func attributes(at location: Int, effectiveRange range: NSRangePointer?) -> [NSAttributedString.Key: Any] {
        storage.attributes(at: location, effectiveRange: range)
    }

    override func replaceCharacters(in range: NSRange, with str: String) {
        beginEditing()
        storage.replaceCharacters(in: range, with: str)
        edited(.editedCharacters, range: range, changeInLength: (str as NSString).length - range.length)
        endEditing()
    }

    override func setAttributes(_ attrs: [NSAttributedString.Key: Any]?, range: NSRange) {
        beginEditing()
        storage.setAttributes(attrs, range: range)
        edited(.editedAttributes, range: range, changeInLength: 0)
        endEditing()
    }
}
```

**Critical:** Mutation methods MUST call `edited(_:range:changeInLength:)` with the correct mask (`.editedCharacters`, `.editedAttributes`, or both). Without this, layout managers won't be notified.

### Editing Lifecycle

```
beginEditing()
├── replaceCharacters(in:with:) → calls edited(.editedCharacters, ...)
├── setAttributes(_:range:)     → calls edited(.editedAttributes, ...)
├── addAttribute(_:value:range:) → calls edited(.editedAttributes, ...)
└── endEditing()
    └── processEditing()
        ├── delegate.textStorage(_:willProcessEditing:range:changeInLength:)
        │   └── Can modify BOTH characters AND attributes
        ├── fixAttributes(in:)  — font substitution, paragraph style fixing
        ├── delegate.textStorage(_:didProcessEditing:range:changeInLength:)
        │   └── Can modify ONLY attributes (characters → crash/undefined)
        └── Notifies all attached layout managers
            └── layoutManager.processEditing(for:edited:range:changeInLength:invalidatedRange:)
```

**Batching edits:** Wrap multiple mutations in `beginEditing()`/`endEditing()` to coalesce into one `processEditing()` call. Without batching, each mutation triggers a separate layout invalidation pass.

### Edit Masks

```swift
NSTextStorage.EditActions.editedCharacters  // Text content changed
NSTextStorage.EditActions.editedAttributes  // Attributes changed (no text change)
// Combine: [.editedCharacters, .editedAttributes]
```

### Delegate Methods

```swift
// BEFORE attribute fixing — can modify characters AND attributes
func textStorage(_ textStorage: NSTextStorage,
                 willProcessEditing editedMask: NSTextStorage.EditActions,
                 range editedRange: NSRange,
                 changeInLength delta: Int)

// AFTER attribute fixing — can modify ONLY attributes
func textStorage(_ textStorage: NSTextStorage,
                 didProcessEditing editedMask: NSTextStorage.EditActions,
                 range editedRange: NSRange,
                 changeInLength delta: Int)
```

**Use case for willProcessEditing:** Syntax highlighting — detect keywords and apply attributes before layout.

**Use case for didProcessEditing:** Attribute cleanup — ensure consistent paragraph styles.

## NSLayoutManager

Translates characters → glyphs, lays out glyphs into line fragments within text containers.

### Glyph Generation

```swift
// Force glyph generation for a range
layoutManager.ensureGlyphs(forCharacterRange: range)
layoutManager.ensureGlyphs(forGlyphRange: glyphRange)

// Query glyphs
let glyph = layoutManager.glyph(at: glyphIndex)
let glyphRange = layoutManager.glyphRange(forCharacterRange: charRange, actualCharacterRange: nil)
let charRange = layoutManager.characterRange(forGlyphRange: glyphRange, actualGlyphRange: nil)
```

**Character → glyph mapping is NOT 1:1.** Ligatures, composed characters, and complex scripts can produce:
- One character → multiple glyphs
- Multiple characters → one glyph (ligatures)

### Layout Process

```swift
// Force layout for specific targets
layoutManager.ensureLayout(for: textContainer)
layoutManager.ensureLayout(forCharacterRange: range)
layoutManager.ensureLayout(forGlyphRange: glyphRange)
layoutManager.ensureLayout(forBoundingRect: rect, in: textContainer)
```

**Layout is lazy by default.** Glyphs and layout are computed on demand when queried. `ensureLayout` forces eager computation.

### Line Fragment Queries

```swift
// Bounding rect for a glyph range
let rect = layoutManager.boundingRect(forGlyphRange: range, in: textContainer)

// Line fragment rect containing a glyph
let lineRect = layoutManager.lineFragmentRect(forGlyphAt: glyphIndex, effectiveRange: &effectiveRange)

// Used rect (accounts for line spacing)
let usedRect = layoutManager.lineFragmentUsedRect(forGlyphAt: glyphIndex, effectiveRange: &effectiveRange)

// Location of glyph within line fragment
let point = layoutManager.location(forGlyphAt: glyphIndex)

// Character index at point
let charIndex = layoutManager.characterIndex(for: point, in: textContainer, fractionOfDistanceBetweenInsertionPoints: &fraction)
```

### Non-Contiguous Layout (Optional)

```swift
layoutManager.allowsNonContiguousLayout = true
```

When enabled, the layout manager can skip laying out text that isn't currently visible. Improves performance for large documents but is **not always reliable** in TextKit 1.

**Checking if layout is complete:**
```swift
if layoutManager.hasNonContiguousLayout {
    // Some ranges may not be laid out yet
}
```

### Temporary Attributes

Overlay visual attributes without modifying the text storage. Used for spell-check underlines, find highlights, etc.

```swift
// Set temporary attributes
layoutManager.setTemporaryAttributes([.foregroundColor: UIColor.red],
                                     forCharacterRange: range)

// Add (merge) temporary attributes
layoutManager.addTemporaryAttribute(.backgroundColor, value: UIColor.yellow,
                                    forCharacterRange: range)

// Remove temporary attributes
layoutManager.removeTemporaryAttribute(.backgroundColor, forCharacterRange: range)
```

**Key difference from text storage attributes:** Temporary attributes don't persist, don't participate in archiving, and don't trigger layout invalidation.

### Delegate Methods

```swift
// Control line spacing
func layoutManager(_ layoutManager: NSLayoutManager,
                   lineSpacingAfterGlyphAt glyphIndex: Int,
                   withProposedLineFragmentRect rect: CGRect) -> CGFloat

// Control paragraph spacing
func layoutManager(_ layoutManager: NSLayoutManager,
                   paragraphSpacingAfterGlyphAt glyphIndex: Int,
                   withProposedLineFragmentRect rect: CGRect) -> CGFloat

// Customize line fragment rect
func layoutManager(_ layoutManager: NSLayoutManager,
                   shouldUse lineFragmentRect: UnsafeMutablePointer<CGRect>,
                   forTextContainer textContainer: NSTextContainer) -> Bool

// Custom glyph drawing
func layoutManager(_ layoutManager: NSLayoutManager,
                   shouldGenerateGlyphs glyphs: UnsafePointer<CGGlyph>,
                   properties: UnsafePointer<NSLayoutManager.GlyphProperty>,
                   characterIndexes: UnsafePointer<Int>,
                   font: UIFont,
                   forGlyphRange glyphRange: NSRange) -> Int
```

## NSTextContainer

Defines the geometric region where text is laid out.

### Configuration

```swift
let container = NSTextContainer(size: CGSize(width: 300, height: .greatestFiniteMagnitude))
container.lineFragmentPadding = 5.0  // Default: 5.0 (inset from edges)
container.maximumNumberOfLines = 0   // 0 = unlimited
container.lineBreakMode = .byWordWrapping
```

### Exclusion Paths

Regions where text should NOT be laid out (e.g., around images):

```swift
let circlePath = UIBezierPath(ovalIn: CGRect(x: 50, y: 50, width: 100, height: 100))
container.exclusionPaths = [circlePath]
```

**Coordinate system:** Exclusion paths are in the text container's coordinate space.

### Multi-Column / Multi-Page Layout

```swift
let layoutManager = NSLayoutManager()
textStorage.addLayoutManager(layoutManager)

let container1 = NSTextContainer(size: CGSize(width: 300, height: 500))
let container2 = NSTextContainer(size: CGSize(width: 300, height: 500))
layoutManager.addTextContainer(container1)
layoutManager.addTextContainer(container2)

// Text overflows from container1 into container2
let textView1 = UITextView(frame: frame1, textContainer: container1)
let textView2 = UITextView(frame: frame2, textContainer: container2)
```

## Custom Drawing

### Drawing Glyphs

```swift
// Override in NSLayoutManager subclass
override func drawGlyphs(forGlyphRange glyphsToShow: NSRange, at origin: CGPoint) {
    // Custom background drawing
    drawCustomBackground(forGlyphRange: glyphsToShow, at: origin)
    // Default glyph drawing
    super.drawGlyphs(forGlyphRange: glyphsToShow, at: origin)
}

override func drawBackground(forGlyphRange glyphsToShow: NSRange, at origin: CGPoint) {
    // Custom background (strikethrough, highlights, etc.)
    super.drawBackground(forGlyphRange: glyphsToShow, at: origin)
}
```

### Text Attachments

```swift
let attachment = NSTextAttachment()
attachment.image = UIImage(named: "icon")
attachment.bounds = CGRect(x: 0, y: -4, width: 20, height: 20)

let attrString = NSAttributedString(attachment: attachment)
textStorage.insert(attrString, at: insertionPoint)
```

## Quick Reference

| Task | API |
|------|-----|
| Force glyph generation | `ensureGlyphs(forCharacterRange:)` |
| Force layout | `ensureLayout(for:)` / `ensureLayout(forCharacterRange:)` |
| Character at point | `characterIndex(for:in:fractionOfDistanceBetweenInsertionPoints:)` |
| Rect for character range | `boundingRect(forGlyphRange:in:)` |
| Line rect at glyph | `lineFragmentRect(forGlyphAt:effectiveRange:)` |
| Total used rect | `usedRect(for:)` |
| Number of glyphs | `numberOfGlyphs` |
| Glyph ↔ character mapping | `glyphRange(forCharacterRange:actualCharacterRange:)` |
| Overlay styling | `setTemporaryAttributes(_:forCharacterRange:)` |
| Invalidate layout | `invalidateLayout(forCharacterRange:actualCharacterRange:)` |
| Invalidate glyphs | `invalidateGlyphs(forCharacterRange:changeInLength:actualCharacterRange:)` |

## Common Pitfalls

1. **Forgetting `edited()` in NSTextStorage subclass** — Layout managers never update. Always call `edited(_:range:changeInLength:)` in mutation primitives.
2. **Modifying characters in `didProcessEditing`** — Causes crashes or undefined behavior. Only modify attributes.
3. **Not batching edits** — Each individual mutation triggers `processEditing()`. Wrap in `beginEditing()`/`endEditing()`.
4. **Accessing `textView.layoutManager` on TextKit 2 views** — Triggers irreversible fallback to TextKit 1. Check `textLayoutManager` first.
5. **`ensureLayout(for:)` on large documents** — O(n) operation. Use `ensureLayout(forBoundingRect:in:)` to limit scope.
6. **Assuming 1:1 character-glyph mapping** — Complex scripts and ligatures break this assumption.

## Related Skills

- Use `/skill apple-text-layout-manager-selection` for migration or stack choice.
- Use `/skill apple-text-fallback-triggers` when TextKit 1 appears unexpectedly.
- Use `/skill apple-text-storage` for deeper storage-layer behavior underneath the glyph APIs.
