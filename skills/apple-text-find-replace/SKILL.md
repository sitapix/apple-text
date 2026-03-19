---
name: apple-text-find-replace
description: Use when implementing find and replace in text editors, using UIFindInteraction (iOS 16+), NSTextFinder, wiring find into custom UITextView or NSTextView subclasses, highlighting search results, or implementing replace-all efficiently — covers both UIKit and AppKit
license: MIT
---

# Find and Replace in Text Editors

Use this skill when the main question is how to add find and replace to a text editor on Apple platforms.

## When to Use

- Adding find/replace to a custom text editor
- Wiring `UIFindInteraction` into a `UITextView` wrapper
- Implementing find in a custom view that is not a text view
- Highlighting search results without affecting layout
- Implementing replace-all efficiently in large documents

## Quick Decision

- Need text view selection or wrapping -> `/skill apple-text-views` or `/skill apple-text-representable`
- Need rendering overlays for highlighting -> `/skill apple-text-viewport-rendering`
- Need attributed string patterns -> `/skill apple-text-attributed-string`

## Core Guidance

## UIFindInteraction (iOS 16+)

### Overview

`UIFindInteraction` is the modern find and replace system for iOS. It provides the standard find bar UI and drives find/replace through the `UITextSearching` protocol.

`UITextView` supports `UIFindInteraction` out of the box. Set `isFindInteractionEnabled = true`:

```swift
textView.isFindInteractionEnabled = true

// Present find bar programmatically
textView.findInteraction?.presentFindNavigator(showingReplace: false)
```

### UITextSearching Protocol

If you have a custom view (not `UITextView`) that needs find, adopt `UITextSearching`:

```swift
class CustomEditorView: UIView, UITextSearching {
    var supportsTextReplacement: Bool { true }

    func decorateFound(
        _ foundRange: UITextRange,
        in document: UITextSearchDocumentIdentifier,
        usingStyle style: UITextSearchFoundTextStyle
    ) {
        // Highlight the found range
        switch style {
        case .found:
            addHighlight(for: foundRange, color: .systemYellow.withAlphaComponent(0.3))
        case .highlighted:
            addHighlight(for: foundRange, color: .systemYellow)
        case .normal:
            removeHighlight(for: foundRange)
        @unknown default:
            break
        }
    }

    func clearAllDecoratedFoundText() {
        removeAllHighlights()
    }

    func performTextSearch(
        queryString: String,
        options: UITextSearchOptions,
        resultAggregator aggregator: UITextSearchAggregator
    ) {
        // Search your text content
        let text = contentString
        var searchRange = text.startIndex..<text.endIndex

        while let range = text.range(of: queryString, options: searchOptions(from: options), range: searchRange) {
            let textRange = convertToUITextRange(range)
            aggregator.foundRange(textRange, searchString: queryString, document: nil)
            searchRange = range.upperBound..<text.endIndex
        }
        aggregator.finishedSearching()
    }

    func replaceFound(
        _ foundRange: UITextRange,
        in document: UITextSearchDocumentIdentifier,
        with replacementText: String
    ) {
        replaceText(in: foundRange, with: replacementText)
    }

    func replaceAllOccurrences(
        ofQueryString queryString: String,
        using options: UITextSearchOptions,
        with replacementText: String
    ) {
        // Replace all — work backward to preserve ranges
        let ranges = findAllRanges(of: queryString, options: options)
        for range in ranges.reversed() {
            replaceText(in: range, with: replacementText)
        }
    }

    func shouldReplaceFound(
        _ foundRange: UITextRange,
        in document: UITextSearchDocumentIdentifier,
        with replacementText: String
    ) -> Bool {
        return true  // Return false to skip protected ranges
    }
}
```

### Adding UIFindInteraction to a Custom View

```swift
class CustomEditorView: UIView, UITextSearching {
    lazy var findInteraction = UIFindInteraction(sessionDelegate: self)

    override var interactions: [any UIInteraction] {
        [findInteraction]
    }

    // ... UITextSearching implementation
}

extension CustomEditorView: UIFindInteractionDelegate {
    func findInteraction(
        _ interaction: UIFindInteraction,
        sessionFor view: UIView
    ) -> UIFindSession? {
        return UITextSearchingFindSession(searchableObject: self)
    }
}
```

## NSTextFinder (macOS)

### Overview

`NSTextFinder` provides the macOS find bar. It works with any view that adopts `NSTextFinderClient`.

