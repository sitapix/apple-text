import type { CatalogResult } from "../catalog/index.js";
import type { SearchOptions, SearchResult, SerializedSearchIndex } from "../search/index.js";
import type {
  Agent,
  Command,
  Skill,
  SkillKind,
  SkillSection,
} from "./parser.js";

export interface BundleV1 {
  version: string;
  generatedAt: string;
  skills: Record<string, Skill>;
  commands: Record<string, Command>;
  agents: Record<string, Agent>;
  catalog?: CatalogResult;
  searchIndex?: SerializedSearchIndex;
}

export interface Loader {
  loadSkills(): Promise<Map<string, Skill>>;
  loadCommands(): Promise<Map<string, Command>>;
  loadAgents(): Promise<Map<string, Agent>>;
  getSkill(name: string): Promise<Skill | undefined>;
  getCommand(name: string): Promise<Command | undefined>;
  getAgent(name: string): Promise<Agent | undefined>;
  getSkillSections(
    name: string,
    sectionNames?: string[],
  ): Promise<{ skill: Skill; content: string; sections: SkillSection[] } | undefined>;
  searchSkills(query: string, options?: SearchOptions): Promise<SearchResult[]>;
  getCatalog(kind?: SkillKind): Promise<CatalogResult>;
}
