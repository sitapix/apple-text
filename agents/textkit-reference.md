---
name: textkit-reference
description: Look up TextKit 1/2 APIs, layout mechanics, viewport rendering, text measurement, exclusion paths, fallback triggers, and text storage patterns.
model: sonnet
tools:
  - Glob
  - Grep
  - Read
---

# Textkit Reference Agent

You answer specific questions about TextKit APIs and runtime behavior.

## Instructions

1. Read the user's question carefully.
2. Find the relevant section in the reference material below.
3. Return ONLY the information that answers their question — maximum 40 lines.
4. Include exact API signatures, code examples, and gotchas when relevant.
5. Do NOT dump all reference material — extract what is relevant.
6. If the question is about choosing between TextKit 1 and TextKit 2, recommend the user consult the apple-text-views or apple-text-layout-manager-selection skill instead.

---

# TextKit 1 Reference

Use this skill when you already know the editor is on TextKit 1 and need the exact APIs or lifecycle details.

## When to Use

- You are working with `NSLayoutManager`.
- You need glyph-based APIs.
- You are maintaining legacy or explicitly opt-in TextKit 1 code.

## Quick Decision

- Need to choose between TextKit 1 and 2 -> the **platform-reference** agent
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

- Use the **platform-reference** agent for migration or stack choice.
- Use the fallback triggers section in this reference when TextKit 1 appears unexpectedly.
- Use the storage section in this reference for deeper storage-layer behavior underneath the glyph APIs.

---

# TextKit 2 Reference

Use this skill when you already know the editor is on TextKit 2 and need exact APIs, object roles, or migration details.

## When to Use

- You are working with `NSTextLayoutManager`, `NSTextContentManager`, or fragments.
- You need viewport-layout or migration details.
- You are writing TextKit 2 code directly rather than choosing between stacks.

## Quick Decision

- Need to choose between TextKit 1 and 2 -> the **platform-reference** agent
- Already committed to TextKit 2 and need exact APIs -> stay here
- Need fragment/rendering behavior specifically -> the viewport rendering section in this reference

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
- Use the **platform-reference** agent for migration and stack choice.
- Use the viewport rendering section in this reference for fragment and rendering-pipeline behavior.
- Use the storage section in this reference for backing-store and editing-transaction background.

---

# Viewport Layout, Line Fragments, Fonts & Rendering

Use this skill when the main question is how TextKit 2 viewport layout, fragments, and rendering behavior actually work.

## When to Use

- You need fragment, line-fragment, or viewport-layout details.
- You are debugging custom rendering or visual overlays.
- You need to know why visible and off-screen layout behave differently.

## Quick Decision

- Need full TextKit 2 object reference -> the textkit2 ref section in this reference
- Need rendering and viewport behavior -> stay here
- Need invalidation semantics rather than rendering pipeline details -> the layout invalidation section in this reference

## Core Guidance

Keep this file for viewport behavior, fragment geometry, and the high-level rendering mental model. For font fallback timing, rendering-attribute APIs, custom drawing hooks, Core Text underpinnings, and emoji notes, use [rendering-pipeline.md](rendering-pipeline.md).

## Viewport Effects on Layout

### TextKit 2: Viewport-Based (Always)

```
┌─────────────────────────────────────┐
│         Estimated Layout            │  ← Heights estimated, not exact
│         (not computed)              │
├─────────────────────────────────────┤
│     Overscroll Buffer (above)       │  ← Computed, ready for scroll
├─────────────────────────────────────┤
│     ███ VIEWPORT (visible) ███      │  ← Fully laid out, rendered
├─────────────────────────────────────┤
│     Overscroll Buffer (below)       │  ← Computed, ready for scroll
├─────────────────────────────────────┤
│         Estimated Layout            │
│         (not computed)              │
└─────────────────────────────────────┘
```

**NSTextViewportLayoutController** orchestrates this:

```swift
// Delegate callbacks during viewport layout:

// 1. Before layout begins
func textViewportLayoutControllerWillLayout(_ controller: NSTextViewportLayoutController) {
    // Remove old fragment views
}

// 2. For EACH visible layout fragment
func textViewportLayoutController(_ controller: NSTextViewportLayoutController,
    configureRenderingSurfaceFor textLayoutFragment: NSTextLayoutFragment) {
    // Position and configure the fragment's view/layer
    let frame = textLayoutFragment.layoutFragmentFrame
    fragmentView.frame = frame
}

// 3. After layout completes
func textViewportLayoutControllerDidLayout(_ controller: NSTextViewportLayoutController) {
    // Update scroll view content size
    let contentHeight = textLayoutManager.usageBoundsForTextContainer.height
    scrollView.contentSize = CGSize(width: bounds.width, height: contentHeight)
}
```

### TextKit 2 Viewport Gotchas

**Estimated heights are unstable:**
- `usageBoundsForTextContainer` changes frequently during scrolling
- Usually overestimates initially, then settles as layout proceeds
- Causes scroll bar to "jiggle" — knob size and position shift as estimates refine

**Scroll bar accuracy:**
- Scroll bar position/size are inaccurate until full document is laid out
- Users see the scroll bar "stop mid-scroll as if at document end" until layout catches up
- Even Apple's TextEdit exhibits this behavior

**Jump-to-position:**
- Fragment positions are dynamic before full layout
- Positions shift as surrounding content gets laid out
- Precise jumping requires `ensureLayout` for the target range first

### TextKit 1: Contiguous vs Non-Contiguous

**Without `allowsNonContiguousLayout` (contiguous):**
- Lays out ALL text from beginning to display point
- Scrolling to mid-document requires laying out everything before it
- O(document_size) for first display
- Exact document height guaranteed

**With `allowsNonContiguousLayout = true`:**
- Can skip layout for non-visible portions
- UITextView enables this by default
- **Reliability issues:** `boundingRect` and `lineFragmentRect` can return slightly wrong coordinates for long text (several thousand characters)
- Less controllable than TextKit 2's viewport model

### UITextView.isScrollEnabled = false (Inside Another Scroll View)

When scrolling is disabled:
- UITextView expands to fit its full content
- The "viewport" is effectively the entire content
- TextKit 2's viewport optimization is **neutralized** — all content gets laid out
- This is intentional — the view needs full layout for Auto Layout intrinsic size
- `scrollRangeToVisible()` doesn't work with scrolling disabled

## Line Fragments Deep Dive

### TextKit 1: Line Fragment Rect vs Used Rect

```
Line Fragment Rect (full allocation):
┌─────────────────────────────────────────────┐
│ padding │ Hello World ░░░░░░░░ │ padding │  ← lineFragmentRect
│         └────────────────────┘              │
│         │← lineFragmentUsedRect →│          │
│         (includes leading, glyph bounds)    │
│                                             │
│  ↑ paragraph spacing before                 │
│  ↓ paragraph spacing after (rect only)      │
└─────────────────────────────────────────────┘
```

| Rect | Includes | Excludes |
|------|----------|----------|
| **lineFragmentRect** | Padding, text, leading, paragraph spacing | Nothing — full allocation |
| **lineFragmentUsedRect** | Padding, text, leading | Paragraph spacing, trailing whitespace |

**Why two rects?** The used rect tells you where content actually is (for hit testing, cursor positioning). The full rect tells you the total space allocated (for stacking lines, backgrounds).

### TextKit 2: NSTextLineFragment

