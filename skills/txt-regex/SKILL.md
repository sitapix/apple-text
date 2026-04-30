---
name: txt-regex
description: Choose between Swift Regex and NSRegularExpression for text parsing, and bridge match results to NSRange for use with NSAttributedString and TextKit. Covers regex literals, RegexBuilder DSL, runtime-constructed regexes, AnyRegexOutput, Foundation parser captures (date, currency, localizedInteger), NSRegularExpression patterns and options, NSTextCheckingResult, the NSRange(_:in:) bridge, syntax-highlighting patterns, and the performance and deployment-target tradeoffs that decide which engine to use. Use when picking a regex API for new code, migrating existing NSRegularExpression code to Swift Regex, wiring matches into syntax highlighting or attribute application in NSTextStorage, or debugging "the match is in the wrong place" bugs caused by NSRange/String.Index mismatch. Do NOT use for NLTagger, NLTokenizer, NSDataDetector, or general Natural Language utilities — see txt-detectors-tagger. Do NOT use for Markdown parsing or PresentationIntent — see txt-markdown.
license: MIT
---

# Swift Regex and NSRegularExpression

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

The regex landscape has two engines: Swift Regex (iOS 16+, compile-time validated, type-safe captures, integrated with Foundation parsers) and NSRegularExpression (every OS, ICU-backed, NSRange-native). The right pick is rarely about performance — it is usually about deployment target and whether the consumer wants `Range<String.Index>` or `NSRange`. The patterns below are starting points; before quoting any specific API signature, fetch the current Apple docs via Sosumi (`sosumi.ai/documentation/swift/regex`) and verify against the actual code, especially around bridging — most "match in the wrong place" bugs are an NSRange / String.Index mismatch, not a pattern bug.

A pattern that works in storage is not the same as a pattern that works in the displayed string after Bidi reordering or normalization. When the result feeds an attribute application against an NSTextStorage, the offsets must round-trip cleanly between the engine's representation and NSRange.

## Contents

