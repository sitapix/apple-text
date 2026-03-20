import { readdir, readFile, stat } from "fs/promises";
import { join } from "path";
import { buildCatalog, type CatalogResult } from "../catalog/index.js";
import { type Config, Logger } from "../config.js";
import { buildIndex, search, type SearchOptions, type SearchResult } from "../search/index.js";
import {
  filterSkillSections,
  parseAgent,
  parseCommand,
  parseSkill,
  type Agent,
  type Command,
  type Skill,
  type SkillAnnotations,
  type SkillCatalogEntry,
  type SkillKind,
  type SkillSection,
} from "./parser.js";
import type { Loader } from "./types.js";
import { detectXcode, loadAppleDocs } from "./xcode-docs.js";

export type ChangeKind = "skills" | "commands" | "agents" | null;

export function classifyChange(relativePath: string): ChangeKind {
  if (relativePath.startsWith("skills/")) return "skills";
  if (relativePath.startsWith("commands/")) return "commands";
  if (relativePath.startsWith("agents/")) return "agents";
  return null;
}

export class DevLoader implements Loader {
  private readonly skillsCache = new Map<string, Skill>();
  private readonly commandsCache = new Map<string, Command>();
  private readonly agentsCache = new Map<string, Agent>();
  private searchIndex: ReturnType<typeof buildIndex> | null = null;
  private catalog: CatalogResult | null = null;
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private polling = false;
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private readonly pendingKinds = new Set<Exclude<ChangeKind, null>>();
  private readonly snapshots = new Map<Exclude<ChangeKind, null>, string>();
  private onChangeCallback: ((kind: ChangeKind) => void) | null = null;

  constructor(
    private readonly repoPath: string,
    private readonly logger: Logger,
    private readonly config?: Config,
  ) {}

  async loadSkills(): Promise<Map<string, Skill>> {
    if (this.skillsCache.size > 0) {
      return this.skillsCache;
    }

    const catalog = await this.loadSkillCatalog();
    const annotations = await this.loadSkillAnnotations();
    const skillsDir = join(this.repoPath, "skills");
    this.skillsCache.clear();

    for (const directory of await this.walkSkillDirectories(skillsDir)) {
      const skillPath = join(directory.path, "SKILL.md");
      const content = await readFile(skillPath, "utf-8");
      const skill = parseSkill(
        content,
        directory.name,
        catalog.get(directory.name),
        annotations[directory.name],
      );
      this.skillsCache.set(skill.name, skill);
    }

    await this.loadAppleDocsIntoMap(this.skillsCache);
    this.logger.debug(`Loaded ${this.skillsCache.size} live skills from ${skillsDir}`);
    return this.skillsCache;
  }

  async loadCommands(): Promise<Map<string, Command>> {
    if (this.commandsCache.size > 0) {
      return this.commandsCache;
    }

    const commandsDir = join(this.repoPath, "commands");
    this.commandsCache.clear();

    for (const entry of await readdir(commandsDir, { withFileTypes: true })) {
      if (!entry.isFile() || !entry.name.endsWith(".md")) continue;
      const name = entry.name.replace(/\.md$/, "");
      const content = await readFile(join(commandsDir, entry.name), "utf-8");
      const command = parseCommand(content, name);
      this.commandsCache.set(command.name, command);
    }

    return this.commandsCache;
  }

  async loadAgents(): Promise<Map<string, Agent>> {
    if (this.agentsCache.size > 0) {
      return this.agentsCache;
    }

    const agentsDir = join(this.repoPath, "agents");
    this.agentsCache.clear();

    for (const entry of await readdir(agentsDir, { withFileTypes: true })) {
      if (!entry.isFile() || !entry.name.endsWith(".md")) continue;
      const name = entry.name.replace(/\.md$/, "");
      const content = await readFile(join(agentsDir, entry.name), "utf-8");
      const agent = parseAgent(content, name);
      this.agentsCache.set(agent.name, agent);
    }

    return this.agentsCache;
  }

  async getSkill(name: string): Promise<Skill | undefined> {
    const skills = await this.loadSkills();
    return skills.get(name);
  }

  async getCommand(name: string): Promise<Command | undefined> {
    const commands = await this.loadCommands();
    return commands.get(name);
  }

  async getAgent(name: string): Promise<Agent | undefined> {
    const agents = await this.loadAgents();
    return agents.get(name);
  }

  async getSkillSections(
    name: string,
    sectionNames?: string[],
  ): Promise<{ skill: Skill; content: string; sections: SkillSection[] } | undefined> {
    const skill = await this.getSkill(name);
    if (!skill) return undefined;

    return filterSkillSections(skill, sectionNames);
  }

  async searchSkills(query: string, options?: SearchOptions): Promise<SearchResult[]> {
    const skills = await this.loadSkills();
    if (!this.searchIndex) {
      this.searchIndex = buildIndex(skills);
    }

    return search(this.searchIndex, query, skills, options);
  }

  async getCatalog(kind?: SkillKind): Promise<CatalogResult> {
    const [skills, agents] = await Promise.all([this.loadSkills(), this.loadAgents()]);
    if (kind) {
      return buildCatalog(skills, agents, kind);
    }

    if (!this.catalog) {
      this.catalog = buildCatalog(skills, agents);
    }

    return this.catalog;
  }

  onChange(callback: (kind: ChangeKind) => void): void {
    this.onChangeCallback = callback;
  }

