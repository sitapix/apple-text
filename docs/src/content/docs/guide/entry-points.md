---
title: "Entry Points"
sidebar:
  order: 6
---

These are the main entry points.

> Start with the smallest entry point that matches the request.

## `/apple-text:ask`

Natural-language entry point for Apple Text. Use when the user has an Apple text question but does not know which skill or agent to invoke.

Good for:

- plain-language prompts
- first-contact questions
- mixed symptoms where the right skill is not obvious yet

## Prominent Skills

### [`apple-text`](/apple-text/skills/apple-text/)

Use when the user clearly has an Apple text-system problem but the right specialist skill is not obvious yet, or when the request mixes TextKit, text views, storage, layout, parsing, and Writing Tools. Reach for this router when you need the next best Apple-text skill, not when the subsystem is already clear.

Best first move:

- Best when the request is broad and the right specialist is not obvious yet.

### [`apple-text-audit`](/apple-text/skills/apple-text-audit/)

Use when the user wants a review-style scan of Apple text code for risks such as TextKit fallback, editing lifecycle bugs, deprecated APIs, performance traps, or Writing Tools breakage. Reach for this when the job is findings from real code, not a symptom-first debug answer or direct API lookup.

Best first move:

- Best when the user wants a guided scan or implementation flow.

### [`apple-text-texteditor-26`](/apple-text/skills/apple-text-texteditor-26/)

Use when building rich-text editing with SwiftUI TextEditor and AttributedString on iOS 26+, or deciding whether the new native APIs are enough versus a UITextView wrapper. Reach for this when the question is specifically about the iOS 26 TextEditor rich-text boundary, not generic SwiftUI wrapping.

Best first move:

- Best when the subsystem is already known and the user needs mechanics or API detail.

### [`apple-text-textkit-diag`](/apple-text/skills/apple-text-textkit-diag/)

Use when the user starts with a broken Apple text symptom such as stale layout, fallback, crashes in editing, rendering artifacts, missing Writing Tools, or large-document slowness. Reach for this when debugging misbehavior, not when reviewing code systematically or looking up APIs.

Best first move:

- Best when something is broken and symptoms are the starting point.

### [`apple-text-views`](/apple-text/skills/apple-text-views/)

Use when the main task is choosing the right Apple text view or deciding whether a problem belongs in SwiftUI text, UIKit/AppKit text views, or TextKit mode. Reach for this when comparing capabilities and tradeoffs, not when implementing a specific wrapper or low-level API.

Best first move:

- Best when the main task is choosing the right API, view, or architecture.

### [`apple-text-apple-docs`](/apple-text/skills/apple-text-apple-docs/)

Use when you need direct access to Apple-authored text-system documentation from the Xcode-bundled for-LLM markdown docs that MCP can expose at runtime, especially for AttributedString updates, styled TextEditor behavior, toolbars near editors, or official Swift diagnostic writeups. Reach for this when Apple’s wording matters more than repo-authored guidance.

Best first move:

- Best when the subsystem is already known and the user needs mechanics or API detail.

## Direct Specialist Skills

These are the next stop once the request is already scoped:

- [`apple-text-attributed-string`](/apple-text/skills/apple-text-attributed-string/): Use when choosing between AttributedString and NSAttributedString, defining custom attributes, converting between them, or deciding which model should own rich text in a feature. Reach for this when the main task is the attributed-string model decision, not low-level formatting catalog lookup.
- [`apple-text-layout-manager-selection`](/apple-text/skills/apple-text-layout-manager-selection/): Use when the main task is choosing between TextKit 1 and TextKit 2, especially NSLayoutManager versus NSTextLayoutManager for performance, migration risk, large documents, or feature fit. Reach for this when the stack choice is still open, not when the user already needs API-level mechanics.
- [`apple-text-swiftui-bridging`](/apple-text/skills/apple-text-swiftui-bridging/): Use when deciding whether a text type or attribute model crosses the SwiftUI and TextKit boundary cleanly, such as AttributedString, NSAttributedString, UITextView, or SwiftUI Text. Reach for this when the main question is interoperability and support boundaries, not wrapper mechanics.
- [`apple-text-fallback-triggers`](/apple-text/skills/apple-text-fallback-triggers/): Use when the user needs to know exactly what makes TextKit 2 fall back to TextKit 1, or wants to audit code for fallback risk before it ships. Reach for this when the question is specifically about compatibility-mode triggers, not general text-system debugging.
- [`apple-text-accessibility`](/apple-text/skills/apple-text-accessibility/): Use when making custom Apple text editors accessible, including VoiceOver behavior, Dynamic Type support in wrapped text views, accessibility value updates during editing, or text-specific accessibility traits and context. Reach for this when the problem is editor accessibility, not general color or sizing guidance alone.
- [`apple-text-drag-drop`](/apple-text/skills/apple-text-drag-drop/): Use when customizing drag and drop in Apple text editors, including UITextDraggable or UITextDroppable, drag previews, multi-line selections, iPhone drag enablement, or custom drop handling in UITextInput views. Reach for this when the task is editor drag-and-drop behavior, not pasteboard-only workflows.
- [`apple-text-find-replace`](/apple-text/skills/apple-text-find-replace/): Use when implementing find and replace in Apple text editors, wiring UIFindInteraction or NSTextFinder, highlighting matches, or handling replace-all efficiently. Reach for this when the task is editor search UX and mechanics, not generic regex parsing alone.
- [`apple-text-interaction`](/apple-text/skills/apple-text-interaction/): Use when customizing text-editor interactions in UIKit, such as selection behavior, edit menus, link taps, gestures, cursor appearance, or long-press actions. Reach for this when the problem is interaction behavior, not custom text input protocol plumbing.
- [`apple-text-pasteboard`](/apple-text/skills/apple-text-pasteboard/): Use when handling copy, cut, and paste in Apple text editors, including stripping formatting, sanitizing rich text, custom pasteboard types, pasted attachments, or NSItemProvider bridging. Reach for this when the problem is pasteboard behavior, not general editor interaction.
- [`apple-text-representable`](/apple-text/skills/apple-text-representable/): Use when embedding UITextView or NSTextView inside SwiftUI and the hard part is wrapper behavior: two-way binding, focus, sizing, cursor preservation, update loops, toolbars, or environment bridging. Reach for this when native SwiftUI text views are not enough, not when choosing between text stacks at a high level.
- [`apple-text-spell-autocorrect`](/apple-text/skills/apple-text-spell-autocorrect/): Use when implementing spell checking, autocorrect, or text completion in Apple text editors, including UITextChecker, NSSpellChecker, UITextInputTraits, or custom correction UI. Reach for this when the problem is spelling or correction behavior, not generic text interaction.
- [`apple-text-undo`](/apple-text/skills/apple-text-undo/): Use when implementing or debugging undo and redo in text editors, especially grouping, coalescing, programmatic edits, or integration with NSTextStorage, NSTextContentManager, or NSUndoManager. Reach for this when the problem is undo behavior, not generic editing lifecycle.
- [`apple-text-writing-tools`](/apple-text/skills/apple-text-writing-tools/): Use when integrating Writing Tools into a native or custom text editor, configuring writingToolsBehavior, adopting UIWritingToolsCoordinator, protecting ranges, or debugging why Writing Tools do not appear. Reach for this when the problem is specifically Writing Tools, not generic editor debugging.
