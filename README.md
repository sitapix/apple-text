# Apple Text

Deep text-system expertise for AI coding assistants. Covers TextKit 1 and 2, UITextView, NSTextView, attributed strings, text input, Core Text, Writing Tools, and everything in between.

## What is Apple Text?

Apple Text gives AI coding assistants focused guidance on Apple's text rendering and editing stack, including TextKit behavior, text view selection, attributed text, layout, and Writing Tools integration.

- **35 focused text skills** covering TextKit, views, formatting, storage, input, layout, accessibility, and more
- **1 agent** for autonomous code auditing (fallback triggers, editing lifecycle bugs, deprecated APIs)
- **1 command** for plain-language text questions

> Status: Apple Text is still in an early phase. Some routes, docs, or packaging paths may still be incomplete or wrong. If you hit a bug or something looks off, please open an issue. Feedback is welcome too.

## Quick Start

Apple Text is one collection with three practical entry points:

- **Claude Code plugin** for the native `/plugin` and `/apple-text:ask` flow
- **MCP server** for VS Code, Cursor, Gemini CLI, Claude Desktop, and similar clients
- **Xcode via MCP** for Claude Agent or Codex inside Xcode

### 1. Add the Marketplace

```bash
/plugin marketplace add sitapix/apple-text
```

### 2. Install the Plugin

Use `/plugin` to open the plugin menu, search for `apple-text`, then install it.

### 3. Verify Installation

Use `/plugin`, then open `Manage and install`. Apple Text should be listed there.

### 4. Use Skills

Skills are suggested automatically in Claude Code based on your question and context. Start with prompts like these:

```
"My UITextView fell back to TextKit 1"
"Which text view should I use?"
"How do I wrap UITextView in SwiftUI?"
"Audit this editor for anti-patterns"
"What changed in Apple's latest styled text editing docs?"
"How do I use TextEditor with AttributedString in iOS 26?"
```

The default starting point for broad questions is `/apple-text:ask`.

```
/apple-text:ask your question here
```

## Other Ways to Use Apple Text

### Xcode Via MCP

