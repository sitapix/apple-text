---
name: txt-swiftui-texteditor
description: Build rich-text editing in SwiftUI using the iOS 26+ TextEditor with AttributedString binding, AttributedTextSelection for selection-aware formatting, AttributedTextFormattingDefinition and AttributedTextValueConstraint for restricting allowed attributes, and FontResolutionContext for resolving semantic fonts. Use when targeting iOS 26 or later, when evaluating whether the native TextEditor replaces a UIViewRepresentable wrapper, when building a formatting toolbar for a SwiftUI editor, when constraining which formatting users can apply, or when migrating from a UITextView-based wrapper. Do NOT use for plain-text TextEditor on older iOS versions, for UIViewRepresentable wrappers around UITextView (txt-wrap-textview), or for Writing Tools integration (txt-writing-tools).
license: MIT
---

# SwiftUI TextEditor Rich Text (iOS 26+)

Authored against iOS 26.x / Swift 6.x / Xcode 26.x.

The iOS 26 SwiftUI rich-text APIs are a first-generation surface and the type names, member signatures, and behavior are still in flux across Xcode point releases. Before claiming any specific signature for `AttributedTextSelection`, `AttributedTextFormattingDefinition`, `AttributedTextValueConstraint`, `FontResolutionContext`, or `transformAttributes(in:body:)`, fetch the current Apple docs via Sosumi (`sosumi.ai/documentation/swiftui/<symbol>`). The patterns below describe the model; the exact type members may have shifted since this skill was authored. Verify before quoting.

This skill covers what TextEditor can and cannot do as a rich-text editor, and how to build with the new selection and formatting types when it can. It does not cover plain-text TextEditor (any iOS version), UIViewRepresentable wrappers (which remain the right answer for many production rich-text needs), or Writing Tools delegate integration. The default assumption for production code on iOS 26 is still that a wrapped `UITextView` is more capable; pick TextEditor when the requirement set fits.

## Contents

