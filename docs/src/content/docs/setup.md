---
title: "Setup"
description: "Install the Apple Text plugin or individual skills."
---

Use this page when you are installing Apple Text and choosing the fastest path into the skills.

## Claude Code Quick Start

Apple Text is one collection with multiple entry points. This page helps you pick the right installation surface first:

- **Claude Code plugin** -> native `/apple-text:ask` command flow
- **Generic MCP client** -> `apple_text_route` plus `apple_text_read_skill`
- **Xcode Claude Agent or Codex** -> Apple Text MCP inside Xcode, optionally alongside `xcrun mcpbridge`

### 1. Add the Marketplace

```bash
/plugin marketplace add sitapix/apple-text
```

### 2. Install the Plugin

```bash
/plugin install apple-text@apple-text
```

### 3. Start Using It

Use `/apple-text:ask` for broad Apple text intake, or browse [Skills](/apple-text/skills/) when the subsystem is already clear.

Good first prompts:

- "My UITextView fell back to TextKit 1"
- "Which text view should I use?"
- "How do I wrap UITextView in SwiftUI?"
- "Audit this editor for anti-patterns"
- "What changed in Apple's latest styled text editing docs?"
- "How do I use TextEditor with AttributedString in iOS 26?"

## Advanced Paths

### Use The Repo Directly

```bash
git clone https://github.com/sitapix/apple-text
cd apple-text
```

Use this path when your client can discover skills from a cloned repo or workspace.

If that client exposes commands, start with `/apple-text:ask` for broad Apple text questions.

If it only loads direct skills, open the matching Apple Text skill or copy one focused skill into your local skills folder.

Pick this path when you want the full Apple Text collection available immediately.

### Use The MCP Server

If your tool supports MCP, read [MCP Server](/apple-text/guide/mcp-server/) for local setup and client configuration snippets. In MCP clients, start with `apple_text_route`, then follow the suggested `apple_text_read_skill` call.

For Xcode Claude Agent or Codex, use [Xcode Integration](/apple-text/guide/xcode-integration/).

### Copy Selected Skills

```bash
mkdir -p /path/to/your/project/.agents/skills
cp -R skills/apple-text-views /path/to/your/project/.agents/skills/
```

Pick this path when you already know the subsystem and want a smaller local surface in another workspace.

## What You Get

- **3 commands**: `/apple-text:ask` for plain-language questions.
- **6 agents**: domain reference lookups in isolated context, plus `editor-reference` for code audits.
- **Skills**: browse the [full catalog](/apple-text/skills/) or start from [problem routing](/apple-text/guide/problem-routing/).

## Troubleshooting

- If Apple Text does not appear after install, use `/plugin` and check `Manage and install`.
- If `/apple-text:ask` is unavailable, confirm the plugin is installed from the marketplace flow above.

## Read Next

- [Skills](/apple-text/skills/)
- [Commands](/apple-text/commands/)
- [Agents](/apple-text/agents/)
- [MCP Server](/apple-text/guide/mcp-server/)
- [Problem Routing](/apple-text/guide/problem-routing/)
