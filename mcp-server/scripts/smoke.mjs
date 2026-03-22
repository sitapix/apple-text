import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const mode = process.env.APPLE_TEXT_MCP_SMOKE_MODE === "development" ? "development" : "production";

const transport = new StdioClientTransport({
  command: "node",
  args: ["dist/index.js"],
  cwd: process.cwd(),
  env:
    mode === "development"
      ? {
          APPLE_TEXT_MCP_MODE: "development",
          APPLE_TEXT_DEV_PATH: "..",
          APPLE_TEXT_APPLE_DOCS: "false",
          APPLE_TEXT_MCP_LOG_LEVEL: "error",
          PATH: process.env.PATH ?? "",
          HOME: process.env.HOME ?? "",
        }
      : {
          APPLE_TEXT_APPLE_DOCS: "false",
          APPLE_TEXT_MCP_LOG_LEVEL: "error",
          PATH: process.env.PATH ?? "",
          HOME: process.env.HOME ?? "",
        },
  stderr: "pipe",
});

const client = new Client(
  { name: "apple-text-mcp-smoke", version: "1.0.0" },
  { capabilities: {} },
);

function fail(message) {
  console.error(message);
  process.exitCode = 1;
}

try {
  await client.connect(transport);

  const [tools, resources, prompt] = await Promise.all([
    client.listTools(),
    client.listResources(),
    client.getPrompt({ name: "ask" }),
  ]);

  const toolNames = tools.tools.map((tool) => tool.name);
  const expectedTools = [
    "apple_text_ask",
    "apple_text_route",
    "apple_text_get_catalog",
    "apple_text_search_skills",
    "apple_text_read_skill",
    "apple_text_get_agent",
  ];

  for (const toolName of expectedTools) {
    if (!toolNames.includes(toolName)) {
      throw new Error(`Missing MCP tool: ${toolName}`);
    }
  }

  if (resources.resources.length === 0) {
    throw new Error("No MCP resources were exposed");
  }

  if (!resources.resources.some((resource) => resource.uri === "apple-text://skill/apple-text")) {
    throw new Error("Router skill resource apple-text://skill/apple-text is missing");
  }

  if (!prompt.messages.length) {
    throw new Error('Prompt "ask" returned no messages');
  }

  const askTool = await client.callTool({
    name: "apple_text_ask",
    arguments: {
      question: "How do I choose between UITextView and TextEditor?",
      includeSkillContent: false,
    },
  });

  const askText = askTool.content
    .filter((item) => item.type === "text")
    .map((item) => item.text)
    .join("\n");
  if (!askText.includes("Start with:")) {
    throw new Error("apple_text_ask did not return a routed skill");
  }

  const diagnosticAsk = await client.callTool({
    name: "apple_text_ask",
    arguments: {
      question:
        "A macOS rich text / TextKit editor in dark mode shows newly typed text as black until the next keystroke, then it becomes the expected light color. Logs show typing presentation snapshots where expectedColor and typingColor are correct, but storageColor is nil during insertText preflight and didChangeText.postEdit. What usually causes this, and what should be checked in TextKit / NSTextView / attributed string update flow?",
      includeSkillContent: false,
    },
  });

  const diagnosticAskText = diagnosticAsk.content
    .filter((item) => item.type === "text")
    .map((item) => item.text)
    .join("\n");
  if (!diagnosticAskText.includes("Start with: apple-text-textkit-diag")) {
    throw new Error("apple_text_ask did not route the TextKit symptom prompt to apple-text-textkit-diag");
  }

  // ── Verify routing sends questions to the right skills ──────────────

  // ── Verify routing sends questions to the right skills ──────────────
  // Tests check that the expected skill appears in the top 3 results,
  // not necessarily #1. The router is a valid first result for broad
  // queries — what matters is that the specialist surfaces.

  const routingTests = [
    // Format: [question, expected skill in top 3, description]

    // Entry point skills (should be #1 — these are explicit triggers)
    ["audit my UITextView code for issues", "apple-text-audit", "audit → audit skill", true],
    ["which text view should I use for a chat composer", "apple-text-views", "view choice → views skill", true],
    ["my UITextView layout is stale after editing", "apple-text-textkit-diag", "symptom → diag skill", true],

    // TextKit runtime domain
    ["how to measure text bounding rects with boundingRect", "apple-text-measurement", "measurement → measurement skill", false],
    ["Writing Tools writingToolsBehavior UIWritingToolsCoordinator", "apple-text-writing-tools", "Writing Tools → writing-tools skill", false],
    ["AttributedString vs NSAttributedString custom attributes", "apple-text-attributed-string", "attr string → attributed-string skill", false],
    ["implement undo redo for NSTextStorage edits", "apple-text-undo", "undo → undo skill", false],
    ["NSTextView vs UITextView platform differences", "apple-text-appkit-vs-uikit", "platform comparison → appkit-vs-uikit", false],
    ["exclusionPaths text wrapping around images NSTextContainer", "apple-text-exclusion-paths", "exclusion → exclusion skill", false],
    ["UITextView copy paste pasteboard rich text", "apple-text-pasteboard", "paste → pasteboard skill", false],
    ["VoiceOver accessibility for custom text editor", "apple-text-accessibility", "a11y → accessibility skill", false],
    ["NSTextLayoutManager viewport rendering fragments", "apple-text-textkit2-ref", "TextKit 2 → textkit2-ref", false],
  ];

  let routePassed = 0;
  let routeFailed = 0;
  const routeFailures = [];

  for (const [question, expectedSkill, label, mustBeFirst] of routingTests) {
    const limit = mustBeFirst ? 1 : 3;
    const result = await client.callTool({
      name: "apple_text_route",
      arguments: { question, limit, preferEntrypoints: false },
    });
    const text = result.content
      .filter((item) => item.type === "text")
      .map((item) => item.text)
      .join("\n");

    const found = mustBeFirst
      ? text.includes(`Start with: ${expectedSkill}`)
      : text.includes(expectedSkill);

    if (found) {
      routePassed++;
    } else {
      routeFailed++;
      const startMatch = text.match(/Start with: ([\w-]+)/);
      const actual = startMatch ? startMatch[1] : "unknown";
      const scope = mustBeFirst ? "as #1" : "in top 3";
      routeFailures.push(`  ✗ ${label}: expected ${expectedSkill} ${scope}, got ${actual}`);
    }
  }

  // Fail if more than 25% of routes miss entirely
  const threshold = Math.floor(routingTests.length * 0.75);
  if (routePassed < threshold) {
    throw new Error(
      `Routing accuracy too low: ${routePassed}/${routingTests.length} passed (need ${threshold})\n${routeFailures.join("\n")}`,
    );
  }

  // ── Verify skill content is actually readable (not just metadata) ─────

  const readResult = await client.callTool({
    name: "apple_text_read_skill",
    arguments: {
      skills: [{ name: "apple-text-textkit1-ref" }],
    },
  });

  const readText = readResult.content
    .filter((item) => item.type === "text")
    .map((item) => item.text)
    .join("\n");
  if (!readText.includes("NSLayoutManager")) {
    throw new Error("apple_text_read_skill for textkit1-ref did not return actual skill content (expected NSLayoutManager)");
  }
  if (readText.length < 500) {
    throw new Error(`apple_text_read_skill returned suspiciously short content (${readText.length} chars)`);
  }

  // ── Verify section filtering returns partial content ───────────────────

  const sectionResult = await client.callTool({
    name: "apple_text_read_skill",
    arguments: {
      skills: [{ name: "apple-text-textkit1-ref", sections: ["Core Guidance"] }],
    },
  });

  const sectionText = sectionResult.content
    .filter((item) => item.type === "text")
    .map((item) => item.text)
    .join("\n");
  if (sectionText.length >= readText.length) {
    throw new Error("Section-filtered read was not shorter than full read — filtering may be broken");
  }

  // ── Verify all 5 entry-point skills are readable with real content ────

  const entrySkills = [
    { name: "apple-text", mustContain: "Router" },
    { name: "apple-text-audit", mustContain: "P0" },
    { name: "apple-text-views", mustContain: "UITextView" },
    { name: "apple-text-textkit-diag", mustContain: "Symptom" },
    { name: "apple-text-recipes", mustContain: "func" },
  ];

  for (const { name, mustContain } of entrySkills) {
    const result = await client.callTool({
      name: "apple_text_read_skill",
      arguments: { skills: [{ name }] },
    });
    const text = result.content
      .filter((item) => item.type === "text")
      .map((item) => item.text)
      .join("\n");
    if (!text.includes(mustContain)) {
      throw new Error(`Entry skill ${name} content missing expected keyword "${mustContain}"`);
    }
  }

  // ── Verify agents are readable ────────────────────────────────────────

  const expectedAgents = [
    { name: "textkit-auditor", mustContain: "P0" },
    { name: "textkit-reference", mustContain: "NSLayoutManager" },
    { name: "editor-reference", mustContain: "Writing Tools" },
    { name: "rich-text-reference", mustContain: "AttributedString" },
    { name: "platform-reference", mustContain: "UIViewRepresentable" },
  ];

  for (const { name, mustContain } of expectedAgents) {
    const result = await client.callTool({
      name: "apple_text_get_agent",
      arguments: { agent: name },
    });
    const text = result.content
      .filter((item) => item.type === "text")
      .map((item) => item.text)
      .join("\n");
    if (!text.includes(mustContain)) {
      throw new Error(`Agent ${name} content missing expected keyword "${mustContain}"`);
    }
    if (text.length < 200) {
      throw new Error(`Agent ${name} returned suspiciously short content (${text.length} chars)`);
    }
  }

  // ── Verify ask with includeSkillContent returns actual content ─────────

  const askWithContent = await client.callTool({
    name: "apple_text_ask",
    arguments: {
      question: "How do I measure text bounding rects?",
      includeSkillContent: true,
    },
  });

  const askContentText = askWithContent.content
    .filter((item) => item.type === "text")
    .map((item) => item.text)
    .join("\n");
  if (askContentText.length < 500) {
    throw new Error(`apple_text_ask with includeSkillContent returned too little content (${askContentText.length} chars)`);
  }

  console.log(
    JSON.stringify(
      {
        server: client.getServerVersion(),
        mode,
        toolCount: tools.tools.length,
        resourceCount: resources.resources.length,
        promptName: "ask",
        askTool: "apple_text_ask",
        routing: {
          passed: routePassed,
          failed: routeFailed,
          total: routingTests.length,
          failures: routeFailures,
        },
      },
      null,
      2,
    ),
  );
} catch (error) {
  fail(`Apple Text MCP smoke test failed: ${error instanceof Error ? error.message : String(error)}`);
} finally {
  await transport.close().catch(() => {});
}