- [What changed in iOS 26](#what-changed-in-ios-26)
- [Selection-aware formatting](#selection-aware-formatting)
- [Formatting constraints](#formatting-constraints)
- [Programmatic selection editing](#programmatic-selection-editing)
- [What TextEditor cannot do](#what-texteditor-cannot-do)
- [Migrating from a UITextView wrapper](#migrating-from-a-uitextview-wrapper)
- [Common mistakes](#common-mistakes)
- [References](#references)

## What changed in iOS 26

`TextEditor` on iOS 26 accepts a binding to `AttributedString`, not just `String`. Switching the binding type enables real rich-text editing in pure SwiftUI:

```swift
struct RichEditor: View {
    @State private var text = AttributedString("Edit this text…")

    var body: some View {
        TextEditor(text: $text)
    }
}
```

That single change brings in:

- Bold, italic, underline, strikethrough — including the Cmd+B / Cmd+I / Cmd+U keyboard shortcuts.
- Format menu items (the standard system menu).
- Genmoji insertion from the emoji keyboard.
- `AttributedString` properties like `alignment`, `lineHeight`, and `writingDirection` work directly on the bound content.

Five new types support custom formatting UI:

| Type | Role |
|------|------|
| `AttributedTextSelection` | Two-way binding for the user's current selection |
| `AttributedTextFormattingDefinition` | Declares the scope of allowed formatting |
| `AttributedTextValueConstraint` | Constrains which values are permitted for an attribute |
| `Font.Context` (via `\.fontResolutionContext`) | Resolves a semantic `Font` to concrete typographic traits through `Font.resolve(in:)` |
| `DiscontiguousAttributedSubstring` | Non-contiguous selection via `RangeSet` |

Verify the exact signatures via Sosumi before writing against them. The API shape is consistent with what's described here at the time of authoring, but type members are the most likely thing to change in point releases.

## Selection-aware formatting

The toolbar pattern uses `AttributedTextSelection` plus `transformAttributes(in:body:)` to mutate the selected range:

```swift
struct FormattedEditor: View {
    @State private var text = AttributedString("Select text to format")
    @State private var selection = AttributedTextSelection()

    @Environment(\.fontResolutionContext) private var fontResolutionContext

    var body: some View {
        VStack {
            TextEditor(text: $text, selection: $selection)

            HStack {
                Button(action: toggleBold) { Image(systemName: "bold") }
                Button(action: toggleItalic) { Image(systemName: "italic") }
                Button(action: toggleUnderline) { Image(systemName: "underline") }
            }
        }
    }

    private func toggleBold() {
        text.transformAttributes(in: &selection) {
            let font = $0.font ?? .default
            let resolved = font.resolve(in: fontResolutionContext)
            $0.font = font.bold(!resolved.isBold)
        }
    }

    private func toggleItalic() {
        text.transformAttributes(in: &selection) {
            let font = $0.font ?? .default
            let resolved = font.resolve(in: fontResolutionContext)
            $0.font = font.italic(!resolved.isItalic)
        }
    }

    private func toggleUnderline() {
        text.transformAttributes(in: &selection) {
            $0.underlineStyle = $0.underlineStyle == nil ? .single : nil
        }
    }
}
```

Two things are worth noting. First, `Font` is semantic — `.body`, `.title`, etc. To check whether the selection is currently bold or italic, you have to *resolve* the semantic font into concrete traits via `font.resolve(in: fontResolutionContext)`. Without that resolution, you can't tell what the user is actually seeing. Read `fontResolutionContext` from the environment.

Second, `transformAttributes(in:body:)` takes the selection by `inout` because mutation can shift selection bounds. The closure receives a mutable view of the run's attributes; setting `$0.font` or `$0.underlineStyle` applies across the selection.

For attributes that don't depend on resolution (alignment, line height, foreground color), the resolution step isn't needed:

```swift
text.transformAttributes(in: &selection) {
    $0.foregroundColor = .red
}
```

## Formatting constraints

`AttributedTextFormattingDefinition` lets the editor declare which attributes are allowed and how their values are constrained. This is where TextEditor diverges from a "free-form attributed editor" — instead of accepting any attribute, it asks the formatting definition whether each potential change is valid.

The shape is a protocol you conform to. The conforming type pins a `Scope` (typically `AttributeScopes.SwiftUIAttributes`) and supplies one or more `AttributedTextValueConstraint` types — each constraint is itself an `AttributedTextFormattingDefinition`-conforming type that nominates an `AttributeKey` and implements `constrain(_ container: inout Attributes)` to mutate an attribute container in place. `AttributedTextValueConstraint` is `Hashable` and `Sendable`. The protocol is the right tool when the editor needs to enforce a style guide ("only headings 1-3," "no custom fonts," "single underline only"). For a fully free-form editor, omit the definition.

Attach the definition to the editor with the `.attributedTextFormattingDefinition(_:)` modifier. It takes an instance (not a metatype):

```swift
TextEditor(text: $text, selection: $selection)
    .attributedTextFormattingDefinition(MyFormatting())
```

The exact protocol requirements and constraint APIs have shifted across iOS 26 betas. Before writing a real conformance, fetch `https://sosumi.ai/documentation/swiftui/attributedtextformattingdefinition` and `https://sosumi.ai/documentation/swiftui/attributedtextvalueconstraint` and follow the current associated-type and method requirements verbatim — the surface is small, but signatures change between point releases.

When a constraint needs to inspect a SwiftUI `Font`, resolve it through the environment's `fontResolutionContext` (a `Font.Context`) before reading weight/size/design — `Font.resolve(in:)` is the only public path to a `Font.Resolved`. Calling `resolve()` with no argument does not compile.

## Programmatic selection editing

The new APIs let SwiftUI code drive the selection without dropping to UIKit:

```swift
// Replace the selected characters with plain text
text.replaceSelection(&selection, withCharacters: "replacement")

// Replace with attributed content
let styled = AttributedString("styled replacement")
text.replaceSelection(&selection, with: styled)

// Read the current selection's range information
let indices = selection.indices(in: text)
```

These work without involving a coordinator, delegate, or representable. For inserting templated content (date stamps, mentions, emoji, code blocks), `replaceSelection` is the path.

`AttributedString` itself gained block-level properties on iOS 26:

```swift
text.alignment = .center
text.lineHeight = .exact(points: 32)        // exact point height
text.lineHeight = .multiple(factor: 1.5)    // multiplier
text.lineHeight = .loose                    // loose preset
text.writingDirection = .rightToLeft
```

These apply to the entire `AttributedString`. To apply to a selection, scope through `transformAttributes(in:body:)`.

## What TextEditor cannot do

Everything below requires a wrapped `UITextView` (or another approach):

- **Inline image attachments.** Genmoji works. Arbitrary images do not — there is no SwiftUI equivalent of `NSTextAttachment`.
- **Lists** (bulleted, numbered) at the editor level. `NSTextList` lives in TextKit and is not exposed.
- **Text tables**. AppKit-only feature, not in TextEditor.
- **Exclusion paths**, multi-column layout, custom layout fragments. Anything that depends on `NSTextLayoutManager` access is out of scope.
- **Syntax highlighting** with custom rendering attributes. Limited styling is possible via attributes; full TextKit-backed highlighting is not.
- **Full first-responder control.** Programmatically focusing or dismissing the keyboard is less reliable than `becomeFirstResponder()` on a `UITextView`.
- **Custom input accessory views.** No `inputAccessoryView` equivalent; the SwiftUI keyboard toolbar is the substitute.
- **Spell-check customization** beyond `UITextInputTraits` defaults.
- **Custom context menus on tapped text items.** `UITextItemInteraction`-style customization is not exposed.
- **Writing Tools delegate control.** The default behavior is on; full coordinator integration requires `UITextView`.
- **iOS 25 and earlier.** Plain text only.

This list is the production gap. For a notes app, comment field, or simple rich-text input on iOS 26+, TextEditor is genuinely usable. For a document editor, code editor, or anything with attachments, lists, or TextKit access, a wrapped `UITextView` remains the correct path.

The maturity gap is also real. This is a first-generation API — edge cases in undo behavior, paste formatting, complex formatting interactions, and SwiftData persistence have surfaced through the beta cycle. Treat TextEditor's rich-text path as additive: usable when the requirements fit, not a wholesale replacement for `UITextView` wrappers in shipping apps.

## Migrating from a UITextView wrapper

If an existing wrapper does roughly what TextEditor now does, evaluate migration before rewriting:

- **List the formatting requirements.** Walk through what the wrapper actually applies to the text (bold, italic, underline, alignment, line height, colors, fonts, etc.) and check each against TextEditor's capability set. Anything not in the supported list — attachments, lists, TextKit access — keeps the wrapper.
- **Check the deployment target.** TextEditor with `AttributedString` is iOS 26+. Earlier deployment floors require keeping the wrapper.
- **Audit TextKit usage.** Any reference to `textLayoutManager`, `textStorage`, `layoutManager`, or `NSTextAttachment` means the wrapper stays. These are not exposed through TextEditor.
- **Test edge cases.** Undo behavior across formatting changes, paste from rich-text source apps, VoiceOver navigation, Dynamic Type at accessibility sizes, and external-keyboard shortcuts. The new APIs cover these but the maturity is uneven.
- **Keep the wrapper as fallback.** Don't delete the UIViewRepresentable until the TextEditor path has shipped to production users and survived a few releases. The cost of keeping a wrapper around is low; the cost of regressing rich-text editing for users is not.

When migration succeeds, the SwiftUI side gets cleaner — no `Coordinator`, no `updateUIView` equality dance, no focus bridging. When it fails, you've learned which capability gap matters and the wrapper stays.

## Common mistakes

1. **Assuming TextEditor replaces UITextView in all cases.** It handles common formatting on iOS 26+. It cannot do attachments, lists, TextKit access, custom input accessories, or full first-responder control. For document editors, code editors, or anything with non-trivial rich text, a wrapped `UITextView` is still the right answer. Pick TextEditor based on capability fit, not novelty.

2. **Forgetting `FontResolutionContext` when checking selection state.** SwiftUI fonts are semantic — `.body`, `.headline`, `.system(size:)`. Without resolving against a context, you cannot tell whether the current selection is bold or italic. Read the context from `@Environment(\.fontResolutionContext)` and call `font.resolve(in: context)` to get concrete traits. Toolbar buttons that don't update their selected state are usually missing this resolution step.

3. **Trying to embed inline images.** TextEditor has no `NSTextAttachment` equivalent. Genmoji works because it goes through the keyboard insertion path. Arbitrary `UIImage`s do not. If image embedding is on the requirements list, the path is a wrapped `UITextView`.

4. **Storing AttributedString in SwiftData without custom encoding.** `AttributedString` is `Codable`, but the default encoding strategy may not round-trip every attribute scope. For SwiftData persistence, custom encoding via `@Attribute(.transformable)` or explicit `Codable` configuration is usually needed. Test the round-trip before depending on it.

5. **Mutating the binding outside `transformAttributes(in:body:)`.** Direct mutation of the `AttributedString` binding works for whole-text changes but not for selection-scoped attribute changes. The `transformAttributes` API is what handles selection bounds correctly across the mutation. Direct edits can leave selection in an invalid state.

6. **Quoting API signatures from memory.** This API surface has churned through Xcode point releases. `AttributedTextValueConstraint`, `transformAttributes`, and the formatting-definition shape have all changed at least once. Before writing against any specific signature, fetch the current Apple docs via Sosumi and confirm the type members. Skill content cannot keep up with point releases; the docs can.

## References

- references/latest-apis.md — verified Apple API surface, refresh after Xcode 26.x point releases
- `/skill txt-wrap-textview` — UIViewRepresentable wrappers when TextEditor's limits apply
- `/skill txt-view-picker` — full view selection comparison including TextEditor
- `/skill txt-swiftui-interop` — what SwiftUI Text/TextEditor renders vs ignores
- `/skill txt-attributed-string` — AttributedString model and Foundation conversions
- `/skill txt-writing-tools` — Writing Tools coordinator integration
- [SwiftUI TextEditor](https://sosumi.ai/documentation/swiftui/texteditor)
- [AttributedTextSelection](https://sosumi.ai/documentation/swiftui/attributedtextselection)
- [AttributedTextFormattingDefinition](https://sosumi.ai/documentation/swiftui/attributedtextformattingdefinition)
- [AttributedString](https://sosumi.ai/documentation/foundation/attributedstring)
