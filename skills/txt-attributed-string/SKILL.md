---
name: txt-attributed-string
description: Choose between AttributedString and NSAttributedString, define custom attributes via AttributeScope, and convert safely at API boundaries. Use when picking the model for new code, designing a custom attribute key (`AttributedStringKey`, `CodableAttributedStringKey`, `MarkdownDecodableAttributedStringKey`), wiring a scope so attributes round-trip across SwiftUI/UIKit, or when a conversion silently dropped data. AttributedString gains capabilities every Foundation release; before claiming a specific scope, key, or conversion overload is current, fetch via Sosumi (`sosumi.ai/documentation/foundation/attributedstring`). Do NOT use for looking up specific NSAttributedString.Key values like underline or shadow — see txt-attribute-keys. Do NOT use for Markdown parsing semantics — see txt-markdown.
license: MIT
---

# AttributedString and NSAttributedString

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill is the picker between Swift's `AttributedString` (value type, type-safe attributes, Codable, Markdown-aware) and Foundation's older `NSAttributedString` (reference type, untyped key/value dictionary, required by every UIKit/AppKit text API and TextKit). It also covers defining custom attribute keys, building an `AttributeScope`, and converting cleanly across the boundary. The Foundation team has expanded `AttributedString` in every recent release — added scopes, refined Codable behavior, gained Markdown attributes — so before claiming a specific scope, key protocol, or conversion overload is current, fetch the canonical entry via Sosumi (`sosumi.ai/documentation/foundation/attributedstring`).

The model decision is rarely about preference; it is about the destination. SwiftUI Text consumes `AttributedString` directly. UIKit `attributedText`, AppKit `attributedString`, and every TextKit storage class consume `NSAttributedString`. Cross that boundary and you must convert — and conversion silently drops attributes that aren't in the scope you specify. Most "my custom highlight disappeared" bugs trace to a missing `including:` argument.

## Contents

