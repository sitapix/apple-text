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
  documentTerms: Map<string, Set<string>>;
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
  documentTerms?: Record<string, string[]>;
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
  const documentTerms = new Map<string, Set<string>>();
  const documents: SkillDocument[] = [];

  for (const [name, skill] of skills) {
    const document = {
      name,
      title: name.replace(/-/g, " "),
      description: skill.description,
      category: skill.category ?? "",
      tags: skill.tags.join(" "),
      aliases: skill.aliases.join(" "),
      headings: skill.sections.map((section) => section.heading).join(" "),
      body: skill.content,
      kind: skill.kind,
    };

    documents.push(document);
    sectionTerms.set(name, buildSectionTerms(skill));
    documentTerms.set(
      name,
      new Set(
        keywordTerms(
          [
            document.title,
            document.description,
            document.category,
            document.tags,
            document.aliases,
            document.headings,
            document.body,
          ].join(" "),
        ),
      ),
    );
  }

  engine.addAll(documents);

  return {
    engine,
    sectionTerms,
    documentTerms,
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
  const queryTerms = keywordTerms(query);
  if (queryTerms.length === 0) return [];

  const results =
    runSearch(index, query, options, "AND") || fallbackSearch(index, query, queryTerms, options);

  if (!results) return [];

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
  const documentTerms: Record<string, string[]> = {};

  for (const [skillName, sections] of index.sectionTerms) {
    sectionTerms[skillName] = {};
    for (const [heading, terms] of sections) {
      sectionTerms[skillName][heading] = Array.from(terms);
    }
  }

  for (const [skillName, terms] of index.documentTerms) {
    documentTerms[skillName] = Array.from(terms);
  }

  return {
    engine: index.engine.toJSON(),
    sectionTerms,
    documentTerms,
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

    const documentTerms = new Map<string, Set<string>>();
    for (const [skillName, terms] of Object.entries(data.documentTerms ?? {})) {
      documentTerms.set(skillName, new Set(terms));
    }

    return {
      engine,
      sectionTerms,
      documentTerms,
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

    const documentTerms = new Map<string, Set<string>>();
    for (const document of data.documents) {
      documentTerms.set(
        document.name,
        new Set(
          keywordTerms(
            [
              document.title,
              document.description,
              document.category,
              document.tags,
              document.aliases,
              document.headings,
              document.body,
            ].join(" "),
          ),
        ),
      );
    }

    return {
      engine,
      sectionTerms,
      documentTerms,
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

function keywordTerms(text: string): string[] {
  return text
    .toLowerCase()
    .split(/[^a-z0-9@]+/)
    .filter((term) => term.length > 1 && !STOPWORDS.has(term));
}

function runSearch(
  index: SearchIndex,
  query: string,
  options: SearchOptions | undefined,
  combineWith: "AND" | "OR",
) {
  const results = index.engine.search(query, {
    prefix: true,
    fuzzy: 0.2,
    combineWith,
    filter: (result) => {
      if (options?.kind && result.kind !== options.kind) return false;
      if (options?.category && result.category !== options.category) return false;
      return true;
    },
  });

  return results.length > 0 ? results : null;
}

function fallbackSearch(
  index: SearchIndex,
  query: string,
  queryTerms: string[],
  options?: SearchOptions,
) {
  const results = runSearch(index, query, options, "OR");
  if (!results) return null;

  const minimumCoverage = queryTerms.length <= 2 ? 1 : 2;
  const ranked = results
    .map((result) => {
      const name = result.id as string;
      const matchedTerms = countMatchedTerms(index.documentTerms.get(name), queryTerms);
      const matchedNameTerms = countLooseMatchedTerms(keywordTerms(name), queryTerms);
      const matchedSections = collectMatchingSections(index.sectionTerms.get(name), queryTerms).length;

      return {
        result,
        matchedTerms,
        matchedNameTerms,
        matchedSections,
      };
    })
    .filter(({ matchedTerms }) => matchedTerms >= minimumCoverage);

  const candidates =
    ranked.length > 0
      ? ranked
      : results
          .map((result) => {
            const name = result.id as string;
            return {
              result,
              matchedTerms: countMatchedTerms(index.documentTerms.get(name), queryTerms),
              matchedNameTerms: countLooseMatchedTerms(keywordTerms(name), queryTerms),
              matchedSections: collectMatchingSections(index.sectionTerms.get(name), queryTerms)
                .length,
            };
          })
          .filter(({ matchedTerms }) => matchedTerms > 0);

  return candidates
    .sort((left, right) => {
      return (
        right.matchedNameTerms - left.matchedNameTerms ||
        right.matchedTerms - left.matchedTerms ||
        right.matchedSections - left.matchedSections ||
        right.result.score - left.result.score ||
        String(left.result.id).localeCompare(String(right.result.id))
      );
    })
    .map(({ result }) => result);
}

function buildSectionTerms(skill: Skill): Map<string, Set<string>> {
  const lines = skill.content.split("\n");
  const sections = new Map<string, Set<string>>();

  for (const section of skill.sections) {
    const body = lines.slice(section.startLine, section.endLine + 1).join(" ");
    sections.set(section.heading, new Set(keywordTerms(`${section.heading} ${body}`)));
  }

  return sections;
}

function countMatchedTerms(documentTerms: Set<string> | undefined, queryTerms: string[]): number {
  if (!documentTerms) return 0;

  let count = 0;
  for (const term of queryTerms) {
    if (documentTerms.has(term)) {
      count += 1;
    }
  }

  return count;
}

function countLooseMatchedTerms(documentTerms: string[], queryTerms: string[]): number {
  let count = 0;

  for (const queryTerm of queryTerms) {
    if (
      documentTerms.some(
        (documentTerm) =>
          documentTerm === queryTerm ||
          documentTerm.startsWith(queryTerm) ||
          queryTerm.startsWith(documentTerm),
      )
    ) {
      count += 1;
    }
  }

  return count;
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
