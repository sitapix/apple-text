#!/usr/bin/env node

/**
 * Generates lightweight domain agent files from skill metadata.
 *
 * Each domain agent carries a routing table and discovery instructions so
 * it can read the relevant skill file(s) on demand, instead of bundling
 * all skill content upfront. This cuts per-spawn token cost from ~25k to
 * ~3-6k while keeping answers focused on the relevant content.
 *
 * Run:  node scripts/build-agents.mjs
 * Check: node scripts/build-agents.mjs --check
 */

import { readFileSync, writeFileSync, existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SKILLS_DIR = join(ROOT, "skills");
const AGENTS_DIR = join(ROOT, "agents");
const CATALOG_PATH = join(SKILLS_DIR, "catalog.json");

// ── Load catalog for keyword aliases ───────────────────────────────────────

const catalog = JSON.parse(readFileSync(CATALOG_PATH, "utf-8"));
const catalogByName = new Map();
for (const entry of catalog.skills) {
  catalogByName.set(entry.name, entry);
}

// ── Domain agent definitions ────────────────────────────────────────────────

const agents = [
  {
    name: "textkit-reference",
    description:
      "Look up TextKit 1/2 APIs, layout mechanics, viewport rendering, text measurement, exclusion paths, fallback triggers, and text storage patterns.",
    skills: [
      "apple-text-textkit1-ref",
      "apple-text-textkit2-ref",
      "apple-text-viewport-rendering",
      "apple-text-layout-invalidation",
      "apple-text-measurement",
      "apple-text-exclusion-paths",
      "apple-text-storage",
      "apple-text-fallback-triggers",
    ],
    preamble: `You answer specific questions about TextKit APIs and runtime behavior.

**You MUST read the relevant skill file before answering.** Do not answer from memory or training knowledge. The skill files contain authoritative, up-to-date reference content that may differ from your training data.

## Instructions

1. Read the user's question carefully.
2. Match it to one or two topics in the routing table below.
3. Use Glob to find the skill file, then Read it. **This step is mandatory — never skip it.**
4. Answer from the loaded skill content — maximum 40 lines.
5. Include exact API signatures, code examples, and gotchas from the skill file.
6. Do NOT dump all reference material — extract what is relevant.
7. If the question is about choosing between TextKit 1 and TextKit 2, recommend the user consult the apple-text-views or apple-text-layout-manager-selection skill instead.`,
  },
  {
    name: "editor-reference",
    description:
      "Look up editor feature APIs — Writing Tools, text interaction, text input, undo/redo, find/replace, pasteboard, spelling, drag-and-drop, accessibility, and Dynamic Type.",
    skills: [
      "apple-text-writing-tools",
      "apple-text-interaction",
      "apple-text-input-ref",
      "apple-text-undo",
      "apple-text-find-replace",
      "apple-text-pasteboard",
      "apple-text-spell-autocorrect",
      "apple-text-drag-drop",
      "apple-text-accessibility",
      "apple-text-dynamic-type",
    ],
    preamble: `You answer specific questions about text editor features and interaction APIs.

**You MUST read the relevant skill file before answering.** Do not answer from memory or training knowledge. The skill files contain authoritative, up-to-date reference content that may differ from your training data.

## Instructions

1. Read the user's question carefully.
2. Match it to one or two topics in the routing table below.
3. Use Glob to find the skill file, then Read it. **This step is mandatory — never skip it.**
4. Answer from the loaded skill content — maximum 40 lines.
5. Include exact API signatures, code examples, and gotchas from the skill file.
6. Do NOT dump all reference material — extract what is relevant.`,
  },
  {
    name: "rich-text-reference",
    description:
      "Look up attributed string APIs, text formatting attributes, colors, Markdown rendering, text attachments, line breaking, and bidirectional text.",
    skills: [
      "apple-text-attributed-string",
      "apple-text-formatting-ref",
      "apple-text-colors",
      "apple-text-markdown",
      "apple-text-attachments-ref",
      "apple-text-line-breaking",
      "apple-text-bidi",
    ],
    preamble: `You answer specific questions about rich text modeling, formatting, and content attributes.

**You MUST read the relevant skill file before answering.** Do not answer from memory or training knowledge. The skill files contain authoritative, up-to-date reference content that may differ from your training data.

## Instructions

1. Read the user's question carefully.
2. Match it to one or two topics in the routing table below.
3. Use Glob to find the skill file, then Read it. **This step is mandatory — never skip it.**
4. Answer from the loaded skill content — maximum 40 lines.
5. Include exact API signatures, code examples, and gotchas from the skill file.
6. Do NOT dump all reference material — extract what is relevant.
7. When the user needs to choose between AttributedString and NSAttributedString, include the trade-off summary.`,
  },
  {
    name: "platform-reference",
    description:
      "Look up SwiftUI bridging, UIViewRepresentable wrappers, TextEditor iOS 26+, AppKit vs UIKit differences, TextKit 1 vs 2 selection, Core Text, Foundation text utilities, and parsing.",
    skills: [
      "apple-text-representable",
      "apple-text-swiftui-bridging",
      "apple-text-texteditor-26",
      "apple-text-appkit-vs-uikit",
      "apple-text-layout-manager-selection",
      "apple-text-apple-docs",
      "apple-text-core-text",
      "apple-text-foundation-ref",
      "apple-text-parsing",
    ],
    preamble: `You answer specific questions about platform choices, SwiftUI bridging, and low-level text utilities.

**You MUST read the relevant skill file before answering.** Do not answer from memory or training knowledge. The skill files contain authoritative, up-to-date reference content that may differ from your training data.

## Instructions

1. Read the user's question carefully.
2. Match it to one or two topics in the routing table below.
3. Use Glob to find the skill file, then Read it. **This step is mandatory — never skip it.**
4. Answer from the loaded skill content — maximum 40 lines.
5. Include exact API signatures, code examples, and gotchas from the skill file.
6. Do NOT dump all reference material — extract what is relevant.
7. For "which view should I use" questions, start with the view selection guidance.`,
  },
];

// ── Skills that remain registered (keep as `/skill` references) ─────────────

const registeredSkills = new Set([
  "apple-text",
  "apple-text-audit",
  "apple-text-views",
  "apple-text-textkit-diag",
  "apple-text-recipes",
]);

// ─��� Skill-to-agent mapping (for cross-references) ───────────────────────────

const skillToAgent = new Map();
for (const agent of agents) {
  for (const skill of agent.skills) {
    skillToAgent.set(skill, agent.name);
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Read the description from a skill's SKILL.md frontmatter.
 */
function readSkillDescription(skillName) {
  const path = join(SKILLS_DIR, skillName, "SKILL.md");
  if (!existsSync(path)) {
    console.error(`  ⚠ Skill not found: ${path}`);
    return "";
  }
  const raw = readFileSync(path, "utf-8");
  const match = raw.match(/^---\n[\s\S]*?description:\s*(.+)\n[\s\S]*?\n---/);
  return match ? match[1].trim() : skillName;
}

/**
 * Detect sidecar .md files in a skill directory (files other than SKILL.md).
 */
function detectSidecars(skillName) {
  const dir = join(SKILLS_DIR, skillName);
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith(".md") && f !== "SKILL.md")
    .sort();
}

/**
 * Get keyword aliases from catalog.json for a skill.
 */
function getKeywords(skillName) {
  const entry = catalogByName.get(skillName);
  if (!entry || !entry.aliases) return [];
  return entry.aliases;
}

/**
 * Build a routing table row for a single skill.
 */
function buildRoutingRow(skillName) {
  const desc = readSkillDescription(skillName);
  const keywords = getKeywords(skillName);
  const sidecars = detectSidecars(skillName);

  // Derive a readable topic label from the skill name
  const topic = skillName
    .replace("apple-text-", "")
    .replace(/-/g, " ")
    .replace(/\bref\b/, "reference");

  const keywordStr = keywords.length > 0 ? keywords.join(", ") : "—";
  const sidecarStr =
    sidecars.length > 0 ? sidecars.join(", ") : "—";

  return `| ${topic} | ${keywordStr} | \`${skillName}\` | ${sidecarStr} |`;
}

/**
 * Build cross-reference section listing registered skills and other agents.
 */
function buildCrossReferences(currentAgentName) {
  const lines = [];

  lines.push("## Cross-References");
  lines.push("");

  // Registered skills
  for (const skill of registeredSkills) {
    const entry = catalogByName.get(skill);
    if (entry) {
      const desc = readSkillDescription(skill);
      lines.push(`- \`/skill ${skill}\` — ${desc}`);
    }
  }
  lines.push("");

  // Other domain agents
  for (const agent of agents) {
    if (agent.name !== currentAgentName) {
      lines.push(
        `- **${agent.name}** agent — ${agent.description}`,
      );
    }
  }

  return lines.join("\n");
}

/**
 * Build the complete agent file content.
 */
function buildAgent(agent) {
  const frontmatter = [
    "---",
    `name: ${agent.name}`,
    `description: ${agent.description}`,
    "model: sonnet",
    "tools:",
    "  - Glob",
    "  - Grep",
    "  - Read",
    "  - Bash",
    "---",
  ].join("\n");

  const heading = `# ${agent.name
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ")} Agent`;

  // Routing table
  const tableHeader = [
    "## Routing Table",
    "",
    "| Topic | Keywords | Skill | Sidecars |",
    "|-------|----------|-------|----------|",
  ].join("\n");

  const tableRows = agent.skills.map(buildRoutingRow).join("\n");

  const discoveryInstructions = `## Required Workflow

Your FIRST action on every question must be to locate and read the relevant skill file — before writing any text. You do not have the reference content in your instructions. It lives in external skill files that you must load.

1. Match the question to one or two skill names in the routing table.
2. **Discover the skills directory** — run this Bash command once, before your first Read:
   \`\`\`bash
   find "$HOME/.claude/plugins/marketplaces" -path "*/skills/apple-text-*/SKILL.md" 2>/dev/null | head -1 | sed 's|/apple-text-[^/]*/SKILL.md$||'
   \`\`\`
   Save the output as your skills base path (e.g. \`/Users/me/.claude/plugins/.../skills\`). If empty, fall back to \`skills\` in the current working directory (local development).
3. **Read the skill file**: \`{skills-base}/{skill-name}/SKILL.md\`
4. Write your answer using the loaded content. Maximum 40 lines.

If the Sidecars column lists additional files, they are in the same directory as SKILL.md. Read sidecars only when the primary file is insufficient.

**Never load more than 3 files.** For broad questions, answer from the most relevant skill and suggest follow-ups.

**You have NO reference content embedded in these instructions.** If you answer without reading a file, your answer will lack the Apple-specific gotchas and edge cases that make it valuable.`;

  const crossRefs = buildCrossReferences(agent.name);

  const body = [
    frontmatter,
    "",
    heading,
    "",
    agent.preamble,
    "",
    discoveryInstructions,
    "",
    tableHeader,
    tableRows,
    "",
    crossRefs,
    "", // trailing newline
  ].join("\n");

  return body;
}

// ── Main ────────────────────────────────────────────────────────────────────

const checkMode = process.argv.includes("--check");

if (checkMode) {
  let stale = 0;
  for (const agent of agents) {
    const expected = buildAgent(agent);
    const outPath = join(AGENTS_DIR, `${agent.name}.md`);
    if (!existsSync(outPath)) {
      console.error(`Missing agent file: ${outPath}`);
      stale++;
      continue;
    }
    const actual = readFileSync(outPath, "utf-8");
    if (actual !== expected) {
      console.error(`Stale agent file: agents/${agent.name}.md`);
      stale++;
    }
  }
  if (stale > 0) {
    console.error(
      `\nERROR: ${stale} agent file(s) out of date. Run: node scripts/build-agents.mjs`,
    );
    process.exit(1);
  }
  console.log("Agent files are up to date.");
  process.exit(0);
}

console.log("Building domain agents from skills...\n");

for (const agent of agents) {
  const output = buildAgent(agent);
  const outPath = join(AGENTS_DIR, `${agent.name}.md`);
  writeFileSync(outPath, output, "utf-8");

  const lineCount = output.split("\n").length;
  const charCount = output.length;
  console.log(
    `  ✓ ${agent.name}.md (${lineCount} lines, ~${Math.round(charCount / 4)} tokens, ${agent.skills.length} skills)`,
  );
}

console.log("\nDone. Agent files written to agents/");