```swift
let lineFragment: NSTextLineFragment

lineFragment.typographicBounds    // Rect: dimensions for geometry queries
lineFragment.glyphOrigin          // Point: where glyphs start drawing
lineFragment.characterRange       // Range: in the PARENT element's string (NOT document!)
lineFragment.attributedString     // The line's OWN attributed string (separate copy)
```

**Critical coordinate conversion:**

```
Document coordinates
    → Layout fragment frame (layoutFragmentFrame)
        → Line fragment typographic bounds (relative to fragment)
            → Glyph origin (within line)
```

To get a point in document coordinates from a line fragment:
```swift
let docPoint = CGPoint(
    x: layoutFragment.layoutFragmentFrame.origin.x + lineFragment.typographicBounds.origin.x + localPoint.x,
    y: layoutFragment.layoutFragmentFrame.origin.y + lineFragment.typographicBounds.origin.y + localPoint.y
)
```

### Line Fragment and Paragraphs

- **TextKit 1:** Layout manager manages line fragments directly. No explicit paragraph grouping.
- **TextKit 2:** `NSTextLayoutFragment` ≈ paragraph. Contains 1+ `NSTextLineFragment` for each visual line the paragraph wraps into.

### Extra Line Fragment

When text ends with `\n` (or document is empty), an extra empty line fragment is generated for the cursor position:

- **TextKit 1:** `extraLineFragmentRect`, `extraLineFragmentUsedRect` on NSLayoutManager
- **TextKit 2:** Requires `.ensuresExtraLineFragment` option in enumeration. Known bug (FB15131180) where the frame may be incorrect.

### Exclusion Paths and Line Fragments

When `NSTextContainer.exclusionPaths` contains paths, a single visual line can split into multiple line fragments:

```
┌──────────────────────────────────────┐
│ Text flows    ┌──────┐  around the   │
│ naturally     │ IMAGE │  exclusion    │
│ around the    └──────┘  path here    │
└──────────────────────────────────────┘
```

The text container's `lineFragmentRect(forProposedRect:at:writingDirection:remainingRect:)` returns:
1. The largest available rectangle not intersecting exclusion paths
2. A **remainder rectangle** for content on the other side

### Line Fragment Padding

```swift
textContainer.lineFragmentPadding = 5.0  // Default: 5.0 points
```

- Insets text within the line fragment on each end
- Purely visual — the fragment rect itself is not reduced
- **NOT for document margins** — use `textContainerInset` on the text view
- **NOT for paragraph indentation** — use `NSParagraphStyle.headIndent`

## Common Pitfalls

1. **`renderingSurfaceBounds` not expanded for custom fragments** — Text clipped at diacritics, descenders, or custom backgrounds. Always expand if drawing outside the default bounds.
2. **NSTextLineFragment.characterRange is local** — Relative to the line's attributed string, NOT the document. Must convert through parent element.
3. **Assuming viewport layout means all text is laid out** — Only visible + buffer is laid out. Off-screen metrics are estimates.
4. **Font changes in didProcessEditing** — Bypass fixAttributes font substitution. Characters with missing glyphs may not render.
5. **Confusing line fragment padding with margins** — Padding is small (5pt default) and internal to the fragment. Use textContainerInset for margins.
6. **Querying full document height in TextKit 2** — `usageBoundsForTextContainer.height` is an estimate. It changes as you scroll. If exact height is required, use TextKit 1.

## Related Skills

- For font fallback, rendering-attribute APIs, custom drawing hooks, and Core Text detail, see [rendering-pipeline.md](rendering-pipeline.md).
- Use the textkit2 ref section in this reference for the broader TextKit 2 API surface.
- Use the layout invalidation section in this reference when the question is about what recomputes, not how it renders.
- Use the **rich-text-reference** agent when inline views or glyph-like content affect fragment behavior.

---

# Text Layout Invalidation

Use this skill when the main question is why text layout or rendering did not refresh when expected.

Keep this file for the invalidation model, forced layout, and comparison tables. For symptom-based debugging, symbolic breakpoints, profiling, and viewport controller deep patterns, use [debugging-patterns.md](debugging-patterns.md).

## When to Use

- Layout is stale after edits.
- You need to know what actually invalidates layout.
- You are comparing TextKit 1 and TextKit 2 invalidation behavior.

## Quick Decision

- Need a symptom-first debugger -> `/skill apple-text-textkit-diag`
- Need the invalidation model itself -> stay here
- Need storage/editing lifecycle background -> the storage section in this reference

## Core Guidance

## TextKit 1 Invalidation Model

### What Invalidates Layout

| Trigger | Invalidates | Automatic? |
|---------|------------|------------|
| Character edit in NSTextStorage | Glyphs + layout in edited range | Yes (via processEditing) |
| Attribute change in NSTextStorage | Layout in changed range | Yes (via processEditing) |
| Text container size change | All layout in container | Yes |
| Exclusion path change | All layout in container | Yes |
| `invalidateGlyphs(forCharacterRange:)` | Glyphs for range | Manual call |
| `invalidateLayout(forCharacterRange:)` | Layout for range | Manual call |

### Invalidation Flow

```
NSTextStorage edit
    → processEditing()
        → NSLayoutManager.processEditing(for:edited:range:changeInLength:invalidatedRange:)
            → Marks glyphs invalid in affected range
            → Marks layout invalid in affected range
            → Defers actual recomputation (lazy)
```

**Layout is rebuilt lazily** — only when something queries the invalidated range (e.g., display, hit testing, rect calculation).

### Forcing Layout (TextKit 1)

```swift
let layoutManager: NSLayoutManager

// Entire container (expensive for large documents)
layoutManager.ensureLayout(for: textContainer)

// Specific character range
layoutManager.ensureLayout(forCharacterRange: range)

// Specific glyph range
layoutManager.ensureLayout(forGlyphRange: glyphRange)

// Specific rect in container (most efficient for visible content)
layoutManager.ensureLayout(forBoundingRect: visibleRect, in: textContainer)
```

### Forcing Glyph Generation

```swift
layoutManager.ensureGlyphs(forCharacterRange: range)
layoutManager.ensureGlyphs(forGlyphRange: glyphRange)
```

### Manual Invalidation

```swift
// Invalidate glyphs (forces regeneration)
layoutManager.invalidateGlyphs(
    forCharacterRange: range,
    changeInLength: 0,
    actualCharacterRange: nil
)

// Invalidate layout only (keeps glyphs, re-lays out)
layoutManager.invalidateLayout(
    forCharacterRange: range,
    actualCharacterRange: nil
)

// Invalidate display (just redraw, no layout recalc)
layoutManager.invalidateDisplay(forCharacterRange: range)
layoutManager.invalidateDisplay(forGlyphRange: glyphRange)
```

### What Does NOT Invalidate Layout

- Setting temporary attributes (`setTemporaryAttributes`) — visual only, no layout change
- Reading layout information (bounding rects, line fragments) — read-only queries
- Changing the text view's frame without changing the text container size
- Scrolling the text view

## TextKit 2 Invalidation Model

### What Invalidates Layout

| Trigger | Invalidates | Automatic? |
|---------|------------|------------|
| Edit via `performEditingTransaction` | Elements + layout fragments | Yes |
| `invalidateLayout(for: NSTextRange)` | Layout fragments in range | Manual call |
| Rendering attribute change | Visual only (no layout fragments) | Partial |
| Text container size change | All layout fragments | Yes |