- [Picking AttributedString vs NSAttributedString](#picking-attributedstring-vs-nsattributedstring)
- [AttributedString basics](#attributedstring-basics)
- [Runs and views](#runs-and-views)
- [Index invalidation](#index-invalidation)
- [NSAttributedString basics](#nsattributedstring-basics)
- [Conversion across the boundary](#conversion-across-the-boundary)
- [Custom attributes and scopes](#custom-attributes-and-scopes)
- [Storage backing for production editors](#storage-backing-for-production-editors)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Picking AttributedString vs NSAttributedString

`AttributedString` is a Swift value type with type-safe attributes accessed via key paths (`str.font`, `str[range].foregroundColor`). It is Codable, parses Markdown, and is what SwiftUI Text expects. Mutation is in-place on a `var` — there is no separate "mutable" subtype.

`NSAttributedString` is a Foundation reference type with a `[NSAttributedString.Key: Any]` dictionary. It is what UIKit, AppKit, and TextKit have consumed since 10.4 / iOS 3.2, and it is the only attributed type that survives an RTF or RTFD round-trip without custom encoding. Mutation requires `NSMutableAttributedString`.

The destination usually picks the model:

- SwiftUI `Text(_:)` consumes `AttributedString`
- UIKit `UILabel.attributedText`, `UITextView.attributedText` consume `NSAttributedString`
- AppKit `NSTextField.attributedStringValue`, `NSTextView.textStorage` consume `NSAttributedString`
- TextKit (1 and 2) — `NSTextStorage` is itself an `NSMutableAttributedString` subclass
- Core Text — `CFAttributedString`, toll-free bridged to `NSAttributedString`

A practical rule for new code: keep an `AttributedString` as the in-memory model, convert to `NSAttributedString` at UIKit/AppKit/TextKit boundaries, and define an `AttributeScope` that includes the standard scopes plus any custom keys so conversions round-trip cleanly.

## AttributedString basics

```swift
var str = AttributedString("Hello World")
str.font = .body
str.foregroundColor = .red

if let range = str.range(of: "World") {
    str[range].font = .body.bold()
    str[range].link = URL(string: "https://example.com")
}
```

Concatenation with `+` is value-type-safe — neither operand is mutated:

```swift
var greeting = AttributedString("Hello ")
greeting.font = .body

var name = AttributedString("World")
name.font = .body.bold()
name.foregroundColor = .blue

let combined = greeting + name
```

An `AttributeContainer` lets you build a bag of attributes once and merge it into multiple ranges:

```swift
var emphasis = AttributeContainer()
emphasis.font = .body.bold()
emphasis.foregroundColor = .accentColor

str.mergeAttributes(emphasis)            // entire string
str[range].mergeAttributes(emphasis)     // sub-range
```

Markdown parsing is built in. The default option parses block-level structure into `presentationIntent`; the inline-only option is safer for user-generated short strings:

```swift
let inline = try AttributedString(
    markdown: "Visit [Apple](https://apple.com) for **details**.",
    options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)
)
```

Markdown rendering semantics — what SwiftUI actually shows, how `presentationIntent` maps to UITextView paragraph styles — belong in the `txt-markdown` skill.

## Runs and views

A run is a maximal contiguous range of identical attributes. Iterating runs is the standard way to walk an attributed string:

```swift
for run in str.runs {
    let substring = str[run.range]
    let font = run.font
    let color = run.foregroundColor
}
```

Runs can be filtered by attribute, which is the cleanest way to find all spans with a particular value:

```swift
for (color, range) in str.runs[\.foregroundColor] {
    print("Color: \(String(describing: color)) at \(range)")
}
```

For character-level iteration that doesn't care about attributes, `AttributedString` exposes the same view types as `String`: `characters`, `unicodeScalars`, `utf8`, `utf16`. These are useful when bridging to UTF-16-based APIs (anything that takes `NSRange`).

## Index invalidation

Mutating an `AttributedString` invalidates every existing index and range derived from it. This is the single most common pitfall and the one that catches refactors:

```swift
// WRONG — `range` is invalidated by the replaceSubrange call below
var str = AttributedString("Hello World")
let range = str.range(of: "World")!
str.replaceSubrange(str.range(of: "Hello")!, with: AttributedString("Hi"))
str[range].font = .body.bold()  // crash or silent corruption

// CORRECT — re-derive the range after each mutation
var str = AttributedString("Hello World")
str.replaceSubrange(str.range(of: "Hello")!, with: AttributedString("Hi"))
if let range = str.range(of: "World") {
    str[range].font = .body.bold()
}
```

This is identical to Swift `String` index behavior. Treat any `AttributedString.Index` or `Range<AttributedString.Index>` as scoped to the mutation that produced it.

## NSAttributedString basics

```swift
let attrs: [NSAttributedString.Key: Any] = [
    .font: UIFont.systemFont(ofSize: 16),
    .foregroundColor: UIColor.label,
    .kern: 1.5,
]
let str = NSAttributedString(string: "Hello", attributes: attrs)
```

Mutation requires `NSMutableAttributedString`:

```swift
let mutable = NSMutableAttributedString(string: "Hello World")

mutable.addAttribute(.font, value: UIFont.boldSystemFont(ofSize: 16),
                     range: NSRange(location: 6, length: 5))

mutable.replaceCharacters(in: NSRange(location: 0, length: 5), with: "Hi")
```

Enumeration walks runs in NSRange terms:

```swift
let full = NSRange(location: 0, length: str.length)

str.enumerateAttributes(in: full) { attrs, range, _ in
    if let font = attrs[.font] as? UIFont { /* ... */ }
}

str.enumerateAttribute(.foregroundColor, in: full) { value, range, _ in
    if let color = value as? UIColor { /* ... */ }
}
```

`NSTextStorage` is itself an `NSMutableAttributedString` subclass, so anything that mutates an attributed string applies to text storage as well — but storage mutation has its own lifecycle (`processEditing`, `edited(_:range:changeInLength:)`) covered in `txt-nstextstorage`.

## Conversion across the boundary

The two type initializers carry an `including:` parameter that selects which `AttributeScope` to translate. Without it, conversion uses the default Foundation scope and silently drops anything outside it — including custom attributes.

```swift
// AttributedString → NSAttributedString
let nsAS = NSAttributedString(swiftAS)                       // Foundation only
let nsAS = try NSAttributedString(swiftAS, including: \.myApp) // custom scope

// NSAttributedString → AttributedString
let swiftAS = try AttributedString(nsAS, including: \.foundation)
let swiftAS = try AttributedString(nsAS, including: \.myApp)
```

For round-trip code, define one scope that combines Foundation, the platform UI scope, and any app-specific keys, and use it for both directions. See [Custom attributes and scopes](#custom-attributes-and-scopes).

Behavioral notes that catch people:

- `URL` and `String` are interchangeable for `.link` in NSAttributedString but `AttributedString.link` is typed `URL?`. A `String` link converted from NS doesn't survive cleanly — wrap it in `URL(string:)` first.
- `NSParagraphStyle` carries over as a single value; sub-paragraph splits remain stuck to whole paragraphs after `fixAttributes`.
- `NSTextAttachment` round-trips only if both ends understand the same attachment type. Image-only attachments are fine; view-provider attachments lose the live view (the attachment data survives).

## Custom attributes and scopes

A custom attribute key is a type that conforms to `AttributedStringKey`, plus optional protocols for Codable storage and Markdown parsing. The `name` is the string key under which the value is stored in `NSAttributedString` representations.

```swift
enum HighlightAttribute: AttributedStringKey {
    typealias Value = Bool
    static let name = "com.example.highlight"
}

// For Codable serialization round-tripping
enum HighlightAttribute2: CodableAttributedStringKey {
    typealias Value = Bool
    static let name = "com.example.highlight"
}

// For ^[text](key: value) Markdown syntax
enum HighlightAttribute3: CodableAttributedStringKey, MarkdownDecodableAttributedStringKey {
    typealias Value = Bool
    static let name = "com.example.highlight"
}
```

To make the attribute usable via key path (`str.highlight = true`), wrap it in an `AttributeScope` and extend `AttributeDynamicLookup`:

```swift
extension AttributeScopes {
    struct MyAppAttributes: AttributeScope {
        let highlight: HighlightAttribute
        // include the standard scopes you want round-tripped:
        let foundation: FoundationAttributes
        let swiftUI: SwiftUIAttributes
    }

    var myApp: MyAppAttributes.Type { MyAppAttributes.self }
}

extension AttributeDynamicLookup {
    subscript<T: AttributedStringKey>(
        dynamicMember keyPath: KeyPath<AttributeScopes.MyAppAttributes, T>
    ) -> T { self[T.self] }
}
```

Now `str.highlight = true` and `str[range].highlight = true` work, and conversions that pass `including: \.myApp` carry custom values cleanly:

```swift
var str = AttributedString("Read this")
if let range = str.range(of: "this") {
    str[range].highlight = true
}

let nsAS = try NSAttributedString(str, including: \.myApp)
// ...UIKit code path...
let roundTripped = try AttributedString(nsAS, including: \.myApp)
```

A scope that doesn't include `FoundationAttributes` will strip font, color, and link on conversion. The standard scopes worth including by default: `FoundationAttributes`, `SwiftUIAttributes` (when targeting SwiftUI), and `UIKitAttributes` or `AppKitAttributes` (for the platform UI). Availability differs by platform: `UIKitAttributes` is iOS, tvOS, watchOS, visionOS, and Mac Catalyst — *not* native macOS. `AppKitAttributes` is macOS-only. A cross-platform editor that picks the wrong scope per build target will silently strip the platform's UI attributes. Use `#if canImport(UIKit)` / `#if canImport(AppKit)` to gate scope composition.

## Storage backing for production editors

The on-disk representation of a document and the in-memory model are different decisions. Shipping editors that handle real document workloads — Bear, iA Writer, Drafts, Pretext, Runestone — keep the document on disk in plain UTF-8 (or Markdown) and recompute attributes on load. They do not store an `NSAttributedString`, an `AttributedString`, or a Codable archive of either as the document. Ulysses uses Markdown XL serialization for the same reason. The persistent format is plain text; the attributed representation is a derived view of it.

The reason is that attributed-string persistence loses information. RTF and RTFD carry a Cocoa-specific subset of attributes — anything outside RTF's vocabulary is dropped (the per-key survival list is in `txt-attribute-keys`). HTML import requires a hidden WebKit parser that drags in main-thread cost and brittle CSS interpretation. `NSKeyedArchiver` of an `NSAttributedString` (or Codable encoding of an `AttributedString` with platform scopes) ties the document to whatever the local app and OS understand today; cross-version reads degrade silently when an attribute moves, a key is renamed, or a custom scope changes. Diff and merge tools have no insight into the binary blob, so cross-device sync, version control, and document recovery all become format-specific tooling problems.

Plain text plus a reproducible attribute pipeline avoids those costs. The document is git-diffable, search-indexable, and trivially mergeable. The attribute layer is regenerated from the source on each load — Markdown parsed into `presentationIntent`, syntax highlighting applied from a tree-sitter parse, link detection run from a single pass. If the attribute pipeline changes, every existing document picks up the new behavior automatically; no migration runs.

Use `AttributedString` (or `NSTextStorage`'s `NSMutableAttributedString` content) as the in-memory model and the editor view's source of truth for live editing. Persist the document as plain text or Markdown. The boundary at save/load is where the attributed model is rebuilt — typically `AttributedString(markdown:)` or a custom highlighter — not where it is serialized verbatim. Code editors take this further by treating `NSTextStorage` as a view-side cache backed by a separate document data structure (see `txt-textkit-choice` for the storage architecture variants).

`NSAttributedString` archives still have a place — pasteboard payloads, undo snapshots, user-visible "rich-text export" features. They do not have a place as the canonical document.

## Common Mistakes

1. **Conversion without `including:` drops custom attributes.** Both `NSAttributedString(swiftAS)` and `AttributedString(nsAS)` use the default Foundation scope. Custom keys (and platform UI keys) silently disappear. The fix is always to specify the scope: `including: \.myApp`.

2. **Reusing an index across a mutation.** Once `replaceSubrange`, `insert`, or any structural change runs, every previously captured index/range is invalid. Re-derive ranges from `str.range(of:)` after the mutation, or perform mutations inside an iteration that captures fresh ranges.

3. **Trying to mutate an `NSParagraphStyle` after assignment.** It's immutable. Configure `NSMutableParagraphStyle` first, then set it as the attribute value. After it's stored in an attributed string, treat it as frozen.

4. **`AttributedString.link` accepts only URL.** `NSAttributedString` accepts `URL` or `String` for `.link`; `AttributedString.link` is typed `URL?`. Strings round-tripped from NS need to be wrapped.

   ```swift
   // WRONG — Swift compiler will reject; in dynamic Any-based code, won't render
   str.link = "https://apple.com"

   // CORRECT
   str.link = URL(string: "https://apple.com")
   ```

5. **Forgetting that `NSTextStorage` is `NSMutableAttributedString`.** No conversion is needed to apply attributes to a TextKit storage — it already supports all `NSMutableAttributedString` APIs. The `attributedText` property on UITextView is a *copy* of the storage's contents at access time; mutating it doesn't mutate storage.

6. **Custom scope without standard scopes.** A scope that only includes the app's custom attributes will strip `.font`, `.foregroundColor`, `.link`, etc. on conversion. Compose with `FoundationAttributes` plus the platform UI scope.

7. **Using `String` ranges with `NSAttributedString`.** Bridging requires NSRange in UTF-16 units. `NSRange(swiftRange, in: text)` is the correct converter; `text.distance(from: ...)` is wrong.

## References

- `references/latest-apis.md` — current Apple API surface refreshed against Sosumi (signatures, since-annotations, scope membership)
- `references/advanced-patterns.md` — custom-attribute walkthrough, paragraph-style catalog, RTF/HTML/Codable persistence matrix
- `txt-attribute-keys` — full catalog of NSAttributedString.Key values, value types, and view compatibility
- `txt-markdown` — Markdown parsing in AttributedString, `presentationIntent`, custom Markdown attributes
- `txt-swiftui-interop` — SwiftUI/TextKit boundary rules for which attributes survive
- `txt-nstextstorage` — NSTextStorage subclassing and the editing lifecycle
- [AttributedString](https://sosumi.ai/documentation/foundation/attributedstring)
- [NSAttributedString](https://sosumi.ai/documentation/foundation/nsattributedstring)
- [AttributeScope](https://sosumi.ai/documentation/foundation/attributescope)
- [AttributeContainer](https://sosumi.ai/documentation/foundation/attributecontainer)
- [MarkdownDecodableAttributedStringKey](https://sosumi.ai/documentation/foundation/markdowndecodableattributedstringkey)
