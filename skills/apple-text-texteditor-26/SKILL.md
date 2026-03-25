---
name: apple-text-texteditor-26
description: Use when building rich-text editing with SwiftUI TextEditor on iOS 26+ or evaluating whether it replaces a UITextView wrapper
license: MIT
---

# SwiftUI TextEditor Rich Text Editing (iOS 26+)

Use this skill when the main question is whether SwiftUI's native TextEditor can handle a rich text editing need, or when implementing the iOS 26 rich text APIs.

## When to Use

- Building a rich text editor in SwiftUI targeting iOS 26+
- Evaluating whether TextEditor is enough or UIViewRepresentable is still needed
- Implementing formatting toolbars with AttributedTextSelection
- Constraining allowed formatting with AttributedTextFormattingDefinition

## Quick Decision

```
Need rich text editing in SwiftUI?
    Target iOS 26+?
        YES → Can TextEditor handle your needs? (see Limitations below)
            YES → Use TextEditor with AttributedString
            NO → UIViewRepresentable wrapping UITextView
        NO → UIViewRepresentable wrapping UITextView (only option)
```

**Default assumption: UIViewRepresentable is still the safer, more capable choice.** TextEditor with AttributedString is new (iOS 26), less battle-tested, and has real limitations. Use it when your needs fit within its capabilities and you don't need backward compatibility.

## Core Guidance

## What's New in iOS 26

TextEditor gained first-class `AttributedString` support, transforming it from plain-text-only to a genuine rich text editor for common formatting needs.

### Basic Rich Text Editing

```swift
struct RichEditor: View {
    @State private var text = AttributedString("Edit this text...")

    var body: some View {
        TextEditor(text: $text)
    }
}
```

Just changing the binding from `String` to `AttributedString` enables:
- Bold/italic/underline keyboard shortcuts (Cmd+B, Cmd+I, Cmd+U)
- Format menu items
- Genmoji insertion from the emoji keyboard

### Selection-Aware Formatting

```swift
struct FormattedEditor: View {
    @State private var text = AttributedString("Select text to format")
    @State private var selection = AttributedTextSelection()

    @Environment(\.fontResolutionContext) private var fontResolutionContext

    var body: some View {
        VStack {
            TextEditor(text: $text, selection: $selection)

            HStack {
                Button(action: toggleBold) {
                    Image(systemName: "bold")
                }
                Button(action: toggleItalic) {
                    Image(systemName: "italic")
                }
                Button(action: toggleUnderline) {
                    Image(systemName: "underline")
                }
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
            if $0.underlineStyle != nil {
                $0.underlineStyle = nil
            } else {
                $0.underlineStyle = .single
            }
        }
    }
}
```

### Key New Types

| Type | Purpose |
|------|---------|
| `AttributedTextSelection` | Two-way binding to user's text selection |
| `AttributedTextFormattingDefinition` | Define allowed formatting scope |
| `AttributedTextValueConstraint` | Constrain which attribute values are permitted |
| `FontResolutionContext` | Resolve semantic `Font` to concrete typographic attributes |
| `DiscontiguousAttributedSubstring` | Non-contiguous selections via `RangeSet` |

### Formatting Constraints

Restrict which formatting users can apply:

```swift
struct MyFormatting: AttributedTextFormattingDefinition {
    typealias Scope = AttributeScopes.SwiftUIAttributes

    // TextEditor probes constraints to determine valid changes
    static let fontWeight = ValueConstraint(
        \.font,
        constraint: { font in
            guard let font else { return nil }
            let weight = font.resolve().weight
            return font.weight(weight == .bold ? .regular : .bold)
        }
    )
}

TextEditor(text: $text, selection: $selection)
    .textFormattingDefinition(MyFormatting.self)
```

### Programmatic Selection Manipulation

```swift
// Replace selected text
text.replaceSelection(&selection, withCharacters: "replacement")

// Replace with attributed content
let styled = AttributedString("styled replacement")
text.replaceSelection(&selection, with: styled)

// Read selection indices
let indices = selection.indices(in: text)
```

### New AttributedString Properties

```swift
// Text alignment (new in iOS 26)
text.alignment = .center

// Line height control
text.lineHeight = .exact(points: 32)
text.lineHeight = .multiple(factor: 1.5)
text.lineHeight = .loose

// Writing direction
text.writingDirection = .rightToLeft
```

## What TextEditor Supports

