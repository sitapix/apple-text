import matter from "gray-matter";

export type SkillKind = "router" | "workflow" | "diag" | "decision" | "ref";

export interface SkillCatalogEntry {
  name: string;
  kind: SkillKind;
  category?: string;
  entrypoint_priority?: number;
  agent?: string;
}

export interface SkillAnnotation {
  category?: string;
  tags?: string[];
  aliases?: string[];
  related?: string[];
}

export interface SkillAnnotations {
  [skillName: string]: SkillAnnotation;
}

export interface SkillSection {
  heading: string;
  level: number;
  startLine: number;
  endLine: number;
  charCount: number;
}

export interface Skill {
  name: string;
  description: string;
  content: string;
  kind: SkillKind;
  category?: string;
  tags: string[];
  aliases: string[];
  relatedSkills: string[];
  entrypointPriority?: number;
  agent?: string;
  sections: SkillSection[];
}

export interface Command {
  name: string;
  description: string;
  content: string;
  argumentHints: string[];
}

export interface Agent {
  name: string;
  description: string;
  model?: string;
  tools: string[];
  content: string;
}

export function formatDisplayName(name: string): string {
  return name
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function parseSections(content: string): SkillSection[] {
  const lines = content.split("\n");
  const sections: SkillSection[] = [];
  let currentHeading: string | null = null;
  let currentLevel = 0;
  let currentStart = 0;

  for (let index = 0; index < lines.length; index += 1) {
    const match = lines[index].match(/^(#{1,6})\s+(.+)$/);
    if (match && match[1].length <= 2) {
      if (currentHeading !== null || (index > 0 && sections.length === 0)) {
        const heading = currentHeading ?? "_preamble";
        const sectionContent = lines.slice(currentStart, index).join("\n");
        sections.push({
          heading,
          level: currentHeading ? currentLevel : 0,
          startLine: currentStart,
          endLine: index - 1,
          charCount: sectionContent.length,
        });
      }

      currentHeading = match[2].trim();
      currentLevel = match[1].length;
      currentStart = index;
    } else if (index === 0 && !lines[index].match(/^#{1,2}\s/)) {
      currentHeading = null;
      currentStart = 0;
    }
  }

  const finalHeading = currentHeading ?? (sections.length === 0 ? "_preamble" : null);
  if (finalHeading !== null) {
    const sectionContent = lines.slice(currentStart).join("\n");
    sections.push({
      heading: finalHeading,
      level: currentHeading ? currentLevel : 0,
      startLine: currentStart,
      endLine: lines.length - 1,
      charCount: sectionContent.length,
    });
  }

  return sections;
}

export function parseSkill(
  content: string,
  fallbackName: string,
  catalogEntry?: SkillCatalogEntry,
  annotation?: SkillAnnotation,
): Skill {
  const parsed = matter(content);
  const data = parsed.data as Record<string, unknown>;
  const name = asString(data.name) ?? fallbackName;

  return {
    name,
    description: asString(data.description) ?? "",
    content: parsed.content.trim(),
    kind: catalogEntry?.kind ?? inferSkillKind(name),
    category: annotation?.category ?? catalogEntry?.category,
    tags: annotation?.tags ?? [],
    aliases: annotation?.aliases ?? [],
    relatedSkills: annotation?.related ?? [],
    entrypointPriority: catalogEntry?.entrypoint_priority,
    agent: catalogEntry?.agent,
    sections: parseSections(parsed.content.trim()),
  };
}

export function parseCommand(content: string, fallbackName: string): Command {
  const parsed = matter(content);
  const data = parsed.data as Record<string, unknown>;

  return {
    name: asString(data.name) ?? fallbackName,
    description: asString(data.description) ?? "",
    content: parsed.content.trim(),
    argumentHints: normalizeStringList(data["argument-hint"]),
  };
}

export function parseAgent(content: string, fallbackName: string): Agent {
  const parsed = matter(content);
  const data = parsed.data as Record<string, unknown>;

  return {
    name: asString(data.name) ?? fallbackName,
    description: asString(data.description) ?? "",
    model: asString(data.model),
    tools: normalizeStringList(data.tools),
    content: parsed.content.trim(),
  };
}

export function parseAppleDoc(
  content: string,
  filename: string,
  docType: "guide" | "diagnostic",
): Skill {
  const normalizedContent = content.trim();
  const baseName = filename.replace(/\.md$/, "");
  const slug = baseName
    .replace(/[^a-zA-Z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .toLowerCase();
  const name = `${docType === "diagnostic" ? "apple-diag" : "apple-guide"}-${slug}`;
  const title = extractAppleDocTitle(normalizedContent, baseName);
  const description = extractAppleDocDescription(normalizedContent, title);

  return {
    name,
    description,
    content: normalizedContent,
    kind: docType === "diagnostic" ? "diag" : "ref",
    category: undefined,
    tags: extractAppleDocTags(baseName),
    aliases: [],
    relatedSkills: [],
    sections: parseSections(normalizedContent),
  };
}

export function filterSkillSections(
  skill: Skill,
  sectionNames?: string[],
): { skill: Skill; content: string; sections: SkillSection[] } {
  if (!sectionNames || sectionNames.length === 0) {
    return { skill, content: skill.content, sections: skill.sections };
  }

  const lines = skill.content.split("\n");
  const needles = sectionNames.map((name) => name.toLowerCase());
  const matchedSections = skill.sections.filter((section) =>
    needles.some((needle) => section.heading.toLowerCase().includes(needle)),
  );

  const content = matchedSections
    .map((section) => lines.slice(section.startLine, section.endLine + 1).join("\n").trim())
    .filter(Boolean)
    .join("\n\n");

  return { skill, content, sections: matchedSections };
}

function inferSkillKind(name: string): SkillKind {
  if (name === "apple-text") return "router";
  if (name.endsWith("-diag")) return "diag";
  if (name.endsWith("-ref")) return "ref";
  if (
    name.includes("selection") ||
    name.includes("appkit-vs-uikit") ||
    name.endsWith("-views") ||
    name.endsWith("-parsing") ||
    name.endsWith("-swiftui-bridging")
  ) {
    return "decision";
  }

  return "workflow";
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function normalizeStringList(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === "string");
  }

  if (typeof value === "string") {
    return [value];
  }

  return [];
}

function extractAppleDocTitle(content: string, fallback: string): string {
  const titleMatch = content.match(/^#\s+(.+)$/m);
  return titleMatch ? titleMatch[1].trim() : fallback.replace(/-/g, " ");
}

function extractAppleDocDescription(content: string, fallback: string): string {
  const lines = content.split("\n");
  let pastTitle = false;

  for (const line of lines) {
    if (!pastTitle) {
      if (line.match(/^#\s+/)) {
        pastTitle = true;
      }
      continue;
    }

    const trimmed = line.trim();
    if (!trimmed) continue;
    if (trimmed.startsWith("#")) break;
    return trimmed;
  }

  return fallback;
}

function extractAppleDocTags(baseName: string): string[] {
  return baseName
    .split(/[-_]/)
    .map((token) => token.toLowerCase())
    .filter((token) => token.length > 2);
}
