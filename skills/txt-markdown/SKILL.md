---
name: txt-markdown
description: Render and parse Markdown in SwiftUI Text and AttributedString — inline syntax that works, block-level syntax that doesn't, PresentationIntent interpretation, and custom `^[text](key:value)` attributes via MarkdownDecodableAttributedStringKey. Use when Markdown isn't rendering as expected, headings/lists are silently dropped, a `String` variable shows literal asterisks, you're choosing between native parsing and a third-party renderer, or you need block-level formatting in UITextView. Do NOT use for the AttributedString-vs-NSAttributedString decision in general — see txt-attributed-string. Do NOT use for parser/regex mechanics on non-Markdown text — see txt-regex.
license: MIT
---

# Markdown in Apple Text

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

This skill covers what Markdown actually does inside Apple's text APIs — which syntax SwiftUI Text renders, which it silently ignores, how `AttributedString(markdown:)` parses block structure into `presentationIntent`, and what it takes to render that block structure in TextKit. The patterns here describe how Markdown rendering usually fails; before assuming a feature is missing, check the actual `interpretedSyntax` option on the call site and verify whether the destination view is SwiftUI Text or a TextKit-backed view, since those have very different rendering surfaces.

The rule that catches every team: SwiftUI Text renders inline Markdown (bold, italic, code, links, strikethrough) and silently drops everything else. There is no error, no warning, no fallback rendering — headings render as plain text, lists render as plain lines with literal `-` characters, code blocks render as inline-code spans without block formatting. Block-level Markdown requires either a TextKit view interpreting `presentationIntent` or a third-party SwiftUI renderer.

## Contents

