---
name: apple-text-textkit-diag
description: Use when debugging broken text — stale layout, editing crashes, fallback, Writing Tools issues, or rendering artifacts
license: MIT
---

# TextKit Diagnostics

Use this skill when the main question starts with a symptom rather than an API name.

## When to Use

- Layout is stale, text disappears, or rendering is wrong.
- Editing crashes or performance collapses.
- Writing Tools, fallback, or custom input behavior is broken.

## Quick Decision

- Need a code review with severity-ranked findings -> `/skill apple-text-audit`
- Need direct API reference, not debugging -> launch the relevant domain agent (textkit-reference, editor-reference, rich-text-reference, or platform-reference)
- Start with a broken symptom -> stay here and use the decision tree below

## Before You Start: Is This Actually a TextKit Problem?

These diagnostics assume the text system itself is broken. Check these common non-TextKit causes first:

| Symptom | Likely non-TextKit cause | Where to look |
|---------|--------------------------|---------------|
| Text view appears blank or zero-sized | Auto Layout constraints missing or conflicting | Check the text view's frame/bounds and superview constraints |
| Text resets or flickers in SwiftUI | `updateUIView` called too often or re-creating the text view | `/skill apple-text-representable` — check for update loops |
| Text edits crash or produce wrong results only on background threads | Threading violation — TextKit must run on main thread | Wrap all text system access in `DispatchQueue.main` |
| Layout wrong only after rotation or resize | Container geometry not updating | Verify text view's bounds update after layout pass, not before |
| Problem only in SwiftUI, works fine in pure UIKit | UIViewRepresentable lifecycle issue | `/skill apple-text-representable` |
| Custom view (not UITextView/NSTextView) has input issues | UITextInput protocol implementation | `/skill apple-text-input-ref` |

If none of these apply, continue with the TextKit decision tree.

## Decision Tree

```
What's the symptom?
├── Layout not updating after text change → #1 Layout Stale
├── Crash in processEditing / text editing → #2 Editing Crash
├── TextKit 1 fallback triggered unexpectedly → #3 Fallback
├── Writing Tools not appearing/working → #4 Writing Tools
├── Performance issues with large text → #5 Performance
├── Text rendering artifacts / wrong appearance → #6 Rendering
├── Custom text input not working → #7 Input
└── Text content lost / corrupted → #8 Data Loss
```

## Core Guidance

## #1 Layout Not Updating

**Symptom:** Text changes but display doesn't update, or layout metrics are stale.

### TextKit 1 Checklist

1. **Is `edited()` being called?** (NSTextStorage subclass)
   ```swift
   // In replaceCharacters(in:with:)
   edited(.editedCharacters, range: range, changeInLength: delta)
   // In setAttributes(_:range:)
   edited(.editedAttributes, range: range, changeInLength: 0)
   ```

2. **Is the edit mask correct?**
   - Character changes need `.editedCharacters`
   - Attribute changes need `.editedAttributes`
   - Both? Use `[.editedCharacters, .editedAttributes]`

3. **Is `changeInLength` accurate?**
   ```swift
   // CORRECT
   let delta = (newString as NSString).length - range.length
   edited(.editedCharacters, range: range, changeInLength: delta)

   // WRONG — causes range misalignment
   edited(.editedCharacters, range: range, changeInLength: 0)
   ```

4. **Are edits batched?**
   - Each un-batched mutation triggers `processEditing()` separately
   - Wrap in `beginEditing()` / `endEditing()`

5. **Is `ensureLayout` needed?**
   - Layout is lazy. If querying before display, call `ensureLayout`.

6. **Did the text view's geometry change?**
   - Rotation, split-view resize, keyboard appear/disappear, or programmatic frame changes
   - TextKit re-layouts when the text container size changes, but only if the container size actually updated
   - If text wraps correctly in portrait but not landscape, the container bounds are stale
   - Check: `textView.textContainer.size` matches the expected width after the geometry change

### TextKit 2 Checklist

1. **Are edits wrapped in transaction?**
   ```swift
   textContentStorage.performEditingTransaction {
       textStorage.replaceCharacters(in: range, with: newText)
   }
   ```

2. **Is viewport layout triggering?**
   - `textViewportLayoutController.layoutViewport()` forces visible re-layout

3. **Was layout invalidated?**
   - `textLayoutManager.invalidateLayout(for: range)` for manual invalidation

