---
name: txt-find-replace
description: Add find and replace to text editors using UIFindInteraction with UITextSearching, NSTextFinder with NSTextFinderClient, and the highlighting paths that don't pollute the document — temporary attributes on TextKit 1, rendering attributes on TextKit 2, plus the reversed-iteration replace-all pattern. Trigger on 'add a search bar to my editor', 'cmd-F UI', 'replace-all', 'find next', or 'why isn't UIFindInteraction showing up' even without UIFindInteraction named. Use when the user asks for find bars, search highlighting, replace UX, custom find sessions on non-text views, or replace-all crashes on long documents.
license: MIT
---

# Find and Replace

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill covers find/replace integration into text editors on Apple platforms — the `UIFindInteraction` plumbing on iOS, `NSTextFinder` on macOS, and the rendering paths that highlight matches without leaving traces in storage or undo. Before relying on a specific protocol method signature, fetch via Sosumi (`sosumi.ai/documentation/uikit/uitextsearching`) — `UITextSearching` has gained methods across iOS releases and old recipes drift.

A common bug class here is highlighting through `textStorage.addAttribute`, which creates undo entries and re-triggers layout. The right surface is *temporary attributes* on TextKit 1 or *rendering attributes* on TextKit 2. Both are rendering-only and bypass the storage edit cycle.

## Contents

