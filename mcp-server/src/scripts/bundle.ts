#!/usr/bin/env node

import { mkdir, readdir, readFile, writeFile } from "fs/promises";
import { join } from "path";
import { fileURLToPath } from "url";
import { buildCatalog } from "../catalog/index.js";
import {
  parseAgent,
  parseCommand,
  parseSkill,
  type Agent,
  type Command,
  type Skill,
  type SkillCatalogEntry,
} from "../loader/parser.js";
import type { BundleV1 } from "../loader/types.js";
import { buildIndex, serializeIndex } from "../search/index.js";

async function main(): Promise<void> {
  const repoPath = process.argv[2] ? join(process.cwd(), process.argv[2]) : join(process.cwd(), "..");
  const outputDir = join(process.cwd(), "dist");
  const outputPath = join(outputDir, "bundle.json");

  const bundle = await generateBundle(repoPath);
  await mkdir(outputDir, { recursive: true });
  await writeFile(outputPath, `${JSON.stringify(bundle, null, 2)}\n`, "utf-8");

  console.log(`Wrote Apple Text MCP bundle to ${outputPath}`);
  console.log(`Skills: ${Object.keys(bundle.skills).length}`);
  console.log(`Commands: ${Object.keys(bundle.commands).length}`);
  console.log(`Agents: ${Object.keys(bundle.agents).length}`);
}

async function generateBundle(repoPath: string): Promise<BundleV1> {
  const skills = new Map<string, Skill>();
  const commands = new Map<string, Command>();
  const agents = new Map<string, Agent>();
  const catalogEntries = await loadSkillCatalog(repoPath);

  for (const directory of await walkSkillDirectories(join(repoPath, "skills"))) {
    const skillPath = join(directory.path, "SKILL.md");
    const content = await readFile(skillPath, "utf-8");
    const skill = parseSkill(content, directory.name, catalogEntries.get(directory.name));
    skills.set(skill.name, skill);
  }

  for (const entry of await readdir(join(repoPath, "commands"), { withFileTypes: true })) {
    if (!entry.isFile() || !entry.name.endsWith(".md")) continue;
    const content = await readFile(join(repoPath, "commands", entry.name), "utf-8");
    const name = entry.name.replace(/\.md$/, "");
    const command = parseCommand(content, name);
    commands.set(command.name, command);
  }

  for (const entry of await readdir(join(repoPath, "agents"), { withFileTypes: true })) {
    if (!entry.isFile() || !entry.name.endsWith(".md")) continue;
    const content = await readFile(join(repoPath, "agents", entry.name), "utf-8");
    const name = entry.name.replace(/\.md$/, "");
    const agent = parseAgent(content, name);
    agents.set(agent.name, agent);
  }

  const searchIndex = buildIndex(skills);
  const catalog = buildCatalog(skills, agents);

  return {
    version: "0.1.0",
    generatedAt: new Date().toISOString(),
    skills: Object.fromEntries(skills),
    commands: Object.fromEntries(commands),
    agents: Object.fromEntries(agents),
    catalog,
    searchIndex: serializeIndex(searchIndex),
  };
}

async function loadSkillCatalog(repoPath: string): Promise<Map<string, SkillCatalogEntry>> {
  const catalogPath = join(repoPath, "skills", "catalog.json");
  const raw = await readFile(catalogPath, "utf-8");
  const parsed = JSON.parse(raw) as { skills?: SkillCatalogEntry[] };
  const entries = new Map<string, SkillCatalogEntry>();

  for (const entry of parsed.skills ?? []) {
    entries.set(entry.name, entry);
  }

  return entries;
}

async function walkSkillDirectories(root: string): Promise<Array<{ name: string; path: string }>> {
  const directories: Array<{ name: string; path: string }> = [];

  const walk = async (currentPath: string): Promise<void> => {
    for (const entry of await readdir(currentPath, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;

      const directoryPath = join(currentPath, entry.name);
      const children = await readdir(directoryPath, { withFileTypes: true });
      if (children.some((child) => child.isFile() && child.name === "SKILL.md")) {
        directories.push({ name: entry.name, path: directoryPath });
      }

      await walk(directoryPath);
    }
  };

  await walk(root);
  return directories.sort((left, right) => left.name.localeCompare(right.name));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error("Failed to build Apple Text MCP bundle:", error);
    process.exit(1);
  });
}
