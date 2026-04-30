---
name: txt-fallback-triggers
description: Catalog every API access and content shape that flips a UITextView or NSTextView from TextKit 2 (NSTextLayoutManager) to TextKit 1 (NSLayoutManager) compatibility mode. Covers explicit layoutManager access, glyph APIs, multi-container layout, NSTextTable / NSTextTableBlock content, the macOS field-editor cascade, framework-internal fallbacks, detection notifications, and recovery. Use when textView.textLayoutManager unexpectedly returns nil, when Writing Tools degrades to panel-only, when scrolling collapses on large documents after a build, or when auditing third-party code or your own extensions for fallback risk before shipping. Trigger on 'why did Writing Tools go panel-only', 'TextKit 2 stopped working', 'scrolling collapses', or any unexplained `textLayoutManager == nil`, even when 'fallback' isn't named. Do NOT use for symptom-driven debugging — see txt-textkit-debug. Do NOT use for the TK1 vs TK2 picker decision — see txt-textkit-choice.
license: MIT
---

# TextKit 1 fallback triggers

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill is the exhaustive catalog of what causes `UITextView` and `NSTextView` to abandon `NSTextLayoutManager` and revert to `NSLayoutManager`. Fallback is permanent on a given view instance — once `textLayoutManager` is `nil`, no API call will return it. The triggers below are clues, not guarantees: framework internals also fall back without your code on the stack, and the set of triggers shifts each OS release. Before claiming a specific trigger applies to a codebase, open the call site and verify the actual code path matches; before quoting an API signature here, fetch the current docs via Sosumi (`sosumi.ai/documentation/<framework>/<api>`).

## Contents

