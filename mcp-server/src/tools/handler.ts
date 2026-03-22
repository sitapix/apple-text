import type { CallToolResult, ToolAnnotations } from "@modelcontextprotocol/sdk/types.js";
import { orderedKinds } from "../catalog/index.js";
import { Logger } from "../config.js";
import { formatDisplayName, type Agent, type Skill, type SkillKind } from "../loader/parser.js";
import type { Loader } from "../loader/types.js";

export interface McpTool {
  name: string;
  description: string;
  inputSchema: {
    type: string;
    properties?: Record<string, unknown>;
    required?: string[];
  };
  annotations?: ToolAnnotations;
}

export class DynamicToolsHandler {
  constructor(
    private readonly loader: Loader,
    private readonly logger: Logger,
  ) {}

  async listTools(): Promise<{ tools: McpTool[] }> {
    return {
      tools: [
        {
          name: "apple_text_ask",
          description:
            "Natural-language front door for Apple Text. Routes the question to the best skill and returns the relevant skill content directly. Use this when clients do not surface MCP prompts well.",
          inputSchema: {
            type: "object",
            properties: {
              question: {
                type: "string",
                description: "User question to route and answer from Apple Text.",
              },
              includeSkillContent: {
                type: "boolean",
                description: "Include the routed skill content in the response. Default true.",
              },
              preferEntrypoints: {
                type: "boolean",
                description: "Prefer prominent entry-point skills when scores are close. Default true.",
              },
            },
            required: ["question"],
          },
          annotations: readOnlyAnnotations("Ask Apple Text"),
        },
        {
          name: "apple_text_route",
          description:
            "Always start here for natural-language Apple text questions unless the user explicitly asked to browse the catalog. Returns the most relevant skills and the next apple_text_read_skill call.",
          inputSchema: {
            type: "object",
            properties: {
              question: {
                type: "string",
                description: "User question to route.",
              },
              limit: {
                type: "number",
                description: "Maximum number of routed skills to return. Default 3.",
              },
              preferEntrypoints: {
                type: "boolean",
                description: "Prefer prominent entry-point skills when scores are close. Default true.",
              },
            },
            required: ["question"],
          },
          annotations: readOnlyAnnotations("Route Apple Text Question"),
        },
        {
          name: "apple_text_get_catalog",
          description:
            "Browse the Apple Text skill catalog grouped by collection kind such as router, workflow, decision, diagnostic, and reference. Use this when the user explicitly wants an overview or route/search was not enough.",
          inputSchema: {
            type: "object",
            properties: {
              kind: {
                type: "string",
                enum: orderedKinds(),
                description: "Optional skill kind filter.",
              },
              includeDescriptions: {
                type: "boolean",
                description: "Include skill descriptions and aliases in the listing.",
              },
            },
          },
          annotations: readOnlyAnnotations("Browse Apple Text Catalog"),
        },
        {
          name: "apple_text_search_skills",
          description:
            "Search Apple Text skills by keyword across names, descriptions, aliases, section headings, and body text. Prefer apple_text_route first for normal user questions.",
          inputSchema: {
            type: "object",
            properties: {
              query: {
                type: "string",
                description: "Search query.",
              },
              limit: {
                type: "number",
                description: "Maximum number of results to return. Default 10.",
              },
              kind: {
                type: "string",
                enum: orderedKinds(),
                description: "Optional skill kind filter.",
              },
              category: {
                type: "string",
                description: "Optional MCP category filter.",
              },
            },
            required: ["query"],
          },
          annotations: readOnlyAnnotations("Search Apple Text Skills"),
        },
        {
          name: "apple_text_read_skill",
          description:
            "Read one or more Apple Text skills, optionally limited to selected section headings to reduce token usage. Usually call this after apple_text_route suggests the names and sections.",
          inputSchema: {
            type: "object",
            properties: {
              skills: {
                type: "array",
                items: {
                  type: "object",
                  properties: {
                    name: { type: "string", description: "Skill name." },
                    sections: {
                      type: "array",
                      items: { type: "string" },
                      description: "Optional section heading filters.",
                    },
                  },
                  required: ["name"],
                },
                description: "Skills to read.",
              },
              listSections: {
                type: "boolean",
                description: "Return only the section table of contents for each skill.",
              },
            },
            required: ["skills"],
          },
          annotations: readOnlyAnnotations("Read Apple Text Skill Content"),
        },
        {
          name: "apple_text_get_agent",
          description:
            "Read an Apple Text specialist agent definition including its instructions, model hint, and declared tools.",
          inputSchema: {
            type: "object",
            properties: {
              agent: {
                type: "string",
                description: "Agent name.",
              },
            },
            required: ["agent"],
          },
          annotations: readOnlyAnnotations("Read Apple Text Agent"),
        },
      ],
    };
  }

