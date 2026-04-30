# AGENTS.md

This file guides agents authoring or revising skills in this repository.

## Communication style

No AI fluff ("Thanks for the thoughtful feedback!", "Happy to help!"). No trailing solicitation ("Would you like me to…"). State facts, give options when relevant, then stop.

## What this repo is

Apple Text holds Agent Skills for Apple's text-editing stack: TextKit 1, TextKit 2, UITextView, NSTextView, AttributedString, Core Text, Writing Tools, and the SwiftUI text views.

This isn't a buildable app. The work is authoring, refining, and reorganizing skill content. Validation stays editorial and structural.

## Hard limits

- Skill frontmatter: `name` ≤64 chars, `description` ≤1024 chars, body ≤500 lines.
- Aggressive formatting (`MUST` / `NEVER` / `IMPORTANT` calibrated for older models) reduces output quality on the current generation.
- Bloat past the attention budget makes the model ignore all instructions uniformly, not just the new ones. Each line taxes every other line.

## Repo shape

- `skills/<skill>/SKILL.md` — canonical instructions for one skill
- `skills/<skill>/references/*.md` — deeper material, loaded only when the skill points to it
- `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json` — bundle membership
- `README.md` — public catalog
- `CHANGELOG.md` — public-surface history
- `references/topic-boundaries.md` — deliberate splits between sibling skills (do not merge without reason)

## Authoring rules

### Skill structure (preserve unless a skill doesn't fit it)

1. Frontmatter (`name`, `description`, `license`)
2. One-paragraph opening scope statement, including a grounding sentence for diagnostic/reference skills (see below)
3. `## Contents` linking to subject sections
4. Subject-based sections named for the topic, not for a category number
5. `## Common Mistakes` — numbered prose entries with reason + `// WRONG` / `// CORRECT` code blocks where useful
6. `## Review Checklist` — only for skills that guide a fixed procedure (audit, integration); skip for diagnostic/reference skills
7. `## References` — sibling skills + sosumi.ai links

Body length target: 150-300 lines. Hard cap 500.

### Description rules

Agents decide whether to invoke a skill from its description alone. The description has to do real work in ≤1024 chars.

- Lead with a concrete verb. "Diagnose…", "Configure…", "Choose between…" work. "Use when…" is too generic.
- Name the actual frameworks, APIs, or symptoms in the first ~30 chars after the verb so it survives slash-picker truncation.
- End with a "Use when…" clause listing concrete triggers (symptoms, file types, user phrasings).
- Skills under-trigger in practice. Push the description when triggers come up phrased without naming the API: "use whenever the user mentions text layout problems, even if they don't say TextKit."
- Add a "Do NOT use for…" exclusion clause when an adjacent skill competes on keyword overlap. The clause suppresses false triggers more than real ones. Sample: `"…customize text selection, edit menus, link taps, or cursor gestures. Do NOT use for full UITextInput protocol implementation in custom views (see txt-uitextinput)."`

### Anti-patterns

Failure modes I've hit in this repo and others:

1. **Decision trees and "Quick Decision" arrows at the top.** They train the agent to classify and recite the matching row, skipping the user's actual code.
2. **Symptom | Cause | Fix tables** for non-tabular content. Tables compress reasoning into rows the agent recites verbatim. Convert to prose that explains *why* the failure happens. Keep tables only when the data is real tabular data (e.g., "Symbolic breakpoint | What it catches").
3. **Mid-content rerouting** (`→ /skill txt-other`). Trains the agent to re-route instead of commit. Cross-skill links live in `## References` at the bottom.
4. **Redundant "Use this skill when…" preamble.** The description already does this work.
5. **Stale-model imperatives** (`MUST`, `ALWAYS`, `NEVER`, `IMPORTANT:`). They reduce output quality on Claude 4.6+. Explain the *why* and let the model apply judgment.
6. **Numbered checklists for diagnosis.** Right for fixed procedures like deployment runbooks. Wrong for debugging, since the agent walks the checklist instead of the codebase.
7. **Inline date conditionals.** "If before August 2025…" doesn't age. Use a "Current method" section plus a collapsed "Old patterns" section with deprecation dates.

