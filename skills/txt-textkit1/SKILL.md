---
name: txt-textkit1
description: Reference for TextKit 1 — NSTextStorage, NSLayoutManager, NSTextContainer. Covers the storage / layout manager / container triad, glyph generation and queries, line-fragment geometry, multi-container layout, exclusion paths, temporary attributes, non-contiguous layout, and NSLayoutManager / NSTextStorage delegate hooks. Use when working with code that already uses NSLayoutManager, when an editor was created with UITextView(usingTextLayoutManager: false), when maintaining legacy TextKit 1 code, or when Apple's apps (Pages, Xcode, Notes) and other TextKit 1 codebases need glyph-level access. Do NOT use for the picker decision between TK1 and TK2 — see txt-textkit-choice. Do NOT use for symptom-driven debugging — see txt-textkit-debug.
license: MIT
---

# TextKit 1 reference

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This is the API reference for the original TextKit stack — `NSTextStorage`, `NSLayoutManager`, `NSTextContainer` — available since iOS 7 / macOS 10.0 and still the right choice for glyph access, multi-container layout, `NSTextTable`, and reliable temporary attributes. The class is not deprecated; Apple's own apps (Pages, Xcode, Notes) ship on it as of recent releases. Before claiming any specific signature here is current, fetch the relevant page from Sosumi (`sosumi.ai/documentation/uikit/<class>`) — TextKit 1's surface area is large and stable, but enumeration options and delegate signatures pick up small additions each release.

## Contents

