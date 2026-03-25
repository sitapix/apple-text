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

Use when the user has an Apple text-system problem but the right specialist skill is not obvious, or when the request mixes multiple text subsystems.

Best first move:

- Best when the request is broad and the right specialist is not obvious yet.

### [`apple-text-audit`](/apple-text/skills/apple-text-audit/)

Use when reviewing Apple text code for TextKit fallback risk, editing lifecycle bugs, deprecated APIs, or Writing Tools breakage.

Best first move:

- Best when the user wants a guided scan or implementation flow.

### [`apple-text-recipes`](/apple-text/skills/apple-text-recipes/)

Use when building common text features or looking up quick recipes — background colors, line numbers, character limits, links, placeholders.

Best first move:

- Best when the user wants a guided scan or implementation flow.

### [`apple-text-texteditor-26`](/apple-text/skills/apple-text-texteditor-26/)

Use when building rich-text editing with SwiftUI TextEditor on iOS 26+ or evaluating whether it replaces a UITextView wrapper.

Best first move:

- Best when the subsystem is already known and the user needs mechanics or API detail.

### [`apple-text-textkit-diag`](/apple-text/skills/apple-text-textkit-diag/)

Use when debugging broken text — stale layout, editing crashes, fallback, Writing Tools issues, or rendering artifacts.

Best first move:

- Best when something is broken and symptoms are the starting point.

### [`apple-text-views`](/apple-text/skills/apple-text-views/)

Use when choosing between SwiftUI Text/TextField/TextEditor, UITextView, or NSTextView — capabilities and tradeoffs.

Best first move:

- Best when the main task is choosing the right API, view, or architecture.

### [`apple-text-apple-docs`](/apple-text/skills/apple-text-apple-docs/)

Use when you need official Apple-authored documentation, exact API signatures, or Swift diagnostic explanations from Xcode-bundled docs.

Best first move:

- Best when the subsystem is already known and the user needs mechanics or API detail.

## Direct Specialist Skills

These are the next stop once the request is already scoped:

- [`apple-text-attributed-string`](/apple-text/skills/apple-text-attributed-string/): Use when choosing between AttributedString and NSAttributedString, defining custom attributes, or converting between them.
- [`apple-text-layout-manager-selection`](/apple-text/skills/apple-text-layout-manager-selection/): Use when choosing between TextKit 1 and TextKit 2, evaluating migration risk, or comparing NSLayoutManager vs NSTextLayoutManager.
- [`apple-text-swiftui-bridging`](/apple-text/skills/apple-text-swiftui-bridging/): Use when deciding whether a text type or attribute crosses the SwiftUI/TextKit boundary cleanly, or checking interoperability rules.
- [`apple-text-accessibility`](/apple-text/skills/apple-text-accessibility/): Use when implementing VoiceOver, Dynamic Type, or accessibility traits in custom Apple text editors.
- [`apple-text-drag-drop`](/apple-text/skills/apple-text-drag-drop/): Use when customizing drag and drop in Apple text editors — UITextDraggable, UITextDroppable, drag previews, or custom drop handling.
- [`apple-text-find-replace`](/apple-text/skills/apple-text-find-replace/): Use when implementing find and replace in text editors — UIFindInteraction, NSTextFinder, highlighting, or replace-all.
- [`apple-text-interaction`](/apple-text/skills/apple-text-interaction/): Use when customizing selection, edit menus, link taps, gestures, cursor appearance, or long-press actions in text editors.
- [`apple-text-pasteboard`](/apple-text/skills/apple-text-pasteboard/): Use when handling copy, cut, or paste in text editors — format stripping, rich text sanitization, custom pasteboard types.
- [`apple-text-representable`](/apple-text/skills/apple-text-representable/): Use when wrapping UITextView or NSTextView in SwiftUI — binding, focus, sizing, cursor preservation, or update loops.
- [`apple-text-spell-autocorrect`](/apple-text/skills/apple-text-spell-autocorrect/): Use when implementing spell checking, autocorrect, or text completion — UITextChecker, NSSpellChecker, UITextInputTraits.
- [`apple-text-undo`](/apple-text/skills/apple-text-undo/): Use when implementing or debugging undo/redo in text editors — grouping, coalescing, or NSUndoManager integration.
- [`apple-text-writing-tools`](/apple-text/skills/apple-text-writing-tools/): Use when integrating Writing Tools — writingToolsBehavior, UIWritingToolsCoordinator, protected ranges, or inline vs panel mode.
