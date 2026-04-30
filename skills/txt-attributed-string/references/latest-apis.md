# Latest API surface — txt-attributed-string

Authored against iOS 26.x / Swift 6.x / Xcode 26.x. Last refreshed 2026-04-29 against Sosumi.

This is the rapid-churn signature companion to the SKILL.md mental model. Update via the `txt-refresh-against-sosumi` skill after each Xcode point release. Don't migrate signatures here into SKILL.md — they live here precisely so SKILL.md ages slowly.

## Core types

- `AttributedString` — `@dynamicMemberLookup struct AttributedString`, since: iOS 15.0 / macOS 12.0. Conforms to `Sendable`, `Copyable`, `Hashable`, `Codable`, `Transferable`, `AttributedStringProtocol`, `AttributedStringAttributeMutation`, `Equatable`, `ExpressibleByStringLiteral`, `DecodableWithConfiguration`, `EncodableWithConfiguration`.
- `NSAttributedString` — `class NSAttributedString`, since: iOS 3.2 / macOS 10.0. Foundation reference type with `[NSAttributedString.Key: Any]` storage; subclassed by `NSMutableAttributedString`.
- `AttributeContainer` — `@dynamicMemberLookup struct AttributeContainer`, since: iOS 15.0 / macOS 12.0. Holds attribute keys/values outside an `AttributedString`; primary helpers: `init()`, `merge(_:mergePolicy:)`, `subscript(_:)`.
- `AttributedString.Runs` — `struct Runs`, since: iOS 15.0 / macOS 12.0. `BidirectionalCollection` view; nested `AttributesSlice1` … `AttributesSlice5` allow filtering by 1–5 keys via `runs[\.foregroundColor]`.
- `AttributedString.Index` — `struct Index`, since: iOS 15.0 / macOS 12.0. Conforms to `Comparable`. `init(_:within:)` constructs from another index, `isValid(within:)` checks validity against a `DiscontiguousAttributedSubstring`. Invalidated by any structural mutation.
- `DiscontiguousAttributedSubstring` — `@dynamicMemberLookup struct DiscontiguousAttributedSubstring`, since: iOS 26.0 / macOS 26.0. Returned by `AttributedString.subscript(_:)` when indexed with a `RangeSet<AttributedString.Index>` or `AttributedTextSelection`. `base` exposes the source `AttributedString`; conforms to `AttributedStringAttributeMutation` so attribute mutation propagates back.

## Attribute scopes

- `AttributeScope` — `protocol AttributeScope : DecodingConfigurationProviding, EncodingConfigurationProviding, SendableMetatype`, since: iOS 15.0 / macOS 12.0. Compose a custom scope by declaring `let foundation: FoundationAttributes` (and platform UI scopes) alongside your custom keys.
- `AttributeScopes` — `@frozen enum AttributeScopes`, since: iOS 15.0 / macOS 12.0. Namespace; access via `\.foundation`, `\.swiftUI`, `\.uiKit`, `\.appKit`, plus `\.accessibility` and the framework scopes documented under conforming types.
- `AttributeScopes.FoundationAttributes` — `struct FoundationAttributes`, since: iOS 15.0 / macOS 12.0. Carries `link`, `languageIdentifier`, `imageURL`, `inlinePresentationIntent`, `presentationIntent`, `alternateDescription`, `replacementIndex`, `measurement`, `byteCount`, `dateField`, plus the Markdown source-position keys.
- `AttributeScopes.SwiftUIAttributes` — `struct SwiftUIAttributes`, since: iOS 15.0 / macOS 12.0. Carries `font`, `foregroundColor`, `backgroundColor`, `strikethroughStyle`, `underlineStyle`, `kern`, `tracking`, `baselineOffset`. Includes the Foundation scope via the `foundation` property.
- `AttributeScopes.UIKitAttributes` — `struct UIKitAttributes`, since: iOS 15.0 (no macOS). UIKit-typed counterparts of `font`, `foregroundColor`, `backgroundColor`, paragraph styling, `attachment`, plus expansion/obliqueness keys. Includes the Foundation scope.
- `AttributeScopes.AppKitAttributes` — `struct AppKitAttributes`, since: macOS 12.0 only. AppKit-typed counterparts plus cursor, marked-text, and tool-tip keys. Includes the Foundation scope.

## Custom attribute keys

- `AttributedStringKey` — `protocol AttributedStringKey : SendableMetatype`, since: iOS 15.0 / macOS 12.0. Required members: `associatedtype Value`, `static var name: String`. Conform an `enum`/`struct` and reference it from an `AttributeScope` to enable key-path access.
- `CodableAttributedStringKey` — `typealias CodableAttributedStringKey = DecodableAttributedStringKey & EncodableAttributedStringKey`, since: iOS 15.0 / macOS 12.0. Conform a key to participate in `AttributedString` Codable round-trips and `NSKeyedArchiver` storage.
- `MarkdownDecodableAttributedStringKey` — `protocol MarkdownDecodableAttributedStringKey : AttributedStringKey`, since: iOS 15.0 / macOS 12.0. Adds `static var markdownName: String` and `static func decodeMarkdown(from:)` so the key participates in Apple's `^[text](attribute: value)` Markdown extension.
- `AttributeDynamicLookup` — extension hook used to project custom scope members as key-paths on `AttributedString`. Subscript signature: `subscript<T: AttributedStringKey>(dynamicMember keyPath: KeyPath<AttributeScopes.MyScope, T>) -> T`.

## Codable persistence