```swift
class EditorView: NSView, NSTextFinderClient {
    let textFinder = NSTextFinder()

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        textFinder.client = self
        textFinder.findBarContainer = enclosingScrollView
        textFinder.isIncrementalSearchingEnabled = true
    }

    // NSTextFinderClient required methods
    var string: String { textStorage.string }
    var isEditable: Bool { true }

    func stringLength() -> Int { (string as NSString).length }

    func string(at characterIndex: Int, effectiveRange: NSRangePointer, endsWithSearchBoundary: UnsafeMutablePointer<ObjCBool>) -> String {
        effectiveRange.pointee = NSRange(location: 0, length: stringLength())
        endsWithSearchBoundary.pointee = true
        return string
    }

    func shouldReplaceCharacters(in ranges: [NSValue], with strings: [String]) -> Bool {
        return true
    }

    func replaceCharacters(in range: NSRange, with string: String) {
        textStorage.replaceCharacters(in: range, with: string)
    }

    func scrollRangeToVisible(_ range: NSRange) {
        // Scroll the text view to show the range
    }

    var firstSelectedRange: NSRange {
        // Return current selection
    }

    var selectedRanges: [NSValue] {
        get { /* current selections */ }
        set { /* update selections */ }
    }
}
```

`NSTextView` has built-in `NSTextFinder` support via `usesFindBar = true`.

## Highlighting Search Results

### TextKit 1: Temporary Attributes

Use temporary attributes to highlight search results without affecting the document or undo:

```swift
func highlightSearchResults(_ ranges: [NSRange], in layoutManager: NSLayoutManager) {
    // Clear previous highlights
    let fullRange = NSRange(location: 0, length: layoutManager.textStorage!.length)
    layoutManager.removeTemporaryAttribute(.backgroundColor, forCharacterRange: fullRange)

    // Apply new highlights
    for range in ranges {
        layoutManager.addTemporaryAttribute(.backgroundColor,
                                            value: UIColor.systemYellow.withAlphaComponent(0.3),
                                            forCharacterRange: range)
    }
}
```

Temporary attributes do not trigger layout invalidation, do not affect undo, and do not persist to the document.

### TextKit 2: Rendering Attributes

```swift
func highlightSearchResults(_ ranges: [NSTextRange], in textLayoutManager: NSTextLayoutManager) {
    // Clear previous highlights
    textLayoutManager.removeRenderingAttribute(.backgroundColor,
                                               forTextRange: textLayoutManager.documentRange)

    // Apply new highlights
    for range in ranges {
        textLayoutManager.addRenderingAttribute(.backgroundColor,
                                                value: UIColor.systemYellow.withAlphaComponent(0.3),
                                                forTextRange: range)
    }
}
```

### Performance: Large Result Sets

For documents with thousands of matches, avoid applying highlights to all results at once. Instead, highlight only results near the viewport:

```swift
func highlightVisibleResults(near viewportRange: NSTextRange) {
    let extendedRange = extendRange(viewportRange, by: 2000)  // characters of overdraw
    let visibleResults = allResults.filter { extendedRange.contains($0) }
    for result in visibleResults {
        textLayoutManager.addRenderingAttribute(.backgroundColor,
                                                value: highlightColor,
                                                forTextRange: result)
    }
}
```

## Replace-All Performance

Replace-all in large documents must work backward to preserve range validity:

```swift
func replaceAll(matching query: String, with replacement: String) {
    let ranges = findAllRanges(of: query)

    textStorage.beginEditing()
    for range in ranges.reversed() {  // MUST be reversed
        textStorage.replaceCharacters(in: range, with: replacement)
    }
    textStorage.endEditing()
    // Single processEditing pass for all replacements
}
```

Working forward invalidates subsequent ranges because each replacement changes character offsets. Working backward keeps earlier ranges valid.

## Common Pitfalls

1. **Highlighting via text storage attributes creates undo entries.** Use temporary attributes (TextKit 1) or rendering attributes (TextKit 2) for search highlights.
2. **Replace-all forward corrupts ranges.** Always work backward (highest range first).
3. **Not calling `finishedSearching()` on the aggregator.** `UIFindInteraction` waits for this signal. Without it, the find bar spins forever.
4. **Regex search without escaping.** `UITextSearchOptions` may or may not indicate regex mode. Check `wordMatch` and `caseInsensitive` options and apply them correctly.
5. **Find bar not appearing.** `UIFindInteraction` needs a `UIFindSession`. Make sure the delegate returns a session and the view is in the responder chain.

## Related Skills

- Use `/skill apple-text-viewport-rendering` for custom rendering overlay patterns.
- Use `/skill apple-text-attributed-string` for attribute-based highlighting choices.
- Use `/skill apple-text-undo` when find-replace undo grouping is wrong.
