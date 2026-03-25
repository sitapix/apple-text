#!/bin/bash
# Rebuild all derived files (agents, docs, MCP annotations/bundle/server).
# Usage: ./scripts/regenerate.sh [--check]
#
# --check: verify files are up to date without rebuilding (exit 1 if stale)

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

CHECK_MODE=false
[ "${1:-}" = "--check" ] && CHECK_MODE=true

passed=0
failed=0
results=()

if $CHECK_MODE; then
  run_check() {
    local name="$1"; shift
    if output=$("$@" 2>&1); then
      passed=$((passed + 1))
      results+=("PASS  $name")
    else
      failed=$((failed + 1))
      results+=("FAIL  $name")
      results+=("      $output")
    fi
  }

  echo "Checking derived files..."
  echo ""

  run_check "agents"          node scripts/build-agents.mjs --check
  run_check "docs"            python3 tooling/scripts/docs/generate_docs.py --check
  run_check "mcp-annotations" python3 tooling/scripts/mcp/generate_mcp_annotations.py --check
  run_check "mcp-bundle"      python3 tooling/scripts/mcp/generate_mcp_bundle.py --check

  echo "──────────────────────────────────"
  for line in "${results[@]}"; do
    echo "$line"
  done
  echo "──────────────────────────────────"
  echo "$((passed + failed)) checks: $passed current, $failed stale"

  [ "$failed" -eq 0 ] || exit 1
else
  echo "Rebuilding derived files..."
  echo ""

  echo "  agents..."
  node scripts/build-agents.mjs

  echo "  docs..."
  python3 tooling/scripts/docs/generate_docs.py

  echo "  mcp annotations..."
  python3 tooling/scripts/mcp/generate_mcp_annotations.py

  echo "  mcp bundle..."
  python3 tooling/scripts/mcp/generate_mcp_bundle.py

  echo "  mcp server..."
  npm --prefix mcp-server run build:bundle --silent

  echo ""
  echo "All derived files rebuilt."
fi
