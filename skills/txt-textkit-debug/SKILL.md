---
name: txt-textkit-debug
description: Diagnose broken behavior in TextKit text editors — stale layout, crashes during editing, TextKit 1 fallback, Writing Tools failures, rendering artifacts, content loss. Use when the question starts with a symptom rather than an API name. Read the actual code before reciting causes from this skill — the patterns here are clues, not answers. Trigger on 'text disappeared', 'layout is wrong', 'editor crashed', 'fonts look weird', 'characters are clipped' even without TextKit named. Do NOT use for the complete TK1-fallback trigger catalog (txt-fallback-triggers), the invalidation model itself (txt-layout-invalidation), or severity-ranked code review findings (txt-audit).
license: MIT
---

# TextKit Diagnostics

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

The patterns in this skill describe how TextKit failures *typically* present. They are not a lookup table. Before quoting any cause from this document, open the relevant source — the NSTextStorage subclass, the call site that resolves a glyph rect, the delegate that mutates text — and verify the actual code matches the pattern. If you have to guess between three plausible causes, you haven't read enough of the code yet.

A symptom often has a non-TextKit root cause. If text disappears in SwiftUI, the bug is usually `updateUIView` re-creating the view, not TextKit. If layout is wrong only after rotation, the container size hasn't propagated, not TextKit. Skip to the relevant section only after ruling out the layer above.

## Contents

