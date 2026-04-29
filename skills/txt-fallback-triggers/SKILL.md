---
name: txt-fallback-triggers
description: Use when debugging or preventing TextKit 2 fallback to TextKit 1 — complete trigger catalog, detection, and recovery
license: MIT
---

# TextKit 1 Fallback Triggers — Complete Catalog

Use this skill when the main question is why a TextKit 2 view entered compatibility mode or how to avoid doing that.

## When to Use

- `textLayoutManager` unexpectedly becomes `nil`
- Writing Tools loses inline behavior
- You need to audit fallback risk before touching a text view

## Quick Decision

- Need a symptom-first debugger -> `/skill txt-textkit-debug`
- Need the exact fallback trigger catalog -> stay here
- Need to choose TextKit 1 on purpose -> `/skill txt-textkit-choice`

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
| Printing (before macOS 15) | Automatic fallback for print layout |

### Field Editor Cascade (macOS Critical Gotcha)

macOS uses a **shared `NSTextView`** as the field editor for ALL `NSTextField` instances in a window. If ANY field triggers a TextKit 1 fallback on the field editor, **every text field in that window loses TextKit 2**.

```swift
// ❌ One bad field editor access breaks ALL fields in the window
let fieldEditor = window.fieldEditor(true, for: someTextField) as? NSTextView
let lm = fieldEditor?.layoutManager  // Fallback — now ALL fields are TextKit 1
```

This cascade is especially dangerous with third-party libraries that inspect the field editor.

**Detection (macOS):**
```swift
NotificationCenter.default.addObserver(
    forName: NSTextView.willSwitchToNSLayoutManagerNotification,
    object: nil, queue: .main  // nil = any text view, catches field editor
) { notification in
    print("⚠️ \(notification.object) switching to TK1")
    Thread.callStackSymbols.forEach { print($0) }
}
```

### macOS 26 Changes

- `NSTextViewAllowsDowngradeToLayoutManager` user default — set to `NO` to prevent fallback entirely (crashes instead of silently degrading)
- `includesTextListMarkers` property on `NSTextList` and `NSTextContentStorage` — controls whether list marker strings appear in attributed string contents. AppKit adopts TextKit 2 list behavior by default in macOS 26.
- `.layoutManager` access on apps linked against macOS 26 SDK triggers a logged, tracked downgrade

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

## Common Pitfalls

1. **Diagnostic check that itself causes fallback** — `if textView.layoutManager != nil { … }` flips the view to TK1. Always check `textView.textLayoutManager != nil` first. Reading `layoutManager` is *the* most common silent fallback in production code.

2. **Reading `textContainer.layoutManager` thinking it's safe** — same trigger as `textView.layoutManager`. The container holds a back-reference to the TK1 layout manager.

3. **A category/extension that "remembers" the layout manager** — caching `weak var lm = textView.layoutManager` in a helper class still triggers fallback the moment the line executes.

4. **Third-party library importing your text view** — many open-source UITextView extensions (line-numbering gutters, syntax highlighters, code editors written before iOS 16) access `layoutManager` unconditionally. Audit dependencies, not just your own code.

5. **NSTextField's shared field editor** — accessing `layoutManager` on the field editor flips ALL `NSTextField`s in the same window into TK1. Subtle and window-scoped.

6. **`drawInsertionPoint(in:color:turnedOn:)` override** — does NOT trigger fallback, but **silently stops being called** under TextKit 2. Custom cursor rendering disappears with no compile error or runtime warning.

7. **Assuming Writing Tools "works" because the panel appears** — the panel is the fallback UX. Inline rewriting requires TK2. If you see only the panel after triggering Writing Tools, the view fell back.

8. **Creating a TK2 view, then immediately falling back to TK1** — wastes the TK2 layout manager initialization. If you need TK1, use `UITextView(usingTextLayoutManager: false)` from the start.

## Related Skills

- Use `/skill txt-textkit-debug` for broader debugging around fallback symptoms.
- Use `/skill txt-textkit-choice` when compatibility mode pressure means TextKit 1 may be the right explicit choice.
- Use `/skill txt-audit` when you want repository findings ranked by severity.