  startWatching(): void {
    if (this.pollTimer) return;
    this.logger.info(`Watching Apple Text repo for MCP changes: ${this.repoPath}`);

    void (async () => {
      try {
        for (const kind of ["skills", "commands", "agents"] as const) {
          this.snapshots.set(kind, await this.snapshotFor(kind));
        }

        this.pollTimer = setInterval(() => {
          void this.pollForChanges();
        }, 250);
      } catch (error) {
        this.logger.error("Apple Text MCP watcher failed:", error);
      }
    })();
  }

  stopWatching(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }

    this.pendingKinds.clear();
    this.snapshots.clear();
  }

  private async loadSkillCatalog(): Promise<Map<string, SkillCatalogEntry>> {
    const catalogPath = join(this.repoPath, "skills", "catalog.json");
    const raw = await readFile(catalogPath, "utf-8");
    const parsed = JSON.parse(raw) as { skills?: SkillCatalogEntry[] };
    const entries = new Map<string, SkillCatalogEntry>();

    for (const entry of parsed.skills ?? []) {
      entries.set(entry.name, entry);
    }

    return entries;
  }

  private async loadSkillAnnotations(): Promise<SkillAnnotations> {
    const annotationsPath = join(this.repoPath, "mcp-server", "skill-annotations.json");
    const raw = await readFile(annotationsPath, "utf-8");
    return JSON.parse(raw) as SkillAnnotations;
  }

  private async walkSkillDirectories(
    root: string,
  ): Promise<Array<{ name: string; path: string }>> {
    const directories: Array<{ name: string; path: string }> = [];

    const walk = async (currentPath: string): Promise<void> => {
      for (const entry of await readdir(currentPath, { withFileTypes: true })) {
        if (!entry.isDirectory()) continue;

        const directoryPath = join(currentPath, entry.name);
        const entries = await readdir(directoryPath, { withFileTypes: true });
        if (entries.some((child) => child.isFile() && child.name === "SKILL.md")) {
          directories.push({ name: entry.name, path: directoryPath });
        }

        await walk(directoryPath);
      }
    };

    await walk(root);
    return directories.sort((left, right) => left.name.localeCompare(right.name));
  }

  private async loadAppleDocsIntoMap(skills: Map<string, Skill>): Promise<void> {
    if (this.config?.enableAppleDocs === false) {
      this.logger.debug("Apple docs disabled via APPLE_TEXT_APPLE_DOCS=false");
      return;
    }

    const xcodeConfig = await detectXcode(this.config?.xcodePath);
    if (!xcodeConfig) {
      this.logger.debug("Xcode docs not detected; continuing with repo skills only");
      return;
    }

    const appleDocs = await loadAppleDocs(xcodeConfig, this.logger);
    for (const [name, skill] of appleDocs) {
      skills.set(name, skill);
    }
  }

  private invalidate(kind: Exclude<ChangeKind, null>): void {
    this.logger.info(`Invalidating Apple Text MCP ${kind} cache`);

    switch (kind) {
      case "skills":
        this.skillsCache.clear();
        this.searchIndex = null;
        this.catalog = null;
        break;
      case "commands":
        this.commandsCache.clear();
        break;
      case "agents":
        this.agentsCache.clear();
        this.catalog = null;
        break;
    }

    this.onChangeCallback?.(kind);
  }

  private scheduleInvalidation(kind: Exclude<ChangeKind, null>): void {
    this.pendingKinds.add(kind);
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }

    // Debounce bursty editor writes into a single invalidation pass.
    this.debounceTimer = setTimeout(() => {
      for (const pendingKind of this.pendingKinds) {
        this.invalidate(pendingKind);
      }
      this.pendingKinds.clear();
    }, 200);
  }

  private async pollForChanges(): Promise<void> {
    if (this.polling) return;
    this.polling = true;

    try {
      for (const kind of ["skills", "commands", "agents"] as const) {
        const nextSnapshot = await this.snapshotFor(kind);
        const previousSnapshot = this.snapshots.get(kind);
        if (previousSnapshot !== nextSnapshot) {
          this.snapshots.set(kind, nextSnapshot);
          this.scheduleInvalidation(kind);
        }
      }
    } finally {
      this.polling = false;
    }
  }

  private async snapshotFor(kind: Exclude<ChangeKind, null>): Promise<string> {
    const parts: string[] = [];

    switch (kind) {
      case "skills":
        await this.collectSnapshot(join(this.repoPath, "skills"), parts);
        await this.collectSnapshot(join(this.repoPath, "mcp-server", "skill-annotations.json"), parts);
        break;
      case "commands":
        await this.collectSnapshot(join(this.repoPath, "commands"), parts);
        break;
      case "agents":
        await this.collectSnapshot(join(this.repoPath, "agents"), parts);
        break;
    }

    return parts.sort().join("\n");
  }

  private async collectSnapshot(path: string, parts: string[]): Promise<void> {
    try {
      const fileStat = await stat(path);
      if (fileStat.isFile()) {
        parts.push(`${path}|${fileStat.size}|${fileStat.mtimeMs}`);
        return;
      }

      parts.push(`${path}|dir|${fileStat.mtimeMs}`);
      for (const entry of await readdir(path, { withFileTypes: true })) {
        if (entry.name.startsWith(".")) continue;
        await this.collectSnapshot(join(path, entry.name), parts);
      }
    } catch {
      parts.push(`${path}|missing`);
    }
  }
}
