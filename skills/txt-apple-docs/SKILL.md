---
name: txt-apple-docs
description: Use when you need official Apple-authored documentation, exact API signatures, or Swift diagnostic explanations from Xcode-bundled docs
license: MIT
---

# Apple Documentation Access

Router skill providing direct access to Apple's official for-LLM markdown documentation bundled inside Xcode.

Use this skill when you want Apple-authored guidance from the Xcode-bundled Apple docs that MCP can expose at runtime, rather than only repo-authored summaries.

## When to Use

- You need the exact API signature or behavior from Apple.
- A Swift compiler diagnostic needs explanation with examples.
- Another Apple Text skill references an Apple framework and you want the official source.
- You want authoritative code examples for `AttributedString`, styled `TextEditor`, toolbar behavior, or related text-system changes that ship in Xcode docs.

Priority: Apple Text skills provide opinionated guidance and project-specific tradeoffs. Apple docs provide authoritative API detail. Use both together.

## Quick Decision

- Need opinionated guidance, not Apple's exact wording -> use the relevant Apple Text skill directly
- Need symptom-first debugging -> `/skill txt-textkit-debug`
- Need Apple-authored API detail or Swift diagnostic explanation -> stay here

## Example Prompts

- "What does Apple's AttributedString update doc say about the newest Foundation text changes?"
- "Show me Apple's official guidance for styled TextEditor editing."
- "What does the Swift diagnostic `actor-isolated-call` mean?"
- "What Apple-authored docs ship in Xcode for text and editor-adjacent APIs?"

## What's Covered

### Apple Guide Topics

- `AttributedString` updates and Foundation text changes.
- SwiftUI styled text editing behavior.
- Toolbar features near editing and text-centric UI.
- The checked-in sidecar index at [xcode-docs-index.md](references/xcode-docs-index.md) listing the local Apple-text subset and the bundled Swift diagnostics catalog.

### Swift Compiler Diagnostics

- Official explanations with examples for Swift diagnostics bundled in the Xcode toolchain.
- Especially useful when concurrency or type-system diagnostics intersect with text code and editor integrations.

## How It Works

Apple bundles for-LLM markdown documentation inside Xcode at two locations:

- `AdditionalDocumentation` for framework guides and implementation patterns.
- Swift diagnostics for compiler error and warning explanations with examples.

Apple Text can read these files at runtime from the local Xcode installation when `APPLE_TEXT_APPLE_DOCS=true`.

When runtime Apple docs are enabled in the current client, use them first. Treat the checked-in sidecars in this skill as the repo-backed fallback and the fastest local subset for Apple text questions.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `APPLE_TEXT_XCODE_PATH` | `/Applications/Xcode.app` | Custom Xcode path, such as `Xcode-beta.app` |
| `APPLE_TEXT_APPLE_DOCS` | `false` | Set to `true` to enable runtime loading of Apple-authored markdown docs from the local Xcode install |

## Related Skills

- Use `/skill txt-swiftui-texteditor` for project-specific `TextEditor` guidance after reading Apple’s docs results.
- Use `/skill txt-attributed-string` for AttributedString vs NSAttributedString decisions and conversion strategy.
- Use `/skill txt-writing-tools` when the real problem is Writing Tools integration, not Apple-doc lookup.
- Use `/skill txt-foundation-utils` for broader Foundation text utilities beyond the Xcode-bundled subset.
