# Apple Text MCP Server

Model Context Protocol server for the Apple Text skills collection.

It exposes:

- Apple Text skills as MCP resources
- repo commands as MCP prompts
- read-only tools for ask-style routing, catalog lookup, search, skill reads, and agent inspection

Apple Text MCP is a read-only knowledge server. If you also want build, test, and project actions from Xcode, run Apple's separate Xcode MCP bridge alongside it with `xcrun mcpbridge`.

For generic MCP clients, the main front door is `apple_text_ask`. If you want the lower-level route-first flow, call `apple_text_route` and then follow its suggested `apple_text_read_skill` call.

The repo also keeps a committed source bundle at `mcp-server/bundle.json` so hooks and CI can verify MCP data freshness without compiling TypeScript first.
`mcp-server/skill-annotations.json` is generated from `skills/catalog.json` plus optional hand-tuned overrides in `mcp-server/skill-annotations.overrides.json`.

## Install

### Published package

Once `apple-text-mcp` is published to npm, MCP clients can launch it directly with:

```bash
npx -y apple-text-mcp
```

### Development from this repo

```bash
cd mcp-server
npm install
npm run build
npm run smoke:dev
npm run start:dev
```

That runs against the live repo one directory above `mcp-server/`.

### Production bundle

```bash
cd mcp-server
npm install
npm run build:bundle
npm start
```

Production mode reads `dist/bundle.json`, so it does not need the repo files after build.

### From the repo root

```bash
npm run setup
npm run mcp:bundle
npm run mcp:smoke
npm run mcp:start
```

That path validates the bundled production server and still leaves `npm run mcp:start` available for live-repo development mode.

## Use Alongside Xcode Tools

Apple Text and Xcode serve different purposes:

- `apple-text` provides text-system guidance, search, and references
- `xcode` via `xcrun mcpbridge` provides Xcode actions

For Codex:

```bash
codex mcp add xcode -- xcrun mcpbridge
```

## Keeping It Current

From the repo root:

```bash
npm run mcp:generate
npm run mcp:check
```

- `mcp:generate` refreshes `mcp-server/skill-annotations.json` and `mcp-server/bundle.json`
- `mcp:check` fails if either generated file is stale

The repo hook and main `npm run check` path both run this validation now.

## Publish Workflow

### Local Dry Run

```bash
npm run setup:all
npm run mcp:bundle
npm run mcp:smoke
npm run mcp:pack:check
npm run mcp:pack:dry-run
```

If the packed contents look correct, you can also run:

```bash
npm run mcp:publish:dry-run
```

### Actual Publish

The repo includes a GitHub Actions workflow that can dry-run the MCP package on manual dispatch and publish `apple-text-mcp` to npm on a version tag like `mcp-v1.0.1`.

Set the `NPM_TOKEN` repository secret before using the publish path.

## Example MCP Config

### Published package

```json
{
  "mcpServers": {
    "apple-text": {
      "command": "npx",
      "args": ["-y", "apple-text-mcp"]
    }
  }
}
```

### Local checkout

```json
{
  "mcpServers": {
    "apple-text": {
      "command": "node",
      "args": ["/absolute/path/to/apple-text/mcp-server/dist/index.js"],
      "env": {
        "APPLE_TEXT_MCP_MODE": "development",
        "APPLE_TEXT_DEV_PATH": "/absolute/path/to/apple-text"
      }
    }
  }
}
```

For bundled production use, omit the env vars and point to the built server.

If you also want Xcode actions, add a second MCP server for `xcrun mcpbridge`.

### VS Code + GitHub Copilot

Add to `settings.json`:

```json
{
  "github.copilot.chat.mcp.servers": {
    "apple-text": {
      "command": "node",
      "args": ["/absolute/path/to/apple-text/mcp-server/dist/index.js"],
      "env": {
        "APPLE_TEXT_MCP_MODE": "development",
        "APPLE_TEXT_DEV_PATH": "/absolute/path/to/apple-text"
      }
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "apple-text": {
      "command": "node",
      "args": ["/absolute/path/to/apple-text/mcp-server/dist/index.js"],
      "env": {
        "APPLE_TEXT_MCP_MODE": "development",
        "APPLE_TEXT_DEV_PATH": "/absolute/path/to/apple-text"
      }
    }
  }
}
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "apple-text": {
      "command": "node",
      "args": ["/absolute/path/to/apple-text/mcp-server/dist/index.js"],
      "env": {
        "APPLE_TEXT_MCP_MODE": "development",
        "APPLE_TEXT_DEV_PATH": "/absolute/path/to/apple-text"
      }
    }
  }
}
```

### Gemini CLI

Add to `~/.gemini/config.toml`:

```toml
[[mcp_servers]]
name = "apple-text"
command = "node"
args = ["/absolute/path/to/apple-text/mcp-server/dist/index.js"]

[mcp_servers.env]
APPLE_TEXT_MCP_MODE = "development"
APPLE_TEXT_DEV_PATH = "/absolute/path/to/apple-text"
```

## Environment Variables

- `APPLE_TEXT_MCP_MODE`: `development` or `production` (default `production`)
- `APPLE_TEXT_DEV_PATH`: repo root to read in development mode
- `APPLE_TEXT_APPLE_DOCS`: `true` or `false` (default `false`) to enable Apple-authored markdown docs from the local Xcode install
- `APPLE_TEXT_XCODE_PATH`: override the `Xcode.app` path used for Apple docs discovery
- `APPLE_TEXT_MCP_LOG_LEVEL`: `debug`, `info`, `warn`, or `error`

## Exposed Surface

### Resources

- `apple-text://skill/{skill-name}`

### Prompts

- repo command markdown files from `../commands/`

### Tools

- `apple_text_ask`
- `apple_text_route`
- `apple_text_get_catalog`
- `apple_text_search_skills`
- `apple_text_read_skill`
- `apple_text_get_agent`

## Validation

- `npm run build` compiles the MCP package
- `npm run smoke` verifies the bundled production server through the official MCP SDK client
- `npm run smoke:dev` verifies the live development loader against the repo checkout
- `npm run pack:check` asserts the npm tarball includes the runnable server and bundle
- `npm run build:bundle` regenerates bundle data and compiles the production server