- [Inline Markdown in SwiftUI Text](#inline-markdown-in-swiftui-text)
- [LocalizedStringKey vs String](#localizedstringkey-vs-string)
- [AttributedString markdown parsing](#attributedstring-markdown-parsing)
- [PresentationIntent and block structure](#presentationintent-and-block-structure)
- [Rendering block formatting in UITextView](#rendering-block-formatting-in-uitextview)
- [Custom Markdown attributes](#custom-markdown-attributes)
- [Native vs third-party renderers](#native-vs-third-party-renderers)
- [Common Mistakes](#common-mistakes)
- [References](#references)

## Inline Markdown in SwiftUI Text

A string literal passed to `Text(_:)` is a `LocalizedStringKey`, and `LocalizedStringKey` parses inline Markdown automatically:

```swift
Text("**Bold** and *italic* and `code`")
Text("~~Strikethrough~~ and [Link](https://apple.com)")
Text("***Bold italic*** together")
```

The inline syntax that renders:

| Syntax | Renders as |
|--------|-----------|
| `**bold**`, `__bold__` | Bold |
| `*italic*`, `_italic_` | Italic |
| `***bold italic***` | Bold + italic |
| `` `code` `` | Monospaced inline span |
| `~~strikethrough~~` | Strikethrough |
| `[text](url)` | Tappable link in accent color |

The block-level syntax that does *not* render in SwiftUI Text: headings (`# Heading`), unordered lists (`- item`), ordered lists (`1. item`), block quotes (`> quote`), fenced code blocks, images (`![alt](url)`), tables, horizontal rules, task lists (`- [ ]`). They are silently dropped — heading characters are stripped, list bullets become literal `-` characters, code fences appear as inline-code spans.

## LocalizedStringKey vs String

The most common "Markdown stopped working" bug is feeding a `String` variable to `Text` instead of a literal:

```swift
// String literal — Text(_:) takes LocalizedStringKey, Markdown renders
Text("**bold** text")

// String variable — Text(_:) takes a String overload, Markdown does NOT render
let text: String = "**bold** text"
Text(text)  // displays literal asterisks

// Force Markdown on a String variable
Text(LocalizedStringKey(text))

// Disable Markdown on a literal
Text(verbatim: "**not bold**")
```

For attributed text, parse to an `AttributedString` first and pass that:

```swift
let str = try AttributedString(
    markdown: userMessage,
    options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)
)
Text(str)
```

`Text(_: AttributedString)` is the third overload and renders all attributes the SwiftUI compatibility scope understands.

## AttributedString markdown parsing

`AttributedString(markdown:)` runs Apple's parser and returns an attributed string with attributes set per the matching syntax. The `interpretedSyntax` option controls how aggressive the parser is:

| Option | Parses | Whitespace | Best for |
|--------|--------|-----------|---------|
| `.inlineOnly` | Inline only — bold, italic, code, links, strikethrough | Collapsed (Markdown rules) | Simple formatted strings |
| `.inlineOnlyPreservingWhitespace` | Inline only | Preserved verbatim | Chat messages, multi-line user input |
| `.full` | Full Markdown — inline plus block-level | Markdown rules | Documents, articles, reading content |

`.inlineOnlyPreservingWhitespace` is usually the right choice for short user-generated content because it doesn't fold runs of whitespace or strip newlines. `.full` enables block parsing but requires the destination view to interpret `presentationIntent` — passing a `.full`-parsed `AttributedString` to SwiftUI Text gives the same inline-only rendering as `.inlineOnly`, just with extra metadata stored that nothing reads.

```swift
let inline = try AttributedString(
    markdown: "Visit [Apple](https://apple.com) for **details**",
    options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)
)

let document = try AttributedString(
    markdown: rawDocumentMarkdown,
    options: .init(interpretedSyntax: .full)
)
```

## PresentationIntent and block structure

Block-level structure parsed by `.full` is stored in the `presentationIntent` attribute on each run. It is structural metadata, not visual instructions — `presentationIntent` describes "this run is part of a level-2 heading inside a block quote," and rendering is left to the destination.

```swift
for run in document.runs {
    guard let intent = run.presentationIntent else { continue }
    for component in intent.components {
        switch component.kind {
        case .header(let level):       break  // level 1-6
        case .unorderedList:            break
        case .orderedList:              break
        case .listItem(let ordinal):    break
        case .blockQuote:               break
        case .codeBlock(let lang):      break  // language hint or nil
        case .paragraph:                break
        case .table:                    break
        case .tableHeaderRow:           break
        case .tableRow(let index):      break
        case .tableCell(let column):    break
        case .thematicBreak:            break  // horizontal rule
        @unknown default:               break
        }
    }
}
```

A run can carry multiple intents — a paragraph inside a list item inside a block quote produces three components on each run in that paragraph. The components are ordered outermost-first.

## Rendering block formatting in UITextView

To render block-level Markdown in a TextKit view, walk the runs, read `presentationIntent`, and translate each kind into the corresponding `NSAttributedString` attributes (paragraph style for indentation/spacing, font for headings, background color for code blocks). The translation isn't built in — Apple parses but doesn't render block structure outside SwiftUI's own document-rendering surfaces.

```swift
func applyBlockFormatting(to attrStr: AttributedString) -> NSAttributedString {
    let mutable = NSMutableAttributedString(attrStr)

    for run in attrStr.runs {
        guard let intent = run.presentationIntent else { continue }
        let nsRange = NSRange(run.range, in: attrStr)
        let style = NSMutableParagraphStyle()

        for component in intent.components {
            switch component.kind {
            case .header(let level):
                let sizes: [Int: CGFloat] = [1: 28, 2: 24, 3: 20, 4: 18, 5: 16, 6: 14]
                let size = sizes[level] ?? 16
                mutable.addAttribute(.font, value: UIFont.boldSystemFont(ofSize: size), range: nsRange)
                style.paragraphSpacingBefore = 12
                style.paragraphSpacing = 8

            case .unorderedList, .orderedList:
                style.headIndent = 24
                style.firstLineHeadIndent = 8

            case .blockQuote:
                style.headIndent = 16
                style.firstLineHeadIndent = 16
                mutable.addAttribute(.foregroundColor, value: UIColor.secondaryLabel, range: nsRange)

            case .codeBlock:
                mutable.addAttribute(.font,
                    value: UIFont.monospacedSystemFont(ofSize: 14, weight: .regular),
                    range: nsRange)
                mutable.addAttribute(.backgroundColor,
                    value: UIColor.secondarySystemBackground,
                    range: nsRange)

            default: break
            }
        }

        mutable.addAttribute(.paragraphStyle, value: style, range: nsRange)
    }

    return mutable
}
```

This is the minimal version. Lists with bullets need text-list configuration; nested lists need indent multiplied by depth; code blocks need padding via line layout — all of which is the work the third-party renderers do for you.

## Custom Markdown attributes

Apple's Markdown parser supports a custom inline syntax: `^[text](key1: value1, key2: value2)`. Custom attribute keys that conform to `MarkdownDecodableAttributedStringKey` are populated automatically when the parser encounters their `name`.

```swift
enum HighlightAttribute: CodableAttributedStringKey, MarkdownDecodableAttributedStringKey {
    typealias Value = Bool
    static let name = "highlight"
}

enum ColorNameAttribute: CodableAttributedStringKey, MarkdownDecodableAttributedStringKey {
    typealias Value = String
    static let name = "color"
}

extension AttributeScopes {
    struct MyMarkdownAttributes: AttributeScope {
        let highlight: HighlightAttribute
        let color: ColorNameAttribute
        let foundation: FoundationAttributes
        let swiftUI: SwiftUIAttributes
    }
    var myMarkdown: MyMarkdownAttributes.Type { MyMarkdownAttributes.self }
}

extension AttributeDynamicLookup {
    subscript<T: AttributedStringKey>(
        dynamicMember keyPath: KeyPath<AttributeScopes.MyMarkdownAttributes, T>
    ) -> T { self[T.self] }
}

let str = try AttributedString(
    markdown: "Read ^[this](highlight: true, color: 'blue') carefully",
    including: \.myMarkdown
)
```

Without `including: \.myMarkdown`, the parser ignores `^[...](...)` syntax and the inline text renders without the custom attributes. The scope is required at parse time, not just at render time.

The general protocol — defining a custom `AttributedStringKey`, building a scope, extending `AttributeDynamicLookup` — is covered in `txt-attributed-string`. The Markdown-specific bit is `MarkdownDecodableAttributedStringKey` conformance, which gives the parser permission to populate the key from `^[...](key: value)` syntax.

## Native vs third-party renderers

Native parsing (`AttributedString(markdown:)` plus `Text` or a TextKit translator) is dependency-free, type-safe, Codable-friendly, and localization-aware. Its weakness is rendering: SwiftUI Text doesn't render block structure, and writing the TextKit translator is real work for every project.

Third-party libraries solve different problems:

- **MarkdownUI** (gonzalezreal/swift-markdown-ui): renders full Markdown — headings, lists, fenced code blocks with syntax highlighting, images, tables, block quotes — directly in SwiftUI. Themeable. Trades native simplicity for rendering completeness.
- **swift-markdown** (Apple): a CommonMark *parser* with full AST access. Useful when you need to manipulate the document tree before rendering, or build a non-Markdown rendering pipeline (DocC uses this internally). It does not include views.

A practical decision rule: simple bold/italic/links in SwiftUI is native Text territory; a full reading view with images and code blocks is MarkdownUI territory; an editor with live syntax highlighting is a TextKit view with parsed `presentationIntent` plus custom attribute application.

## Common Mistakes

1. **Expecting SwiftUI Text to render headings or lists.** Inline Markdown only. The fix is either an inline-only data model (no headings expected) or switch to MarkdownUI / a TextKit-rendered view. There is no Text-only escape hatch.

2. **Markdown not rendering on a String variable.** `Text(_:)` has overloads for both `LocalizedStringKey` and `String`; Swift picks `String` for a variable, which doesn't parse Markdown.

   ```swift
   // WRONG — picks String overload, displays literal asterisks
   let body: String = userInput
   Text(body)

   // CORRECT — force LocalizedStringKey
   Text(LocalizedStringKey(body))

   // CORRECT — parse to AttributedString first
   Text(try AttributedString(markdown: body, options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)))
   ```

3. **Parsing with `.full` and expecting block rendering.** `.full` populates `presentationIntent` but doesn't render block structure visually. Without an interpreter, the result in SwiftUI Text is identical to `.inlineOnly`. The visual difference appears only when something walks the runs and applies paragraph styles.

4. **Forgetting `including: \.myMarkdown` for custom attributes.** The parser doesn't know about your scope unless you tell it at parse time. Custom `^[text](...)` syntax without the matching scope is silently ignored — no error, no warning.

5. **Treating `presentationIntent` as a per-paragraph attribute.** It is per-run. A single paragraph with a bold word in the middle is three runs, all carrying the paragraph's intent. When applying paragraph styles, take the union of intents across the paragraph or apply on a per-paragraph basis derived from intent boundaries.

6. **Whitespace folding eating user content.** `.inlineOnly` collapses runs of whitespace per Markdown rules, which is wrong for chat-style content with intentional line breaks. Use `.inlineOnlyPreservingWhitespace` for any user-typed string.

7. **Unhandled `@unknown default` on intent kind.** `PresentationIntent.Kind` is a non-frozen enum; future Foundation releases can add cases. A switch over the kinds needs `@unknown default` to compile cleanly under `-Wexhaustive-switch`.

## References

- `txt-attributed-string` — choosing between AttributedString and NSAttributedString, custom attribute keys and scopes
- `txt-attribute-keys` — full catalog of NSAttributedString.Key values applied during PresentationIntent rendering
- `txt-swiftui-interop` — what survives the SwiftUI/TextKit boundary
- [AttributedString.MarkdownParsingOptions](https://sosumi.ai/documentation/foundation/attributedstring/markdownparsingoptions)
- [MarkdownDecodableAttributedStringKey](https://sosumi.ai/documentation/foundation/markdowndecodableattributedstringkey)
- [PresentationIntent](https://sosumi.ai/documentation/foundation/presentationintent)
- [SwiftUI Text](https://sosumi.ai/documentation/swiftui/text)
