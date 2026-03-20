import { readdir, readFile, stat } from "fs/promises";
import { join } from "path";
import { Logger } from "../config.js";
import { parseAppleDoc, type Skill } from "./parser.js";

export interface XcodeDocsConfig {
  xcodePath: string;
  additionalDocsPath: string | null;
  diagnosticsPath: string | null;
}

const DEFAULT_XCODE_PATH = "/Applications/Xcode.app";
const ADDITIONAL_DOCS_SUBPATH =
  "Contents/PlugIns/IDEIntelligenceChat.framework/Versions/A/Resources/AdditionalDocumentation";
const DIAGNOSTICS_SUBPATH =
  "Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/share/doc/swift/diagnostics";

async function isDirectory(path: string): Promise<boolean> {
  try {
    return (await stat(path)).isDirectory();
  } catch {
    return false;
  }
}

export async function detectXcode(overridePath?: string): Promise<XcodeDocsConfig | null> {
  const xcodePath = overridePath ?? DEFAULT_XCODE_PATH;
  if (!(await isDirectory(xcodePath))) {
    return null;
  }

  const additionalDocsPath = join(xcodePath, ADDITIONAL_DOCS_SUBPATH);
  const diagnosticsPath = join(xcodePath, DIAGNOSTICS_SUBPATH);
  const hasAdditionalDocs = await isDirectory(additionalDocsPath);
  const hasDiagnostics = await isDirectory(diagnosticsPath);

  if (!hasAdditionalDocs && !hasDiagnostics) {
    return null;
  }

  return {
    xcodePath,
    additionalDocsPath: hasAdditionalDocs ? additionalDocsPath : null,
    diagnosticsPath: hasDiagnostics ? diagnosticsPath : null,
  };
}

export async function loadAppleDocs(
  config: XcodeDocsConfig,
  logger: Logger,
): Promise<Map<string, Skill>> {
  const docs = new Map<string, Skill>();

  if (config.additionalDocsPath !== null) {
    const loaded = await loadAppleDocDirectory(config.additionalDocsPath, "guide", docs, logger);
    logger.info(`Loaded ${loaded} Apple guides from Xcode AdditionalDocumentation`);
  }

  if (config.diagnosticsPath !== null) {
    const loaded = await loadAppleDocDirectory(config.diagnosticsPath, "diagnostic", docs, logger);
    logger.info(`Loaded ${loaded} Apple diagnostics from Xcode toolchain`);
  }

  return docs;
}

async function loadAppleDocDirectory(
  directory: string,
  docType: "guide" | "diagnostic",
  docs: Map<string, Skill>,
  logger: Logger,
): Promise<number> {
  let loaded = 0;

  try {
    const files = (await readdir(directory)).filter((entry) => entry.endsWith(".md"));
    for (const file of files) {
      try {
        const content = await readFile(join(directory, file), "utf-8");
        const skill = parseAppleDoc(content, file, docType);
        docs.set(skill.name, skill);
        loaded += 1;
      } catch (error) {
        logger.warn(`Failed to parse Apple ${docType} doc ${file}:`, error);
      }
    }
  } catch (error) {
    logger.warn(`Failed to read Apple ${docType} docs from ${directory}:`, error);
  }

  return loaded;
}
