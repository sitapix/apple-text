# Apple Text

Deep text-system expertise skills. Covers TextKit 1 and 2, UITextView, NSTextView, attributed strings, text input, Core Text, and Writing Tools.

## Install

### Recommended: any agent via [skills CLI](https://github.com/vercel-labs/skills)

```sh
# Interactive picker for skills and agents
npx skills add sitapix/apple-text

# Install everything
npx skills add sitapix/apple-text --all

# Install specific skills
npx skills add sitapix/apple-text --skill txt-views --skill txt-recipes
npx skills add sitapix/apple-text --skill txt-writing-tools

# Check for and apply updates
npx skills check
npx skills update
```

### Claude Code (plugin marketplace)

```sh
# Add the marketplace
/plugin marketplace add sitapix/apple-text

# Install the plugin
/plugin install apple-text@apple-text
```

## Skills

### Routing & Diagnostics

| Skill | What it covers |
|-------|----------------|
| [txt-audit](skills/txt-audit/) | Review code for TextKit fallback risk, editing-lifecycle bugs, deprecated APIs |
| [txt-textkit-debug](skills/txt-textkit-debug/) | Debug stale layout, editing crashes, fallback, Writing Tools issues, rendering artifacts |
| [txt-fallback-triggers](skills/txt-fallback-triggers/) | TextKit 2 → 1 fallback catalog, detection, and recovery |
| [txt-recipes](skills/txt-recipes/) | Quick snippets for background colors, line numbers, character limits, links, placeholders |

### Choosing the Right API

| Skill | What it covers |
|-------|----------------|
| [txt-views](skills/txt-views/) | Choose between SwiftUI Text/TextField/TextEditor, UITextView, or NSTextView |
| [txt-textkit-choice](skills/txt-textkit-choice/) | TextKit 1 vs TextKit 2 decisions and migration risk |
| [txt-attributed-string](skills/txt-attributed-string/) | AttributedString vs NSAttributedString, custom attributes, conversions |
| [txt-appkit-vs-uikit](skills/txt-appkit-vs-uikit/) | NSTextView vs UITextView capability comparison and porting notes |
| [txt-swiftui-texteditor](skills/txt-swiftui-texteditor/) | SwiftUI TextEditor on iOS 26+ — when it replaces a UITextView wrapper |

### TextKit & Layout

| Skill | What it covers |
|-------|----------------|
| [txt-textkit1](skills/txt-textkit1/) | TextKit 1 APIs — NSLayoutManager, NSTextStorage, NSTextContainer, glyphs |
| [txt-textkit2](skills/txt-textkit2/) | TextKit 2 APIs — NSTextLayoutManager, NSTextContentManager, viewport, fragments |
| [txt-storage](skills/txt-storage/) | NSTextStorage, NSTextContentStorage, processEditing, delegate hooks |
| [txt-viewport-rendering](skills/txt-viewport-rendering/) | Viewport layout, fragment geometry, rendering attributes, font substitution |
| [txt-layout-invalidation](skills/txt-layout-invalidation/) | ensureLayout, invalidateLayout, debugging stale layout in TextKit 1 and 2 |
| [txt-exclusion-paths](skills/txt-exclusion-paths/) | Wrap text around shapes, multi-column, linked containers, NSTextTable |
| [txt-line-breaking](skills/txt-line-breaking/) | Line break mode, hyphenation, truncation, line height, paragraph spacing, tab stops |
| [txt-measurement](skills/txt-measurement/) | Measure text size, boundingRect, sizing views to fit content |
| [txt-core-text](skills/txt-core-text/) | Glyph-level access, custom typesetting, hit testing, font tables |

### Attributed Text & Formatting

| Skill | What it covers |
|-------|----------------|
| [txt-formatting](skills/txt-formatting/) | NSAttributedString.Key values, underline styles, shadows, lists, tables |
| [txt-attachments](skills/txt-attachments/) | Embed images, custom views, Genmoji — NSTextAttachment, view providers, baseline |
| [txt-markdown](skills/txt-markdown/) | Markdown in SwiftUI Text and AttributedString, PresentationIntent, rendering gaps |
| [txt-colors](skills/txt-colors/) | Text colors, semantic colors, dark mode, wide-color/HDR across UIKit, AppKit, SwiftUI |
| [txt-foundation-utils](skills/txt-foundation-utils/) | NSRegularExpression, NSDataDetector, NLTagger, NLTokenizer, NSString bridging |

### Editing & Interaction

| Skill | What it covers |
|-------|----------------|
| [txt-interaction](skills/txt-interaction/) | Selection, edit menus, link taps, gestures, cursor appearance, long-press actions |
| [txt-find-replace](skills/txt-find-replace/) | UIFindInteraction, NSTextFinder, highlighting, replace-all |
| [txt-undo](skills/txt-undo/) | Undo/redo grouping, coalescing, NSUndoManager integration |
| [txt-pasteboard](skills/txt-pasteboard/) | Copy/cut/paste, format stripping, rich text sanitization, custom pasteboard types |
| [txt-drag-drop](skills/txt-drag-drop/) | UITextDraggable, UITextDroppable, drag previews, custom drop handling |
| [txt-spell-autocorrect](skills/txt-spell-autocorrect/) | UITextChecker, NSSpellChecker, UITextInputTraits, text completion |

### Input & Internationalization

| Skill | What it covers |
|-------|----------------|
| [txt-input](skills/txt-input/) | UITextInput, UIKeyInput, NSTextInputClient, marked text, custom input |
| [txt-bidi](skills/txt-bidi/) | Bidirectional text, RTL languages, writing direction, cursor behavior |
| [txt-parsing](skills/txt-parsing/) | Swift Regex vs NSRegularExpression, bridging to NSRange |

### SwiftUI Bridging

| Skill | What it covers |
|-------|----------------|
| [txt-swiftui-bridging](skills/txt-swiftui-bridging/) | When a text type or attribute crosses the SwiftUI/TextKit boundary cleanly |
| [txt-representable](skills/txt-representable/) | Wrap UITextView/NSTextView in SwiftUI — binding, focus, sizing, cursor preservation |

### Modern Features & Accessibility

| Skill | What it covers |
|-------|----------------|
| [txt-writing-tools](skills/txt-writing-tools/) | Writing Tools — writingToolsBehavior, UIWritingToolsCoordinator, protected ranges |
| [txt-dynamic-type](skills/txt-dynamic-type/) | Dynamic Type scaling, custom font metrics, content size category changes |
| [txt-accessibility](skills/txt-accessibility/) | VoiceOver, Dynamic Type, accessibility traits in custom Apple text editors |
| [txt-apple-docs](skills/txt-apple-docs/) | Apple-authored docs, exact API signatures, Swift diagnostic explanations |

## Getting Started

Skills activate from your questions. Ask your assistant:

```
"My UITextView fell back to TextKit 1"
"Which text view should I use?"
"How do I wrap UITextView in SwiftUI?"
"Audit this editor for anti-patterns"
"What changed in Apple's latest styled text editing docs?"
"How do I use TextEditor with AttributedString in iOS 26?"
```

Or invoke a skill directly:

```
/txt-audit          # scan code for TextKit anti-patterns
/txt-views          # choose the right text view
/txt-textkit-debug  # debug broken text behavior
/txt-recipes        # quick how-do-I snippets
```

Installed via the Claude Code plugin marketplace? Prefix each command with `apple-text:` — e.g. `/apple-text:txt-audit`.

## Acknowledgments

Apple Text borrows its packaging and documentation patterns from [Axiom](https://github.com/CharlesWiltgen/Axiom) by Charles Wiltgen.