## #2 Editing Crashes

### Crash in `processEditing()`

**Most common cause:** Modifying characters in `didProcessEditing` delegate.

```swift
// ❌ CRASH — characters must not change in didProcessEditing
func textStorage(_ textStorage: NSTextStorage,
                 didProcessEditing editedMask: NSTextStorage.EditActions,
                 range editedRange: NSRange,
                 changeInLength delta: Int) {
    textStorage.replaceCharacters(in: someRange, with: "text")  // CRASH
}

// ✅ CORRECT — only modify attributes
func textStorage(_ textStorage: NSTextStorage,
                 didProcessEditing editedMask: NSTextStorage.EditActions,
                 range editedRange: NSRange,
                 changeInLength delta: Int) {
    textStorage.addAttribute(.foregroundColor, value: UIColor.red,
                             range: editedRange)  // OK
}
```

### Crash with "range out of bounds"

**Cause:** Stale range after text mutation.

```swift
// ❌ WRONG — range invalidated by previous edit
let range1 = findRange(of: "foo")
textStorage.replaceCharacters(in: range1, with: "bar")
let range2 = findRange(of: "baz")  // Must re-find, not use stale offset
```

### EXC_BAD_ACCESS in NSLayoutManager

**Possible causes:**
- NSTextStorage subclass returning incorrect `string` property
- Thread-unsafe access to text storage from background
- Deallocated text view while layout manager is processing

**Fix:** Ensure all text system access is on the main thread. Verify NSTextStorage subclass primitives are consistent.

## #3 TextKit 1 Fallback

**Symptom:** TextKit 2 features stop working. Writing Tools goes panel-only. Performance degrades for large documents.

**Quick check:** If `textView.textLayoutManager == nil`, fallback has occurred. Set symbolic breakpoint on `_UITextViewEnablingCompatibilityMode` to catch it in the debugger.

**Common triggers:**
- Accessing `textView.layoutManager` or `textContainer.layoutManager`
- Using NSLayoutManager delegate methods
- Incompatible text attachments
- Third-party libraries that access `layoutManager` internally

**Fallback is irreversible** on a given text view instance. To recover, create a new text view with TextKit 2 and transfer the content.

For the complete fallback trigger catalog, detection patterns, and macOS field editor warnings, use `/skill apple-text-fallback-triggers`.

## #4 Writing Tools Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Not in menu at all | `writingToolsBehavior = .none` | Set to `.default` |
| Only panel, no inline | TextKit 1 mode/fallback | Ensure TextKit 2, check for fallback |
| Rewrites code/quotes | No protected ranges | Implement `writingToolsIgnoredRangesIn` |
| Text corrupted after | Editing during session | Check `isWritingToolsActive` |
| Not available | Apple Intelligence not enabled | User must enable in Settings |
| Custom view no support | Not using UITextInput | Adopt UITextInput + UITextInteraction |

## #5 Performance Issues

### Large Document Slow (TextKit 1)

1. **Enable non-contiguous layout:**
   ```swift
   layoutManager.allowsNonContiguousLayout = true
   ```

2. **Avoid full-document `ensureLayout`:**
   ```swift
   // ❌ O(document_size)
   layoutManager.ensureLayout(for: textContainer)

   // ✅ O(visible_content)
   layoutManager.ensureLayout(forBoundingRect: visibleRect, in: textContainer)
   ```

3. **Consider migrating to TextKit 2** — Always non-contiguous, viewport-based.

### Large Document Slow (TextKit 2)

1. **Don't use `ensuresLayout` for full document:**
   ```swift
   // ❌ Defeats viewport optimization
   textLayoutManager.enumerateTextLayoutFragments(
       from: textLayoutManager.documentRange.location,
       options: [.ensuresLayout]  // Forces layout for EVERYTHING
   ) { ... }
   ```

2. **Don't call `ensureLayout(for: documentRange)`**

3. **Check for accidental full-document enumeration** in delegate callbacks

### Typing Lag

1. **Profile `processEditing` / `didProcessEditing`** — Syntax highlighting in delegate may be too slow
2. **Batch attribute changes** — Use `beginEditing()`/`endEditing()`
3. **Limit highlighting scope** — Only re-highlight the edited paragraph, not the entire document

## #6 Rendering Artifacts

