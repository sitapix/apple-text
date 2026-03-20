export type ServerMode = "development" | "production";

export interface Config {
  mode: ServerMode;
  devSourcePath?: string;
  xcodePath?: string;
  enableAppleDocs: boolean;
  logLevel: "debug" | "info" | "warn" | "error";
}

export function loadConfig(): Config {
  const mode = normalizeMode(process.env.APPLE_TEXT_MCP_MODE);
  const logLevel = normalizeLogLevel(process.env.APPLE_TEXT_MCP_LOG_LEVEL);
  const devSourcePath = mode === "development" ? process.env.APPLE_TEXT_DEV_PATH : undefined;
  const xcodePath = process.env.APPLE_TEXT_XCODE_PATH;
  const enableAppleDocs = normalizeBoolean(process.env.APPLE_TEXT_APPLE_DOCS, false);

  return {
    mode,
    devSourcePath,
    xcodePath,
    enableAppleDocs,
    logLevel,
  };
}

function normalizeMode(value: string | undefined): ServerMode {
  return value === "development" ? "development" : "production";
}

function normalizeLogLevel(value: string | undefined): Config["logLevel"] {
  switch (value) {
    case "debug":
    case "warn":
    case "error":
      return value;
    default:
      return "info";
  }
}

function normalizeBoolean(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined) return fallback;
  return value.toLowerCase() !== "false";
}

export class Logger {
  private readonly levels: Config["logLevel"][] = ["debug", "info", "warn", "error"];
  private readonly minLevel: number;

  constructor(private readonly config: Config) {
    this.minLevel = this.levels.indexOf(config.logLevel);
  }

  debug(message: string, ...args: unknown[]): void {
    if (this.minLevel <= 0) {
      console.error("[DEBUG]", message, ...args);
    }
  }

  info(message: string, ...args: unknown[]): void {
    if (this.minLevel <= 1) {
      console.error("[INFO]", message, ...args);
    }
  }

  warn(message: string, ...args: unknown[]): void {
    if (this.minLevel <= 2) {
      console.error("[WARN]", message, ...args);
    }
  }

  error(message: string, ...args: unknown[]): void {
    if (this.minLevel <= 3) {
      console.error("[ERROR]", message, ...args);
    }
  }
}
