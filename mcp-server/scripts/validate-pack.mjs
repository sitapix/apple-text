import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const requiredEntries = [
  "package.json",
  "README.md",
  "LICENSE",
  "dist/index.js",
  "dist/bundle.json",
];

try {
  const { stdout } = await execFileAsync(
    "npm",
    ["pack", "--json", "--dry-run", "--cache", "../.npm-cache"],
    { cwd: process.cwd() },
  );

  const parsed = JSON.parse(stdout);
  const packResult = Array.isArray(parsed) ? parsed[0] : parsed;
  const files = Array.isArray(packResult?.files) ? packResult.files.map((file) => file.path) : [];

  for (const entry of requiredEntries) {
    if (!files.includes(entry)) {
      throw new Error(`npm pack output is missing required entry: ${entry}`);
    }
  }

  console.log(
    JSON.stringify(
      {
        packageName: packResult?.name,
        requiredEntries,
        fileCount: files.length,
      },
      null,
      2,
    ),
  );
} catch (error) {
  console.error(
    `Apple Text MCP pack validation failed: ${error instanceof Error ? error.message : String(error)}`,
  );
  process.exit(1);
}
