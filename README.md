# Apple Text

[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-d97757)](https://code.claude.com)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-blue)](https://github.com/vercel-labs/skills)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Agent Skills for Apple's text stack: TextKit 1 and 2, UITextView, NSTextView, AttributedString, Core Text, Writing Tools, and the iOS 26 SwiftUI TextEditor.

## Install

```sh
# Any agent (Vercel skills CLI)
npx skills add sitapix/apple-text

# Claude Code
/plugin marketplace add sitapix/apple-text
/plugin install apple-text@apple-text
```

For Claude Code installs, prefix slash commands with `apple-text:` (e.g., `/apple-text:txt-audit`).

## Skills

### Diagnostics

| Skill | Covers |
|---|---|
| [txt-audit](skills/txt-audit/) | Severity-ranked code review |
| [txt-textkit-debug](skills/txt-textkit-debug/) | Symptom-driven diagnosis |
| [txt-fallback-triggers](skills/txt-fallback-triggers/) | TextKit 2→1 fallback catalog |
| [txt-snippets](skills/txt-snippets/) | Quick recipes |

### Picking an API

| Skill | Covers |
|---|---|
| [txt-view-picker](skills/txt-view-picker/) | Which text view to use |
| [txt-textkit-choice](skills/txt-textkit-choice/) | TextKit 1 vs 2 |
| [txt-attributed-string](skills/txt-attributed-string/) | AttributedString vs NSAttributedString |
| [txt-appkit-vs-uikit](skills/txt-appkit-vs-uikit/) | NSTextView vs UITextView |
| [txt-swiftui-texteditor](skills/txt-swiftui-texteditor/) | iOS 26 SwiftUI TextEditor |

### TextKit & layout

| Skill | Covers |
|---|---|
| [txt-textkit1](skills/txt-textkit1/) | TextKit 1 reference |
| [txt-textkit2](skills/txt-textkit2/) | TextKit 2 reference |
| [txt-nstextstorage](skills/txt-nstextstorage/) | NSTextStorage subclassing |
| [txt-viewport-rendering](skills/txt-viewport-rendering/) | Viewport, fragments, rendering attributes |
| [txt-layout-invalidation](skills/txt-layout-invalidation/) | The invalidation model |
| [txt-exclusion-paths](skills/txt-exclusion-paths/) | Wrapping around shapes, multi-column |
| [txt-line-breaking](skills/txt-line-breaking/) | Hyphenation, truncation, paragraph spacing |
| [txt-measurement](skills/txt-measurement/) | boundingRect, sizeThatFits |
| [txt-core-text](skills/txt-core-text/) | Glyph-level access |

### Attributes & content

| Skill | Covers |
|---|---|
| [txt-attribute-keys](skills/txt-attribute-keys/) | NSAttributedString.Key catalog |
| [txt-attachments](skills/txt-attachments/) | Inline images, Genmoji |
| [txt-markdown](skills/txt-markdown/) | Markdown in SwiftUI Text and AttributedString |
| [txt-colors](skills/txt-colors/) | Text colors, dark mode, HDR |
| [txt-detectors-tagger](skills/txt-detectors-tagger/) | NSDataDetector, NLTagger, NLTokenizer |

### Editing & input

| Skill | Covers |
|---|---|
| [txt-uitextinput](skills/txt-uitextinput/) | UITextInput / NSTextInputClient |
| [txt-selection-menus](skills/txt-selection-menus/) | Selection UI, edit menus, gestures |
| [txt-find-replace](skills/txt-find-replace/) | UIFindInteraction, NSTextFinder |
| [txt-spell-autocorrect](skills/txt-spell-autocorrect/) | UITextChecker, NSSpellChecker |
| [txt-undo](skills/txt-undo/) | NSUndoManager grouping |
| [txt-pasteboard](skills/txt-pasteboard/) | Copy/cut/paste, format stripping |
| [txt-drag-drop](skills/txt-drag-drop/) | UITextDraggable, UITextDroppable |
| [txt-bidi](skills/txt-bidi/) | RTL, bidirectional text |
| [txt-regex](skills/txt-regex/) | Swift Regex vs NSRegularExpression |

### SwiftUI bridging

| Skill | Covers |
|---|---|
| [txt-swiftui-interop](skills/txt-swiftui-interop/) | What crosses the SwiftUI/TextKit boundary |
| [txt-wrap-textview](skills/txt-wrap-textview/) | UIViewRepresentable around UITextView/NSTextView |

### Modern & maintenance

| Skill | Covers |
|---|---|
| [txt-writing-tools](skills/txt-writing-tools/) | UIWritingToolsCoordinator, behavior, ignored ranges |
| [txt-dynamic-type](skills/txt-dynamic-type/) | UIFontMetrics, adjustsFontForContentSizeCategory |
| [txt-accessibility](skills/txt-accessibility/) | VoiceOver, accessibilityTextualContext |
| [txt-apple-docs](skills/txt-apple-docs/) | Sosumi + `xcrun mcpbridge` |
| [txt-refresh-against-sosumi](skills/txt-refresh-against-sosumi/) | Refresh latest-apis.md after Xcode releases |

## Example prompts

Phrasings that route to the right skill, including ones that don't name the API.

### Diagnose a bug

| Prompt | Triggers |
|---|---|
| "Writing Tools stopped showing the inline rewrite animation — only the floating panel opens now. Started after we added a custom NSTextStorage." | [txt-fallback-triggers](skills/txt-fallback-triggers/) |
| "Lines in our editor sometimes render half-drawn — descenders chopped, characters bleeding into the next paragraph." | [txt-textkit-debug](skills/txt-textkit-debug/) |
| "Cursor jumps to the end every time my SwiftUI binding pushes new text into the wrapped UITextView." | [txt-wrap-textview](skills/txt-wrap-textview/) |
| "Cmd-Z undoes one character at a time after a paste — should be one step." | [txt-undo](skills/txt-undo/) |
| "Diacritics get clipped at the top of my custom NSTextLayoutFragment." | [txt-viewport-rendering](skills/txt-viewport-rendering/) |
| "boundingRect returns a single-line size for multi-line text." | [txt-measurement](skills/txt-measurement/) |
| "Cursor jumps unpredictably when I type Arabic mixed with English." | [txt-bidi](skills/txt-bidi/) |
| "VoiceOver skips punctuation in our code editor." | [txt-accessibility](skills/txt-accessibility/) |

### Pick an API

| Prompt | Triggers |
|---|---|
| "Starting a new code editor — TextKit 1 or TextKit 2?" | [txt-textkit-choice](skills/txt-textkit-choice/) |
| "AttributedString or NSAttributedString for a notes-app model?" | [txt-attributed-string](skills/txt-attributed-string/) |
| "Multi-line search box in SwiftUI — TextField or TextEditor?" | [txt-view-picker](skills/txt-view-picker/) |
| "Porting our Mac editor to iPad — what AppKit features have no UIKit equivalent?" | [txt-appkit-vs-uikit](skills/txt-appkit-vs-uikit/) |

### Build a feature

| Prompt | Triggers |
|---|---|
| "How do I add a placeholder to UITextView?" | [txt-snippets](skills/txt-snippets/) |
| "Wrap article text around an inline circular thumbnail." | [txt-exclusion-paths](skills/txt-exclusion-paths/) |
| "Add cmd-F find UI to my UITextView with replace-all." | [txt-find-replace](skills/txt-find-replace/) |
| "Drop an image into my editor as an inline attachment." | [txt-drag-drop](skills/txt-drag-drop/) |
| "Rewrite is mangling code blocks in our doc editor — protect them from Writing Tools." | [txt-writing-tools](skills/txt-writing-tools/) |
| "Bind AttributedString to TextEditor on iOS 26 with a formatting toolbar." | [txt-swiftui-texteditor](skills/txt-swiftui-texteditor/) |
| "Building a canvas-based code editor and the keyboard / autocorrect / magnifier are wrong." | [txt-uitextinput](skills/txt-uitextinput/) |

### Audit and maintenance

| Prompt | Triggers |
|---|---|
| "Review our text-editor module before we ship — flag fallback risks and deprecated APIs." | [txt-audit](skills/txt-audit/) |
| "Refresh the skills against current Apple docs now that Xcode 26.4 is out." | [txt-refresh-against-sosumi](skills/txt-refresh-against-sosumi/) |
| "Look up the current `AttributedString(markdown:)` initializer signature." | [txt-apple-docs](skills/txt-apple-docs/) |

## Contributing

[`AGENTS.md`](AGENTS.md) covers authoring rules, anti-patterns, and the freshness contract. [`references/topic-boundaries.md`](references/topic-boundaries.md) explains sibling splits. Skill content links to [sosumi.ai](https://sosumi.ai/) instead of `developer.apple.com` (the latter renders with JavaScript and returns a stub to non-browser fetches).
