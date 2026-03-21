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

  console.log(
    JSON.stringify(
      {
        server: client.getServerVersion(),
        mode,
        toolCount: tools.tools.length,
        resourceCount: resources.resources.length,
        promptName: "ask",
        askTool: "apple_text_ask",
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
