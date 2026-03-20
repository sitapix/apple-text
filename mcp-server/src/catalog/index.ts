import { type Agent, type Skill, type SkillKind } from "../loader/parser.js";

export const KIND_LABELS: Record<SkillKind, string> = {
  router: "Routers",
  workflow: "Workflows",
  diag: "Diagnostics",
  decision: "Decisions",
  ref: "References",
};

const KIND_ORDER: SkillKind[] = ["router", "workflow", "diag", "decision", "ref"];

interface CatalogSkillEntry {
  name: string;
  description: string;
  aliases: string[];
  entrypointPriority?: number;
}

interface CatalogGroup {
  label: string;
  skills: CatalogSkillEntry[];
}

export interface CatalogResult {
  groups: Partial<Record<SkillKind, CatalogGroup>>;
  featured: CatalogSkillEntry[];
  agents: Array<{ name: string; description: string }>;
  totalSkills: number;
  totalAgents: number;
}

export function orderedKinds(): SkillKind[] {
  return [...KIND_ORDER];
}

export function buildCatalog(
  skills: Map<string, Skill>,
  agents: Map<string, Agent>,
  filterKind?: SkillKind,
): CatalogResult {
  const groups: Partial<Record<SkillKind, CatalogGroup>> = {};
  const featured: CatalogSkillEntry[] = [];
  let totalSkills = 0;

  for (const kind of KIND_ORDER) {
    groups[kind] = {
      label: KIND_LABELS[kind],
      skills: [],
    };
  }

  for (const skill of skills.values()) {
    if (filterKind && skill.kind !== filterKind) continue;

    const entry: CatalogSkillEntry = {
      name: skill.name,
      description: skill.description,
      aliases: skill.aliases,
      entrypointPriority: skill.entrypointPriority,
    };

    groups[skill.kind]?.skills.push(entry);
    totalSkills += 1;

    if (!filterKind && skill.entrypointPriority !== undefined) {
      featured.push(entry);
    }
  }

  for (const kind of KIND_ORDER) {
    groups[kind]!.skills.sort((left, right) => left.name.localeCompare(right.name));
    if (groups[kind]!.skills.length === 0) {
      delete groups[kind];
    }
  }

  featured.sort((left, right) => {
    const leftPriority = left.entrypointPriority ?? Number.MAX_SAFE_INTEGER;
    const rightPriority = right.entrypointPriority ?? Number.MAX_SAFE_INTEGER;
    return leftPriority - rightPriority || left.name.localeCompare(right.name);
  });

  const agentList = Array.from(agents.values())
    .map((agent) => ({ name: agent.name, description: agent.description }))
    .sort((left, right) => left.name.localeCompare(right.name));

  return {
    groups,
    featured,
    agents: filterKind ? [] : agentList,
    totalSkills,
    totalAgents: agents.size,
  };
}
