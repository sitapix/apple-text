import { Logger } from "../config.js";
import { type Command } from "../loader/parser.js";
import type { Loader } from "../loader/types.js";

export interface McpPrompt {
  name: string;
  description: string;
  arguments?: Array<{
    name: string;
    description: string;
    required: boolean;
  }>;
}

export class PromptsHandler {
  constructor(
    private readonly loader: Loader,
    private readonly logger: Logger,
  ) {}

  async listPrompts(): Promise<{ prompts: McpPrompt[] }> {
    const commands = await this.loader.loadCommands();
    const prompts = Array.from(commands.values()).map((command) => this.toPrompt(command));
    this.logger.debug(`Returning ${prompts.length} prompts`);
    return { prompts };
  }

  async getPrompt(
    name: string,
    args?: Record<string, string>,
  ): Promise<{
    description?: string;
    messages: Array<{ role: string; content: { type: string; text: string } }>;
  }> {
    const command = await this.loader.getCommand(name);
    if (!command) {
      throw new Error(`Prompt not found: ${name}`);
    }

    return {
      description: command.description,
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: this.substituteArguments(command, args ?? {}),
          },
        },
      ],
    };
  }

  private toPrompt(command: Command): McpPrompt {
    return {
      name: command.name,
      description: command.description,
      arguments:
        command.argumentHints.length > 0
          ? command.argumentHints.map((argument) => ({
              name: argument,
              description: `Value for ${argument}`,
              required: true,
            }))
          : undefined,
    };
  }

  private substituteArguments(command: Command, args: Record<string, string>): string {
    let content = command.content;
    const orderedArgumentValues =
      command.argumentHints.length > 0
        ? command.argumentHints.map((hint) => args[hint]).filter((value): value is string => Boolean(value))
        : Object.values(args).filter((value): value is string => Boolean(value));

    const aggregateArguments = orderedArgumentValues.join(" ").trim();
    const explicitQuestion = typeof args.question === "string" ? args.question.trim() : "";
    const resolvedArguments = aggregateArguments || explicitQuestion;
    content = content.replace(/\$ARGUMENTS/g, resolvedArguments);

    for (const [key, value] of Object.entries(args)) {
      const placeholder = new RegExp(`{{\\s*${escapeForRegex(key)}\\s*}}`, "g");
      content = content.replace(placeholder, value);
    }

    if (command.name === "ask") {
      return [
        "# Apple Text MCP Workflow",
        "",
        "For this prompt, use the MCP tools in this order:",
        "1. Call `apple_text_route` with the user's question.",
        "2. Follow the suggested `apple_text_read_skill` call for the top routed skill.",
        "3. Use `apple_text_search_skills` only if the route result is ambiguous or you need more options.",
        "4. Use `apple_text_get_catalog` only if the user explicitly wants to browse the collection.",
        ...(resolvedArguments ? ["", `User question: ${resolvedArguments}`] : []),
        "",
        content,
      ].join("\n");
    }

    return content;
  }
}

function escapeForRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
