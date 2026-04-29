---
name: txt-viewport-rendering
description: Use when working with viewport layout, line-fragment geometry, rendering attributes, font substitution, or scroll-driven layout
license: MIT
---

# Viewport Layout, Line Fragments, Fonts & Rendering

Use this skill when the main question is how TextKit 2 viewport layout, fragments, and rendering behavior actually work.

## When to Use

- You need fragment, line-fragment, or viewport-layout details.
- You are debugging custom rendering or visual overlays.
- You need to know why visible and off-screen layout behave differently.

## Quick Decision

- Need full TextKit 2 object reference -> `/skill txt-textkit2`
- Need to know **how** viewport layout, fragments, and rendering work -> stay here
- Need to know **what triggers** layout recalculation (when to call `invalidateLayout`) -> `/skill txt-layout-invalidation`

## Core Guidance

Keep this file for viewport behavior, fragment geometry, and the high-level rendering mental model. For font fallback timing, rendering-attribute APIs, custom drawing hooks, Core Text underpinnings, and emoji notes, use [rendering-pipeline.md](references/rendering-pipeline.md).

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

- For font fallback, rendering-attribute APIs, custom drawing hooks, and Core Text detail, see [rendering-pipeline.md](references/rendering-pipeline.md).
- Use `/skill txt-textkit2` for the broader TextKit 2 API surface.
- Use `/skill txt-layout-invalidation` when the question is about what recomputes, not how it renders.
- Use `/skill txt-attachments` when inline views or glyph-like content affect fragment behavior.
