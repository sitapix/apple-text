import { readFile } from "fs/promises";
import { buildCatalog, type CatalogResult } from "../catalog/index.js";
import { type Config, Logger } from "../config.js";
import {
  buildIndex,
  deserializeIndex,
  search,
  type SearchIndex,
  type SearchOptions,
  type SearchResult,
} from "../search/index.js";
import {
  filterSkillSections,
  type Agent,
  type Command,
  type Skill,
  type SkillKind,
  type SkillSection,
} from "./parser.js";
import type { BundleV1, Loader } from "./types.js";
import { detectXcode, loadAppleDocs } from "./xcode-docs.js";

export class ProdLoader implements Loader {
  private loaded = false;
  private readonly skills = new Map<string, Skill>();
  private readonly commands = new Map<string, Command>();
  private readonly agents = new Map<string, Agent>();
  private searchIndex: SearchIndex | null = null;
  private catalog: CatalogResult | null = null;

  constructor(
    private readonly bundlePath: string,
    private readonly logger: Logger,
    private readonly config?: Config,
  ) {}

  async loadSkills(): Promise<Map<string, Skill>> {
    await this.ensureLoaded();
    return this.skills;
  }

  async loadCommands(): Promise<Map<string, Command>> {
    await this.ensureLoaded();
    return this.commands;
  }

  async loadAgents(): Promise<Map<string, Agent>> {
    await this.ensureLoaded();
    return this.agents;
  }

  async getSkill(name: string): Promise<Skill | undefined> {
    await this.ensureLoaded();
    return this.skills.get(name);
  }

  async getCommand(name: string): Promise<Command | undefined> {
    await this.ensureLoaded();
    return this.commands.get(name);
  }

  async getAgent(name: string): Promise<Agent | undefined> {
    await this.ensureLoaded();
    return this.agents.get(name);
  }

  async getSkillSections(
    name: string,
    sectionNames?: string[],
  ): Promise<{ skill: Skill; content: string; sections: SkillSection[] } | undefined> {
    await this.ensureLoaded();
    const skill = this.skills.get(name);
    if (!skill) return undefined;

    return filterSkillSections(skill, sectionNames);
  }

  async searchSkills(query: string, options?: SearchOptions): Promise<SearchResult[]> {
    await this.ensureLoaded();
    return search(this.searchIndex!, query, this.skills, options);
  }

  async getCatalog(kind?: SkillKind): Promise<CatalogResult> {
    await this.ensureLoaded();
    if (kind) return buildCatalog(this.skills, this.agents, kind);

    return this.catalog ?? buildCatalog(this.skills, this.agents);
  }

  private async ensureLoaded(): Promise<void> {
    if (this.loaded) return;

    const raw = await readFile(this.bundlePath, "utf-8");
    const bundle = JSON.parse(raw) as BundleV1;

    for (const [name, skill] of Object.entries(bundle.skills)) {
      this.skills.set(name, skill);
    }

    for (const [name, command] of Object.entries(bundle.commands)) {
      this.commands.set(name, command);
    }

    for (const [name, agent] of Object.entries(bundle.agents)) {
      this.agents.set(name, agent);
    }

    const overlaidAppleDocs = await this.loadAppleDocsIntoCache();

    this.searchIndex =
      overlaidAppleDocs === 0 && bundle.searchIndex ? deserializeIndex(bundle.searchIndex) : null;
    if (!this.searchIndex || overlaidAppleDocs > 0) {
      this.searchIndex = buildIndex(this.skills);
    }

    this.catalog =
      overlaidAppleDocs === 0 && bundle.catalog ? bundle.catalog : buildCatalog(this.skills, this.agents);
    this.loaded = true;
    this.logger.debug(`Loaded bundle from ${this.bundlePath}`);
  }

  private async loadAppleDocsIntoCache(): Promise<number> {
    if (this.config?.enableAppleDocs === false) {
      this.logger.debug("Apple docs disabled via APPLE_TEXT_APPLE_DOCS=false");
      return 0;
    }

    const xcodeConfig = await detectXcode(this.config?.xcodePath);
    if (!xcodeConfig) {
      this.logger.debug("Xcode docs not detected in production mode");
      return 0;
    }

    const appleDocs = await loadAppleDocs(xcodeConfig, this.logger);
    for (const [name, skill] of appleDocs) {
      this.skills.set(name, skill);
    }

    return appleDocs.size;
  }
}
