import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class McpRouteToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        result = subprocess.run(
            ["npm", "--prefix", "mcp-server", "run", "build"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stdout + result.stderr)

    def test_route_tool_prefers_view_decision_skill_for_view_choice_question(self) -> None:
        script = """
            import { Client } from "@modelcontextprotocol/sdk/client/index.js";
            import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

            const transport = new StdioClientTransport({
              command: "node",
              args: ["dist/index.js"],
              cwd: ".",
              env: {
                APPLE_TEXT_APPLE_DOCS: "false",
                APPLE_TEXT_MCP_LOG_LEVEL: "error",
                PATH: process.env.PATH ?? "",
                HOME: process.env.HOME ?? "",
              },
              stderr: "pipe",
            });

            const client = new Client({ name: "route-tool-test", version: "1.0.0" }, { capabilities: {} });

            try {
              await client.connect(transport);
              const response = await client.callTool({
                name: "apple_text_route",
                arguments: {
                  question: "Which text view should I use for my editor?",
                  limit: 2,
                },
              });
              console.log(response.content[0].text);
            } finally {
              await transport.close().catch(() => {});
            }
        """
        result = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT / "mcp-server",
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("Start with: apple-text-views", result.stdout)
        self.assertIn("apple_text_read_skill", result.stdout)


if __name__ == "__main__":
    unittest.main()