- [The MVC triad](#the-mvc-triad)
- [NSTextStorage](#nstextstorage)
- [NSLayoutManager: glyph generation](#nslayoutmanager-glyph-generation)
- [NSLayoutManager: layout queries](#nslayoutmanager-layout-queries)
- [Non-contiguous layout](#non-contiguous-layout)
- [Temporary attributes](#temporary-attributes)
- [NSTextContainer](#nstextcontainer)
- [Multi-container layout](#multi-container-layout)
- [Custom drawing](#custom-drawing)
- [Delegates](#delegates)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## The MVC triad

```
NSTextStorage ←→ NSLayoutManager ←→ NSTextContainer → UITextView / NSTextView
   (model)         (controller)        (geometry)            (view)
```

The relationships are one-to-many in both directions:

- One `NSTextStorage` can have many `NSLayoutManager`s. The same characters, laid out independently in multiple windows or panels.
- One `NSLayoutManager` can have many `NSTextContainer`s. Multi-page and multi-column layout flow text from one container into the next.
- Each `NSTextContainer` is owned by at most one text view.

The storage notifies its layout managers; layout managers feed their containers; containers are exposed by views. The reverse path is direct property access (`textView.layoutManager`, `layoutManager.textStorage`, etc.) — and on iOS 16+ that reverse path is also the most common cause of TextKit 1 fallback on a TextKit 2 view.

## NSTextStorage

`NSTextStorage` is a subclass of `NSMutableAttributedString`. It is an attributed string with edit tracking and notifications.

```swift
class NSTextStorage: NSMutableAttributedString {
    var layoutManagers: [NSLayoutManager] { get }
    var editedMask: EditActions { get }
    var editedRange: NSRange { get }
    var changeInLength: Int { get }

    func addLayoutManager(_ layoutManager: NSLayoutManager)
    func removeLayoutManager(_ layoutManager: NSLayoutManager)

    func edited(_ mask: EditActions, range: NSRange, changeInLength delta: Int)
    func processEditing()

    var delegate: NSTextStorageDelegate?
}
```

The lifecycle on a single mutation:

1. External code calls `replaceCharacters(in:with:)` or `setAttributes(_:range:)`.
2. The override calls `edited(_:range:changeInLength:)` with the right mask and delta.
3. `endEditing()` (or the implicit single-mutation equivalent) calls `processEditing()`.
4. `delegate.textStorage(_:willProcessEditing:…)` fires — characters and attributes both writable here.
5. `fixAttributes(in:)` runs — font substitution, paragraph-style fixing.
6. `delegate.textStorage(_:didProcessEditing:…)` fires — attributes only, characters are committed.
7. Each attached layout manager's `processEditing(for:edited:range:changeInLength:invalidatedRange:)` is called.

Edit masks combine when both kinds of change happen in one mutation:

```swift
NSTextStorage.EditActions.editedCharacters    // text changed
NSTextStorage.EditActions.editedAttributes    // attributes changed
[.editedCharacters, .editedAttributes]        // both
```

Batched edits coalesce into one `processEditing()` pass:

```swift
textStorage.beginEditing()
textStorage.replaceCharacters(in: r1, with: "new text")
textStorage.addAttribute(.font, value: bold, range: r2)
textStorage.deleteCharacters(in: r3)
textStorage.endEditing()
// processEditing() runs once with the union of edits
```

Without `beginEditing()` / `endEditing()`, each individual mutation triggers a separate `processEditing()` and a separate layout invalidation pass. For subclassing detail (rope, piece table, gap buffer) see `txt-nstextstorage`.

## NSLayoutManager: glyph generation

`NSLayoutManager` translates characters into glyphs and lays them out.

```swift
layoutManager.ensureGlyphs(forCharacterRange: range)
layoutManager.ensureGlyphs(forGlyphRange: glyphRange)

let glyph = layoutManager.glyph(at: glyphIndex)
let glyphRange = layoutManager.glyphRange(
    forCharacterRange: charRange,
    actualCharacterRange: nil
)
let charRange = layoutManager.characterRange(
    forGlyphRange: glyphRange,
    actualGlyphRange: nil
)
```

The character-to-glyph mapping is not 1:1. Ligatures combine multiple characters into one glyph; combining marks expand one character into multiple glyphs; complex scripts reorder glyphs. Code that assumes one character equals one glyph fails on Arabic, Devanagari, emoji ZWJ sequences, and most non-Latin scripts.

Glyph generation is lazy. Querying a glyph for an index that hasn't been generated triggers generation. Querying *layout* for a range whose glyphs haven't been laid out triggers both glyph generation and layout. The internal warning `_NSLayoutTreeLineFragmentRectForGlyphAtIndex` in console output usually means a layout query ran ahead of the layout pass — call `ensureLayout(forCharacterRange:)` covering the queried range first.

## NSLayoutManager: layout queries

```swift
layoutManager.ensureLayout(for: textContainer)              // O(document) — avoid
layoutManager.ensureLayout(forCharacterRange: range)
layoutManager.ensureLayout(forGlyphRange: glyphRange)
layoutManager.ensureLayout(forBoundingRect: rect, in: container)  // best for visible
```

Geometry queries:

```swift
let rect = layoutManager.boundingRect(forGlyphRange: range, in: container)

var effective = NSRange()
let lineRect = layoutManager.lineFragmentRect(
    forGlyphAt: glyphIndex,
    effectiveRange: &effective
)
let usedRect = layoutManager.lineFragmentUsedRect(
    forGlyphAt: glyphIndex,
    effectiveRange: &effective
)

let originInLine = layoutManager.location(forGlyphAt: glyphIndex)

var fraction: CGFloat = 0
let charIndex = layoutManager.characterIndex(
    for: point,
    in: container,
    fractionOfDistanceBetweenInsertionPoints: &fraction
)
```

`lineFragmentRect` is the full allocation for the line — padding, leading, paragraph spacing. `lineFragmentUsedRect` is just the part the glyphs actually occupy. Hit-testing and cursor positioning use the used rect; stacking lines and drawing backgrounds use the full rect.

Manual invalidation:

```swift
layoutManager.invalidateGlyphs(
    forCharacterRange: range,
    changeInLength: 0,
    actualCharacterRange: nil
)
layoutManager.invalidateLayout(
    forCharacterRange: range,
    actualCharacterRange: nil
)
layoutManager.invalidateDisplay(forCharacterRange: range)
layoutManager.invalidateDisplay(forGlyphRange: glyphRange)
```

`invalidateDisplay` only marks the screen for redraw — it does not recompute layout. Use it after temporary-attribute changes when the visible rect needs to refresh.

## Non-contiguous layout

```swift
layoutManager.allowsNonContiguousLayout = true
if layoutManager.hasNonContiguousLayout {
    // Some ranges may not be laid out yet.
}
```

When enabled, the layout manager can skip ranges that aren't currently visible. Essential for documents large enough to scroll meaningfully. `UITextView` enables it by default; `NSTextView` does not.

The trade-off is reliability. `boundingRect(forGlyphRange:in:)` and `lineFragmentRect(forGlyphAt:effectiveRange:)` can return slightly wrong coordinates for ranges that haven't been laid out — usually around several thousand characters in. If exact geometry matters for a query, force layout for that range first with `ensureLayout(forCharacterRange:)`.

## Temporary attributes

Temporary attributes are visual overlays that don't modify the storage. Used for spell-check underlines, find highlights, syntax-color overlays. They are TextKit 1 only — TextKit 2's equivalent is rendering attributes on `NSTextLayoutManager`.

```swift
layoutManager.setTemporaryAttributes(
    [.foregroundColor: UIColor.red],
    forCharacterRange: range
)
layoutManager.addTemporaryAttribute(
    .backgroundColor,
    value: UIColor.yellow,
    forCharacterRange: range
)
layoutManager.removeTemporaryAttribute(
    .backgroundColor,
    forCharacterRange: range
)
```

Temporary attributes don't persist across archiving, don't trigger layout invalidation, and are well-tested for syntax highlighting workloads. This last point is one of the standing reasons to stay on TextKit 1 for a code editor.

`addTemporaryAttributes(_:forCharacterRange:)` is the production highlighting path. Because it bypasses storage, it does not invalidate layout, does not run `fixAttributes`, and does not force glyph regeneration. Compare to calling `addAttribute` directly on the storage with the same attribute key — that mutates the document, runs the editing lifecycle, and regenerates glyphs over the affected range. CotEditor's published optimization arc on a syntax-highlight pass measures the difference at roughly 4.46s using storage attributes, 3.35s using temporary attributes synchronously, and effectively 0s when the temporary-attribute application is moved to a background queue and applied per-paragraph in batches. Display-only highlighting (search matches, find-bar results, find-and-replace previews, syntax color overlays that are not part of the persisted document) belongs on temporary attributes; storage attributes are for things the user would expect to copy, paste, save, and undo.

## NSTextContainer

The container defines the geometric region where text is laid out.

```swift
let container = NSTextContainer(
    size: CGSize(width: 300, height: .greatestFiniteMagnitude)
)
container.lineFragmentPadding = 5      // default 5 points
container.maximumNumberOfLines = 0     // 0 = unlimited
container.lineBreakMode = .byWordWrapping
container.exclusionPaths = [
    UIBezierPath(ovalIn: CGRect(x: 50, y: 50, width: 100, height: 100))
]
```

Exclusion paths are in the container's coordinate space. A single visual line that crosses an exclusion path splits into multiple line fragments; the container's `lineFragmentRect(forProposedRect:at:writingDirection:remainingRect:)` returns both the largest available rectangle and the remainder.

Setting the height to `.greatestFiniteMagnitude` is the standard way to say "no clipping, no maximum height" — a finite height clips text and is a common cause of "missing text at the bottom of the view".

## Multi-container layout

Multiple containers on one layout manager give multi-page and multi-column flow:

```swift
let storage = NSTextStorage()
let layoutManager = NSLayoutManager()
storage.addLayoutManager(layoutManager)

let column1 = NSTextContainer(size: CGSize(width: 300, height: 500))
let column2 = NSTextContainer(size: CGSize(width: 300, height: 500))
layoutManager.addTextContainer(column1)
layoutManager.addTextContainer(column2)

let view1 = UITextView(frame: frame1, textContainer: column1)
let view2 = UITextView(frame: frame2, textContainer: column2)
```

Text overflowing `column1` flows into `column2`. This is the pattern used by page-layout, multi-column reading views, and any layout that needs to span multiple frames. There is no equivalent in TextKit 2 — `NSTextLayoutManager` has exactly one container.

## Custom drawing

Custom glyph drawing happens in a `NSLayoutManager` subclass:

```swift
class GutterLayoutManager: NSLayoutManager {
    override func drawGlyphs(forGlyphRange glyphsToShow: NSRange, at origin: CGPoint) {
        drawCustomBackground(forGlyphRange: glyphsToShow, at: origin)
        super.drawGlyphs(forGlyphRange: glyphsToShow, at: origin)
    }

    override func drawBackground(forGlyphRange glyphsToShow: NSRange, at origin: CGPoint) {
        super.drawBackground(forGlyphRange: glyphsToShow, at: origin)
        drawHighlights(forGlyphRange: glyphsToShow, at: origin)
    }
}
```

Inline attachments use `NSTextAttachment` directly:

```swift
let attachment = NSTextAttachment()
attachment.image = UIImage(named: "icon")
attachment.bounds = CGRect(x: 0, y: -4, width: 20, height: 20)
let attrString = NSAttributedString(attachment: attachment)
textStorage.insert(attrString, at: insertionPoint)
```

`NSTextAttachmentCell` is TextKit 1 only; for view-backed attachments on TextKit 2, use `NSTextAttachmentViewProvider` instead.

## Delegates

`NSTextStorageDelegate` exposes `willProcessEditing` (characters and attributes both writable; used for auto-correct and text transforms) and `didProcessEditing` (attributes only; used for syntax highlighting that applies color attributes based on just-committed text). Mutating characters in `didProcessEditing` is the most common storage-related crash; the editing-lifecycle detail lives in `txt-nstextstorage`.

`NSLayoutManagerDelegate` exposes hooks for line and paragraph spacing, custom line-fragment rects, and glyph generation. The notable methods:

- `layoutManager(_:lineSpacingAfterGlyphAt:withProposedLineFragmentRect:)` — return additional spacing after the glyph at the given index.
- `layoutManager(_:paragraphSpacingAfterGlyphAt:withProposedLineFragmentRect:)` — return additional spacing after the paragraph.
- `layoutManager(_:shouldUse:forTextContainer:)` — modify the line fragment rect before layout commits.
- `layoutManager(_:shouldGenerateGlyphs:properties:characterIndexes:font:forGlyphRange:)` — custom glyph mapping. No TextKit 2 equivalent — glyph customization lives in TextKit 1 only.

## Common Mistakes

1. **Forgetting `edited()` in an `NSTextStorage` subclass.** Without the call, layout managers never learn the text changed. The most common subclassing bug.

   ```swift
   // WRONG
   override func replaceCharacters(in range: NSRange, with str: String) {
       backingStore.replaceCharacters(in: range, with: str)
   }

   // CORRECT
   override func replaceCharacters(in range: NSRange, with str: String) {
       backingStore.replaceCharacters(in: range, with: str)
       let delta = (str as NSString).length - range.length
       edited(.editedCharacters, range: range, changeInLength: delta)
   }
   ```

2. **Mutating characters in `didProcessEditing`.** The delegate runs after the storage has committed; characters are no longer writable. Mutating them re-enters the editing lifecycle with stale ranges and crashes. Move character changes to `willProcessEditing`, or use `addAttribute` only.

3. **Not batching edits.** Each unbatched mutation runs `processEditing()` separately. Wrap multi-step changes in `beginEditing()` / `endEditing()` so the layout invalidation pass runs once.

4. **Reading `textView.layoutManager` on a TextKit 2 view.** Triggers irreversible fallback. Always check `textView.textLayoutManager != nil` first. The full catalog is in `txt-fallback-triggers`.

5. **`ensureLayout(for: textContainer)` on a large document.** Forces layout for the entire document — O(document). Use the rect-scoped variant `ensureLayout(forBoundingRect:in:)` over the visible rect, or the range-scoped `ensureLayout(forCharacterRange:)`.

6. **Assuming character-glyph 1:1 mapping.** Ligatures, combining marks, and emoji ZWJ sequences break this. Code that uses `numberOfGlyphs` as a stand-in for `string.count` produces wrong answers on every non-Latin script and most user-generated text with emoji.

7. **`String.count` vs `(string as NSString).length` in range arithmetic.** They diverge on emoji and combining marks. Mixing them inside `edited(_:range:changeInLength:)` corrupts ranges silently. Normalize at the boundary with `(text as NSString).length` or `NSRange(swiftRange, in: text)`.

8. **Setting `isScrollEnabled = false` on a `UITextView` to size-fit it in a cell.** This is the canonical autosizing pattern, and it has a non-obvious cost. `UITextView`'s layout manager has `allowsNonContiguousLayout = true` by default, but only while `isScrollEnabled == true`. Disabling scroll silently re-enables full-document layout because intrinsic content size needs an exact height. A small autosizing field is fine; an autosizing field bound to a long document quietly lays out every line on the first pass, every container resize, and every Dynamic Type change. This is the most common cause of "my autosize `UITextView` got slow" and is called out in WWDC 2018 #221. If the content can grow large, either keep scrolling enabled and constrain the height externally, or page the content so the autosizing path only ever sees a bounded slice.

## References

- `txt-textkit2` — the TextKit 2 API surface, for the same problem on the modern stack
- `txt-textkit-choice` — picking between TextKit 1 and TextKit 2
- `txt-fallback-triggers` — every API access that flips a TextKit 2 view to TextKit 1
- `txt-nstextstorage` — storage subclassing and editing-lifecycle deep dive
- `txt-layout-invalidation` — what invalidates layout and how to force a refresh
- [NSTextStorage](https://sosumi.ai/documentation/uikit/nstextstorage)
- [NSLayoutManager](https://sosumi.ai/documentation/uikit/nslayoutmanager)
- [NSTextContainer](https://sosumi.ai/documentation/uikit/nstextcontainer)
- [NSTextStorageDelegate](https://sosumi.ai/documentation/uikit/nstextstoragedelegate)
- [NSLayoutManagerDelegate](https://sosumi.ai/documentation/uikit/nslayoutmanagerdelegate)