| Symptom | Cause | Fix |
|---------|-------|-----|
| Clipped diacritics/descenders | Layout fragment frame too small | Override `renderingSurfaceBounds` in custom fragment |
| Wrong font for some characters | Font substitution | Check `fixAttributes` behavior, provide fallback fonts |
| Overlapping text | Stale layout after container resize | Call `invalidateLayout` after container changes |
| Missing text at bottom | Text container height too small | Use `.greatestFiniteMagnitude` for height |
| Emoji rendering wrong | NSString/String count mismatch | Use proper range conversion |

## #7 Custom Text Input Issues

**Note:** This section applies to **custom views that don't inherit from UITextView/NSTextView** — views where you implement UITextInput yourself. If you're using UITextView or NSTextView directly and have input problems, the issue is usually in your delegate or configuration, not in the input protocol. For full UITextInput implementation guidance, use `/skill apple-text-input-ref`.

| Symptom | Cause | Fix |
|---------|-------|-----|
| No keyboard appears | `canBecomeFirstResponder` returns false | Override to return `true` |
| CJK input broken | `setMarkedText` not implemented | Implement full UITextInput protocol |
| Autocorrect not working | Not calling `inputDelegate` methods | Call `textWillChange`/`textDidChange` |
| Cursor in wrong position | `caretRect(for:)` returning wrong value | Fix geometry calculation |
| Selection handles misplaced | `selectionRects(for:)` incorrect | Fix rect calculation for multi-line |

## #8 Text Content Loss

| Symptom | Cause | Fix |
|---------|-------|-----|
| Text disappears after edit | Wrong `changeInLength` in `edited()` | Fix delta calculation |
| Attributes lost | NSTextStorage subclass not calling `edited(.editedAttributes)` | Add proper mask |
| Undo restores wrong content | Not using `beginEditing`/`endEditing` | Batch edits properly |
| Content empty after archiving | Custom attributes not Codable | Make attributes Codable or use NSCoding |

## Still Stuck? Check Above the TextKit Layer

If none of the TextKit-specific sections above resolved the issue, the root cause may be in the layer above TextKit:

| Symptom | Actual cause | Where to look |
|---------|-------------|---------------|
| Text updates delayed or batched oddly in SwiftUI | `@State` / `@Binding` update coalescing | Check SwiftUI view update timing, not TextKit |
| Text view resets content on every SwiftUI update | `updateUIView` re-setting text unconditionally | `/skill apple-text-representable` — guard against redundant updates |
| Layout correct in one orientation but wrong after rotation | View geometry updates before Auto Layout pass completes | Use `viewDidLayoutSubviews` or `layoutSubviews` to query layout, not `viewWillTransition` |
| Coordinates from TextKit don't match screen positions | Text view's coordinate space vs window/screen space | Convert using `textView.convert(_:to:)` before using TextKit rects |
| TextKit 2 text view is a black rectangle on first appear | Text view initialized before it's in the window hierarchy | Defer TextKit 2 configuration to `viewDidAppear` or `didMoveToWindow` |

## Debugging Tools

### Symbolic Breakpoints

| Breakpoint | Catches |
|-----------|---------|
| `_UITextViewEnablingCompatibilityMode` | TextKit 1 fallback on UITextView |
| `-[NSTextStorage processEditing]` | Every editing cycle |
| `-[NSLayoutManager invalidateLayoutForCharacterRange:actualCharacterRange:]` | Layout invalidation |

### Runtime Checks

```swift
// Check TextKit mode
print("TextKit 2: \(textView.textLayoutManager != nil)")
print("TextKit 1: \(textView.textLayoutManager == nil)")

// Check text storage consistency (TextKit 1)
let charCount = textStorage.length
let glyphCount = layoutManager.numberOfGlyphs
print("Characters: \(charCount), Glyphs: \(glyphCount)")

// Check layout state (TextKit 2)
textLayoutManager.enumerateTextLayoutFragments(from: nil, options: []) { fragment in
    print("Fragment state: \(fragment.state)")
    return true
}
```

### Instruments

- **Time Profiler** — Find slow `processEditing` or layout passes
- **Allocations** — Detect leaked text storage or layout managers
- **Core Animation** — Find text view redraw performance issues

## Related Skills and Agents

- Launch **textkit-reference** agent for the exact compatibility-mode catalog or layout invalidation details.
- Use `/skill apple-text-audit` when you want repository findings ordered by severity.
