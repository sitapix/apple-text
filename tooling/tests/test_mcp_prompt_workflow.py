import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class McpPromptWorkflowTests(unittest.TestCase):
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

    def test_ask_prompt_instructs_route_first_workflow(self) -> None:
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

            const client = new Client({ name: "prompt-workflow-test", version: "1.0.0" }, { capabilities: {} });

            try {
              await client.connect(transport);
              const prompt = await client.getPrompt({
                name: "ask",
                arguments: {
                  question: "How do I wrap UITextView in SwiftUI?",
                },
              });
              console.log(prompt.messages[0].content.text);
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
        self.assertIn("apple_text_route", result.stdout)
        self.assertIn("apple_text_read_skill", result.stdout)
        self.assertIn("How do I wrap UITextView in SwiftUI?", result.stdout)


if __name__ == "__main__":
    unittest.main()