  async callTool(name: string, args: Record<string, unknown>): Promise<CallToolResult> {
    this.logger.debug(`Handling tools/call for ${name}`);

    switch (name) {
      case "apple_text_ask":
        return this.handleAsk(args);
      case "apple_text_route":
        return this.handleRoute(args);
      case "apple_text_get_catalog":
        return this.handleGetCatalog(args);
      case "apple_text_search_skills":
        return this.handleSearchSkills(args);
      case "apple_text_read_skill":
        return this.handleReadSkill(args);
      case "apple_text_get_agent":
        return this.handleGetAgent(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  private async handleRoute(args: Record<string, unknown>): Promise<CallToolResult> {
    if (typeof args.question !== "string" || args.question.trim() === "") {
      throw new Error('Required parameter "question" must be a non-empty string');
    }

    const question = args.question.trim();
    const limit = clampLimit(args.limit, 3, 1, 8);
    const preferEntrypoints = args.preferEntrypoints !== false;
    const route = await this.routeSkills(question, limit, preferEntrypoints);
    const { intent, routed } = route;

    if (routed.length === 0) {
      const catalog = await this.loader.getCatalog();
      const fallbackSkills = catalog.featured.slice(0, limit);
      const lines = [
        `# Route for "${question}"`,
        "",
        `Primary intent: ${intent.label}`,
        "",
        "No direct lexical match found. Start with these entry points:",
        "",
      ];

      if (fallbackSkills.length === 0) {
        lines.push("- apple-text");
      } else {
        for (const skill of fallbackSkills) {
          lines.push(`- ${skill.name}: ${skill.description}`);
        }
      }

      return { content: [{ type: "text", text: lines.join("\n") }] };
    }

    const lines = [
      `# Route for "${question}"`,
      "",
      `Primary intent: ${intent.label}`,
      `Start with: ${routed[0].result.name}`,
      "",
      "Recommended skills:",
      "",
    ];

    routed.forEach((candidate, index) => {
      const sections =
        candidate.result.matchingSections.length > 0
          ? candidate.result.matchingSections.slice(0, 3)
          : candidate.skill?.sections
              .map((section) => section.heading)
              .filter((heading) => heading !== "_preamble")
              .slice(0, 2) ?? [];
      const readArgs =
        sections.length > 0
          ? JSON.stringify({ skills: [{ name: candidate.result.name, sections }] })
          : JSON.stringify({ skills: [{ name: candidate.result.name }] });

      lines.push(
        `${index + 1}. ${candidate.result.name} [${candidate.result.kind}]`,
        candidate.result.description,
        `Why: ${candidate.reasons.join("; ")}`,
      );

      if (sections.length > 0) {
        lines.push(`Sections: ${sections.join(", ")}`);
      }

      if (candidate.skill?.agent) {
        lines.push(`Agent: ${candidate.skill.agent}`);
      }

      lines.push(`Read next: apple_text_read_skill ${readArgs}`, "");
    });

    return { content: [{ type: "text", text: lines.join("\n") }] };
  }

  private async handleAsk(args: Record<string, unknown>): Promise<CallToolResult> {
    if (typeof args.question !== "string" || args.question.trim() === "") {
      throw new Error('Required parameter "question" must be a non-empty string');
    }

    const question = args.question.trim();
    const preferEntrypoints = args.preferEntrypoints !== false;
    const includeSkillContent = args.includeSkillContent !== false;
    const route = await this.routeSkills(question, 1, preferEntrypoints);
    const top = route.routed[0];

    if (!top) {
      return {
        content: [
          {
            type: "text",
            text: [
              `# Ask Apple Text`,
              "",
              `Question: ${question}`,
              "",
              "No routed skill was found. Try `apple_text_route` for broader options or `apple_text_search_skills` for manual lookup.",
            ].join("\n"),
          },
        ],
      };
    }

    const sectionNames =
      top.result.matchingSections.length > 0 ? top.result.matchingSections.slice(0, 3) : undefined;
    const sectionResult = await this.loader.getSkillSections(top.result.name, sectionNames);
    const skillContent = sectionResult?.content || top.skill?.content || "";
    const sectionList =
      sectionResult && sectionResult.sections.length > 0
        ? sectionResult.sections.map((section) => section.heading)
        : [];

    const lines = [
      `# Ask Apple Text`,
      "",
      `Question: ${question}`,
      `Start with: ${top.result.name}`,
      `Intent: ${route.intent.label}`,
      `Why: ${top.reasons.join("; ")}`,
    ];

    if (sectionList.length > 0) {
      lines.push(`Sections: ${sectionList.join(", ")}`);
    }

    if (top.skill?.agent) {
      lines.push(`Agent: ${top.skill.agent}`);
    }

    lines.push(`Read next: apple_text_read_skill ${JSON.stringify({
      skills: [
        sectionList.length > 0
          ? { name: top.result.name, sections: sectionList }
          : { name: top.result.name },
      ],
    })}`);

    if (includeSkillContent && skillContent) {
      lines.push("", "---", "", skillContent);
    }

    return { content: [{ type: "text", text: lines.join("\n") }] };
  }

  private async handleGetCatalog(args: Record<string, unknown>): Promise<CallToolResult> {
    const kind = normalizeSkillKind(args.kind);
    const includeDescriptions = args.includeDescriptions === true;
    const catalog = await this.loader.getCatalog(kind);
    const lines: string[] = [
      "# Apple Text Catalog",
      `${catalog.totalSkills} skills, ${catalog.totalAgents} agents`,
      "",
    ];

    if (!kind && catalog.featured.length > 0) {
      lines.push("## Entry Points");
      for (const skill of catalog.featured) {
        lines.push(formatCatalogLine(skill.name, skill.description, skill.aliases, includeDescriptions));
      }
      lines.push("");
    }

    for (const catalogKind of orderedKinds()) {
      const group = catalog.groups[catalogKind];
      if (!group) continue;

      lines.push(`## ${group.label} (${group.skills.length})`);
      for (const skill of group.skills) {
        lines.push(formatCatalogLine(skill.name, skill.description, skill.aliases, includeDescriptions));
      }
      lines.push("");
    }

    if (!kind && catalog.agents.length > 0) {
      lines.push(`## Agents (${catalog.agents.length})`);
      for (const agent of catalog.agents) {
        if (includeDescriptions) {
          lines.push(`- **${agent.name}**: ${agent.description}`);
        } else {
          lines.push(`- ${agent.name}`);
        }
      }
      lines.push("");
    }

    return { content: [{ type: "text", text: lines.join("\n") }] };
  }

  private async handleSearchSkills(args: Record<string, unknown>): Promise<CallToolResult> {
    if (typeof args.query !== "string" || args.query.trim() === "") {
      throw new Error('Required parameter "query" must be a non-empty string');
    }

    const results = await this.loader.searchSkills(args.query, {
      limit: typeof args.limit === "number" ? args.limit : undefined,
      kind: normalizeSkillKind(args.kind),
      category: typeof args.category === "string" ? args.category : undefined,
    });

    if (results.length === 0) {
      return {
        content: [{ type: "text", text: `No Apple Text skills found for "${args.query}".` }],
      };
    }

    const lines: string[] = [`# Search Results for "${args.query}"`, `${results.length} results`, ""];
    for (const result of results) {
      lines.push(`## ${result.name} [${result.kind}]`);
      lines.push(result.description);
      if (result.category) {
        lines.push(`Category: ${result.category}`);
      }
      if (result.aliases.length > 0) {
        lines.push(`Aliases: ${result.aliases.join(", ")}`);
      }
      if (result.matchingSections.length > 0) {
        lines.push(`Matching sections: ${result.matchingSections.join(", ")}`);
      }
      lines.push(`Score: ${result.score.toFixed(2)}`);
      lines.push("");
    }

    return { content: [{ type: "text", text: lines.join("\n") }] };
  }

  private async handleReadSkill(args: Record<string, unknown>): Promise<CallToolResult> {
    if (!Array.isArray(args.skills) || args.skills.length === 0) {
      throw new Error('Required parameter "skills" must be a non-empty array');
    }

    const listSections = args.listSections === true;
    const blocks: string[] = [];

    for (const item of args.skills) {
      if (!item || typeof item !== "object") {
        throw new Error('Each entry in "skills" must be an object');
      }

      const name = typeof item.name === "string" ? item.name : undefined;
      if (!name) {
        throw new Error('Each skill entry requires a "name"');
      }

      if (listSections) {
        const skill = await this.loader.getSkill(name);
        if (!skill) {
          blocks.push(`## ${name}\nSkill not found.`);
          continue;
        }

        const toc = skill.sections
          .map((section) => `- ${section.heading} (${section.charCount} chars)`)
          .join("\n");
        blocks.push(`## ${name}\n${toc}`);
        continue;
      }

      const sections =
        Array.isArray(item.sections) &&
        item.sections.every((value: unknown): value is string => typeof value === "string")
          ? (item.sections as string[])
          : undefined;
      const result = await this.loader.getSkillSections(name, sections);
      if (!result) {
        blocks.push(`## ${name}\nSkill not found.`);
        continue;
      }

      const heading =
        sections && sections.length > 0
          ? `## ${result.skill.name} (${result.sections.length} section${result.sections.length === 1 ? "" : "s"})`
          : `## ${result.skill.name}`;
      blocks.push([heading, "", result.content || "_No matching sections found._"].join("\n"));
    }

    return { content: [{ type: "text", text: blocks.join("\n\n") }] };
  }

  private async handleGetAgent(args: Record<string, unknown>): Promise<CallToolResult> {
    if (typeof args.agent !== "string" || args.agent.trim() === "") {
      throw new Error('Required parameter "agent" must be a non-empty string');
    }

    const agent = await this.loader.getAgent(args.agent);
    if (!agent) {
      throw new Error(`Agent not found: ${args.agent}`);
    }

    return { content: [{ type: "text", text: formatAgent(agent) }] };
  }

  private async routeSkills(
    question: string,
    limit: number,
    preferEntrypoints: boolean,
  ): Promise<{
    intent: { label: string; preferredKind: SkillKind };
    routed: RoutedCandidate[];
  }> {
    const intent = inferRouteIntent(question);
    const explicitCandidates = explicitRouteCandidates(question, intent.preferredKind);
    const searchResults = await this.loader.searchSkills(question, {
      limit: Math.max(limit * 4, 8),
    });
    const candidates = new Map<string, SearchResultLike>(
      searchResults.map((result) => [result.name, result]),
    );

    for (const skillName of explicitCandidates) {
      if (candidates.has(skillName)) continue;
      const skill = await this.loader.getSkill(skillName);
      if (!skill) continue;
      candidates.set(skillName, searchResultFromSkill(skill));
    }

    if (candidates.size === 0) {
      return { intent, routed: [] };
    }

    const explicitOrder = new Map(explicitCandidates.map((name, index) => [name, index]));
    const ranked = Array.from(candidates.values())
      .map((result) => rankRouteResult(result, question, intent, preferEntrypoints))
      .sort((left, right) => {
        return (
          compareExplicitCandidates(left.result.name, right.result.name, explicitOrder) ||
          right.adjustedScore - left.adjustedScore ||
          compareEntrypoints(left.result.entrypointPriority, right.result.entrypointPriority) ||
          left.result.name.localeCompare(right.result.name)
        );
      })
      .slice(0, limit);

    const routed = await Promise.all(
      ranked.map(async (candidate) => ({
        ...candidate,
        skill: await this.loader.getSkill(candidate.result.name),
      })),
    );

    return { intent, routed };
  }
}

function readOnlyAnnotations(title: string): ToolAnnotations {
  return {
    title,
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: false,
  };
}

function normalizeSkillKind(value: unknown): SkillKind | undefined {
  if (
    value === "router" ||
    value === "workflow" ||
    value === "diag" ||
    value === "decision" ||
    value === "ref"
  ) {
    return value;
  }

  return undefined;
}

function clampLimit(
  value: unknown,
  defaultValue: number,
  min: number,
  max: number,
): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return defaultValue;
  }

  return Math.max(min, Math.min(max, Math.floor(value)));
}

function compareEntrypoints(left?: number, right?: number): number {
  const leftValue = left ?? Number.MAX_SAFE_INTEGER;
  const rightValue = right ?? Number.MAX_SAFE_INTEGER;
  return leftValue - rightValue;
}

function compareExplicitCandidates(
  left: string,
  right: string,
  explicitOrder: Map<string, number>,
): number {
  const leftIndex = explicitOrder.get(left);
  const rightIndex = explicitOrder.get(right);

  if (leftIndex === undefined && rightIndex === undefined) {
    return 0;
  }

  if (leftIndex === undefined) {
    return 1;
  }

  if (rightIndex === undefined) {
    return -1;
  }

  return leftIndex - rightIndex;
}

function inferRouteIntent(question: string): { label: string; preferredKind: SkillKind } {
  const normalized = question.toLowerCase();

  if (
    /\b(which|choose|choice|should i use|should we use|vs\b|versus|tradeoff|compare)\b/.test(
      normalized,
    )
  ) {
    return {
      label: "Decision or platform choice",
      preferredKind: "decision",
    };
  }

  if (isLikelyDiagnosticQuestion(normalized)) {
    return {
      label: "Debugging or diagnosis",
      preferredKind: "diag",
    };
  }

  if (/\b(api|reference|attribute|exact|docs?|documentation|what does)\b/.test(normalized)) {
    return {
      label: "Reference lookup",
      preferredKind: "ref",
    };
  }

  if (/\b(how|implement|integrate|wrap|build|add|use|adopt)\b/.test(normalized)) {
    return {
      label: "Implementation workflow",
      preferredKind: "workflow",
    };
  }

  return {
    label: "Broad intake or routing",
    preferredKind: "router",
  };
}

function rankRouteResult(
  result: SearchResultLike,
  question: string,
  intent: { label: string; preferredKind: SkillKind },
  preferEntrypoints: boolean,
): { result: SearchResultLike; adjustedScore: number; reasons: string[] } {
  let adjustedScore = result.score;
  const reasons: string[] = [];
  const normalizedQuestion = question.toLowerCase();
  const asksForDiagnosis = isLikelyDiagnosticQuestion(normalizedQuestion);
  const asksForTextViewChoice = /\b(text view|textview|which view|which text view)\b/.test(
    normalizedQuestion,
  );

  if (result.kind === intent.preferredKind) {
    adjustedScore += 1;
    reasons.push(`Matches ${intent.label.toLowerCase()}`);
  } else {
    adjustedScore -= 0.5;
  }

  if (asksForTextViewChoice && result.name === "apple-text-views") {
    adjustedScore += 5;
    reasons.push("Explicit text-view choice request");
  }

  if (asksForTextViewChoice && result.name === "apple-text-interaction") {
    adjustedScore -= 2;
  }

  if (/\b(audit|review|scan)\b/.test(normalizedQuestion) && result.name === "apple-text-audit") {
    adjustedScore += 5;
    reasons.push("Explicit audit request");
  }

  if (asksForDiagnosis && result.name === "apple-text-textkit-diag") {
    adjustedScore += 5;
    reasons.push("Explicit debugging request");
  }

  if (intent.preferredKind === "router" && result.name === "apple-text") {
    adjustedScore += 1;
    reasons.push("Broad router entry point");
  }

  if (preferEntrypoints && result.entrypointPriority !== undefined) {
    adjustedScore += 0.75 / result.entrypointPriority;
    reasons.push(`Entry point priority ${result.entrypointPriority}`);
  }

  if (result.matchingSections.length > 0) {
    adjustedScore += Math.min(result.matchingSections.length, 3) * 0.15;
    reasons.push(`Matched sections: ${result.matchingSections.slice(0, 3).join(", ")}`);
  }

  if (reasons.length === 0) {
    reasons.push("Strong text match");
  }

  return { result, adjustedScore, reasons };
}

interface SearchResultLike {
  name: string;
  description: string;
  kind: SkillKind;
  score: number;
  matchingSections: string[];
  entrypointPriority?: number;
}

interface RoutedCandidate {
  result: SearchResultLike;
  adjustedScore: number;
  reasons: string[];
  skill?: Skill;
}

function explicitRouteCandidates(question: string, preferredKind: SkillKind): string[] {
  const normalized = question.toLowerCase();
  const candidates: string[] = [];

  if (/\b(text view|textview|which view|which text view)\b/.test(normalized)) {
    candidates.push("apple-text-views");
  }

  if (/\b(audit|review|scan)\b/.test(normalized)) {
    candidates.push("apple-text-audit");
  }

  if (isLikelyDiagnosticQuestion(normalized)) {
    candidates.push("apple-text-textkit-diag");
  }

  if (preferredKind === "router" || /\b(apple text|textkit|uitextview|nstextview)\b/.test(normalized)) {
    candidates.push("apple-text");
  }

  return candidates;
}

function isLikelyDiagnosticQuestion(normalizedQuestion: string): boolean {
  if (
    /\b(crash|broken|stale|fallback|wrong|bug|issue|diagnos|debug|not working|fail|missing|slow)\b/.test(
      normalizedQuestion,
    )
  ) {
    return true;
  }

  const asksForCauseOrChecks =
    /\b(why does|why is|what(?: usually)? causes|what should be checked|what should i check|how do i debug|how to debug)\b/.test(
      normalizedQuestion,
    );
  const hasTextSystemContext =
    /\b(textkit|nstextview|uitextview|attributed string|text storage|textstorage|typing attributes?|inserttext|didchangetext|layout manager|storagecolor|typingcolor|expectedcolor)\b/.test(
      normalizedQuestion,
    );
  const hasRuntimeSymptoms =
    /\b(nil|black|white|dark mode|until|next keystroke|newly typed text|typed text|becomes|during|preflight|postedit|logs? show|snapshot)\b/.test(
      normalizedQuestion,
    );

  return asksForCauseOrChecks && hasTextSystemContext && hasRuntimeSymptoms;
}

function searchResultFromSkill(skill: {
  name: string;
  description: string;
  kind: SkillKind;
  entrypointPriority?: number;
}): SearchResultLike {
  return {
    name: skill.name,
    description: skill.description,
    kind: skill.kind,
    score: 0,
    matchingSections: [],
    entrypointPriority: skill.entrypointPriority,
  };
}

function formatCatalogLine(
  name: string,
  description: string,
  aliases: string[],
  includeDescriptions: boolean,
): string {
  if (!includeDescriptions) {
    return `- ${name}`;
  }

  const aliasText = aliases.length > 0 ? ` Aliases: ${aliases.join(", ")}.` : "";
  return `- **${name}**: ${description}${aliasText}`;
}

function formatAgent(agent: Agent): string {
  const lines = [`# ${formatDisplayName(agent.name)}`, "", agent.description, "", "## Metadata"];

  if (agent.model) {
    lines.push(`- Model: ${agent.model}`);
  }

  if (agent.tools.length > 0) {
    lines.push(`- Tools: ${agent.tools.join(", ")}`);
  }

  lines.push("", "---", "", agent.content);
  return lines.join("\n");
}
