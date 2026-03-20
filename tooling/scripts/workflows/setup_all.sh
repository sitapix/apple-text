#!/usr/bin/env bash

set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$ROOT"

python3 tooling/scripts/dev/bootstrap_dev.py "$@"
python3 tooling/scripts/docs/generate_docs.py
python3 tooling/scripts/mcp/generate_mcp_annotations.py
python3 tooling/scripts/mcp/generate_mcp_bundle.py

echo "Setup complete."
