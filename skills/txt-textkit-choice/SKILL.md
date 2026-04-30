---
name: txt-textkit-choice
description: Choose between TextKit 1 (NSLayoutManager) and TextKit 2 (NSTextLayoutManager) and weigh migration risk. Covers feature gates that force one stack (glyph access, multi-container layout, NSTextTable, Writing Tools inline, syntax-highlighting reliability), real-world performance evidence on large documents, scroll-bar behavior under estimated heights, line-counting cost on each stack, and dual-code-path patterns for code that needs to support both. Use when starting a new editor and deciding which stack to commit to, when an existing TextKit 1 codebase is debating migration, or when fallback pressure is forcing the question of whether to stay on TextKit 1 deliberately. Do NOT use for the API reference of either stack — see txt-textkit1 / txt-textkit2.
license: MIT
---

# TextKit 1 vs TextKit 2

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill is the picker. It does not list APIs — see `txt-textkit1` and `txt-textkit2` for those — and it does not chase symptoms — see `txt-textkit-debug`. It owns the decision: which layout manager fits the feature, where each stack still has hard limits, what the performance evidence actually says, and how migration risk decomposes when an existing codebase weighs moving over. The recommendations here are calibrated to current shipping behavior; before committing to one based on a performance claim quoted below, run a benchmark on the target OS with realistic content.

## Contents