### Grounding directives

Diagnostic and reference skills should include a grounding sentence in the opening paragraph that tells the agent to read the actual code or fetch the actual docs before quoting from the skill. One sentence cuts the "list three plausible causes from memory" failure mode. Example:

> The patterns here are clues, not answers. Before quoting any cause from this document, open the relevant source and verify the actual code matches the pattern.

For tool-bound versions (more effective than vague "verify" prose):

> Before claiming any specific API signature, fetch the current Apple docs via Sosumi (`sosumi.ai/documentation/<framework>/<api>`).

## Freshness contract

Apple ships fast. Training cutoffs lag. Every skill in this repo follows three rules so the content ages well:

1. **Name the target versions.** Every skill's first body line states the platform/Swift/Xcode version it targets. Format: `Authored against iOS 26.x / Swift 6.x / Xcode 26.x.` This dates the content without inline conditionals.

2. **Sosumi.ai is the documentation pipe.** Apple's developer.apple.com pages are JS-rendered; raw fetches return a "needs JavaScript" stub. URL-swap `developer.apple.com` → `sosumi.ai` (same path) for any documentation link in skill content. The Sosumi MCP server at `https://sosumi.ai/mcp` is the runtime fetch tool.

3. **Apple-controlled fallbacks.** When Sosumi 404s or Xcode 26.3+ is available, `xcrun mcpbridge` provides on-machine doc lookup against bundled Xcode docs and indexed WWDC transcripts. Use it to verify a path. Skill content itself links to sosumi.ai URLs so the markdown stays portable.

For time-sensitive skills (`txt-swiftui-texteditor`, `txt-writing-tools`, `txt-textkit2`, `txt-attribute-keys`, `txt-attributed-string`), split fast-changing API signatures into a `references/latest-apis.md` companion. The static SKILL.md gives the mental model. The `latest-apis.md` companion gets refreshed against Sosumi after each Xcode point release.

## Topic boundaries

Some skills overlap by design so each one stands on its own. Don't merge them without reason. `references/topic-boundaries.md` documents what each skill owns and where to draw the line. Read it before merging or retargeting any skill.

## Skill metadata

- `name` matches the folder name.
- `description` follows the rules above (≤1024 chars, verb-first, Use when, optional Do NOT use clause).
- `license: MIT`.
- Custom per-skill fields belong under `metadata:`.

## When adding a skill

1. Create `skills/<skill-name>/SKILL.md` matching frontmatter `name`.
2. Apply the structure pattern.
3. If the skill needs deeper material, add `skills/<skill-name>/references/*.md` and link from SKILL.md with a one-line reason.
4. Add the path to both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
5. Add the row to the appropriate table in `README.md`.
6. Sanity-check by reading the description as if you've never seen the skill. Does it disambiguate from siblings? Does the body answer the question without rerouting?

## When making substantial changes

If you rename a skill, change its scope, or rewrite the body:

- Rename the directory; update `name:` in frontmatter.
- Update cross-references in other `SKILL.md` and `references/*.md` files.
- Update `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `README.md`.
- Add a `CHANGELOG.md` entry when the public surface changes.
- Sanity-check by running a realistic prompt and watching whether the right skill triggers and the body produces the right output.

## Review standard

- Installation is obvious from `README.md`.
- Naming is consistent (every skill `txt-*`, every directory matches frontmatter).
- Descriptions disambiguate at a glance.
- Skills stay self-contained. A skill may mention a sibling but not depend on a sibling's files.
- All Apple documentation links are sosumi.ai URLs that resolve (verify with `curl -s -o /dev/null -w "%{http_code}" <url>`).
- No `developer.apple.com` link targets in skill content (this AGENTS.md is the only allowed reference).

## GitHub release notes

Wrap Swift symbols that start with `@` in backticks (`` `@Observable` ``, `` `@MainActor` ``) in release notes and `CHANGELOG.md` entries. GitHub renders bare `@word` as a user mention.