- [What fallback actually changes](#what-fallback-actually-changes)
- [Explicit NSLayoutManager access](#explicit-nslayoutmanager-access)
- [Glyph-based APIs](#glyph-based-apis)
- [Content-driven fallback](#content-driven-fallback)
- [Multi-container layout](#multi-container-layout)
- [Printing](#printing)
- [Framework-internal fallback](#framework-internal-fallback)
- [The macOS field-editor cascade](#the-macos-field-editor-cascade)
- [What does not cause fallback](#what-does-not-cause-fallback)
- [Detection](#detection)
- [Opting out and recovery](#opting-out-and-recovery)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## What fallback actually changes

When the system flips a text view to compatibility mode:

1. `NSTextLayoutManager` is replaced with `NSLayoutManager`.
2. `textView.textLayoutManager` returns `nil` permanently for that instance.
3. Cached references to TextKit 2 objects (fragments, content storage, viewport controller) stop functioning.
4. View-based `NSTextAttachmentViewProvider` attachments are dropped — TextKit 1 cannot render them.
5. Writing Tools degrades to panel-only — no inline rewriting.
6. Viewport-driven layout is gone; layout is contiguous (or non-contiguous-with-known-gotchas if you set the flag).

The storage layer is unchanged. `NSTextStorage` is the backing store on both stacks, so attribute access, `replaceCharacters`, and `beginEditing`/`endEditing` keep working. "Fallback" specifically names the swap of the layout manager.

## Explicit NSLayoutManager access

The single most common trigger. Any read or write of the TextKit 1 layout manager flips the view, even read-only checks:

```swift
// WRONG — every line below triggers fallback
if textView.layoutManager != nil { … }
let lm = textView.textContainer.layoutManager
textView.textContainer.replaceLayoutManager(NSLayoutManager())
textStorage.addLayoutManager(NSLayoutManager())
```

```swift
// CORRECT — branch on the TK2 manager first
if let tlm = textView.textLayoutManager {
    // TextKit 2 path
} else {
    // Already in TextKit 1; safe to use layoutManager now
}
```

`textContainer.layoutManager` is the same trigger as `textView.layoutManager` — the container holds a back-reference to the TextKit 1 layout manager and accessing it forces TextKit 1 infrastructure into existence.

Caching the layout manager in a helper (`weak var lm = textView.layoutManager`) flips the view at the moment that line runs. Categories and extensions that "remember" the layout manager do the same thing.

## Glyph-based APIs

TextKit 2 has no glyph APIs at all. Anything glyph-shaped pulls in TextKit 1:

| TextKit 1 API | What to use instead on TextKit 2 |
|---|---|
| `numberOfGlyphs`, `glyph(at:)` | Enumerate `NSTextLayoutFragment`; drop to Core Text for true glyph access |
| `glyphRange(forCharacterRange:actualCharacterRange:)` | `enumerateTextLayoutFragments(from:options:)` |
| `lineFragmentRect(forGlyphAt:effectiveRange:)` | `NSTextLineFragment.typographicBounds` |
| `boundingRect(forGlyphRange:in:)` | Union of `layoutFragmentFrame` rects |
| `characterIndex(for:in:fractionOfDistanceBetweenInsertionPoints:)` | `location(interactingAt:inContainerAt:)` |
| `drawGlyphs(forGlyphRange:at:)` | Subclass `NSTextLayoutFragment` and override `draw(at:in:)` |
| `drawBackground(forGlyphRange:at:)` | Custom layout fragment subclass |
| `shouldGenerateGlyphs` delegate | No equivalent — customize at fragment level |

The cleanest signal that a code path is TextKit 1 only is the word "glyph" in the symbol name.

## Content-driven fallback

Some content shapes force the layout manager to swap regardless of what your code does:

- **`NSTextTable` / `NSTextTableBlock` (AppKit).** Tables in the attributed string trigger fallback. Apple's TextEdit demonstrates this — opening a document with tables flips it to TextKit 1.
- **`NSTextList`.** Supported on TextKit 2 since iOS 17 / macOS 14. Earlier deployment targets still fall back. macOS 26 adds an `includesTextListMarkers` property on `NSTextList` and `NSTextContentStorage` that controls whether marker strings appear in attributed-string contents.
- **`NSTextAttachment` cell APIs.** `attachmentBounds(for:proposedLineFragment:glyphPosition:characterIndex:)` and `NSTextAttachmentCell` are TextKit 1 only. On iOS 16, the bounds API can crash on a TextKit 2 view. Use `NSTextAttachmentViewProvider` for TextKit 2.

## Multi-container layout

`NSTextLayoutManager` supports exactly one `NSTextContainer`. There is no plural form. Any layout that needs more than one container — multi-page, multi-column, linked text views — runs on TextKit 1.

```swift
// TextKit 1 only
let storage = NSTextStorage()
let layoutManager = NSLayoutManager()
storage.addLayoutManager(layoutManager)
layoutManager.addTextContainer(container1)
layoutManager.addTextContainer(container2)  // overflow target
```

TextEdit's "Wrap to Page" command falls back for this reason.

## Printing

Before macOS 15 / iOS 18, TextKit 2 had no printing path at all and falling back was automatic when print layout ran. Since iOS 18 / macOS 15, basic printing exists, but `NSTextLayoutManager` still has only one container, so multi-page pagination still requires TextKit 1. Apple's TextEdit still falls back for printing as of recent releases.

## Framework-internal fallback

Some fallbacks happen without any of your code on the stack:

- Internal AppKit / UIKit code paths sometimes reach for `layoutManager` themselves. The set is undocumented and shifts release to release.
- Quick Look previews of attachments on macOS 14 and earlier triggered fallback in NSTextView.
- Third-party libraries — line-numbering gutters, syntax highlighters, code editors written before iOS 16 — frequently access `layoutManager` unconditionally. Audit dependencies, not just your own code.

The blunt summary from the STTextView author: *"You never know what might trigger that fallback, and the cases are not documented and will vary from release to release."*

## The macOS field-editor cascade

`NSWindow` shares a single `NSTextView` as the field editor for every `NSTextField` in the window. If any code path triggers fallback on that field editor — including looking at it for diagnostics — every text field in the window loses TextKit 2 simultaneously.

```swift
// WRONG — flips every NSTextField in the window to TK1
let fieldEditor = window.fieldEditor(true, for: someField) as? NSTextView
let lm = fieldEditor?.layoutManager
```

This is window-scoped and silent. Third-party libraries that introspect the field editor for keystroke handling are a frequent culprit.

## What does not cause fallback

Equally important. These are safe on TextKit 2:

- `textView.textLayoutManager` — returns `nil` if the view has already fallen back, but reading it never causes fallback.
- `textView.textStorage` (UIKit) — direct attributed-string access is fine.
- `textContainer.exclusionPaths` — supported on TextKit 2 since iOS 16.
- `textContainerInset`, `typingAttributes`, `selectedRange` / `selectedTextRange`.
- All `UITextViewDelegate` / `NSTextViewDelegate` callbacks.
- Standard `NSAttributedString.Key` attributes — font, foreground color, paragraph style, link, attachment (when using `NSTextAttachmentViewProvider`).
- `NSTextContentStorage.performEditingTransaction { … }` and `NSTextStorage.beginEditing()` / `endEditing()` inside the transaction.
- A custom `NSTextStorage` subclass used as the backing store of `NSTextContentStorage`. The storage layer is shared between stacks; subclassing it does not force TextKit 1.

What is **not** safe and crashes rather than falling back:

- Custom `NSTextContentManager` subclass that doesn't wrap an `NSTextStorage`. Crashes during element generation in current SDKs.
- Custom `NSTextElement` subclasses beyond `NSTextParagraph`. Triggers runtime assertions.

## Detection

UIKit:

```swift
if textView.textLayoutManager == nil {
    // TextKit 1 mode (fell back, or was never TK2)
}
```

Symbolic breakpoint in Xcode on `_UITextViewEnablingCompatibilityMode` catches the moment a `UITextView` flips, with a backtrace pointing at the offending call.

AppKit notifications fire around the field-editor and other NSTextView fallbacks:

```swift
NotificationCenter.default.addObserver(
    forName: NSTextView.willSwitchToNSLayoutManagerNotification,
    object: nil, queue: .main
) { note in
    print("about to fall back: \(String(describing: note.object))")
    Thread.callStackSymbols.forEach { print($0) }
}
```

The system also logs `"UITextView <addr> is switching to TextKit 1 compatibility mode because its layoutManager was accessed"` to the console when fallback occurs.

macOS 26 adds `NSTextViewAllowsDowngradeToLayoutManager` as a user default. Setting it to `NO` causes the runtime to crash on attempted fallback rather than silently degrading — useful for shipping CI builds where any fallback should be a hard failure.

## Opting out and recovery

Production apps deliberately opt out of TextKit 2 on UITextView, treating fallback as a feature rather than a bug. The one-liner shipping editors use:

```swift
_ = textView.layoutManager  // permanently force TextKit 1 on this instance
```

The motivation, from Apple DTS forum thread #729491 and several shipping editors (Runestone, STTextView users), is that TextKit 2 degrades hard above ~3k lines and is unusable around 10k. Krzyżanowski's August 2025 retrospective on four years of TextKit 2 lands on "unstable scrolling, unreliable height estimates" — even Apple's own TextEdit shows the symptoms. Forcing TK1 with the throwaway access lets the same UITextView scroll a million-character document smoothly.

If TextKit 1 is the right stack for the feature, prefer the explicit constructor over the throwaway access — it skips wasted TextKit 2 init:

```swift
// UIKit
let textView = UITextView(usingTextLayoutManager: false)
// textView.textLayoutManager == nil from the start; no wasted TK2 init

// Manual TK1 construction (custom views)
let storage = NSTextStorage()
let layoutManager = NSLayoutManager()
layoutManager.allowsNonContiguousLayout = true
storage.addLayoutManager(layoutManager)
let container = NSTextContainer(size: CGSize(width: 300, height: .greatestFiniteMagnitude))
layoutManager.addTextContainer(container)
let textView = UITextView(frame: .zero, textContainer: container)
```

There is no way to recover TextKit 2 on the same instance once it has fallen back. The recovery procedure is:

1. Build a new `UITextView` / `NSTextView` with TextKit 2.
2. Copy `attributedText` (and `selectedRange`, `typingAttributes`, exclusion paths, container insets) over.
3. Replace the old view in the hierarchy.
4. Re-wire delegate, observers, layout constraints, focus state.

### iOS 16 TextKit 2 scroll-trail bug

On iOS 16, shrinking `attributedText` on a TextKit 2 UITextView leaves a blank scrolled-down void where the removed content used to be — the layout fragment frames don't shrink with the content. Two workarounds:

```swift
// Workaround A — clear before reassigning
textView.attributedText = nil
textView.attributedText = newShorterAttributedString

// Workaround B — opt out of TextKit 2 for this view at construction time
let textView = UITextView(usingTextLayoutManager: false)
```

This is one of the cases where the production opt-out above isn't a perf decision — it's correctness.

## Improvement timeline

| OS | Change |
|---|---|
| iOS 15 / macOS 12 | TextKit 2 introduced as opt-in |
| iOS 16 / macOS 13 | Default for new text controls; compatibility-mode fallback added |
| iOS 17 / macOS 14 | `NSTextList` support; CJK line-breaking improvements |
| iOS 18 / macOS 15 | Basic printing in TextKit 2 |
| iOS 26 / macOS 26 | `includesTextListMarkers` on `NSTextList` and `NSTextContentStorage`; macOS adds `NSTextViewAllowsDowngradeToLayoutManager` user default; `.layoutManager` access on apps linked against macOS 26 SDK is logged |

The trend is in TextKit 2's favor, but multi-container layout and `NSTextTable` remain TextKit 1 only.

## Common Mistakes

1. **Diagnostic check that itself causes fallback.** Reading `if textView.layoutManager != nil { … }` to "see which stack we're on" flips the view to TextKit 1. Always read `textView.textLayoutManager` first; it is `nil`-safe and never triggers a downgrade.

2. **Reading `textContainer.layoutManager` thinking it's safer than the view-level access.** It isn't — it's the same path through the container's back-reference to the TextKit 1 manager.

3. **Caching the layout manager in a helper or category.** A line like `weak var lm = textView.layoutManager` triggers fallback at execution time even if `lm` is never used. Move the access behind a `textLayoutManager == nil` guard, or restructure the helper to operate on a fragment-level abstraction.

4. **Trusting a third-party UITextView extension that hasn't been updated since iOS 16.** Many open-source line-number gutters and syntax highlighters access `layoutManager` unconditionally. Search dependencies for `.layoutManager` and `addLayoutManager(`.

5. **Touching the field editor for diagnostics on macOS.** `window.fieldEditor(true, for:)?.layoutManager` flips every `NSTextField` in the window. The cascade is silent and window-scoped.

6. **Overriding `drawInsertionPoint(in:color:turnedOn:)` on NSTextView.** Does not trigger fallback, but silently stops being called under TextKit 2. Custom cursor drawing disappears with no compile error or runtime warning.

7. **Assuming Writing Tools "works" because the panel appears.** The panel is the fallback UX. Inline rewriting requires TextKit 2. If only the panel opens, the view has already fallen back — `textLayoutManager == nil`.

8. **Creating a TextKit 2 view, then immediately falling back.** Wastes the TextKit 2 layout manager initialization. If the feature requires TextKit 1, use `UITextView(usingTextLayoutManager: false)` from the start.

9. **Subclassing `NSTextContentManager` without wrapping `NSTextStorage`.** Not a fallback — a crash. The supported pattern is subclassing `NSTextStorage` and using it as the backing store of `NSTextContentStorage`.

## References

- `txt-textkit-debug` — symptom-driven debugging when fallback is one of several plausible causes
- `txt-textkit-choice` — TextKit 1 vs TextKit 2 decision and migration risk
- `txt-textkit1` — TextKit 1 API reference
- `txt-textkit2` — TextKit 2 API reference
- `txt-audit` — severity-ranked code review including fallback risk findings
- [NSTextLayoutManager](https://sosumi.ai/documentation/uikit/nstextlayoutmanager)
- [NSLayoutManager](https://sosumi.ai/documentation/uikit/nslayoutmanager)
- [UITextView](https://sosumi.ai/documentation/uikit/uitextview)
- [NSTextView](https://sosumi.ai/documentation/appkit/nstextview)
- [NSTextAttachmentViewProvider](https://sosumi.ai/documentation/uikit/nstextattachmentviewprovider)