| Capability | Supported? |
|------------|-----------|
| Bold / italic / underline / strikethrough | Yes |
| Custom fonts and sizes | Yes |
| Foreground and background colors | Yes |
| Text alignment | Yes |
| Line height | Yes |
| Writing direction | Yes |
| Keyboard shortcuts (Cmd+B, etc.) | Yes, automatic |
| Format menu items | Yes, automatic |
| Genmoji | Yes |
| Custom formatting toolbars | Yes, via `AttributedTextSelection` |
| Formatting constraints | Yes, via `AttributedTextFormattingDefinition` |
| Dynamic Type / Dark Mode | Yes, automatic with `Font` |

## What TextEditor Cannot Do

This is where UIViewRepresentable wrapping UITextView is still required:

| Capability | TextEditor | UITextView |
|------------|-----------|------------|
| **Inline image attachments** | No | Yes (NSTextAttachment) |
| **Text tables** | No | Yes (AppKit) |
| **Lists** (bulleted, numbered) | No | Yes (NSTextList, iOS 17+) |
| **Exclusion paths** | No | Yes |
| **TextKit 2 API access** | No | Yes (NSTextLayoutManager) |
| **Custom text layout** | No | Yes (layout fragments) |
| **Syntax highlighting** | Limited | Full (rendering attributes) |
| **First responder control** | Limited | Full (becomeFirstResponder) |
| **Custom context menus on text** | Limited | Full (UITextItemInteraction) |
| **Spell check customization** | No | Yes (UITextInputTraits) |
| **Custom input accessories** | No | Yes (inputAccessoryView) |
| **Writing Tools coordination** | Default only | Full delegate control |
| **iOS 25 and earlier** | No | Yes |
| **Battle-tested in production** | New (iOS 26) | Mature (iOS 2+) |

### The Maturity Gap

TextEditor's rich text support shipped in iOS 26. It is a **first-generation API**:

- Edge cases in formatting interaction are likely
- SwiftData persistence of AttributedString requires manual encoding workarounds
- The constraint system (`AttributedTextValueConstraint`) is sparsely documented
- Complex formatting combinations may not round-trip perfectly
- Third-party library support (RichTextKit, etc.) targets UITextView, not TextEditor

**If your app ships to production and rich text is critical, UIViewRepresentable wrapping UITextView remains the safer choice.** TextEditor is excellent for simpler formatting needs (notes, comments, basic rich text) where the reduced complexity of staying in SwiftUI outweighs the maturity tradeoff.

## Decision Framework

```
Is iOS 26 your minimum deployment target?
    NO → UIViewRepresentable. Stop here.
    YES → Do you need ANY of these?
        - Inline images / attachments
        - TextKit API access
        - Syntax highlighting with custom rendering
        - Complex list or table structures
        - Custom input accessories
        - Full first responder control
        YES to any → UIViewRepresentable
        NO to all → Is rich text mission-critical to your app?
            YES → Consider UIViewRepresentable for maturity
            NO → TextEditor with AttributedString is a good fit
```

## Migrating from UIViewRepresentable

If you have an existing UIViewRepresentable text editor wrapper and want to evaluate migration:

1. **List your formatting requirements** — check against the "Cannot Do" table above
2. **Check your deployment target** — iOS 26+ required
3. **Audit TextKit usage** — any `textLayoutManager`, `textStorage`, or `layoutManager` access means UIViewRepresentable stays
4. **Test edge cases** — undo behavior, paste formatting, VoiceOver, Dynamic Type at accessibility sizes
5. **Keep the wrapper as fallback** — don't delete it until the TextEditor path is fully validated

## Common Pitfalls

1. **Assuming TextEditor replaces UITextView** — It handles common formatting but lacks the full TextKit stack. For anything beyond basic rich text, UITextView is still needed.
2. **Forgetting `fontResolutionContext`** — Without it, you can't check whether the current selection is bold/italic. The resolved font tells you the concrete traits.
3. **SwiftData persistence** — `AttributedString` requires custom `Codable` handling with `@CodableConfiguration` or manual encoding. Not plug-and-play.
4. **No inline images** — There is no SwiftUI equivalent of `NSTextAttachment`. Genmoji works, but arbitrary image embedding does not.
5. **First responder management** — Programmatically focusing the editor or dismissing the keyboard is less controllable than UITextView.

## Related Skills

- Use `/skill apple-text-representable` for UIViewRepresentable wrapping when TextEditor's limitations apply.
- Use `/skill apple-text-apple-docs` for Apple-authored docs access on styled text editing and nearby SwiftUI APIs.
- Use `/skill apple-text-views` for the full view selection decision tree (which this skill updates for iOS 26).
- Use `/skill apple-text-attributed-string` for AttributedString model and conversion patterns.
- Use `/skill apple-text-swiftui-bridging` for what SwiftUI Text renders vs ignores.