- [Swift Regex](#swift-regex)
- [NSRegularExpression](#nsregularexpression)
- [Bridging Swift Regex to NSRange](#bridging-swift-regex-to-nsrange)
- [Performance and engine choice](#performance-and-engine-choice)
- [Syntax-highlighting patterns](#syntax-highlighting-patterns)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Swift Regex

Three creation paths, with different tradeoffs.

A regex literal (`/pattern/`) is parsed at compile time. Syntax errors are build failures; capture types are inferred and strongly typed. The result is a `Regex<(Substring, Substring, ...)>` whose tuple shape matches the captures. This is the right default for static patterns:

```swift
let email = /(?<user>\w+)@(?<domain>\w+\.\w+)/

if let m = "alice@example.com".firstMatch(of: email) {
    let user = m.user      // Substring
    let domain = m.domain  // Substring
}
```

A string-constructed `Regex(patternString)` runs at runtime. It throws on invalid patterns and produces `AnyRegexOutput`, which loses the typed-tuple shape. This is the path for user-supplied patterns:

```swift
let r = try Regex(userPattern)
```

The RegexBuilder DSL builds a regex from typed components. It is verbose but self-documenting and modular — the right answer for a pattern complex enough that the literal becomes unreadable, or one that mixes literal text with Foundation parsers:

```swift
import RegexBuilder

let parser = Regex {
    "Date: "
    Capture { .date(.numeric, locale: .current, timeZone: .current) }
}

if let m = "Date: 03/15/2025".firstMatch(of: parser) {
    let date: Date = m.1   // Actual Date, not Substring
}
```

Foundation parsers (`.date`, `.localizedCurrency`, `.localizedInteger`) are the largest concrete win over NSRegularExpression: a single pass produces typed values, not strings that need a second parse step.

Swift Regex is Unicode-correct by default — matches operate on extended grapheme clusters, with canonical equivalence applied. NSRegularExpression operates on UTF-16 code units, which produces the wrong answer for emoji and combining-mark text unless the pattern is hand-tuned.

The string methods that take a regex — `contains`, `firstMatch(of:)`, `matches(of:)`, `ranges(of:)`, `replacing(_:with:)`, `split(separator:)`, `trimmingPrefix(_:)` — all produce `Range<String.Index>`, not NSRange. Anything feeding NSAttributedString needs a bridge.

## NSRegularExpression

Available on every OS version, ICU-based, NSRange-native. The construction is throwing because a malformed pattern cannot be detected at compile time:

```swift
let r = try NSRegularExpression(pattern: "\\b(TODO|FIXME|HACK)\\b")
```

`enumerateMatches(in:options:range:using:)` is the high-throughput path; `firstMatch(in:options:range:)` and `matches(in:options:range:)` are alternatives for one-shot or eager use. Each match is an `NSTextCheckingResult` whose `range` is the full match and whose `range(at:)` returns capture group ranges.

The natural pairing with TextKit is direct — no bridging:

```swift
let storage = textStorage
let r = try NSRegularExpression(pattern: "\\b(TODO|FIXME|HACK)\\b")
let full = NSRange(location: 0, length: storage.length)

r.enumerateMatches(in: storage.string, range: full) { match, _, _ in
    guard let range = match?.range else { return }
    storage.addAttribute(.foregroundColor, value: UIColor.orange, range: range)
}
```

Two cautions. First, NSRegularExpression compilation is non-trivial; building the same regex inside a hot loop is wasteful. Hoist the construction outside any per-keystroke or per-frame work. Second, options like `.anchorsMatchLines` change anchor behavior — `^` and `$` match start/end of document by default, not start/end of line. Per-line patterns need the option.

## Bridging Swift Regex to NSRange

`NSRange(range, in: string)` converts a `Range<String.Index>` into UTF-16 offsets suitable for NSAttributedString and TextKit. The conversion is O(1) for contiguous strings and inexpensive in practice; the cost is one line of bridging at every call site:

```swift
let text = textStorage.string

if let m = text.firstMatch(of: /TODO:\s*(.+)/) {
    let fullRange = NSRange(m.range, in: text)
    let captureRange = NSRange(m.1.startIndex..<m.1.endIndex, in: text)

    textStorage.addAttribute(.foregroundColor, value: UIColor.red, range: fullRange)
    textStorage.addAttribute(.font, value: UIFont.boldSystemFont(ofSize: 14),
                             range: captureRange)
}

for m in text.matches(of: /\b\w+\b/) {
    let r = NSRange(m.range, in: text)
    // r is now usable with TextKit
}
```

The bridging is the cost of using Swift Regex against an NSAttributedString. For a syntax highlighter that runs on every keystroke against a long document, the per-call overhead is usually invisible relative to layout costs.

The reverse direction (`Range(_:in:)`) converts NSRange back to `Range<String.Index>`. It returns optional because not every NSRange describes a valid extended-grapheme-cluster boundary in the string.

## Performance and engine choice

Pure throughput is rarely the deciding factor. ICU is mature; the Swift Regex engine has caught up on simple patterns and is improving on complex ones. The differences that matter:

For complex backtracking-heavy patterns, Swift Regex offers `Local { }` (atomic groups) and `.repetitionBehavior(.reluctant)` to bound backtracking explicitly. NSRegularExpression can backtrack catastrophically on adversarial inputs unless the pattern is hand-tuned for it.

For one-shot use, the difference is negligible. For tight loops, hoist the regex out of the loop in either engine.

For a parser that needs to extract typed values (dates, currency), Swift Regex's Foundation parsers do it in one pass. NSRegularExpression captures the substring; a second parse step turns it into a typed value.

The deciding question is usually deployment target plus output type:

| Constraint | Pick |
|---|---|
| Must support pre-iOS 16 | NSRegularExpression |
| TextKit / NSAttributedString consumer, want zero bridging | NSRegularExpression |
| Static pattern in new code | Swift Regex literal |
| Captures need to be typed values, not Substrings | Swift Regex with Foundation parsers |
| User-supplied pattern | Either; both support runtime construction |
| Pattern complex enough that literal is illegible | RegexBuilder DSL |

## Syntax-highlighting patterns

The two engines diverge mostly in ergonomics. Both work; pick by deployment target and by whether the surrounding code already speaks NSRange or `Range<String.Index>`.

NSRegularExpression is the lighter touch when the consumer is `NSTextStorage`:

```swift
func highlight(in range: NSRange, storage: NSTextStorage) {
    let text = storage.string
    let kw = try! NSRegularExpression(
        pattern: "\\b(func|var|let|class|struct|enum|if|else|for|while|return)\\b")

    kw.enumerateMatches(in: text, range: range) { m, _, _ in
        guard let r = m?.range else { return }
        storage.addAttribute(.foregroundColor, value: UIColor.systemPink, range: r)
    }
}
```

Swift Regex with bridging is the lighter touch when the surrounding code is Swift-native and only the application step touches NSTextStorage:

```swift
func highlight(in nsRange: NSRange, storage: NSTextStorage) {
    let text = storage.string
    guard let swiftRange = Range(nsRange, in: text) else { return }
    let sub = text[swiftRange]

    for m in sub.matches(of: /\b(func|var|let|class|struct|enum|if|else|for|while|return)\b/) {
        let r = NSRange(m.range, in: text)
        storage.addAttribute(.foregroundColor, value: UIColor.systemPink, range: r)
    }
}
```

For per-keystroke highlighting, scope the work to the edited paragraph and batch attribute changes inside `beginEditing()` / `endEditing()` regardless of which engine drives it.

## Common Mistakes

1. **`String.count` versus `NSString.length`.** Swift Regex operates on grapheme-cluster indices. NSRegularExpression operates on UTF-16 code units. Mixing them — using `string.count` to build an NSRange, or using a UTF-16 length where a String.Index is expected — produces ranges that are off by however many emoji or combining marks the text contains. Bridge explicitly with `NSRange(_, in:)` or `Range(_, in:)` and never compute NSRange offsets from `String.count`.

2. **Compiling NSRegularExpression in a hot loop.** Construction is non-trivial. A regex used per-keystroke or per-frame should be a `static let` or stored on the owner. The same applies to `Regex(string)` runtime construction; literal regexes are compile-time and free.

3. **Forgetting `try` on `Regex(string)`.** A runtime-constructed regex throws on a malformed pattern. Literal regexes do not throw because the syntax is validated at build time.

4. **`AnyRegexOutput` where typed captures matter.** A string-constructed regex erases the capture tuple. If the call site needs `m.1` to be a `Substring` typed at compile time, use a literal or a RegexBuilder. `AnyRegexOutput` is fine for "did it match" or for indexing by name, costly for everything else.

5. **`^` and `$` not matching per line.** NSRegularExpression's default anchors match document start/end. Per-line matching needs `.anchorsMatchLines`. Swift Regex's equivalent is `.anchorsMatchLineEndings()` on the regex.

6. **Highlighting against the storage string instead of the displayed string.** TextKit 2 rendering attributes attach to layout fragments, not character ranges. For visual-only highlighting (current line, search results), use `setRenderingAttributes(_:for:)` on `NSTextLayoutManager` rather than mutating the storage; the storage path triggers full editing-cycle work.

7. **Matching on the storage string while the editor is mid-mutation.** A regex pass during `processEditing` sees the edited storage but invalidates ranges if the edit shifts characters after the matches. Either run the pass after `endEditing()` or restrict the pass to the edited paragraph.

## References

- `/skill txt-detectors-tagger` — NSDataDetector, NLTagger, NLTokenizer for tasks regex is wrong for
- `/skill txt-markdown` — Markdown rendering and AttributedString intent handling
- `/skill txt-attributed-string` — feeding regex output into AttributedString-based pipelines
- `/skill txt-nstextstorage` — applying matched attributes through NSTextStorage with proper editing batching
- [Swift Regex](https://sosumi.ai/documentation/swift/regex)
- [RegexBuilder](https://sosumi.ai/documentation/regexbuilder)
- [NSRegularExpression](https://sosumi.ai/documentation/foundation/nsregularexpression)
- [NSTextCheckingResult](https://sosumi.ai/documentation/foundation/nstextcheckingresult)
