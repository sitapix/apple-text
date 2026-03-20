#!/usr/bin/env node

import { readFileSync } from "fs";
import { join, resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  GetPromptRequestSchema,
  ListPromptsRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { loadConfig, Logger } from "./config.js";
import { DevLoader } from "./loader/dev-loader.js";
import { ProdLoader } from "./loader/prod-loader.js";
import type { Loader } from "./loader/types.js";
import { PromptsHandler } from "./prompts/handler.js";
import { ResourcesHandler } from "./resources/handler.js";
import { DynamicToolsHandler } from "./tools/handler.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const pkg = JSON.parse(readFileSync(join(__dirname, "..", "package.json"), "utf-8")) as {
  version: string;
};

async function main(): Promise<void> {
  const config = loadConfig();
  const logger = new Logger(config);
  const defaultDevPath = resolve(__dirname, "..", "..");

  logger.info("Starting Apple Text MCP server");
  logger.info(`Mode: ${config.mode}`);

  let loader: Loader;
  let devLoader: DevLoader | null = null;
  if (config.mode === "development") {
    const repoPath = config.devSourcePath ?? defaultDevPath;
    logger.info(`Development repo path: ${repoPath}`);
    devLoader = new DevLoader(repoPath, logger, config);
    devLoader.startWatching();
    loader = devLoader;
  } else {
    const bundlePath = join(__dirname, "bundle.json");
    logger.info(`Production bundle path: ${bundlePath}`);
    loader = new ProdLoader(bundlePath, logger, config);
  }

  const resourcesHandler = new ResourcesHandler(loader, logger);
  const promptsHandler = new PromptsHandler(loader, logger);
  const toolsHandler = new DynamicToolsHandler(loader, logger);

  const server = new Server(
    {
      name: "apple-text-mcp",
      version: pkg.version,
    },
    {
      capabilities: {
        resources: {},
        prompts: {},
        tools: { listChanged: config.mode === "development" },
      },
      instructions: [
        "Apple Text is a read-only knowledge base for Apple text systems.",
        "It covers TextKit 1 and 2, UITextView, NSTextView, attributed strings, text input, layout invalidation, attachments, Writing Tools, and related diagnostics.",
        "In development mode, Apple Text can also opportunistically load Apple-authored markdown docs from the local Xcode install when they are available.",
        "Recommended flow for natural-language questions: call apple_text_route first, then follow its suggested apple_text_read_skill call.",
        "Use apple_text_search_skills only when routing is ambiguous or you need extra specialist options.",
        "Use apple_text_get_catalog only when the user explicitly wants to browse the collection or entry points.",
        "Tools, prompts, and resources are documentation lookups only and never modify files. Pair this server with Apple's Xcode MCP bridge if you also want build, test, or project actions.",
      ].join(" "),
    },
  );

  server.setRequestHandler(ListResourcesRequestSchema, async () => resourcesHandler.listResources());
  server.setRequestHandler(ReadResourceRequestSchema, async (request) =>
    resourcesHandler.readResource(request.params.uri),
  );

  server.setRequestHandler(ListPromptsRequestSchema, async () => promptsHandler.listPrompts());
  server.setRequestHandler(GetPromptRequestSchema, async (request) =>
    promptsHandler.getPrompt(request.params.name, request.params.arguments),
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => toolsHandler.listTools());
  server.setRequestHandler(CallToolRequestSchema, async (request) =>
    toolsHandler.callTool(request.params.name, request.params.arguments ?? {}),
  );

  if (devLoader) {
    devLoader.onChange((kind) => {
      if (kind !== "skills") return;

      logger.info("Apple Text skills changed; notifying MCP clients");
      server.sendToolListChanged().catch((error) => {
        logger.debug(`Could not send tools/list_changed notification: ${error}`);
      });
    });

    const cleanup = (): void => {
      devLoader?.stopWatching();
      process.exit(0);
    };

    process.on("SIGINT", cleanup);
    process.on("SIGTERM", cleanup);
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  logger.info("Apple Text MCP server is ready");
}

main().catch((error) => {
  console.error("Fatal Apple Text MCP error:", error);
  process.exit(1);
});
