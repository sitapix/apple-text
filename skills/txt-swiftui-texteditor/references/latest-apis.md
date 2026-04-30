# Latest API surface — txt-swiftui-texteditor

Authored against iOS 26.x / Swift 6.x / Xcode 26.x. Last refreshed 2026-04-29 against Sosumi.

This sidecar pins the API signatures the SKILL.md describes. SKILL.md owns the mental model; this file owns the call shapes. Refresh on each Xcode 26.x point release via the `txt-refresh-against-sosumi` skill.

## Selection

- `AttributedTextSelection` — value type representing an insertion point or one-or-more character ranges, since: iOS 26.0. <https://sosumi.ai/documentation/swiftui/attributedtextselection>
- `AttributedTextSelection.init()` — default selection for a new editor, since: iOS 26.0.
- `AttributedTextSelection.init(insertionPoint:typingAttributes:)` — caret with typing attributes, since: iOS 26.0.
- `AttributedTextSelection.init(range:)` — selection over a single contiguous range, since: iOS 26.0.
- `AttributedTextSelection.init(ranges:)` — selection over multiple ranges, since: iOS 26.0.
- `AttributedTextSelection.indices(in:) -> AttributedTextSelection.Indices` — resolve selection against an `AttributedString`, since: iOS 26.0.
- `DiscontiguousAttributedSubstring` — `@dynamicMemberLookup struct`; non-contiguous slice projected from an `AttributedString` via a `RangeSet`, since: iOS 26.0. <https://sosumi.ai/documentation/foundation/discontiguousattributedsubstring>

## Formatting definitions

- `AttributedTextFormattingDefinition<Scope>` — protocol declaring an editor's allowed attributes; associated `Scope` (typically `AttributeScopes.SwiftUIAttributes`) and `Body`, since: iOS 26.0. <https://sosumi.ai/documentation/swiftui/attributedtextformattingdefinition>
- `AttributedTextValueConstraint` — `Hashable, Sendable, AttributedTextFormattingDefinition`; associated `AttributeKey` and `Scope`; required `func constrain(_ container: inout Attributes)`, since: iOS 26.0. <https://sosumi.ai/documentation/swiftui/attributedtextvalueconstraint>
- `View.attributedTextFormattingDefinition(_:)` — `nonisolated func attributedTextFormattingDefinition<D>(_ definition: D) -> some View where D : AttributedTextFormattingDefinition`, since: iOS 26.0. <https://sosumi.ai/documentation/swiftui/view/attributedtextformattingdefinition(_:)>
- `AttributeScopes.SwiftUIAttributes` — scope hosting `font`, `foregroundColor`, `underlineStyle`, `alignment`, `lineHeight` (and more), since: iOS 15.0+ (members added per release). <https://sosumi.ai/documentation/foundation/attributescopes/swiftuiattributes>

## Programmatic editing

- `AttributedString.transformAttributes(in:body:)` — `mutating func transformAttributes<E>(in selection: inout AttributedTextSelection, body: (inout AttributeContainer) throws(E) -> Void) throws(E) where E : Error`, since: iOS 26.0. <https://sosumi.ai/documentation/foundation/attributedstring/transformattributes(in:body:)>
- `AttributedString.replaceSelection(_:withCharacters:)` — `mutating func replaceSelection(_ selection: inout AttributedTextSelection, withCharacters newContent: some Collection<Character>)`; uses current typing attributes, since: iOS 26.0. <https://sosumi.ai/documentation/foundation/attributedstring/replaceselection(_:withcharacters:)>
- `AttributedString.replaceSelection(_:with:)` — `mutating func replaceSelection(_ selection: inout AttributedTextSelection, with newContent: some AttributedStringProtocol)`; preserves the inserted content's attributes, since: iOS 26.0. <https://sosumi.ai/documentation/foundation/attributedstring/replaceselection(_:with:)>

## Font resolution

- `Font.Context` — `struct`; bundle of environment values needed to resolve a `Font`, since: iOS 15.0+. <https://sosumi.ai/documentation/swiftui/font/context>
- `Font.resolve(in:)` — `func resolve(in context: Font.Context) -> Font.Resolved`; the only public path from semantic `Font` to a resolved value, since: iOS 26.0. <https://sosumi.ai/documentation/swiftui/font/resolve(in:)>
- `Font.Resolved` — `struct`; concrete font with `ctFont`, `isBold`, `isItalic`, `isMonospaced`, `weight`, `pointSize`, `leading`, since: iOS 26.0. <https://sosumi.ai/documentation/swiftui/font/resolved>
- `EnvironmentValues.fontResolutionContext` — `var fontResolutionContext: Font.Context { get }`; read via `@Environment(\.fontResolutionContext)`, since: iOS 15.0+. <https://sosumi.ai/documentation/swiftui/environmentvalues/fontresolutioncontext>

## AttributedString block attributes

- `AttributedString.lineHeight` — line-height attribute on the SwiftUI scope, since: iOS 26.0. <https://sosumi.ai/documentation/foundation/attributedstring/lineheight>
- `AttributedString.LineHeight` — `struct`; presets `loose`, `normal`, `tight`, `variable` and constructors `exact(points:)`, `leading(increase:)`, `multiple(factor:)`, since: iOS 26.0.
- `AttributedString.writingDirection` — writing-direction attribute (`AttributedString.WritingDirection`), since: iOS 26.0. <https://sosumi.ai/documentation/foundation/attributedstring/writingdirection>
- `AttributedString.WritingDirection` — enum (e.g. `.leftToRight`, `.rightToLeft`), since: iOS 26.0.

## Editor entry point

- `TextEditor` — accepts a `Binding<AttributedString>` on iOS 26+; the rich-text init does not yet have a discrete Sosumi page, fall back to the `TextEditor` overview page until Apple ships one, since: iOS 26.0 for the rich-text path. <https://sosumi.ai/documentation/swiftui/texteditor>

## Signatures verified against Sosumi

| URL | Status | Last fetched |
|---|---|---|
| https://sosumi.ai/documentation/swiftui/attributedtextselection | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/swiftui/attributedtextformattingdefinition | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/swiftui/attributedtextvalueconstraint | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/swiftui/texteditor | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/swiftui/font/context | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/swiftui/font/resolve(in:) | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/swiftui/font/resolved | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/swiftui/environmentvalues/fontresolutioncontext | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/swiftui/view/attributedtextformattingdefinition(_:) | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring/lineheight | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring/writingdirection | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring/transformattributes(in:body:) | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring/replaceselection(_:withcharacters:) | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring/replaceselection(_:with:) | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/discontiguousattributedsubstring | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributescopes/swiftuiattributes | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring/alignment | 404 | 2026-04-29 |
| https://sosumi.ai/documentation/swiftui/fontresolutioncontext | 404 | 2026-04-29 |
