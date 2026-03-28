#!/bin/sh

# Usage: npm run release -- 1.4.0
#
# One command to release Apple Text:
#   1. Bumps version across all manifests
#   2. Rebuilds all derived files (agents, docs, bundle, annotations)
#   3. Runs full validation
#   4. Commits everything
#   5. Tags (vX.Y.Z)
#   6. Pushes (pre-push hook runs full check again)
#
# After push, CI automatically:
#   - Validates (validate.yml)
#   - Deploys docs (deploy-docs.yml)
#   - Publishes MCP to npm (publish-mcp.yml, triggered by v* tag)

set -eu

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
  echo "Usage: npm run release -- X.Y.Z"
  echo ""
  CURRENT=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])")
  echo "Current version: $CURRENT"
  exit 1
fi

# Validate format
echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$' || {
  echo "ERROR: version must be X.Y.Z format"
  exit 1
}

ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"

echo "=== Releasing Apple Text v${VERSION} ==="
echo ""

# 1. Bump version in all manifests
echo "1. Bumping version..."
python3 tooling/scripts/release/set_version.py "$VERSION"
echo ""

# 2. Rebuild all derived files
echo "2. Rebuilding derived files..."
./scripts/regenerate.sh
echo ""

# 3. Run full validation
echo "3. Running full validation..."
./scripts/quality-check.sh --full
echo ""

# 4. Stage and commit
echo "4. Committing..."
git add -A
git commit -m "version ${VERSION}"
echo ""

# 5. Tag
echo "5. Tagging..."
git tag "v${VERSION}"
echo ""

# 6. Push
echo "6. Pushing..."
git push origin main "v${VERSION}"
echo ""

echo "=== Released Apple Text v${VERSION} ==="
echo ""
echo "CI will now:"
echo "  - Validate (validate.yml)"
echo "  - Deploy docs (deploy-docs.yml)"
echo "  - Publish MCP to npm (publish-mcp.yml)"