- [Stale layout](#stale-layout)
- [Editing crashes](#editing-crashes)
- [TextKit 1 fallback](#textkit-1-fallback)
- [Writing Tools failures](#writing-tools-failures)
- [Performance regressions](#performance-regressions)
- [Rendering artifacts](#rendering-artifacts)
- [Custom text input](#custom-text-input)
- [Content loss](#content-loss)
- [Common mistakes](#common-mistakes)
- [Debugging tools](#debugging-tools)
- [References](#references)

## Stale layout

Text changes but the display does not, or measurements return values that don't match what's on screen. On TextKit 1, this is almost always an `NSTextStorage` subclass that mutates characters without telling the layout manager. Open the subclass and verify every override of `replaceCharacters(in:with:)` and `setAttributes(_:range:)` calls `edited(_:range:changeInLength:)` with an accurate delta:

```swift
override func replaceCharacters(in range: NSRange, with str: String) {
    backingStore.replaceCharacters(in: range, with: str)
    let delta = (str as NSString).length - range.length
    edited(.editedCharacters, range: range, changeInLength: delta)
}
```

The mask must match the kind of edit. Character changes need `.editedCharacters`. Attribute changes need `.editedAttributes`. Both kinds in one mutation need both flags. The delta must be in NSString units (UTF-16) — Swift `String.count` is wrong on emoji and combining marks and will silently corrupt ranges. If batched mutations skip `beginEditing()` / `endEditing()`, every individual mutation triggers `processEditing`, multiplying invalidation work and occasionally crashing mid-batch when ranges shift underneath.

Layout itself is lazy. If a measurement queries layout *before* the next display pass, it sees pre-edit data. Force a flush with range-scoped `ensureLayout(forCharacterRange:)`. Avoid `ensureLayout(for: textContainer)` — it forces layout for the entire document and defeats viewport optimization.

On TextKit 2, the equivalent is wrapping mutations in `textContentStorage.performEditingTransaction { … }` and calling `textLayoutManager.invalidateLayout(for: range)` when needed. Viewport-driven layout means most issues here trace back to the viewport controller not running — verify `textViewportLayoutController.layoutViewport()` fires after the mutation.

Container geometry counts. If wrapping is correct in portrait but wrong in landscape, the container size has not been updated. Check `textView.textContainer.size` against the post-rotation bounds.

## Editing crashes

The most common editing crash is mutating characters inside `didProcessEditing`. That delegate runs after the storage has committed an edit; it is allowed to change attributes, not characters. Mutating characters here re-enters the editing lifecycle with stale ranges and crashes:

```swift
// Crashes — character mutation in the post-commit delegate
func textStorage(_ ts: NSTextStorage,
                 didProcessEditing: NSTextStorage.EditActions,
                 range: NSRange, changeInLength: Int) {
    ts.replaceCharacters(in: someRange, with: "x")
}

// Safe — attributes only
func textStorage(_ ts: NSTextStorage,
                 didProcessEditing: NSTextStorage.EditActions,
                 range editedRange: NSRange, changeInLength: Int) {
    ts.addAttribute(.foregroundColor, value: UIColor.red, range: editedRange)
}
```

"Range out of bounds" crashes during editing usually mean a range was captured before a previous mutation shrank the text. Re-find ranges after each mutation; never reuse a stored offset across edits.

`EXC_BAD_ACCESS` deep inside `NSLayoutManager` is almost always one of three things: an `NSTextStorage` subclass whose primitive `string` property doesn't agree with its backing store, an editing call from a background thread, or a deallocated text view whose layout manager is mid-pass. TextKit is main-thread-confined; background mutations produce sporadic crashes with no obvious frame in the offending code.

A few OS-version-specific crashes show up looking like generic editing crashes:

- **iOS 18 `_intelligenceCollectContent` crash.** The Apple Intelligence content collector calls into `selectedRange` on every UITextView in the hierarchy. A subclass that returns an `NSRange` outside `[0, length]` — for example, returning `NSRange(location: NSNotFound, length: 0)` when "no selection" was meant — crashes the collector. Defensive bounds-clamp before returning: `NSRange(location: min(loc, storage.length), length: min(len, storage.length - loc))`.
- **iOS 18.4 beta "ffi" ligature crash.** Attributed strings containing the substring `"ffi"` together with both font and foreground-color attributes crash during shaping. If a recent crash log shows a CoreText frame near a string with `ffi` and the affected device is on an iOS 18.4 beta, check the current Xcode beta release notes for status before treating it as application code.

## TextKit 1 fallback

A `UITextView` configured for TextKit 2 will silently fall back to TextKit 1 the first time something accesses `layoutManager` or `textContainer.layoutManager`. Symptoms: Writing Tools becomes panel-only, large-document performance collapses, viewport features stop working. Confirm fallback by checking `textView.textLayoutManager` — if it returns `nil`, fallback has occurred. The state is permanent for that text view instance; recovery means creating a new view and copying the content over.

Fallback triggers can be hidden inside third-party libraries. Set a symbolic breakpoint on `_UITextViewEnablingCompatibilityMode` to catch the moment it happens and find the offending call. The complete trigger catalog lives in `/skill txt-fallback-triggers`.

## Writing Tools failures

Writing Tools depends on TextKit 2, an enabled `writingToolsBehavior`, and an `UITextInput`-conforming view. If Writing Tools doesn't appear in the menu at all, the behavior is `.none` — set it to `.default`. If only the panel mode appears and inline rewrites are missing, the view has fallen back to TextKit 1 (see above). If rewrites corrupt code or quoted text, the view hasn't declared protected ranges via `writingToolsIgnoredRangesIn`. If text edits during a Writing Tools session corrupt content, the editor isn't checking `isWritingToolsActive` before applying its own mutations. If the entire feature is missing on the device, Apple Intelligence isn't enabled in Settings — that's not a code bug.

A custom view (one not derived from `UITextView` or `NSTextView`) needs full `UITextInput` adoption plus a `UITextInteraction` to receive Writing Tools at all.

## Performance regressions

Per-keystroke pipelines miss budget for two recurring reasons. First, syntax highlighting in `processEditing` or `didProcessEditing` runs on every mutation; if the highlighter re-attributes the entire document, single-character edits become O(document). Limit re-highlighting to the edited paragraph and batch attribute changes inside `beginEditing()` / `endEditing()`.

Second, full-document layout calls. On TextKit 1, `ensureLayout(for: textContainer)` is O(document) — use the rect-scoped or range-scoped variants instead, and enable `allowsNonContiguousLayout` for any document large enough to scroll. On TextKit 2, `enumerateTextLayoutFragments` with `.ensuresLayout` over the document range defeats viewport optimization; same with `ensureLayout(for: documentRange)`. The TextKit 2 viewport already lays out only what's visible — work *with* it, not against it.

A handful of innocuous-looking idioms hide outsized cost on the typing path:

- **`attributedText` getter has copy semantics.** Reading `textView.attributedText` returns a snapshot copy of the entire attributed string. Doing this inside `textViewDidChange(_:)` copies the document on every keystroke. Read `textView.textStorage` instead; `NSTextStorage` is a live reference, not a copy.
- **`selectedRange` setter inside `textViewDidChange(_:)`** cascades into layout, scroll-to-cursor, find-interaction reconciliation, and accessibility notifications. Setting it from inside the delegate that fires every keystroke is a hidden tax. The OmniGroup `OUITextView` pattern is to defer the assignment via `perform(_:with:afterDelay:)` so the cascade runs after the current text-change cycle has settled.
- **`text =` and `attributedText =` allocate proportional to document size.** Apple Dev Forum thread #118594 documents 50KB of text ballooning to 100MB+ of resident memory after one assignment — roughly 2000× blowup. Streaming long content via `textStorage.replaceCharacters(in:with:)` keeps the allocation bounded; the bulk-assign path doesn't.

ProMotion devices add a separate constraint. iPhone 13 Pro and later run UI animations at 120 Hz only when `CADisableMinimumFrameDurationOnPhone = YES` is set in `Info.plist`. Without that key, custom `CADisplayLink`-driven animations on a text view stay at 60 Hz no matter what the device supports. At 120 Hz the per-frame budget is roughly 5 ms after system overhead — heavy `NSTextStorage` syntax-highlighting work during scroll drops frames first because it shares the main thread with layout. Profile scroll, not just typing, on a ProMotion device.

When a benchmark regression shows up, profile `processEditing` and the differ in Time Profiler before assuming the failure is in TextKit itself. Differs are easy to pessimize without realizing it.

## Rendering artifacts

Clipped diacritics or descenders mean the layout fragment's frame is too small for what's drawn. On TextKit 2, override `renderingSurfaceBounds` on a custom fragment to expand the dirty rect. Wrong fonts on some characters point to font substitution — verify `fixAttributes` behavior or supply explicit fallback fonts. Overlapping text after a container resize means the layout was never invalidated for the new geometry; call `invalidateLayout(for:)` after the bounds change.

Missing text at the bottom of the view almost always traces to a text container with a finite height — set the height to `.greatestFiniteMagnitude` unless you're deliberately clipping. Emoji rendering wrong at the boundary between strings comes from mixing `String.count` and `(string as NSString).length` when computing ranges. Always normalize via `NSRange(swiftRange, in: text)` or `(text as NSString).length`.

A TextKit 2 attribute that doesn't appear to render is often a *rendering attribute* applied as a *character attribute*. TextKit 2 rendering attributes attach to layout fragments, not character ranges — use `setRenderingAttributes(_:for:)` on the layout manager, not `addAttribute(_:value:range:)` on storage.

## Custom text input

This section applies to custom views that don't inherit from `UITextView` or `NSTextView` — views where you implement `UITextInput` yourself. If you're using a stock view and have input problems, the bug is in the delegate or configuration, not the protocol; jump to the implementation guidance in `/skill txt-uitextinput`.

For a custom view: no keyboard usually means `canBecomeFirstResponder` returns `false`. Broken CJK input means `setMarkedText`/`unmarkText` are missing or incomplete. Autocorrect that does nothing means the view isn't notifying its `inputDelegate` via `textWillChange` / `textDidChange` around mutations. Caret in the wrong position means `caretRect(for:)` is computing geometry in the wrong coordinate space. Selection handles offset on multi-line means `selectionRects(for:)` is returning a single rect instead of one per line.

## Content loss

Text disappears after edits when `changeInLength` doesn't match the actual delta — the layout manager's bookkeeping diverges from storage and subsequent edits clobber data. Attribute loss usually means the storage subclass calls `edited()` only with `.editedCharacters` even when attributes changed. Undo restoring the wrong content typically means edits were not batched with `beginEditing()`/`endEditing()`, so the undo manager recorded several small operations instead of one. Custom attributes that vanish across archiving are not Codable — adopt Codable or NSCoding.

## Common mistakes

These tend to look like TextKit bugs but aren't:

1. **"It works in the playground."** Playgrounds wrap text in unusual containers and skip parts of the lifecycle that production apps run. Reproduce in a real app target before debugging.

2. **`String.count` vs `NSString.length`.** They diverge on emoji, ZWJ sequences, and combining marks. Many "wrong range" bugs are this in disguise. Normalize via `(text as NSString).length` or `NSRange(swiftRange, in: text)` at the boundary.

3. **`ensureLayout(for: textContainer)` to "fix" stale layout.** It forces full-document layout on TextKit 1 and defeats viewport optimization on TextKit 2. Use range-scoped or rect-scoped variants, or trigger via the natural draw path.

4. **Background-thread `textStorage` mutations.** `NSTextStorage` is main-thread-confined. Background mutations crash sporadically with no obvious frame. Wrap all access in `DispatchQueue.main` or hop to a `@MainActor` context.

5. **Mutating `attributedText` inside `textViewDidChange`.** Re-entrant editing. Either guard with a flag or dispatch the mutation to the next runloop tick.

6. **Assuming layout invalidation propagates immediately.** Invalidation marks regions; recomputation happens lazily on the next display. A measurement that queries layout before the next pass sees stale data. Force the boundary with `ensureLayout(forCharacterRange:)` or wait a runloop.

7. **TextKit 2 attributes attached to character ranges.** TK2 rendering attributes attach to layout fragments. Use `setRenderingAttributes(_:for:)` on the layout manager, not `addAttribute` on storage.

## Debugging tools

Symbolic breakpoints worth keeping handy:

| Breakpoint | What it catches |
|------------|----------------|
| `_UITextViewEnablingCompatibilityMode` | The exact moment a UITextView falls back to TextKit 1 |
| `-[NSTextStorage processEditing]` | Every editing cycle, useful when chasing performance |
| `-[NSLayoutManager invalidateLayoutForCharacterRange:actualCharacterRange:]` | Layout invalidation, useful when chasing stale-layout bugs |

Runtime probes:

```swift
// Is this a TextKit 2 view?
print("TextKit 2: \(textView.textLayoutManager != nil)")

// Storage / glyph consistency on TextKit 1
print("characters: \(textStorage.length), glyphs: \(layoutManager.numberOfGlyphs)")

// TextKit 2 fragment state
textLayoutManager.enumerateTextLayoutFragments(from: nil, options: []) { frag in
    print(frag.state); return true
}
```

For benchmark regressions, prefer Time Profiler over reasoning about possible causes. If `_NSLayoutTreeLineFragmentRectForGlyphAtIndex` warnings show up alongside performance failures, the layout manager is being asked for rects at glyph indices that haven't been laid out yet — `ensureLayout(forCharacterRange:)` covering the queried range is the usual fix.

## References

- `/skill txt-fallback-triggers` — complete TextKit 1 fallback trigger catalog and recovery patterns
- `/skill txt-layout-invalidation` — invalidation model details for TextKit 1 and 2
- `/skill txt-audit` — severity-ranked code review findings instead of symptom-driven debugging
- [NSTextStorage](https://sosumi.ai/documentation/uikit/nstextstorage)
- [NSTextLayoutManager](https://sosumi.ai/documentation/uikit/nstextlayoutmanager)
- [UIWritingToolsCoordinator](https://sosumi.ai/documentation/UIKit/UIWritingToolsCoordinator)
