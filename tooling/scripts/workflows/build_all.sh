#!/usr/bin/env bash

set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$ROOT"

python3 tooling/scripts/mcp/generate_mcp_annotations.py
python3 tooling/scripts/mcp/generate_mcp_bundle.py
python3 tooling/scripts/docs/generate_docs.py
npm --prefix mcp-server run build:bundle
npm --prefix mcp-server run smoke
npm run docs:build

echo "Build complete."
