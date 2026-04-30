---
name: txt-exclusion-paths
description: Wrap text around shapes, build multi-column or magazine layouts, and embed tables in attributed strings using NSTextContainer.exclusionPaths, linked NSTextContainer arrays, NSTextTable, NSTextTableBlock, NSTextList, and custom NSTextContainer subclasses. Covers TextKit 1 and TextKit 2 differences, the text container coordinate system, the lineFragmentRect override, and the UIKit fallback for tables via NSTextAttachmentViewProvider. Use when text needs to flow around an image, when an article needs side-by-side columns or paginated text flow, when an editor needs an in-text table, or when the question involves non-rectangular text regions. Use whenever the user mentions text wrapping, columns, or magazine layout, even if they do not name exclusion paths. Do NOT use for simple line wrapping, hyphenation, or paragraph spacing — see txt-line-breaking. Do NOT use for embedding interactive views inline — see txt-attachments.
license: MIT
---

# Exclusion Paths and Multi-Region Layout

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

`NSTextContainer.exclusionPaths` carves holes in the text region so glyphs flow around them. A linked array of containers lets a single layout manager spread one document across columns or pages. AppKit's `NSTextTable` builds tables out of paragraph-level attributes. These three mechanisms together cover the layout shapes that don't fit a single rectangle. The patterns below are starting points; before quoting any specific API signature, fetch the current Apple docs via Sosumi (`sosumi.ai/documentation/uikit/nstextcontainer/exclusionpaths`) and verify the actual code matches the pattern — exclusion-path geometry bugs almost always come from the wrong coordinate space, and table bugs almost always come from a missing trailing newline.

The deeper material — full multi-column layout, AppKit table construction, the UIKit attachment-based table fallback, and `NSTextList` markers — lives in `references/multi-container-and-tables.md`. Load it when the work moves past simple text wrapping.

## Contents

