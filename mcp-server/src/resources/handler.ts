import { Logger } from "../config.js";
import { formatDisplayName, type Skill } from "../loader/parser.js";
import type { Loader } from "../loader/types.js";

export interface McpResource {
  uri: string;
  name: string;
  description: string;
  mimeType: string;
}

export class ResourcesHandler {
  constructor(
    private readonly loader: Loader,
    private readonly logger: Logger,
  ) {}

  async listResources(): Promise<{ resources: McpResource[] }> {
    const skills = await this.loader.loadSkills();
    const resources = Array.from(skills.values()).map((skill) => this.toResource(skill));
    this.logger.debug(`Returning ${resources.length} resources`);
    return { resources };
  }

  async readResource(
    uri: string,
  ): Promise<{ contents: Array<{ uri: string; mimeType: string; text: string }> }> {
    const match = uri.match(/^apple-text:\/\/skill\/(.+)$/);
    if (!match) {
      throw new Error(`Invalid resource URI: ${uri}`);
    }

    const skillName = match[1];
    const skill = await this.loader.getSkill(skillName);
    if (!skill) {
      throw new Error(`Skill not found: ${skillName}`);
    }

    return {
      contents: [
        {
          uri,
          mimeType: "text/markdown",
          text: this.formatSkill(skill),
        },
      ],
    };
  }

  private toResource(skill: Skill): McpResource {
    return {
      uri: `apple-text://skill/${skill.name}`,
      name: formatDisplayName(skill.name),
      description: skill.description,
      mimeType: "text/markdown",
    };
  }

  private formatSkill(skill: Skill): string {
    const header: string[] = [
      `# ${formatDisplayName(skill.name)}`,
      "",
      skill.description,
      "",
      "## Metadata",
      `- Kind: ${skill.kind}`,
    ];

    if (skill.category) {
      header.push(`- Category: ${skill.category}`);
    }

    if (skill.tags.length > 0) {
      header.push(`- Tags: ${skill.tags.join(", ")}`);
    }

    if (skill.aliases.length > 0) {
      header.push(`- Aliases: ${skill.aliases.join(", ")}`);
    }

    if (skill.relatedSkills.length > 0) {
      header.push(`- Related skills: ${skill.relatedSkills.join(", ")}`);
    }

    if (skill.entrypointPriority !== undefined) {
      header.push(`- Entrypoint priority: ${skill.entrypointPriority}`);
    }

    if (skill.agent) {
      header.push(`- Related agent: ${skill.agent}`);
    }

    header.push("", "---", "");

    return `${header.join("\n")}${skill.content}`;
  }
}
