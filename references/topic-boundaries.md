# Topic boundaries between sibling skills

These overlaps are deliberate. Each skill stands on its own. Don't merge siblings without a clear reason.

## Debugging vs reference vs catalog

- **`txt-textkit-debug`** — symptom-driven debugging. The user starts with broken behavior and needs to find the cause. Owns: stale layout, editing crashes, generic fallback symptoms, Writing Tools failures, performance regressions, rendering artifacts, content loss.
- **`txt-fallback-triggers`** — the complete TextKit 1 fallback trigger catalog. Owns: every API access that flips a UITextView to TK1, detection patterns, recovery strategies. `txt-textkit-debug` mentions fallback as one symptom; `txt-fallback-triggers` is the exhaustive list.
- **`txt-layout-invalidation`** — the invalidation model itself. Owns: `ensureLayout`, `invalidateLayout`, propagation timing, lazy vs eager layout. `txt-textkit-debug` mentions stale layout as a symptom; this skill owns *how* layout gets invalidated.
- **`txt-audit`** — code-review pass with severity-ranked findings. Owns: pre-release scanning, deprecated API detection, P0/P1 categorization. Symptom-driven debugging belongs in `txt-textkit-debug`, not here.

## TextKit references vs the picker

- **`txt-textkit1`** — TextKit 1 API reference. NSLayoutManager, NSTextStorage primitives, multi-container, glyph APIs.
- **`txt-textkit2`** — TextKit 2 API reference. NSTextLayoutManager, NSTextContentManager, viewport, fragments.
- **`txt-textkit-choice`** — the picker decision and migration risk. Owns: when to use which, what features are TK2-only, migration cost.

## View pickers vs view bridging vs SwiftUI editor

- **`txt-view-picker`** — "which text view should I use" decisions. Owns: capability comparison across SwiftUI Text/TextField/TextEditor, UITextView, NSTextView. Tradeoffs and decision criteria.
- **`txt-wrap-textview`** — wrapping UITextView/NSTextView in SwiftUI via UIViewRepresentable. Owns: binding, focus, sizing, cursor preservation, update loops.
- **`txt-swiftui-interop`** — the boundary-compatibility rules between SwiftUI text types and TextKit attributes. Owns: which attributes survive the boundary, attribute-translation quirks.
- **`txt-swiftui-texteditor`** — the iOS 26 SwiftUI TextEditor for rich-text editing. Owns: when it replaces a UITextView wrapper, what it can and can't do.
- **`txt-appkit-vs-uikit`** — NSTextView vs UITextView capability comparison and porting notes. Macros porting decisions.

## Attributes and formatting

- **`txt-attribute-keys`** — NSAttributedString.Key reference. Owns: the catalog of keys, value types, view-compatibility rules.
- **`txt-attributed-string`** — AttributedString vs NSAttributedString decision and conversions. Owns: which to use, how to convert, defining custom attributes.

## Input

- **`txt-uitextinput`** — full UITextInput / UIKeyInput / NSTextInputClient implementation in custom views. Owns: marked text, selection UI, custom input.
- **`txt-selection-menus`** — selection UI, edit menus, link taps, gestures, cursor appearance. Customization on stock text views, not protocol implementation.
- **`txt-find-replace`** — find/replace UI (UIFindInteraction, NSTextFinder).
- **`txt-spell-autocorrect`** — UITextChecker, NSSpellChecker, UITextInputTraits, text completion.

## Storage

- **`txt-nstextstorage`** — NSTextStorage / NSTextContentStorage / NSTextContentManager subclassing. Owns: processEditing, edited(), delegate hooks, attribute lifecycle.

## Layout details

- **`txt-line-breaking`** — line break mode, hyphenation, truncation, line height, paragraph spacing, tab stops, NSParagraphStyle.
- **`txt-exclusion-paths`** — text wrapping around shapes, multi-column, linked NSTextContainers, NSTextTable.
- **`txt-measurement`** — measuring text size, boundingRect, sizeThatFits, sizing views to fit content.
- **`txt-viewport-rendering`** — viewport layout, line-fragment geometry, rendering attributes, font substitution.
- **`txt-bidi`** — RTL, bidirectional text, Arabic/Hebrew cursor behavior.

## Modern features

- **`txt-writing-tools`** — Writing Tools integration. writingToolsBehavior, UIWritingToolsCoordinator, protected ranges.
- **`txt-dynamic-type`** — Dynamic Type scaling, custom font metrics, content size category changes.
- **`txt-accessibility`** — VoiceOver and accessibility traits in custom text editors. Generic accessibility lives elsewhere; this is text-editor-specific.

## Reference skills

- **`txt-apple-docs`** — official Apple documentation lookup pattern (sosumi.ai / xcrun mcpbridge).
- **`txt-snippets`** — quick recipes for common features (background colors, line numbers, character limits, links, placeholders).
- **`txt-refresh-against-sosumi`** — maintenance sub-skill: refresh time-sensitive `latest-apis.md` companions after Xcode releases.

## Specialized

- **`txt-attachments`** — embedding images, custom views, Genmoji via NSTextAttachment.
- **`txt-core-text`** — Core Text APIs for glyph-level access, custom typesetting, hit testing, font tables.
- **`txt-colors`** — text colors, dark mode, wide-color/HDR.
- **`txt-markdown`** — Markdown in SwiftUI Text and AttributedString.
- **`txt-detectors-tagger`** — NSDataDetector, NLTagger, NLTokenizer, NSString bridging.
- **`txt-regex`** — Swift Regex vs NSRegularExpression, bridging matches to NSRange.
- **`txt-pasteboard`** — copy/cut/paste, format stripping, sanitization.
- **`txt-drag-drop`** — text drag/drop in editors. UITextDraggable, UITextDroppable.
- **`txt-undo`** — undo/redo grouping, coalescing, NSUndoManager.

## When in doubt

Prefer a focused skill with a clear scope over a catch-all. If a question spans two skills, the answer references both. Don't merge.
