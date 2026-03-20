import MiniSearch, { type AsPlainObject } from "minisearch";
import { type Skill, type SkillKind } from "../loader/parser.js";

const STOPWORDS = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "by",
  "for",
  "from",
  "has",
  "have",
  "in",
  "is",
  "it",
  "of",
  "on",
  "or",
  "that",
  "the",
  "this",
  "to",
  "use",
  "when",
  "with",
]);

interface SkillDocument {
  name: string;
  title: string;
  description: string;
  category: string;
  tags: string;
  aliases: string;
  headings: string;
  body: string;
  kind: SkillKind;
}

export interface SearchResult {
  name: string;
  description: string;
  kind: SkillKind;
  category?: string;
  score: number;
  aliases: string[];
  matchingSections: string[];
  entrypointPriority?: number;
}

export interface SearchIndex {
  engine: MiniSearch<SkillDocument>;
  sectionTerms: Map<string, Map<string, Set<string>>>;
  docCount: number;
}

export interface PrecomputedSearchDocument {
  name: string;
  title: string;
  description: string;
  category: string;
  tags: string;
  aliases: string;
  headings: string;
  body: string;
  kind: SkillKind;
}

export interface SerializedSearchIndex {
  version?: string;
  engine?: AsPlainObject;
  documents?: PrecomputedSearchDocument[];
  sectionTerms: Record<string, Record<string, string[]>>;
  docCount: number;
}

export interface SearchOptions {
  limit?: number;
  kind?: SkillKind;
  category?: string;
}

const STORED_FIELDS: (keyof SkillDocument)[] = ["description", "kind", "category"];

const MINISEARCH_OPTIONS = {
  fields: ["title", "description", "category", "tags", "aliases", "headings", "body"],
  storeFields: STORED_FIELDS as string[],
  idField: "name",
  tokenize,
  searchOptions: {
    boost: {
      title: 3,
      description: 2,
      tags: 2,
      aliases: 2,
      headings: 1.5,
      body: 1,
    },
  },
};

export function buildIndex(skills: Map<string, Skill>): SearchIndex {
  const engine = new MiniSearch<SkillDocument>(MINISEARCH_OPTIONS);
  const sectionTerms = new Map<string, Map<string, Set<string>>>();
  const documents: SkillDocument[] = [];

  for (const [name, skill] of skills) {
    documents.push({
      name,
      title: name.replace(/-/g, " "),
      description: skill.description,
      category: skill.category ?? "",
      tags: skill.tags.join(" "),
      aliases: skill.aliases.join(" "),
      headings: skill.sections.map((section) => section.heading).join(" "),
      body: skill.content,
      kind: skill.kind,
    });
    sectionTerms.set(name, buildSectionTerms(skill));
  }

  engine.addAll(documents);

  return {
    engine,
    sectionTerms,
    docCount: documents.length,
  };
}

export function search(
  index: SearchIndex,
  query: string,
  skills: Map<string, Skill>,
  options?: SearchOptions,
): SearchResult[] {
  const limit = Math.max(1, Math.min(options?.limit ?? 10, 50));
  const queryTerms = tokenize(query);
  if (queryTerms.length === 0) return [];

  const results = index.engine.search(query, {
    prefix: true,
    fuzzy: 0.2,
    combineWith: "AND",
    filter: (result) => {
      if (options?.kind && result.kind !== options.kind) return false;
      if (options?.category && result.category !== options.category) return false;
      return true;
    },
  });

  return results.slice(0, limit).map((result) => {
    const skill = skills.get(result.id as string);
    const matchingSections = collectMatchingSections(
      index.sectionTerms.get(result.id as string),
      queryTerms,
    );

    return {
      name: result.id as string,
      description: (result.description as string) ?? skill?.description ?? "",
      kind: (result.kind as SkillKind) ?? skill?.kind ?? "workflow",
      category: (result.category as string) || skill?.category,
      score: result.score,
      aliases: skill?.aliases ?? [],
      matchingSections,
      entrypointPriority: skill?.entrypointPriority,
    };
  });
}

export function serializeIndex(index: SearchIndex): SerializedSearchIndex {
  const sectionTerms: Record<string, Record<string, string[]>> = {};

  for (const [skillName, sections] of index.sectionTerms) {
    sectionTerms[skillName] = {};
    for (const [heading, terms] of sections) {
      sectionTerms[skillName][heading] = Array.from(terms);
    }
  }

  return {
    engine: index.engine.toJSON(),
    sectionTerms,
    docCount: index.docCount,
  };
}

export function deserializeIndex(data: SerializedSearchIndex): SearchIndex | null {
  if (data.engine && typeof data.engine.serializationVersion === "number") {
    const engine = MiniSearch.loadJS<SkillDocument>(data.engine, MINISEARCH_OPTIONS);
    const sectionTerms = new Map<string, Map<string, Set<string>>>();

    for (const [skillName, sections] of Object.entries(data.sectionTerms)) {
      const sectionMap = new Map<string, Set<string>>();
      for (const [heading, terms] of Object.entries(sections)) {
        sectionMap.set(heading, new Set(terms));
      }
      sectionTerms.set(skillName, sectionMap);
    }

    return {
      engine,
      sectionTerms,
      docCount: data.docCount,
    };
  }

  if (data.version === "apple-text-search-v1" && Array.isArray(data.documents)) {
    const engine = new MiniSearch<SkillDocument>(MINISEARCH_OPTIONS);
    engine.addAll(data.documents);

    const sectionTerms = new Map<string, Map<string, Set<string>>>();
    for (const [skillName, sections] of Object.entries(data.sectionTerms)) {
      const sectionMap = new Map<string, Set<string>>();
      for (const [heading, terms] of Object.entries(sections)) {
        sectionMap.set(heading, new Set(terms));
      }
      sectionTerms.set(skillName, sectionMap);
    }

    return {
      engine,
      sectionTerms,
      docCount: data.docCount,
    };
  }

  return null;
}

function tokenize(text: string): string[] {
  return text
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .toLowerCase()
    .split(/[^a-z0-9@]+/)
    .filter((term) => term.length > 1 && !STOPWORDS.has(term));
}

function buildSectionTerms(skill: Skill): Map<string, Set<string>> {
  const lines = skill.content.split("\n");
  const sections = new Map<string, Set<string>>();

  for (const section of skill.sections) {
    const body = lines.slice(section.startLine, section.endLine + 1).join(" ");
    sections.set(section.heading, new Set(tokenize(`${section.heading} ${body}`)));
  }

  return sections;
}

function collectMatchingSections(
  sectionTerms: Map<string, Set<string>> | undefined,
  queryTerms: string[],
): string[] {
  if (!sectionTerms) return [];

  const matches: string[] = [];
  for (const [heading, terms] of sectionTerms) {
    if (queryTerms.some((term) => terms.has(term))) {
      matches.push(heading);
    }
  }

  return matches;
}