- [Exclusion paths](#exclusion-paths)
- [Coordinate system](#coordinate-system)
- [Custom non-rectangular containers](#custom-non-rectangular-containers)
- [Multi-container layout](#multi-container-layout)
- [Tables and lists](#tables-and-lists)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Exclusion paths

`NSTextContainer.exclusionPaths` is an array of `UIBezierPath` (or `NSBezierPath`) objects defining regions where text cannot appear. The text system flows lines around them. Multiple paths combine — pass an array, not separate properties.

```swift
let circle = UIBezierPath(ovalIn: CGRect(x: 200, y: 20, width: 120, height: 120))
textView.textContainer.exclusionPaths = [circle]
```

Mutating the array invalidates layout. On TextKit 1 the relayout is full-document; on TextKit 2 it is viewport-scoped, which is meaningfully cheaper for long documents. Either way, per-frame mutation during a scroll or animation will hammer the layout pipeline. Update on size change, on image load, on the bounds change that motivates the exclusion — not in `scrollViewDidScroll`.

Paths can be any closed shape. An L-shape, a star, an irregular cutout from a die-cut graphic — the typesetter cares only that the path is closed and that points inside it are excluded. Open paths produce undefined results.

## Coordinate system

Exclusion paths live in the **text container's** coordinate space, not the text view's. UITextView and NSTextView both apply a `textContainerInset` between their bounds and the container's origin, plus a `lineFragmentPadding` (default 5pt each side) that further insets the usable region. A path computed from the view's bounds will appear shifted by the inset.

```swift
// Convert from text view coordinates to text container coordinates
let inset = textView.textContainerInset
let containerPoint = CGPoint(x: viewPoint.x - inset.left,
                             y: viewPoint.y - inset.top)
```

For a path that should track a sibling subview (a floating image, a pull quote box), translate the subview's frame into the container's space on every layout pass:

```swift
func updateExclusion(for floatingView: UIView) {
    let frameInTextView = textView.convert(floatingView.frame, from: floatingView.superview)
    let inset = textView.textContainerInset
    let rect = CGRect(x: frameInTextView.minX - inset.left,
                      y: frameInTextView.minY - inset.top,
                      width: frameInTextView.width + 8,
                      height: frameInTextView.height + 8)
    textView.textContainer.exclusionPaths = [UIBezierPath(rect: rect)]
}
```

## Custom non-rectangular containers

Exclusion paths cut holes out of a rectangular region. To shape the region itself — text inside a circle, along a curve, conforming to a die line — subclass `NSTextContainer` and override `lineFragmentRect(forProposedRect:at:writingDirection:remaining:)`. The override receives the rect the typesetter would *like* to use for the next line and returns the rect the typesetter is *allowed* to use. Returning `.zero` skips the line entirely.

When you override that method, also override `isSimpleRectangularTextContainer` to return `false`. The text system uses the simple-rectangular flag as a fast-path gate for layout shortcuts; a `false` return forces the slower path that consults your override.

```swift
class CircularTextContainer: NSTextContainer {
    override var isSimpleRectangularTextContainer: Bool { false }

    override func lineFragmentRect(
        forProposedRect proposedRect: CGRect,
        at characterIndex: Int,
        writingDirection baseWritingDirection: NSWritingDirection,
        remaining remainingRect: UnsafeMutablePointer<CGRect>?
    ) -> CGRect {
        var result = super.lineFragmentRect(
            forProposedRect: proposedRect,
            at: characterIndex,
            writingDirection: baseWritingDirection,
            remaining: remainingRect)

        let center = CGPoint(x: size.width / 2, y: size.height / 2)
        let radius = min(size.width, size.height) / 2
        let dy = (proposedRect.midY) - center.y
        guard abs(dy) < radius else { return .zero }

        let dx = sqrt(radius * radius - dy * dy)
        result.origin.x = center.x - dx + lineFragmentPadding
        result.size.width = (2 * dx) - (2 * lineFragmentPadding)
        return result
    }
}
```

## Multi-container layout

A single `NSLayoutManager` (TextKit 1) manages an ordered array of `NSTextContainer` instances. The first fills first; overflow flows to the next. This is how columns, pages, and magazine spreads are built. Each container can have its own `exclusionPaths`. Each gets its own text view; you place the views yourself.

```swift
let storage = NSTextStorage(attributedString: content)
let lm = NSLayoutManager()
storage.addLayoutManager(lm)

let c1 = NSTextContainer(size: CGSize(width: 300, height: 500))
lm.addTextContainer(c1)
let v1 = UITextView(frame: .zero, textContainer: c1)

let c2 = NSTextContainer(size: CGSize(width: 300, height: 500))
lm.addTextContainer(c2)
let v2 = UITextView(frame: .zero, textContainer: c2)
```

TextKit 2 splits the same job across `NSTextContentStorage` and multiple `NSTextLayoutManager` instances. Editing across linked containers is fragile — selection, caret, and IME marked text assume a single container in the stock UITextView/NSTextView code paths. Read-only flow works well; an editable multi-column editor is a meaningful project. Full TK1 and TK2 setups, overflow detection, and a working two-column subclass live in `references/multi-container-and-tables.md`.

## Tables and lists

`NSTextTable` plus `NSTextTableBlock` render in-attributed-string tables on AppKit's NSTextView. The table is a paragraph-level attribute: each cell is a paragraph whose `NSParagraphStyle.textBlocks` includes the cell's `NSTextTableBlock`, and **every cell must end with `\n`** or adjacent cells merge. UIKit has the classes but no rendering for them — on iOS, embed a `UITableView` (or any view) via an `NSTextAttachmentViewProvider` instead.

`NSTextList` produces ordered or unordered list markers (decimal, alpha, roman, disc, circle, square, hyphen). Like tables, lists are paragraph-level: a paragraph style with `textLists = [list]` and a hanging indent that accounts for the marker width.

Full table-construction code, the AppKit `NSTextBlock` property reference, the UIKit attachment fallback, and nested-list patterns are in `references/multi-container-and-tables.md`. Load that reference before writing real table code.

## Common Mistakes

1. **Exclusion path in the wrong coordinate space.** Computing the path from the text view's bounds without subtracting `textContainerInset` and `lineFragmentPadding` produces a path shifted by ~10-15 points. The symptom is a wrap that "almost works" but consistently misses by a small amount. Convert via the inset before constructing the path.

2. **Mutating exclusion paths every frame.** Each assignment to `exclusionPaths` invalidates layout — full-document on TK1, viewport-scoped on TK2. A scroll handler or animation that updates paths per frame will tank scroll performance. Update on the events that actually change the geometry, not on every redraw.

3. **Open path used as an exclusion.** The typesetter's containment test assumes a closed path. An open path returns undefined inside/outside results, manifesting as text passing through the "exclusion" or vanishing inside it. Call `path.close()` before assignment.

4. **Custom NSTextContainer without overriding `isSimpleRectangularTextContainer`.** The default returns `true`, which lets the text system take fast paths that bypass `lineFragmentRect`. The custom geometry never runs and the text lays out as if the container were rectangular. Override to `false` whenever the lineFragmentRect override is non-trivial.

5. **NSTextTable cell missing trailing newline.** Each cell is a paragraph; without the `\n` terminator the next cell's content joins this one's paragraph and the layout manager merges the cells visually. Append `\n` to every cell string.

6. **NSTextTable expected to render on UIKit.** UITextView has the classes but not the rendering. Tables either render incompletely or not at all. The supported pattern on iOS is `NSTextAttachmentViewProvider` with a `UITableView` or custom view (see `references/multi-container-and-tables.md`).

7. **Editing in a linked-container layout.** Multi-container flow is read-stable but edit-fragile. Selection, caret rendering, and IME marked text assume a single container in stock views; cursor placement at container boundaries misbehaves. If editing is required, expect to write substantial selection/caret code or constrain the editor to a single container per session.

8. **Assuming `lineFragmentPadding` is zero.** UITextView's default container has 5pt of padding on each side. A custom container subclass that ignores `lineFragmentPadding` in its computed rect produces lines that are 10pt wider than the apparent shape, with glyphs spilling into the exclusion.

## References

- `references/multi-container-and-tables.md` — full multi-column setups (TK1 and TK2), AppKit `NSTextTable` construction, UIKit table fallback via `NSTextAttachmentViewProvider`, `NSTextList` patterns
- `/skill txt-attachments` — `NSTextAttachment` and view providers when the goal is embedding interactive content
- `/skill txt-line-breaking` — paragraph style settings (line break mode, hyphenation, line height)
- `/skill txt-viewport-rendering` — viewport-scoped layout details for TextKit 2
- `/skill txt-layout-invalidation` — what `exclusionPaths` mutations invalidate, and when
- [NSTextContainer.exclusionPaths](https://sosumi.ai/documentation/uikit/nstextcontainer/exclusionpaths)
- [NSTextContainer.lineFragmentRect](https://sosumi.ai/documentation/uikit/nstextcontainer/linefragmentrect(forproposedrect:at:writingdirection:remaining:))
- [NSTextTable](https://sosumi.ai/documentation/appkit/nstexttable)
- [NSTextList](https://sosumi.ai/documentation/appkit/nstextlist)
- [NSTextAttachmentViewProvider](https://sosumi.ai/documentation/uikit/nstextattachmentviewprovider)