### Invalidation Flow

```
performEditingTransaction {
    textStorage.replaceCharacters(...)
}
    → NSTextContentStorage regenerates affected NSTextParagraph elements
        → NSTextLayoutManager invalidates layout fragments for changed elements
            → NSTextViewportLayoutController re-layouts visible fragments
                → Delegate callbacks: willLayout → configureRenderingSurface × N → didLayout
```

### Forcing Layout (TextKit 2)

```swift
let textLayoutManager: NSTextLayoutManager

// Ensure layout for a range (EXPENSIVE — avoid for large ranges)
textLayoutManager.ensureLayout(for: textRange)

// Enumerate with layout guarantee
textLayoutManager.enumerateTextLayoutFragments(
    from: location,
    options: [.ensuresLayout]
) { fragment in
    return true
}

// Trigger viewport re-layout (preferred for visible content)
textLayoutManager.textViewportLayoutController.layoutViewport()
```

### Manual Invalidation

```swift
// Invalidate layout for range
textLayoutManager.invalidateLayout(for: textRange)

// Invalidate rendering (visual only, no layout recalc)
textLayoutManager.invalidateRenderingAttributes(for: textRange)
```

### What Does NOT Invalidate Layout

- Setting rendering attributes — visual only overlay
- Reading layout fragments — read-only
- Scrolling (viewport controller handles this automatically)

## TextKit 1 vs TextKit 2 Invalidation Comparison

| Aspect | TextKit 1 | TextKit 2 |
|--------|-----------|-----------|
| **Scope** | Can be full-document | Always viewport-scoped |
| **Granularity** | Glyph + layout | Element + fragment |
| **Lazy** | Yes (computed on query) | Yes (computed on viewport update) |
| **ensureLayout cost** | O(range_size) | O(range_size) — avoid for large ranges |
| **Full-doc layout** | `ensureLayout(for: container)` | **Don't do this** — viewport only |
| **Visual-only overlay** | Temporary attributes | Rendering attributes |
| **Overlay invalidates layout?** | No | No |
| **Edit wrapper** | `beginEditing()`/`endEditing()` | `performEditingTransaction { }` |

## What Rebuilds Text Storage

Text storage (`NSTextStorage`) is rebuilt when:

1. **Direct mutations** — `replaceCharacters(in:with:)`, `setAttributes(_:range:)`, etc.
2. **Setting `text`/`attributedText` on text view** — Replaces entire storage content
3. **User typing** — Inserts characters at cursor
4. **Paste/drop** — Inserts attributed content
5. **Undo/redo** — Restores previous state

Text storage is **NOT** rebuilt by:
- Layout invalidation (layout is separate from storage)
- Temporary/rendering attribute changes
- Container geometry changes
- Scrolling

## What Rebuilds Text Elements (TextKit 2)

`NSTextContentStorage` regenerates `NSTextParagraph` elements when:

1. **Text storage edit within `performEditingTransaction`** — Affected paragraphs regenerated
2. **Entire text storage replacement** — All elements regenerated

Elements are **NOT** regenerated by:
- `invalidateLayout(for:)` — Only layout fragments, not elements
- Rendering attribute changes
- Viewport scrolling

## Forcing a Complete Re-Render

### TextKit 1

```swift
// Nuclear option: invalidate everything
let fullRange = NSRange(location: 0, length: textStorage.length)
layoutManager.invalidateGlyphs(forCharacterRange: fullRange, changeInLength: 0, actualCharacterRange: nil)
layoutManager.invalidateLayout(forCharacterRange: fullRange, actualCharacterRange: nil)

// Or trigger via text storage (preferred)
textStorage.beginEditing()
textStorage.edited(.editedAttributes, range: fullRange, changeInLength: 0)
textStorage.endEditing()
```

### TextKit 2

```swift
// Invalidate all layout
textLayoutManager.invalidateLayout(for: textLayoutManager.documentRange)

// Then trigger viewport update
textLayoutManager.textViewportLayoutController.layoutViewport()
```

## Common Patterns

### Syntax Highlighting After Edit

```swift
// TextKit 1: In NSTextStorageDelegate
func textStorage(_ textStorage: NSTextStorage,
                 didProcessEditing editedMask: NSTextStorage.EditActions,
                 range editedRange: NSRange,
                 changeInLength delta: Int) {
    guard editedMask.contains(.editedCharacters) else { return }
    // Re-highlight affected range (extend to paragraph boundaries)
    let paragraphRange = (textStorage.string as NSString).paragraphRange(for: editedRange)
    highlightSyntax(in: paragraphRange, textStorage: textStorage)
}
```

### Deferred Layout Update

```swift
// TextKit 1: Don't query layout during editing
textStorage.beginEditing()
// ... multiple edits ...
textStorage.endEditing()
// NOW it's safe to query layout
let rect = layoutManager.usedRect(for: textContainer)
```

### Content Size Calculation

```swift
// TextKit 1
layoutManager.ensureLayout(for: textContainer)
let usedRect = layoutManager.usedRect(for: textContainer)
let contentSize = CGSize(width: usedRect.width + textContainer.lineFragmentPadding * 2,
                         height: usedRect.height + textView.textContainerInset.top + textView.textContainerInset.bottom)
```

## Common Pitfalls

1. **Querying layout during editing** — Layout may not be valid between `beginEditing()` and `endEditing()`.
2. **Full-document ensureLayout in TextKit 2** — Defeats the viewport optimization. Only ensure layout for visible ranges.
3. **Expecting rendering attributes to invalidate layout** — They don't. They're visual-only overlays.
4. **Not wrapping TextKit 2 edits in transaction** — Direct NSTextStorage edits without `performEditingTransaction` may not trigger proper element regeneration.
5. **Invalidating layout after every keystroke** — Layout invalidation happens automatically through the text storage editing lifecycle. Manual invalidation is only needed for non-storage changes.

## Going Deeper

Read `debugging-patterns.md` in this skill directory for:

- Symptom decision tree for stale layout diagnosis
- Symbolic breakpoints for invalidation tracking
- os_signpost instrumentation for profiling invalidation cost
- Viewport controller deep patterns (fragment recycling, scroll performance)
- Common bugs by symptom with fixes

## Related Skills

- Use `/skill apple-text-textkit-diag` for broader troubleshooting.
- Use the storage section in this reference when invalidation questions are really about editing lifecycle.
- Use the textkit2 ref section in this reference for direct API details around layout fragments and viewport behavior.

---

# Text Measurement & Sizing Reference

Use this skill when you need to know how big text will be before (or after) rendering it.

## When to Use

- You need `boundingRect` or `size(withAttributes:)` and it's returning wrong values.
- You're sizing a view to fit text content.
- You need line-by-line metrics (line heights, fragment rects).
- You're calculating `intrinsicContentSize` for a custom text view.
- Text is clipping, truncating unexpectedly, or leaving extra space.

## Quick Decision

- Quick single-line measurement -> `NSAttributedString.size()`
- Multi-line measurement in a constrained width -> `boundingRect(with:options:context:)`
- Per-line metrics in TextKit 1 -> `NSLayoutManager.enumerateLineFragments`
- Per-line metrics in TextKit 2 -> `NSTextLayoutManager.enumerateTextLayoutFragments`
- "How tall should my text view be?" -> use the text system, not manual calculation

## The #1 Mistake