- [UIFindInteraction on stock UITextView](#uifindinteraction-on-stock-uitextview)
- [UITextSearching for custom views](#uitextsearching-for-custom-views)
- [NSTextFinder on macOS](#nstextfinder-on-macos)
- [Highlighting matches without polluting storage](#highlighting-matches-without-polluting-storage)
- [Replace-all on long documents](#replace-all-on-long-documents)
- [Search options and regex](#search-options-and-regex)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## UIFindInteraction on stock UITextView

`UITextView` ships with full find support; flipping a flag exposes the system find bar.

```swift
textView.isFindInteractionEnabled = true

// Present from a button or keyboard shortcut
textView.findInteraction?.presentFindNavigator(showingReplace: false)
textView.findInteraction?.presentFindNavigator(showingReplace: true)  // includes Replace
```

The find bar itself is system-rendered; you don't draw it. Search runs against the text view's own content and highlights are drawn by the system. If the find bar appears but doesn't navigate, it usually means the view is not first responder or is offscreen — the bar attaches to the view it's bound to and stops driving when that view loses keyboard focus.

To present search-and-replace by default, use the `showingReplace:` parameter; setting it later requires re-presenting.

## UITextSearching for custom views

`UITextSearching` is the protocol that drives a `UIFindInteraction` against a non-`UITextView` view. The interaction calls into your view to perform searches, decorate matches, and apply replacements.

```swift
final class CustomEditor: UIView, UITextSearching {
    var supportsTextReplacement: Bool { true }

    func performTextSearch(queryString: String,
                           options: UITextSearchOptions,
                           resultAggregator: any UITextSearchAggregator) {
        let text = contentString
        var idx = text.startIndex
        let opts = stringSearchOptions(from: options)
        while let range = text.range(of: queryString, options: opts, range: idx..<text.endIndex) {
            resultAggregator.foundRange(convert(range), searchString: queryString, document: nil)
            idx = range.upperBound
        }
        resultAggregator.finishedSearching()
    }

    func decorate(foundTextRange: UITextRange,
                  document: UITextSearchDocumentIdentifier?,
                  usingStyle style: UITextSearchFoundTextStyle) {
        switch style {
        case .found:       addHighlight(foundTextRange, color: .yellow.withAlphaComponent(0.3))
        case .highlighted: addHighlight(foundTextRange, color: .systemYellow)
        case .normal:      removeHighlight(foundTextRange)
        @unknown default:  break
        }
    }

    func clearAllDecoratedFoundText() { removeAllHighlights() }

    func replace(foundTextRange: UITextRange,
                 document: UITextSearchDocumentIdentifier?,
                 withText replacementText: String) {
        applyReplacement(in: foundTextRange, with: replacementText)
    }

    func replaceAll(queryString: String,
                    options: UITextSearchOptions,
                    withText replacementText: String) {
        let ranges = findAllRanges(of: queryString, options: options)
        for range in ranges.reversed() {
            applyReplacement(in: range, with: replacementText)
        }
    }
}
```

Three points are easy to get wrong. The aggregator must receive `finishedSearching()` — without it the find bar shows a spinner and never lands on the first match. The decoration styles include a `.normal` case for "remove decoration"; conflating it with "no decoration" leaves stale highlights. And `replaceAll` must walk the matches in reverse so earlier ranges aren't shifted out from under later ones.

To install the interaction:

```swift
lazy var findInteraction = UIFindInteraction(sessionDelegate: self)

override init(frame: CGRect) {
    super.init(frame: frame)
    addInteraction(findInteraction)
}

extension CustomEditor: UIFindInteractionDelegate {
    func findInteraction(_ interaction: UIFindInteraction,
                         sessionFor view: UIView) -> UIFindSession? {
        UITextSearchingFindSession(searchableObject: self)
    }
}
```

## NSTextFinder on macOS

`NSTextFinder` is the macOS analog. `NSTextView` adopts `NSTextFinderClient` already; toggling `usesFindBar` on the text view enables the find bar without further work.

For non-`NSTextView` clients, adopt `NSTextFinderClient` and supply a finder:

```swift
final class EditorView: NSView, NSTextFinderClient {
    let textFinder = NSTextFinder()

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        textFinder.client = self
        textFinder.findBarContainer = enclosingScrollView
        textFinder.isIncrementalSearchingEnabled = true
    }

    var string: String { textStorage.string }
    var isEditable: Bool { true }
    func stringLength() -> Int { (string as NSString).length }

    func string(at characterIndex: Int,
                effectiveRange: NSRangePointer,
                endsWithSearchBoundary: UnsafeMutablePointer<ObjCBool>) -> String {
        effectiveRange.pointee = NSRange(location: 0, length: stringLength())
        endsWithSearchBoundary.pointee = true
        return string
    }

    func replaceCharacters(in range: NSRange, with string: String) {
        textStorage.replaceCharacters(in: range, with: string)
    }
}
```

The `endsWithSearchBoundary` flag is how `NSTextFinder` chunks the document. Returning the entire string in one call is fine for small documents; for streamed or paginated content, return the chunk that contains the requested character index.

## Highlighting matches without polluting storage

Highlights drawn through `textStorage.addAttribute(.backgroundColor, …)` create undo entries, run through `processEditing`, and persist if the document is saved. Use the rendering-only paths instead.

TextKit 1 — temporary attributes on the layout manager:

```swift
let full = NSRange(location: 0, length: textStorage.length)
layoutManager.removeTemporaryAttribute(.backgroundColor, forCharacterRange: full)
for r in matches {
    layoutManager.addTemporaryAttribute(.backgroundColor,
                                        value: UIColor.systemYellow.withAlphaComponent(0.3),
                                        forCharacterRange: r)
}
```

TextKit 2 — rendering attributes on the layout manager. These attach to layout fragments, not character ranges in storage; that's why "TK2 rendering attribute applied as character attribute" is a recurring no-op bug.

```swift
textLayoutManager.removeRenderingAttribute(.backgroundColor,
                                           for: textLayoutManager.documentRange)
for r in textRanges {
    textLayoutManager.addRenderingAttribute(.backgroundColor,
                                            value: UIColor.systemYellow.withAlphaComponent(0.3),
                                            for: r)
}
```

For very long documents with thousands of matches, applying attributes for every match up front costs memory and slows the render pass. Restrict highlights to ranges near the viewport and refresh on scroll:

```swift
func highlightVisible(near viewportRange: NSTextRange) {
    let extended = extend(viewportRange, by: 2000)   // overdraw window
    for match in allMatches where extended.contains(match) {
        textLayoutManager.addRenderingAttribute(.backgroundColor,
                                                value: highlightColor,
                                                for: match)
    }
}
```

## Replace-all on long documents

The single most common replace-all bug: iterating matches forward. Each replacement shifts subsequent character offsets, and the loop reads stale ranges. Iterate in reverse and wrap the whole batch in a single editing transaction so `processEditing` fires once:

```swift
let matches = findAllRanges(of: query)

textStorage.beginEditing()
for r in matches.reversed() {
    textStorage.replaceCharacters(in: r, with: replacement)
}
textStorage.endEditing()
```

For TextKit 2 with `NSTextContentStorage`, wrap in `performEditingTransaction` instead of bare `beginEditing/endEditing`. The replacement still happens through `textStorage.replaceCharacters`, but the content manager observes the change and updates its element cache once.

Undo grouping happens automatically when the storage edits are inside one transaction. To force "Replace All" to be a single undo, also wrap in `undoManager.beginUndoGrouping/endUndoGrouping`. See `txt-undo`.

## Search options and regex

`UITextSearchOptions` carries `wordMatch` and `stringCompareOptions` (case-insensitive, diacritic-insensitive). It does not declare regex mode — if your editor exposes regex search, route to `NSRegularExpression` directly rather than relying on string compare options:

```swift
func stringSearchOptions(from o: UITextSearchOptions) -> String.CompareOptions {
    var s: String.CompareOptions = []
    if o.stringCompareOptions.contains(.caseInsensitive) { s.insert(.caseInsensitive) }
    if o.stringCompareOptions.contains(.diacriticInsensitive) { s.insert(.diacriticInsensitive) }
    return s
}
```

Word match (`wordMatch`) requires boundary checking that `String.range(of:options:)` doesn't do natively. Either wrap matches with `\b` regex when in word-match mode or post-filter for boundaries.

## Common Mistakes

1. **Highlighting via `textStorage.addAttribute`.** Creates undo entries that the user undoes alongside their typing. Use temporary attributes on TextKit 1 or rendering attributes on TextKit 2.

2. **TextKit 2 rendering attributes applied to a character range with `addAttribute(_:value:range:)` on storage.** The attribute disappears on re-layout. TK2 rendering attributes attach to layout fragments via `addRenderingAttribute(_:value:for:)` on the layout manager.

3. **`replaceAll` walking matches forward.** Each replacement shifts subsequent offsets. The pattern reads stale ranges and produces gibberish or out-of-bounds crashes. Iterate `matches.reversed()`.

4. **No `finishedSearching()` on the aggregator.** The find bar shows the activity indicator forever and never advances to the first match. The aggregator only finalizes when explicitly told to.

5. **Find bar appears but doesn't navigate.** The `UIFindInteraction` is bound to a view that has lost first-responder status, or is offscreen. The interaction stops driving when its view detaches from the responder chain.

6. **`isFindInteractionEnabled` set, but no find bar appears on the keyboard shortcut.** The text view needs to be in the responder chain when the find shortcut is dispatched. Verify it's first responder before invoking.

7. **Word-match mode treated as a string compare option.** `String.CompareOptions` doesn't have a word-boundary mode. Either use a `\b...\b` regex or post-filter results for non-word characters at the boundaries.

8. **NSTextFinder client returning `endsWithSearchBoundary = false` on the only chunk.** The finder keeps asking for more chunks. For monolithic documents, return the whole string with `endsWithSearchBoundary = true`.

## References

- `txt-selection-menus` — selection rect customization, edit menu integration
- `txt-uitextinput` — when find runs against a custom view that implements UITextInput
- `txt-undo` — single-undo grouping for Replace All
- `txt-viewport-rendering` — rendering attributes and viewport-aware highlight strategies
- [UIFindInteraction](https://sosumi.ai/documentation/uikit/uifindinteraction)
- [UITextSearching](https://sosumi.ai/documentation/uikit/uitextsearching)
- [NSTextFinder](https://sosumi.ai/documentation/appkit/nstextfinder)