For Claude Agent or Codex inside Xcode, use the dedicated [Xcode integration guide](https://sitapix.github.io/apple-text/guide/xcode-integration/).

Run Apple Text for text-system guidance and `xcrun mcpbridge` alongside it if you also want Xcode actions.

### Repo Clone For Agent Skills Clients

```bash
git clone https://github.com/sitapix/apple-text
cd apple-text
```

Use this path when your client can discover skills from a cloned repo or workspace.

If that client exposes commands, start with `/apple-text:ask` for broad Apple text questions.

If it only loads direct skills, open the matching Apple Text skill or copy one focused skill into your local skills folder.

### Standalone MCP Server

If your coding tool supports Model Context Protocol, use the standalone MCP package in `mcp-server/`.

Setup and client configuration examples for Claude Desktop, Cursor, VS Code, and Gemini CLI are in [`mcp-server/README.md`](https://github.com/sitapix/apple-text/blob/main/mcp-server/README.md).

### Copy Specific Skills Elsewhere

```bash
mkdir -p /path/to/your/project/.agents/skills
cp -R skills/apple-text-views /path/to/your/project/.agents/skills/
```


## Troubleshooting

- If Apple Text does not appear after install, use `/plugin` and check `Manage and install` first.
- If `/apple-text:ask` is unavailable, confirm the plugin is installed from the marketplace flow above.

## Start Here

- **`/skill apple-text`** — Use when the user clearly has an Apple text-system problem but the right specialist skill is not obvious yet, or when the request mixes TextKit, text views, storage, layout, parsing, and Writing Tools. Reach for this router when you need the next best Apple-text skill, not when the subsystem is already clear.
- **`/skill apple-text-audit`** — Use when the user wants a review-style scan of Apple text code for risks such as TextKit fallback, editing lifecycle bugs, deprecated APIs, performance traps, or Writing Tools breakage. Reach for this when the job is findings from real code, not a symptom-first debug answer or direct API lookup.
- **`/skill apple-text-texteditor-26`** — Use when building rich-text editing with SwiftUI TextEditor and AttributedString on iOS 26+, or deciding whether the new native APIs are enough versus a UITextView wrapper. Reach for this when the question is specifically about the iOS 26 TextEditor rich-text boundary, not generic SwiftUI wrapping.
- **`/skill apple-text-textkit-diag`** — Use when the user starts with a broken Apple text symptom such as stale layout, fallback, crashes in editing, rendering artifacts, missing Writing Tools, or large-document slowness. Reach for this when debugging misbehavior, not when reviewing code systematically or looking up APIs.
- **`/skill apple-text-views`** — Use when the main task is choosing the right Apple text view or deciding whether a problem belongs in SwiftUI text, UIKit/AppKit text views, or TextKit mode. Reach for this when comparing capabilities and tradeoffs, not when implementing a specific wrapper or low-level API.
- **`/skill apple-text-apple-docs`** — Use when you need direct access to Apple-authored text-system documentation from the Xcode-bundled for-LLM markdown docs that MCP can expose at runtime, especially for AttributedString updates, styled TextEditor behavior, toolbars near editors, or official Swift diagnostic writeups. Reach for this when Apple’s wording matters more than repo-authored guidance.

## Skill Families

Choose the topic family first. The skill role (`router`, `workflow`, `diag`, `decision`, `ref`) is the second pass.

- **Front Door Skills** — Start here when the request is broad, needs triage, or should route through the shortest high-signal entry point. Includes `/skill apple-text`, `/skill apple-text-audit`, `/skill apple-text-textkit-diag`, `/skill apple-text-apple-docs`.
- **View And Stack Decisions** — Use these when the main job is choosing the right text view, platform surface, or TextKit stack. Includes `/skill apple-text-views`, `/skill apple-text-layout-manager-selection`, `/skill apple-text-appkit-vs-uikit`.
- **SwiftUI And Wrapper Boundaries** — Use these when the hard part is crossing between SwiftUI and UIKit or AppKit text systems. Includes `/skill apple-text-texteditor-26`, `/skill apple-text-representable`, `/skill apple-text-swiftui-bridging`.
- **TextKit Runtime And Layout** — Use these for fallback behavior, layout invalidation, viewport rendering, and direct TextKit runtime mechanics. Includes `/skill apple-text-fallback-triggers`, `/skill apple-text-layout-invalidation`, `/skill apple-text-textkit1-ref`, `/skill apple-text-textkit2-ref`, `/skill apple-text-viewport-rendering`.
- **Editor Features And Interaction** — Use these for editing behaviors such as Writing Tools, undo, input, interaction, accessibility, and clipboard flows. Includes `/skill apple-text-accessibility`, `/skill apple-text-drag-drop`, `/skill apple-text-find-replace`, `/skill apple-text-interaction`, `/skill apple-text-pasteboard`, `/skill apple-text-spell-autocorrect`, `/skill apple-text-undo`, `/skill apple-text-writing-tools`, `/skill apple-text-dynamic-type`, `/skill apple-text-input-ref`.
- **Rich Text And Formatting** — Use these when the work centers on attributed content, formatting attributes, attachments, colors, or Markdown semantics. Includes `/skill apple-text-attributed-string`, `/skill apple-text-attachments-ref`, `/skill apple-text-colors`, `/skill apple-text-formatting-ref`, `/skill apple-text-markdown`.
- **Text Model And Foundation Utilities** — Use these for storage, parsing, Core Text, bidirectional text, and Foundation or NaturalLanguage text utilities. Includes `/skill apple-text-storage`, `/skill apple-text-bidi`, `/skill apple-text-core-text`, `/skill apple-text-foundation-ref`, `/skill apple-text-parsing`.

## Documentation

Full documentation, skill catalog, MCP setup, and Xcode integration guides are at [sitapix.github.io/apple-text](https://sitapix.github.io/apple-text/).

## Acknowledgments

Apple Text was inspired by [Axiom](https://github.com/CharlesWiltgen/Axiom) by Charles Wiltgen, especially its packaging and documentation structure.

## Contributing

Contributor setup, validation, and release notes live in [`.github/CONTRIBUTING.md`](https://github.com/sitapix/apple-text/blob/main/.github/CONTRIBUTING.md).