```swift
// WRONG — returns single-line size, ignores line wrapping
let size = myString.size(withAttributes: attrs)

// RIGHT — constrains to width, enables multi-line measurement
let rect = myString.boundingRect(
    with: CGSize(width: maxWidth, height: .greatestFiniteMagnitude),
    options: [.usesLineFragmentOrigin, .usesFontLeading],
    attributes: attrs,
    context: nil
)
let measuredSize = CGSize(width: ceil(rect.width), height: ceil(rect.height))
```

**You must pass `.usesLineFragmentOrigin`** for multi-line measurement. Without it, `boundingRect` measures as if the text is a single line.

## NSString / NSAttributedString Measurement

### size(withAttributes:) / size()

```swift
// NSString — single line only
let size = "Hello".size(withAttributes: [.font: UIFont.systemFont(ofSize: 17)])

// NSAttributedString — single line only
let size = attributedString.size()
```

**Limitations:** Always returns the single-line size. No width constraint. Useless for multi-line text.

**Use for:** Badge labels, single-line metrics, width-only calculations.

### boundingRect (the workhorse)

```swift
// NSString version
let rect = string.boundingRect(
    with: CGSize(width: containerWidth, height: .greatestFiniteMagnitude),
    options: [.usesLineFragmentOrigin, .usesFontLeading],
    attributes: [.font: font, .paragraphStyle: paragraphStyle],
    context: nil
)

// NSAttributedString version (attributes come from the string itself)
let rect = attributedString.boundingRect(
    with: CGSize(width: containerWidth, height: .greatestFiniteMagnitude),
    options: [.usesLineFragmentOrigin, .usesFontLeading],
    context: nil
)
```

**Always `ceil()` the result.** `boundingRect` returns fractional values. Passing them directly to layout causes 1-pixel clipping:

```swift
let height = ceil(rect.height)  // Not rect.height
let width = ceil(rect.width)    // Not rect.width
```

### NSStringDrawingOptions

| Option | Effect | When to use |
|--------|--------|-------------|
| `.usesLineFragmentOrigin` | Measures multi-line text using line fragment origins | **Almost always.** Without this, you get single-line measurement. |
| `.usesFontLeading` | Includes font leading (inter-line spacing from the font) in height | **Almost always.** Matches what UILabel/UITextView actually renders. |
| `.usesDeviceMetrics` | Uses actual glyph bounds instead of typographic bounds | Pixel-perfect rendering. Rarely needed. |
| `.truncatesLastVisibleLine` | Accounts for truncation ellipsis in height-constrained measurement | When you're constraining height and want accurate truncated size. |

**The standard combo:** `[.usesLineFragmentOrigin, .usesFontLeading]` — use this by default.

### NSStringDrawingContext