- [The two layout managers at a glance](#the-two-layout-managers-at-a-glance)
- [When TextKit 1 is the right choice](#when-textkit-1-is-the-right-choice)
- [When TextKit 2 is the right choice](#when-textkit-2-is-the-right-choice)
- [Performance evidence](#performance-evidence)
- [Creating each stack explicitly](#creating-each-stack-explicitly)
- [Detecting which stack a view is on](#detecting-which-stack-a-view-is-on)
- [Migration risk and strategy](#migration-risk-and-strategy)
- [Storage architecture for large documents](#storage-architecture-for-large-documents)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## The two layout managers at a glance

| Aspect | NSLayoutManager (TextKit 1) | NSTextLayoutManager (TextKit 2) |
|---|---|---|
| Available since | iOS 7 / macOS 10.0 | iOS 15 / macOS 12 |
| Default for new text views | Through iOS 15 | iOS 16+ / macOS 13+ |
| Layout model | Contiguous (or non-contiguous opt-in) | Always non-contiguous, viewport-driven |
| Abstraction | Glyph-based | Element / fragment-based |
| Text containers per manager | Multiple | Exactly one |
| Performance model | O(document) or O(visible) | O(viewport) |
| International text | Manual glyph handling | Correct by design |
| Writing Tools | Panel only | Full inline rewriting |
| Custom rendering | `NSLayoutManager` subclass + `drawGlyphs` | `NSTextLayoutFragment` subclass |
| Visual overlay | Temporary attributes (`setTemporaryAttributes`) | Rendering attributes (`setRenderingAttributes`) |
| Printing | Full | Basic on iOS 18+ / macOS 15+; multi-page still TK1 |
| `NSTextTable` | Supported | Triggers fallback |
| Glyph APIs | Yes | None |

`NSLayoutManager` is fully supported and not deprecated. Apple's own apps — Pages, Xcode, Notes — still use TextKit 1 as of recent releases. TextEdit uses TextKit 2 and falls back to TextKit 1 for tables, page layout, and printing. TextKit 1 is not "legacy mode to migrate away from"; it is the correct choice when feature requirements include things TextKit 2 does not support.

## When TextKit 1 is the right choice

1. **Glyph-level access.** Custom glyph substitution, glyph inspection, hand-tuned typography. TextKit 2 has no glyph APIs — the alternative is dropping to Core Text directly.

2. **Multi-page or multi-column layout.** `NSTextLayoutManager` supports exactly one `NSTextContainer`. There is no workaround.

3. **`NSTextTable` / `NSTextTableBlock` content (AppKit).** Tables in the attributed string force TextKit 1. Even Apple's TextEdit demonstrates this — opening a document with tables flips it into compatibility mode.

4. **Reliable syntax highlighting via temporary attributes.** `addTemporaryAttribute` is rendering-only and well-tested. TextKit 2's `setRenderingAttributes` has known drawing bugs (FB9692714) and the workaround is a custom `NSTextLayoutFragment` subclass per attribute combination.

5. **Print pagination.** TextKit 2 gained basic printing in iOS 18 / macOS 15, but multi-page pagination still falls back because the layout manager has only one container.

6. **Existing custom `NSLayoutManager` subclass.** Significant investment in `drawGlyphs`, `drawBackground`, or the `shouldGenerateGlyphs` delegate. None of these have direct TextKit 2 equivalents; rewriting against `NSTextLayoutFragment` is a real port, not a swap.

7. **Exact document height required.** `usageBoundsForTextContainer.height` is an estimate that refines while scrolling. TextKit 1 contiguous layout gives an exact value. Code that wires document height directly to a scroll view's content size will see scroll-bar jiggle on TextKit 2.

8. **Scroll-bar accuracy critical.** Same root cause: the scroll bar is positioned and sized off the estimated height, so it shifts as fragments lay out. Apple's own TextEdit shows this on long documents.

9. **Targeting iOS 15.** `UITextView` defaults to TextKit 1 on iOS 15. Roughly 2-3% of devices as of early 2026, but the share matters for apps with broad reach.

## When TextKit 2 is the right choice

1. **New iOS 16+ app with no specific TK1 feature requirement.** It's the default. Fighting it adds complexity for no benefit.

2. **Writing Tools inline experience.** Inline rewriting requires TextKit 2. Panel-only mode works on TextKit 1 but is a different UX.

3. **International text correctness.** Arabic, Devanagari, CJK rendering and selection without writing manual glyph code.

4. **Custom rendering via fragments.** Subclassing `NSTextLayoutFragment` is a cleaner, more maintainable API than overriding `drawGlyphs` on `NSLayoutManager`.

5. **Short text (labels, chat bubbles).** Viewport overhead is irrelevant at small sizes; the modern API and rendering attributes are net wins.

6. **Viewport-based display of large content** when exact document metrics are not required.

7. **Custom text elements via `NSTextContentManager` subclass.** Backing stores that aren't attributed strings (HTML DOM, AST, CRDT) only fit on TextKit 2.

## Performance evidence

Apple's WWDC21 framing was that TextKit 2 is fast across a wide range from short labels to hundreds-of-megabytes documents at interactive rates. That framing is technically true and practically misleading: each release has improved TextKit 2 performance, but several real-world reports as recent as 2025 still show problems above 3,000 lines on some configurations.

What the public evidence says:

- **ChimeHQ TextViewBenchmark, macOS 14 beta:** "TextKit 1 is extremely fast and TextKit 2 actually even a small amount faster." For comparable document sizes on recent macOS, the two stacks are at parity or TextKit 2 is slightly faster.
- **Large-document scrolling reports (Apple Developer Forums, multiple authors):** TextKit 2 scrolling above ~3,000 lines was described as degraded, and 10K+ lines as "an absolute nightmare" in some configurations. Switching to TextKit 1 restored smooth scrolling on a 1,000,000-character document. These reports are primarily from iOS 16 / 17 era; later releases have improved.
- **Memory usage (developer measurement):** ~0.5 GB for a TextKit 1 custom-label workload, ~1.2 GB for the same content on TextKit 2. The immutable `NSTextLayoutFragment` / `NSTextLineFragment` value types have real overhead.
- **Apple's own apps:** Pages, Xcode, Notes are still TextKit 1 as of reports through 2025. TextEdit is TextKit 2 but falls back for tables, page layout, and printing.

For short text — labels, chat bubbles, single-line fields — TextKit 2 is the right call regardless. The penalty is zero and the international-text correctness wins are free.

For documents large enough to scroll meaningfully, the answer depends on the target OS and the actual content. The benchmark is more reliable than the framing.

### Line counting

Both systems struggle with this. On TextKit 1, line counting requires `numberOfGlyphs` and enumeration with `allowsNonContiguousLayout = false` for accuracy, or accept approximate counts with non-contiguous layout. On TextKit 2, line counting requires enumerating every layout fragment with `.ensuresLayout`, defeating the viewport optimization.

The right approach on either stack is to maintain a separate line count incrementally on edit rather than asking the layout system.

## Creating each stack explicitly

Both `UITextView` and `NSTextView` default to TextKit 2 on iOS 16+ / macOS 13+. Force a specific stack only with a documented reason.

```swift
// TextKit 1 — explicit, no fallback risk
let textView = UITextView(usingTextLayoutManager: false)
// textView.textLayoutManager == nil from the start
```

```swift
// Manual TextKit 1 construction (custom views)
let storage = NSTextStorage()
let layoutManager = NSLayoutManager()
layoutManager.allowsNonContiguousLayout = true   // critical for scroll perf
storage.addLayoutManager(layoutManager)
let container = NSTextContainer(size: CGSize(width: 300, height: .greatestFiniteMagnitude))
layoutManager.addTextContainer(container)
let textView = UITextView(frame: .zero, textContainer: container)
```

```swift
// TextKit 2 — default
let textView = UITextView()
assert(textView.textLayoutManager != nil)
```

```swift
// Manual TextKit 2 construction (custom views)
let contentStorage = NSTextContentStorage()
let layoutManager = NSTextLayoutManager()
let container = NSTextContainer()
contentStorage.addTextLayoutManager(layoutManager)
layoutManager.textContainer = container
contentStorage.attributedString = NSAttributedString(string: "Hello")
```

If TextKit 1 is the right call, opt in explicitly with `usingTextLayoutManager: false`. Don't construct a TextKit 2 view and let it fall back — that wastes the TextKit 2 layout manager initialization and produces a worse view than starting on TextKit 1.

## Detecting which stack a view is on

The check that does not flip the view:

```swift
func currentStack(for textView: UITextView) -> String {
    textView.textLayoutManager != nil ? "TextKit 2" : "TextKit 1"
}
```

The check that flips the view to TextKit 1 by reading it:

```swift
// WRONG — this triggers fallback
if textView.layoutManager != nil { … }
```

`textView.layoutManager` and `textView.textContainer.layoutManager` both pull TextKit 1 infrastructure into existence on a TextKit 2 view. Always check `textLayoutManager` first; only after confirming it's `nil` is it safe to use the TextKit 1 layout manager. Full catalog of fallback triggers in `txt-fallback-triggers`.

## Migration risk and strategy

Reasons not to migrate an existing TextKit 1 codebase:

- It works.
- It uses glyph APIs that have no TextKit 2 equivalent.
- It uses multi-container layout.
- No specific TextKit 2 feature is required.
- Target OS includes iOS 15 or earlier.
- Custom `NSLayoutManager` subclass with `drawGlyphs` represents real investment.

Reasons to consider migration:

- Inline Writing Tools is a feature requirement.
- International text rendering issues on TextKit 1 are user-visible.
- Net-new text features being built from scratch.
- Viewport performance for very large documents matters and target OS is recent.

Strategy when migrating:

1. **Branch on `textLayoutManager` everywhere new.** Write all new code so it works on either stack and falls through cleanly when one is unavailable.
2. **Run dual code paths through transition.** Don't rip-and-replace — keep both paths alive while the migration progresses, feature by feature.
3. **Test fallback explicitly.** A migration that produces a view that silently falls back is worse than no migration. Treat unexpected fallback as a bug.
4. **Migrate incrementally.** One feature, one screen, one editor at a time. Big-bang migrations of editor stacks tend to surface scrollbar accuracy and line-counting edge cases late.

```swift
// Dual code path
if let textLayoutManager = textView.textLayoutManager {
    textLayoutManager.enumerateTextLayoutFragments(
        from: textLayoutManager.documentRange.location,
        options: []
    ) { fragment in
        // TextKit 2 path
        return true
    }
} else {
    let layoutManager = textView.layoutManager
    layoutManager.ensureLayout(forBoundingRect: textView.bounds, in: textView.textContainer)
    // TextKit 1 path
}
```

## Storage architecture for large documents

Production code editors at >100K LOC do not treat `NSTextStorage` as the source of truth. They treat it as a view cache. The document lives in a structure designed for fast random insertion and line-indexed access, and `NSTextStorage` is a thin window onto whatever slice the layout manager currently needs to render. The pattern shows up across every shipping editor that has had to handle million-line files at interactive rates.

Runestone ports AvalonEdit's red-black-tree line manager from C# to Swift. The tree is the document; the `NSTextStorage` is fed paragraphs out of it on demand. CodeEditTextView abandoned TextKit entirely after hitting issues that could not be fixed inside the framework — it now uses Core Text directly with a lazy line-layout pipeline, and loads million-line files in milliseconds. Bear, iA Writer, Drafts, Pretext, and Runestone all keep UTF-8 on disk and recompute attributes from Markdown on load; the persisted document is plain text and the attributed string is rebuilt every session. None of them store `NSAttributedString` as the document. ChimeHQ's `BufferingTextStorage` is a related but smaller-scoped pattern: it interposes a low-overhead mutation history between the user's edit and the displayed storage so that highlighters, language servers, and tree-sitter parsers run asynchronously with respect to the display path rather than blocking inside the edit transaction. The throughline is the same in every case: the editing transaction stays cheap because the heavy work is never inside it.

The decision this forces on the picker: if the editor is for code, structured prose, or any content type where the user expects the editor to feel snappy at sizes above a few thousand lines, the storage model is more important than the choice between TextKit 1 and TextKit 2. Plan the document layer first; let the choice of layout manager follow from what the document layer needs to render.

There is also a TextKit-2-specific reason this pattern bites code editors particularly hard: TextKit 2 has no glyph-index API. There is no way to ask "what is the visual rect of character index 12345" without forcing layout of every fragment ahead of it, because offscreen fragments only have estimated geometry. This is Runestone's stated reason for staying on TextKit 1 — its line-numbers gutter needs to know exactly where each line will draw, and `NSLayoutManager`'s glyph-rect APIs answer that in O(line) on TextKit 1 versus O(document-prefix) on TextKit 2. A custom line-numbers gutter on TextKit 2 has to be built as a `NSTextViewportLayoutControllerDelegate` that creates one `CALayer` per visible fragment in `configureRenderingSurfaceFor` and tears them down on the way out — a different architecture entirely from the AppKit ruler-view pattern.

## Common Mistakes

1. **Migrating without a reason.** TextKit 1 is supported, used by Apple's own apps, and not deprecated. The default answer when the existing code works is to keep it.

2. **Assuming TextKit 2 is always faster.** Performance depends on document size, OS version, and workload. Benchmark on the target OS with realistic content; don't argue from WWDC framing.

3. **Not testing on the minimum deployment target.** TextKit 2 has improved every release. A benchmark on macOS 26 doesn't tell you what users on iOS 16 see. Test on the lowest OS you support.

4. **`ensureLayout(for: textContainer)` on TextKit 1 large documents.** O(document_size). Use the rect-scoped variant `ensureLayout(forBoundingRect:in:)` over the visible rect, or the range-scoped variant.

5. **Full-document `ensureLayout` on TextKit 2.** Defeats the viewport optimization. Either limit the range to the viewport or accept estimated geometry off-screen via `.estimatesSize`.

6. **Expecting exact scroll metrics from TextKit 2.** `usageBoundsForTextContainer.height` is an estimate that refines while scrolling. If exact metrics matter, stay on TextKit 1.

7. **Reading `textView.layoutManager` to "see which stack we're on".** Triggers irreversible fallback. Always check `textLayoutManager` first.

8. **Constructing a TextKit 2 view and then forcing TextKit 1.** Wastes TK2 initialization. Use `UITextView(usingTextLayoutManager: false)` from the start when TextKit 1 is the right stack.

## References

- `txt-textkit1` — TextKit 1 API reference
- `txt-textkit2` — TextKit 2 API reference
- `txt-fallback-triggers` — every API access that flips a TextKit 2 view to TextKit 1
- `txt-textkit-debug` — symptom-driven debugging when stack-related bugs are showing
- `txt-view-picker` — picking between SwiftUI Text/TextField/TextEditor, UITextView, NSTextView when the question is the view, not the layout manager
- [NSLayoutManager](https://sosumi.ai/documentation/uikit/nslayoutmanager)
- [NSTextLayoutManager](https://sosumi.ai/documentation/uikit/nstextlayoutmanager)
- [UITextView](https://sosumi.ai/documentation/uikit/uitextview)
- [NSTextView](https://sosumi.ai/documentation/appkit/nstextview)