- `@CodableConfiguration` — `@propertyWrapper struct CodableConfiguration<T, ConfigurationProvider>` where `T: DecodableWithConfiguration & EncodableWithConfiguration` and `ConfigurationProvider: DecodingConfigurationProviding & EncodingConfigurationProviding`, since: iOS 15.0 / macOS 12.0. Use as `@CodableConfiguration(from: \.myApp) var body: AttributedString = AttributedString()` to declare which scope an `AttributedString` field encodes against.
- `AttributeScopeCodableConfiguration` — configuration type produced by `AttributeScope` conformance; usually injected automatically via `@CodableConfiguration(from:)`.
- `AttributedString` Codable conformance — `Decodable`, `Encodable`, `DecodableWithConfiguration`, `EncodableWithConfiguration`. Without `@CodableConfiguration` or an explicit `including:` argument, only Foundation-scope attributes survive.

## Markdown parsing

- `AttributedString.MarkdownParsingOptions` — `struct MarkdownParsingOptions`, since: iOS 15.0 / macOS 12.0. Initializer: `init(allowsExtendedAttributes:interpretedSyntax:failurePolicy:languageCode:)`. Properties: `allowsExtendedAttributes: Bool`, `interpretedSyntax: InterpretedSyntax` (`.full`, `.inlineOnly`, `.inlineOnlyPreservingWhitespace`), `failurePolicy: FailurePolicy` (`.throwError`, `.returnPartiallyParsedIfPossible`), `languageCode: String?`.
- `AttributedString.init(markdown:options:baseURL:)` and `init(markdown:including:options:baseURL:)` — Markdown initializers, since: iOS 15.0 / macOS 12.0. Use the `including:` overload to surface custom `MarkdownDecodableAttributedStringKey` keys.
- `AttributedString.MarkdownSourcePosition` — `struct MarkdownSourcePosition`, attribute carried on Markdown-parsed runs that records the byte range in the source string. Useful for round-tripping edits back into Markdown.

## Transforms and indexing

- `AttributedString.transform(updating:body:)` — five overloads, since: iOS 26.0 / macOS 26.0. Variants accept `inout Range<AttributedString.Index>`, `inout [Range<AttributedString.Index>]`, `inout AttributedTextSelection`, plus return-style variants that yield the updated range/ranges instead of mutating in place. Use this to keep ranges valid across structural mutation. Fatal-errors when tracking fails for the in-place forms; the `Optional`-returning variants give a fallback path.
- `AttributedString.transformingAttributes(_:_:)` and the 2-/3-/4-/5-key arities — since: iOS 15.0 / macOS 12.0, `@preconcurrency`. Signature for the single-attribute form: `func transformingAttributes<K>(_ k: K.Type, _ c: (inout AttributedString.SingleAttributeTransformer<K>) -> Void) -> AttributedString where K: AttributedStringKey, K.Value: Sendable`. Each arity has a key-path variant alongside the `K.Type` variant.
- `AttributedString.transformAttributes(in:body:)` — `mutating func transformAttributes<E>(in selection: inout AttributedTextSelection, body: (inout AttributeContainer) throws(E) -> Void) throws(E) where E: Error`, since: iOS 26.0 / macOS 26.0. The selection-aware mutation primitive used by SwiftUI's iOS 26 rich-text TextEditor; the same pattern lives in `txt-swiftui-texteditor`.
- `AttributedString.replaceSelection(_:with:)` and `replaceSelection(_:withCharacters:)` — since: iOS 26.0 / macOS 26.0. Replace the content covered by an `AttributedTextSelection` with a new `AttributedString` or with raw characters that inherit typing attributes.
- `AttributedString.SingleAttributeTransformer` — generic struct passed into `transformingAttributes`. Members: `range`, `value`, plus mutation helpers to alter range or replace the value.
- `AttributedString.removeSubranges(_:)` — `mutating func removeSubranges(_ subranges: RangeSet<AttributedString.Index>)`, the discontiguous counterpart to `removeSubrange(_:)`, complements `DiscontiguousAttributedSubstring`.

## Signatures verified against Sosumi

| URL | Status | Last fetched |
|---|---|---|
| https://sosumi.ai/documentation/foundation/attributedstring | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/nsattributedstring | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributecontainer | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributescope | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributescopes | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributescopes/foundationattributes | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributescopes/swiftuiattributes | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributescopes/uikitattributes | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributescopes/appkitattributes | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstringkey | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/codableattributedstringkey | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/markdowndecodableattributedstringkey | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/codableconfiguration | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring/index | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring/runs | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/discontiguousattributedsubstring | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring/markdownparsingoptions | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring/transform(updating:body:)-1b6eb | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring/transformingattributes(_:_:)-9prm2 | 200 | 2026-04-29 |
| https://sosumi.ai/documentation/foundation/attributedstring/transformattributes(in:body:) | 200 | 2026-04-29 |

## Discrepancies noted during refresh

- `transformingAttributes(_:_:)` exists in eleven overloads (one through five attribute keys, each with both a `K.Type` form and a `KeyPath` form, plus a `@preconcurrency` annotation on the type-based form) — the brief description "transform one attribute" undersells the matrix; downstream callers should browse the AttributedString page for the right arity.
- `DiscontiguousAttributedSubstring` is gated to iOS 26.0+ / macOS 26.0+ even though `AttributedString` itself remains iOS 15.0+. Custom Codable code that builds against a discontiguous substring will not back-deploy.
- `transform(updating:body:)` and `transformAttributes(in:body:)` are iOS 26.0+ only and tightly coupled to `AttributedTextSelection`. The mental model lives in `txt-swiftui-texteditor`; this skill mentions the signatures so cross-skill readers can find them.
- `@CodableConfiguration` is documented as available since iOS 15.0 / macOS 12.0 — older claims that it shipped later are stale.
- `AttributeScopes.UIKitAttributes` is unavailable on macOS (UIKit runs only under Catalyst on the Mac); use `AppKitAttributes` for native AppKit. SwiftUI scope works on every Apple platform.