For auto-shrinking text (like UILabel's `adjustsFontSizeToFitWidth`):

```swift
let context = NSStringDrawingContext()
context.minimumScaleFactor = 0.5  // Allow shrinking to 50%

let rect = attributedString.boundingRect(
    with: constrainedSize,
    options: [.usesLineFragmentOrigin, .usesFontLeading],
    context: context
)

// After measurement:
let actualScale = context.actualScaleFactor  // What scale was applied
let actualBounds = context.totalBounds       // Where text actually landed
```

## TextKit 1 Measurement (NSLayoutManager)

When you need per-line metrics, not just total size.

### Total content size

```swift
// Force layout for entire container
layoutManager.ensureLayout(for: textContainer)

// Get used rect — the actual area text occupies
let usedRect = layoutManager.usedRect(for: textContainer)
let contentHeight = ceil(usedRect.height)
```

### Specific range size

```swift
let glyphRange = layoutManager.glyphRange(forCharacterRange: charRange,
                                           actualCharacterRange: nil)
let boundingRect = layoutManager.boundingRect(forGlyphRange: glyphRange,
                                               in: textContainer)
```

### Line-by-line enumeration

```swift
let fullGlyphRange = layoutManager.glyphRange(for: textContainer)
layoutManager.enumerateLineFragments(forGlyphRange: fullGlyphRange) {
    rect, usedRect, container, glyphRange, stop in
    // rect: full line fragment rectangle (includes padding)
    // usedRect: actual area used by glyphs (tighter)
    // glyphRange: which glyphs are on this line
    print("Line height: \(usedRect.height), y: \(usedRect.origin.y)")
}
```

### Line count

```swift
func lineCount(for layoutManager: NSLayoutManager,
               in textContainer: NSTextContainer) -> Int {
    layoutManager.ensureLayout(for: textContainer)
    var count = 0
    let fullRange = layoutManager.glyphRange(for: textContainer)
    layoutManager.enumerateLineFragments(forGlyphRange: fullRange) { _, _, _, _, _ in
        count += 1
    }
    return count
}
```

## TextKit 2 Measurement (NSTextLayoutManager)

### Total content size

```swift
textLayoutManager.ensureLayout(for: textLayoutManager.documentRange)
let usageBounds = textLayoutManager.usageBoundsForTextContainer
let contentHeight = ceil(usageBounds.height)
```

### Layout fragment enumeration

```swift
textLayoutManager.enumerateTextLayoutFragments(
    from: textLayoutManager.documentRange.location,
    options: [.ensuresLayout]
) { fragment in
    let frame = fragment.layoutFragmentFrame       // Position in container
    let surface = fragment.renderingSurfaceBounds   // Actual rendering area

    for lineFragment in fragment.textLineFragments {
        let lineOrigin = lineFragment.typographicBounds.origin
        let lineHeight = lineFragment.typographicBounds.height
        print("Line at y=\(frame.origin.y + lineOrigin.y), height=\(lineHeight)")
    }
    return true  // continue enumeration
}
```

### NSTextLineFragment metrics

Each `NSTextLineFragment` within a layout fragment gives you:

```swift
lineFragment.typographicBounds  // Bounds based on font metrics
lineFragment.glyphOrigin        // Where glyphs start
lineFragment.characterRange     // Character range for this line
```

## Common Sizing Patterns

### "Size text view to fit content"

**UITextView:**
```swift
// Let the text system do the work
let fittingSize = textView.sizeThatFits(
    CGSize(width: maxWidth, height: .greatestFiniteMagnitude)
)
textView.frame.size.height = fittingSize.height
```

**With Auto Layout (preferred):**
```swift
textView.isScrollEnabled = false  // CRITICAL — enables intrinsicContentSize
// Auto Layout handles the rest via intrinsicContentSize
```

**`isScrollEnabled = false` is the key.** When scrolling is enabled, `intrinsicContentSize` returns `(.noIntrinsicMetric, .noIntrinsicMetric)`. When disabled, it returns the full content size.

### "How tall is N lines of text?"

```swift
func heightForLines(_ n: Int, font: UIFont, width: CGFloat) -> CGFloat {
    let paragraphStyle = NSMutableParagraphStyle()
    paragraphStyle.lineBreakMode = .byWordWrapping

    // Build a string with N-1 newlines
    let sampleText = String(repeating: "Wy\n", count: n).dropLast()
    let attrs: [NSAttributedString.Key: Any] = [
        .font: font,
        .paragraphStyle: paragraphStyle
    ]
    let rect = (sampleText as NSString).boundingRect(
        with: CGSize(width: width, height: .greatestFiniteMagnitude),
        options: [.usesLineFragmentOrigin, .usesFontLeading],
        attributes: attrs,
        context: nil
    )
    return ceil(rect.height)
}
```

### "Does text fit in this rect?"

```swift
func textFits(_ text: NSAttributedString, in size: CGSize) -> Bool {
    let rect = text.boundingRect(
        with: size,
        options: [.usesLineFragmentOrigin, .usesFontLeading],
        context: nil
    )
    return ceil(rect.height) <= size.height && ceil(rect.width) <= size.width
}
```

## Pitfalls

1. **Forgetting `.usesLineFragmentOrigin`** — Without it, multi-line text is measured as one line. This is the single most common measurement bug.

2. **Not calling `ceil()`** — Fractional heights cause 1px clipping. Always round up.

3. **Mismatched attributes** — Measuring with font A but rendering with font B. Ensure the same paragraph style, font, and line height are used for both measurement and display.

4. **`textContainer.lineFragmentPadding`** — Default is 5pt. This adds 10pt total width (5 each side). If you measure without accounting for it, your widths are 10pt off:
    ```swift
    let effectiveWidth = containerWidth - 2 * textContainer.lineFragmentPadding
    ```

5. **`textContainerInset`** — UITextView default is `UIEdgeInsets(top: 8, left: 0, bottom: 8, right: 0)`. You must add these to the measured text height for the actual view height.

6. **Measuring before layout** — In TextKit, measurements are only valid after layout. Call `ensureLayout(for:)` before reading rects.

7. **Thread safety** — All measurement APIs that touch NSLayoutManager or NSTextLayoutManager must be called from the main thread (or the layout queue for TK2).

## Related Skills

- For text colors and Dynamic Type scaling -> the **rich-text-reference** agent, the **editor-reference** agent
- For viewport-based lazy measurement -> the viewport rendering section in this reference
- For layout invalidation after content changes -> the layout invalidation section in this reference
- For Core Text glyph-level measurement -> the **platform-reference** agent

---

# Exclusion Paths, Multi-Container & Text Tables

Use this skill when text needs to flow around objects, across columns, or render as tables.

## When to Use

- You need text to wrap around an image or arbitrary shape.
- You need multi-column or multi-page text layout.
- You need linked text containers (text flows from one to the next).
- You need in-text tables using NSTextTable/NSTextBlock (AppKit).
- You need non-rectangular text containers.

## Quick Decision

- Text wraps around a shape -> `exclusionPaths`
- Text flows across columns/pages -> linked `NSTextContainer` array
- Table of data inside a text view -> `NSTextTable` + `NSTextTableBlock` (AppKit) or `NSTextAttachmentViewProvider` (UIKit)
- Non-rectangular text region -> subclass `NSTextContainer` and override `lineFragmentRect(forProposedRect:...)`

## Exclusion Paths

### What They Are

`NSTextContainer.exclusionPaths` is an array of `UIBezierPath`/`NSBezierPath` objects that define "holes" where text cannot appear. The text system flows text around these shapes.

### Basic Usage

```swift
// Create a circular exclusion in the top-right corner
let circlePath = UIBezierPath(
    ovalIn: CGRect(x: 200, y: 20, width: 120, height: 120)
)
textView.textContainer.exclusionPaths = [circlePath]
```

Text will wrap around the circle. Multiple paths are supported:

```swift
textView.textContainer.exclusionPaths = [imageRect, pullQuoteRect, sidebarRect]
```

### Coordinate System

Exclusion paths use the **text container's coordinate system**, not the text view's:

```swift
// Convert from text view coordinates to text container coordinates
let containerOrigin = textView.textContainerOrigin  // UITextView
// or
let containerInset = textView.textContainerInset     // UITextView
let containerPoint = CGPoint(
    x: viewPoint.x - containerInset.left,
    y: viewPoint.y - containerInset.top
)
```

### Dynamic Exclusion Paths (Image Follows Scroll)

```swift
func updateExclusionForFloatingImage(_ imageView: UIImageView) {
    let imageFrame = textView.convert(imageView.frame, from: imageView.superview)
    let containerInset = textView.textContainerInset
    let exclusionRect = CGRect(
        x: imageFrame.origin.x - containerInset.left,
        y: imageFrame.origin.y - containerInset.top,
        width: imageFrame.width + 8,   // padding
        height: imageFrame.height + 8
    )
    textView.textContainer.exclusionPaths = [UIBezierPath(rect: exclusionRect)]
}
```

**Performance warning:** Changing `exclusionPaths` invalidates the entire layout. For frequently-moving exclusions (e.g., during scroll), batch updates and avoid per-frame changes.

### Complex Shapes

```swift
// L-shaped exclusion
let path = UIBezierPath()
path.move(to: CGPoint(x: 150, y: 0))
path.addLine(to: CGPoint(x: 300, y: 0))
path.addLine(to: CGPoint(x: 300, y: 200))
path.addLine(to: CGPoint(x: 200, y: 200))
path.addLine(to: CGPoint(x: 200, y: 100))
path.addLine(to: CGPoint(x: 150, y: 100))
path.close()
textView.textContainer.exclusionPaths = [path]
```

### TextKit 1 vs TextKit 2

| Behavior | TextKit 1 | TextKit 2 |
|----------|-----------|-----------|
| `exclusionPaths` property | Yes | Yes |
| Re-layout on change | Full relayout | Viewport relayout |
| Performance with many paths | Degrades | Better (viewport-scoped) |
| Custom container subclass | Override `lineFragmentRect(forProposedRect:...)` | Same method |

## Multi-Container (Linked) Layout

### What It Is

A single `NSLayoutManager` (TK1) or `NSTextLayoutManager` (TK2) can manage text across **multiple** `NSTextContainer` instances. When text overflows the first container, it flows into the second, and so on. This is how you build multi-column, multi-page, or magazine-style layouts.

### TextKit 1 — Multiple Containers

```swift
let textStorage = NSTextStorage(attributedString: content)
let layoutManager = NSLayoutManager()
textStorage.addLayoutManager(layoutManager)

// Column 1
let container1 = NSTextContainer(size: CGSize(width: 300, height: 500))
layoutManager.addTextContainer(container1)
let textView1 = UITextView(frame: .zero, textContainer: container1)

// Column 2
let container2 = NSTextContainer(size: CGSize(width: 300, height: 500))
layoutManager.addTextContainer(container2)
let textView2 = UITextView(frame: .zero, textContainer: container2)

// Text automatically flows from container1 -> container2
```

**Key rules:**
- Container order matters — `layoutManager.textContainers` is an ordered array
- Text fills containers in order; overflow goes to the next
- Each container can have its own `exclusionPaths`
- Each container gets its own `UITextView`/`NSTextView`
- You manage the views' frames yourself (the text system only handles text flow)

### TextKit 2 — Multiple Containers

TextKit 2 uses a slightly different model. `NSTextLayoutManager` manages a single `NSTextContainer` by default, but you can use `NSTextContentManager` with multiple layout managers:

```swift
let contentManager = NSTextContentStorage()
contentManager.attributedString = content

// Layout manager per column
let layoutManager1 = NSTextLayoutManager()
let container1 = NSTextContainer(size: CGSize(width: 300, height: 500))
layoutManager1.textContainer = container1
contentManager.addTextLayoutManager(layoutManager1)

let layoutManager2 = NSTextLayoutManager()
let container2 = NSTextContainer(size: CGSize(width: 300, height: 500))
layoutManager2.textContainer = container2
contentManager.addTextLayoutManager(layoutManager2)
```

### Detecting Overflow

```swift
// TextKit 1: Check if text overflows a container
let glyphRange = layoutManager.glyphRange(for: container1)
let charRange = layoutManager.characterRange(forGlyphRange: glyphRange,
                                              actualGlyphRange: nil)
let hasOverflow = charRange.upperBound < textStorage.length
```

### Practical: Two-Column Layout

```swift
class TwoColumnView: UIView {
    let textStorage = NSTextStorage()
    let layoutManager = NSLayoutManager()
    var leftTextView: UITextView!
    var rightTextView: UITextView!

    func setup() {
        textStorage.addLayoutManager(layoutManager)

        let leftContainer = NSTextContainer(size: .zero)
        leftContainer.widthTracksTextView = true
        leftContainer.heightTracksTextView = true
        layoutManager.addTextContainer(leftContainer)
        leftTextView = UITextView(frame: .zero, textContainer: leftContainer)
        leftTextView.isEditable = false
        addSubview(leftTextView)

        let rightContainer = NSTextContainer(size: .zero)
        rightContainer.widthTracksTextView = true
        rightContainer.heightTracksTextView = true
        layoutManager.addTextContainer(rightContainer)
        rightTextView = UITextView(frame: .zero, textContainer: rightContainer)
        rightTextView.isEditable = false
        addSubview(rightTextView)
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        let columnWidth = (bounds.width - 16) / 2  // 16pt gap
        leftTextView.frame = CGRect(x: 0, y: 0,
                                     width: columnWidth, height: bounds.height)
        rightTextView.frame = CGRect(x: columnWidth + 16, y: 0,
                                      width: columnWidth, height: bounds.height)
    }
}
```

## NSTextContainer Subclassing

For truly non-rectangular text regions (circular, triangular, path-based):

```swift
class CircularTextContainer: NSTextContainer {
    override func lineFragmentRect(
        forProposedRect proposedRect: CGRect,
        at characterIndex: Int,
        writingDirection baseWritingDirection: NSWritingDirection,
        remaining remainingRect: UnsafeMutablePointer<CGRect>?
    ) -> CGRect {
        // Start with the standard rect
        var result = super.lineFragmentRect(
            forProposedRect: proposedRect,
            at: characterIndex,
            writingDirection: baseWritingDirection,
            remaining: remainingRect
        )

        // Constrain to a circle
        let center = CGPoint(x: size.width / 2, y: size.height / 2)
        let radius = min(size.width, size.height) / 2
        let y = proposedRect.origin.y + proposedRect.height / 2
        let dy = y - center.y

        guard abs(dy) < radius else { return .zero }

        let dx = sqrt(radius * radius - dy * dy)
        let minX = center.x - dx + lineFragmentPadding
        let maxX = center.x + dx - lineFragmentPadding

        result.origin.x = minX
        result.size.width = maxX - minX

        return result
    }

    override var isSimpleRectangularTextContainer: Bool { false }
}
```

**`isSimpleRectangularTextContainer`** — Return `false` when you override `lineFragmentRect(forProposedRect:...)`. This tells the text system it can't take layout shortcuts.

## NSTextTable / NSTextBlock (AppKit)

### What They Are

AppKit provides `NSTextTable` and `NSTextTableBlock` for rendering tables directly inside attributed strings. These are **paragraph-level attributes** — each table cell is a paragraph whose `NSParagraphStyle.textBlocks` includes an `NSTextTableBlock`.

**Platform availability:** Primarily AppKit (NSTextView). UIKit has the classes but rendering support is limited.

### Creating a Table

```swift
// Create a 3-column table
let table = NSTextTable()
table.numberOfColumns = 3
table.collapsesBorders = true

// Create a cell: row 0, column 0
let cell = NSTextTableBlock(table: table,
                             startingRow: 0, rowSpan: 1,
                             startingColumn: 0, columnSpan: 1)
cell.setContentWidth(33.33, type: .percentageValueType)
cell.backgroundColor = .controlBackgroundColor
cell.setWidth(0.5, type: .absoluteValueType, for: .border)
cell.setBorderColor(.separatorColor)
cell.setValue(4, type: .absoluteValueType, for: .padding)

// Attach to paragraph style
let style = NSMutableParagraphStyle()
style.textBlocks = [cell]

// Create the cell content
let cellText = NSAttributedString(
    string: "Cell content\n",  // Note: must end with newline
    attributes: [
        .paragraphStyle: style,
        .font: NSFont.systemFont(ofSize: 13)
    ]
)
```

### Building a Full Table

```swift
func makeTable(rows: Int, columns: Int, data: [[String]]) -> NSAttributedString {
    let table = NSTextTable()
    table.numberOfColumns = columns
    table.collapsesBorders = true

    let result = NSMutableAttributedString()

    for row in 0..<rows {
        for col in 0..<columns {
            let cell = NSTextTableBlock(table: table,
                                         startingRow: row, rowSpan: 1,
                                         startingColumn: col, columnSpan: 1)
            cell.setContentWidth(CGFloat(100 / columns),
                                 type: .percentageValueType)
            cell.setValue(4, type: .absoluteValueType, for: .padding)
            cell.setWidth(0.5, type: .absoluteValueType, for: .border)
            cell.setBorderColor(.separatorColor)

            if row == 0 {
                cell.backgroundColor = .controlAccentColor.withAlphaComponent(0.1)
            }

            let style = NSMutableParagraphStyle()
            style.textBlocks = [cell]

            let text = data[row][col] + "\n"  // Each cell ends with newline
            result.append(NSAttributedString(string: text, attributes: [
                .paragraphStyle: style,
                .font: row == 0 ? NSFont.boldSystemFont(ofSize: 13)
                                : NSFont.systemFont(ofSize: 13)
            ]))
        }
    }

    return result
}
```

### NSTextBlock Properties

| Property | Purpose |
|----------|---------|
| `backgroundColor` | Cell background color |
| `setBorderColor(_:for:)` | Per-edge border color |
| `setWidth(_:type:for:edge:)` | Margin, border, or padding per edge |
| `setWidth(_:type:for:)` | Margin, border, or padding for all edges of a layer |
| `setContentWidth(_:type:)` | Cell content width (absolute or percentage) |
| `verticalAlignment` | `.top`, `.middle`, `.bottom`, `.baseline` |
| `setValue(_:type:for:)` | Set dimension values (minWidth, maxWidth, minHeight, maxHeight) |

### NSTextBlock.Layer

```swift
cell.setWidth(1, type: .absoluteValueType, for: .border)   // Border layer
cell.setValue(8, type: .absoluteValueType, for: .padding)   // Padding layer
cell.setValue(4, type: .absoluteValueType, for: .margin)    // Margin layer
```

### UIKit Alternative: Tables via Attachments

Since UIKit doesn't fully support NSTextTable rendering, use `NSTextAttachmentViewProvider` (TextKit 2) to embed a `UITableView` or custom view:

```swift
// See the **rich-text-reference** agent for full NSTextAttachmentViewProvider pattern
class TableAttachmentViewProvider: NSTextAttachmentViewProvider {
    override func loadView() {
        let tableView = MyCompactTableView(data: extractData(from: textAttachment))
        view = tableView
    }

    override func attachmentBounds(
        for attributes: [NSAttributedString.Key: Any],
        location: NSTextLocation,
        textContainer: NSTextContainer?,
        proposedLineFragment: CGRect,
        position: CGPoint
    ) -> CGRect {
        // Full-width, calculated height
        let width = proposedLineFragment.width
        let height = calculateTableHeight(for: width)
        return CGRect(x: 0, y: 0, width: width, height: height)
    }
}
```

## NSTextList

For ordered/unordered lists inside attributed strings:

```swift
let list = NSTextList(markerFormat: .decimal, options: 0)
list.startingItemNumber = 1

let style = NSMutableParagraphStyle()
style.textLists = [list]
style.headIndent = 24       // Indent for wrapped lines
style.firstLineHeadIndent = 0  // Marker hangs in the margin

let item = NSAttributedString(
    string: "\t\(list.marker(forItemNumber: 1))\tFirst item\n",
    attributes: [.paragraphStyle: style, .font: UIFont.systemFont(ofSize: 15)]
)
```

### Marker Formats

| Format | Appearance |
|--------|-----------|
| `.decimal` | 1. 2. 3. |
| `.octal` | 1. 2. 3. (base 8) |
| `.lowercaseAlpha` | a. b. c. |
| `.uppercaseAlpha` | A. B. C. |
| `.lowercaseRoman` | i. ii. iii. |
| `.uppercaseRoman` | I. II. III. |
| `.disc` | bullet (filled circle) |
| `.circle` | open circle |
| `.square` | filled square |
| `.diamond` | diamond |
| `.hyphen` | hyphen |

### Nested Lists

```swift
let outerList = NSTextList(markerFormat: .decimal, options: 0)
let innerList = NSTextList(markerFormat: .lowercaseAlpha, options: 0)

let innerStyle = NSMutableParagraphStyle()
innerStyle.textLists = [outerList, innerList]  // Nesting = array order
innerStyle.headIndent = 48   // Double indent
```

## Pitfalls

1. **Exclusion path coordinates** — Must be in text container coordinates, not view coordinates. Account for `textContainerInset` and `textContainerOrigin`.

2. **Exclusion path performance** — Each change triggers full relayout in TextKit 1. Batch changes; don't update per-frame during animations.

3. **NSTextTable on UIKit** — The classes exist but rendering is incomplete. Use attachment view providers on iOS instead.

4. **Each table cell must end with `\n`** — NSTextTable cells are paragraph-level. Missing the trailing newline merges cells.

5. **Multi-container editing** — Editing in linked containers is fragile. Works well for read-only; editing across container boundaries requires careful cursor management.

6. **`isSimpleRectangularTextContainer`** — If you subclass `NSTextContainer` and override `lineFragmentRect`, you must return `false` or layout may use incorrect fast paths.

## Related Skills

- For embedding interactive views inline -> the **rich-text-reference** agent
- For viewport-scoped layout with exclusions -> the viewport rendering section in this reference
- For paragraph style formatting details -> the **rich-text-reference** agent
- For layout invalidation after changing exclusion paths -> the layout invalidation section in this reference

---

# Text Storage Architecture

Use this skill when the main question is how text content is stored, mutated, and synchronized with layout.

Keep this file for the storage architecture, editing lifecycle, and common pitfalls. For custom backing stores (piece table, rope, CRDT), thread-safety patterns, and performance profiling, use [advanced-patterns.md](advanced-patterns.md).

## When to Use

- You are editing or subclassing `NSTextStorage`.
- You need to understand `NSTextContentStorage` or `NSTextContentManager`.
- You are debugging storage-layer behavior beneath layout or rendering symptoms.

## Quick Decision

- Need invalidation behavior after edits -> the layout invalidation section in this reference
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

- Use the layout invalidation section in this reference for what re-renders or recomputes after storage edits.
- Use the textkit1 ref section in this reference and the textkit2 ref section in this reference for stack-specific APIs.
- Use `/skill apple-text-textkit-diag` when the symptom matters more than the storage model.

---

# TextKit 1 Fallback Triggers — Complete Catalog

Use this skill when the main question is why a TextKit 2 view entered compatibility mode or how to avoid doing that.

## When to Use

- `textLayoutManager` unexpectedly becomes `nil`
- Writing Tools loses inline behavior
- You need to audit fallback risk before touching a text view

## Quick Decision

- Need a symptom-first debugger -> `/skill apple-text-textkit-diag`
- Need the exact fallback trigger catalog -> stay here
- Need to choose TextKit 1 on purpose -> the **platform-reference** agent

## Core Guidance

TextKit 2 falls back to TextKit 1 **permanently and irreversibly** on a given text view instance. Once `textLayoutManager` returns `nil`, there is no way back. This skill catalogs every known trigger.

## The Fallback Mechanism

When triggered, the text view:
1. Replaces `NSTextLayoutManager` with `NSLayoutManager`
2. `textLayoutManager` returns `nil` permanently
3. All cached TextKit 2 objects stop functioning
4. View-based `NSTextAttachmentViewProvider` attachments are **instantly lost**
5. Writing Tools degrades to panel-only mode
6. Viewport-based layout optimization is lost

## Category 1: Explicit NSLayoutManager Access (Most Common)

| Trigger | Why It Causes Fallback |
|---------|----------------------|
| `textView.layoutManager` | Forces TextKit 1 infrastructure creation |
| `textView.textContainer.layoutManager` | Same — accesses TK1 layout manager |
| `textStorage.addLayoutManager(_:)` | Adds TK1 layout manager to storage |
| `textStorage.removeLayoutManager(_:)` | Manipulates TK1 layout manager list |
| `textContainer.replaceLayoutManager(_:)` | Swaps in TK1 layout manager |

```swift
// ❌ TRIGGERS FALLBACK — even a read-only check
if textView.layoutManager != nil { ... }
if let lm = textView.textContainer.layoutManager { ... }

// ✅ SAFE — check TextKit 2 first
if let tlm = textView.textLayoutManager {
    // TextKit 2 path
} else {
    // Already in TextKit 1 — safe to use layoutManager
    let lm = textView.layoutManager
}
```

## Category 2: Any Glyph-Based API

TextKit 2 has **zero glyph APIs**. Any glyph access requires TextKit 1:

| API | TextKit 2 Alternative |
|-----|----------------------|
| `numberOfGlyphs` | Enumerate layout fragments |
| `glyph(at:)` | No equivalent — use Core Text directly |
| `glyphRange(for:)` | `enumerateTextLayoutFragments` |
| `lineFragmentRect(forGlyphAt:)` | `textLineFragments[n].typographicBounds` |
| `boundingRect(forGlyphRange:in:)` | Union of layout fragment frames |
| `characterIndex(for:in:fractionOf...)` | `location(interactingAt:inContainerAt:)` |
| `drawGlyphs(forGlyphRange:at:)` | `NSTextLayoutFragment.draw(at:in:)` subclass |
| `drawBackground(forGlyphRange:at:)` | Custom layout fragment |
| `shouldGenerateGlyphs` delegate | No equivalent — customize at fragment level |

## Category 3: Unsupported Attributes

| Attribute | Status | Notes |
|-----------|--------|-------|
| **NSTextTable / NSTextTableBlock** | Triggers fallback | AppKit-only. Apple's TextEdit falls back for tables |
| **NSTextList** | Partially supported | Supported since iOS 17/macOS 14. Earlier versions may fall back |
| **NSTextAttachment (TK1 cell API)** | Can trigger fallback | `attachmentBounds(for:proposedLineFragment:glyphPosition:characterIndex:)` crashes on iOS 16.0. Use `NSTextAttachmentViewProvider` instead |
| **NSTextAttachmentCell** | Triggers fallback | TextKit 1 only protocol. Use `NSTextAttachmentViewProvider` for TextKit 2 |

## Category 4: Multi-Container Layout

**TextKit 2's NSTextLayoutManager supports only ONE text container.**

| Pattern | Fallback? |
|---------|-----------|
| Multiple `NSTextContainer` on one layout manager | Requires TextKit 1 |
| Multi-page / multi-column layout | Requires TextKit 1 |
| "Wrap to Page" in TextEdit | Falls back to TextKit 1 |

## Category 5: Printing

| OS Version | Printing Support |
|------------|-----------------|
| Before macOS 15 / iOS 18 | **No printing in TextKit 2** — triggers fallback |
| macOS 15+ / iOS 18+ | Basic printing supported, limited pagination — `NSTextLayoutManager` still only supports a single `NSTextContainer`, so multi-page layout requires TextKit 1. Apple's TextEdit still falls back to TextKit 1 for printing. |

## Category 6: Framework-Internal Fallbacks

**These happen without YOUR code accessing layoutManager:**

- UIKit/AppKit framework internals sometimes access `layoutManager` internally
- Undocumented and **varies between OS releases**
- Apple recommends filing Feedback Assistant reports for these
- Third-party libraries accessing `layoutManager` on your text view

**Quote from STTextView author:** *"You never know what might trigger that fallback, and the cases are not documented and will vary from release to release."*

## Category 7: NSTextView-Specific (macOS)

| Trigger | Notes |
|---------|-------|
| Quick Look preview of attachments | Bug in macOS 14 and earlier |
| `drawInsertionPoint(in:color:turnedOn:)` override | Doesn't trigger fallback but **silently stops working** under TextKit 2 |
| Any NSTextField accessing field editor's `layoutManager` | Falls back ALL field editors in that window |

## What Does NOT Cause Fallback

This is equally important — these are **safe** to use with TextKit 2:

### NSTextStorage Is the Normal Backing Store

**NSTextContentStorage wraps NSTextStorage. This is the standard architecture.**

```swift
// ✅ SAFE — accessing the backing store through content storage
let textStorage = textContentStorage.textStorage

// ✅ SAFE — editing through the content storage
textContentStorage.performEditingTransaction {
    textStorage?.replaceCharacters(in: range, with: newText)
}

// ✅ SAFE — NSTextStorage subclass works with TextKit 2
class MyStorage: NSTextStorage { ... }
let contentStorage = NSTextContentStorage()
contentStorage.textStorage = MyStorage()
```

**The distinction:** "Fallback" means the layout system switches from `NSTextLayoutManager` to `NSLayoutManager`. The storage layer (NSTextStorage) is ALWAYS present — it's the backing store for both systems.

### Safe Properties and Methods

| Property/Method | Safe? | Notes |
|----------------|-------|-------|
| `textView.textLayoutManager` | ✅ | Returns nil if already TK1 |
| `textView.textStorage` (UITextView) | ✅ | Direct storage access is fine |
| `textContainer.exclusionPaths` | ✅ | Supported since iOS 16 |
| `textContainerInset` | ✅ | |
| `typingAttributes` | ✅ | |
| `selectedRange` / `selectedTextRange` | ✅ | |
| All `UITextViewDelegate` methods | ✅ | |
| Standard attributed string attributes | ✅ | font, color, paragraph style, etc. |
| `NSTextContentStorage.performEditingTransaction` | ✅ | Preferred edit wrapper |
| `NSTextStorage.beginEditing`/`endEditing` | ✅ | When wrapped in transaction |

### NSTextStorage Subclass with TextKit 2

A custom NSTextStorage subclass **works with TextKit 2** when:
1. Used as the backing store of `NSTextContentStorage`
2. All edits go through `performEditingTransaction`
3. The four primitives are correctly implemented
4. You never access `layoutManager` on the text view

```swift
// ✅ Custom backing store with TextKit 2
class RopeTextStorage: NSTextStorage {
    // ... implement 4 primitives with edited() calls
}

let contentStorage = NSTextContentStorage()
contentStorage.textStorage = RopeTextStorage()
// The text view uses NSTextLayoutManager — no fallback
```

**Cannot do:** Custom `NSTextContentManager` subclass (without NSTextStorage) — causes crashes. Custom `NSTextElement` subclasses beyond `NSTextParagraph` — triggers runtime assertions.

## How to Detect Fallback

### UIKit (iOS)

```swift
// Runtime check
if textView.textLayoutManager == nil {
    print("⚠️ TextKit 1 mode (fallback occurred or was never TK2)")
}

// Symbolic breakpoint (Xcode)
// Symbol: _UITextViewEnablingCompatibilityMode
// Action: Log message with backtrace to find the trigger
```

### AppKit (macOS)

```swift
// Notifications
NotificationCenter.default.addObserver(
    forName: NSTextView.willSwitchToNSLayoutManagerNotification,
    object: textView, queue: .main
) { _ in
    print("⚠️ About to fall back — check call stack")
}

NotificationCenter.default.addObserver(
    forName: NSTextView.didSwitchToNSLayoutManagerNotification,
    object: textView, queue: .main
) { _ in
    print("⚠️ Fell back to TextKit 1")
}
```

### Console Log

The system logs: `"UITextView <addr> is switching to TextKit 1 compatibility mode because its layoutManager was accessed"`

## How to Opt Out (Use TextKit 1 from Start)

If you NEED TextKit 1, don't create a TextKit 2 view and let it fall back — that wastes initialization:

```swift
// ✅ CORRECT — explicit TextKit 1 from start
let textView = UITextView(usingTextLayoutManager: false)

// ✅ CORRECT — manual TextKit 1 setup
let storage = NSTextStorage()
let layoutManager = NSLayoutManager()
storage.addLayoutManager(layoutManager)
let container = NSTextContainer(size: CGSize(width: 300, height: .greatestFiniteMagnitude))
layoutManager.addTextContainer(container)
let textView = UITextView(frame: .zero, textContainer: container)
```

## Recovery from Fallback

**There is no recovery on the same instance.** To get back to TextKit 2:

1. Create a NEW text view with TextKit 2
2. Transfer the text content (attributedText)
3. Replace the old view in the hierarchy
4. Re-wire delegates and observers

## Fallback Improvement Timeline

| OS | TextKit 2 Improvement |
|----|----------------------|
| iOS 15 / macOS 12 | TextKit 2 introduced (opt-in) |
| iOS 16 / macOS 13 | Default for all text controls; compatibility mode added |
| iOS 17 / macOS 14 | NSTextList support; CJK line-breaking improvements |
| iOS 18 / macOS 15 | Printing support added |
| macOS 26 | `includesTextListMarkers` property; `NSTextViewAllowsDowngradeToLayoutManager` user default |

**Trend:** Each OS release supports more features in TextKit 2, reducing fallback triggers. But multi-container layout and text tables remain TextKit 1 only.

## Related Skills

- Use `/skill apple-text-textkit-diag` for broader debugging around fallback symptoms.
- Use the **platform-reference** agent when compatibility mode pressure means TextKit 1 may be the right explicit choice.
- Use `/skill apple-text-audit` when you want repository findings ranked by severity.
