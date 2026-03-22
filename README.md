# Apple Text

Deep text-system expertise for AI coding assistants. Covers TextKit 1 and 2, UITextView, NSTextView, attributed strings, text input, Core Text, Writing Tools, and everything in between.

## What is Apple Text?

Apple Text gives AI coding assistants focused guidance on Apple's text rendering and editing stack, including TextKit behavior, text view selection, attributed text, layout, and Writing Tools integration.

- **39 focused text skills** covering TextKit, views, formatting, storage, input, layout, accessibility, and more
- **5 agents** for isolated reference lookups and autonomous code auditing
- **1 command** for plain-language text questions

> Status: Apple Text is still in an early phase. Some routes, docs, or packaging paths may still be incomplete or wrong. If you hit a bug or something looks off, please open an issue. Feedback is welcome too.

## Quick Start

### Claude Code (native plugin)

```bash
# Add marketplace
/plugin marketplace add sitapix/apple-text

# Install plugin
/plugin install apple-text@apple-text
```

### MCP (VS Code, Cursor, Gemini CLI, and more)

Add to your MCP config:

```json
{
  "mcpServers": {
    "apple-text": {
      "command": "npx",
      "args": ["-y", "@sitapix/apple-text-mcp"]
    }
  }
}
```

Client-specific paths (VS Code, Cursor, Claude Desktop, Gemini CLI) are in the [MCP setup guide](https://sitapix.github.io/apple-text/guide/mcp-install).

### Xcode (Claude Agent / Codex)

See the [Xcode integration guide](https://sitapix.github.io/apple-text/guide/xcode-integration/).

## Getting Started

Skills activate automatically based on your questions. Just ask:

```
"My UITextView fell back to TextKit 1"
"Which text view should I use?"
"How do I wrap UITextView in SwiftUI?"
"Audit this editor for anti-patterns"
"What changed in Apple's latest styled text editing docs?"
"How do I use TextEditor with AttributedString in iOS 26?"
```

You can also use commands directly:

```
/apple-text:ask your question here
/skill apple-text-audit           # scan code for TextKit anti-patterns
/skill apple-text-views           # choose the right text view
/skill apple-text-textkit-diag    # debug broken text behavior
/skill apple-text-recipes         # quick how-do-I snippets
```

## How It Works

39 skills organized into 5 lightweight entry points and 4 domain agents. Entry-point skills load inline for routing and quick answers. Domain agents handle deep API lookups in isolated context — the full reference runs in a separate agent and only the focused answer comes back.

## Documentation

Full documentation, skill catalog, MCP setup, and Xcode integration guides at **[sitapix.github.io/apple-text](https://sitapix.github.io/apple-text/)**.

## Acknowledgments

Apple Text was inspired by [Axiom](https://github.com/CharlesWiltgen/Axiom) by Charles Wiltgen, especially its packaging and documentation structure.

## Contributing

Contributor setup, validation, and release notes live in [`.github/CONTRIBUTING.md`](https://github.com/sitapix/apple-text/blob/main/.github/CONTRIBUTING.md).
