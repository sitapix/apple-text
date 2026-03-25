#!/bin/bash
# Run all quality and validation checks.
# Usage: ./scripts/quality-check.sh [--full]
#
# Default: fast quality checks only (lint, descriptions, routing, freshness)
# --full:  adds staleness checks, MCP smoke/pack, python tests, doc links

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

FULL=false
[ "${1:-}" = "--full" ] && FULL=true

passed=0
failed=0
results=()

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

echo "Running quality checks..."
echo ""

# ── Always run ────────────────────────────────────────────────────────────────
run_check "repo-lint"           python3 tooling/scripts/quality/lint_repo.py
run_check "skill-validation"    bash scripts/validate-skills.sh
run_check "description-lint"    python3 tooling/scripts/quality/evaluate_skill_descriptions.py
run_check "description-dataset" python3 tooling/scripts/quality/evaluate_skill_descriptions.py --dataset tooling/evals/description-triggers.json
run_check "routing-evals"       python3 tooling/scripts/quality/validate_routing_evals.py
run_check "freshness"           python3 tooling/scripts/quality/skill_freshness.py --all
run_check "plugin-validation"   python3 tooling/scripts/quality/validate_plugin.py

# ── Full mode only ────────────────────────────────────────────────────────────
if $FULL; then
  run_check "agents-up-to-date"     node scripts/build-agents.mjs --check
  run_check "docs-up-to-date"       python3 tooling/scripts/docs/generate_docs.py --check
  run_check "mcp-annotations"       python3 tooling/scripts/mcp/generate_mcp_annotations.py --check
  run_check "mcp-bundle"            python3 tooling/scripts/mcp/generate_mcp_bundle.py --check
  run_check "mcp-server-build"      npm --prefix mcp-server run build:bundle --silent
  run_check "mcp-smoke"             npm --prefix mcp-server run smoke --silent
  run_check "mcp-pack"              npm --prefix mcp-server run pack:check --silent
  run_check "python-tests"          bash -c 'PYTHONPATH=tooling python3 -m unittest discover -s tooling/tests'
  run_check "doc-links"             python3 tooling/scripts/docs/validate_doc_links.py
fi

echo "──────────────────────────────────"
for line in "${results[@]}"; do
  echo "$line"
done
echo "──────────────────────────────────"
echo "$((passed + failed)) checks: $passed passed, $failed failed"

[ "$failed" -eq 0 ] || exit 1
