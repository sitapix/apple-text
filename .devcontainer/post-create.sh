#!/usr/bin/env bash

set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/.uv-cache}"
mkdir -p "$UV_CACHE_DIR"

if ! command -v uv >/dev/null 2>&1; then
  python3 -m pip install --user uv
  export PATH="$HOME/.local/bin:$PATH"
fi

if [ -f package.json ]; then
  npm install
fi

uv run python scripts/generate_docs.py
uv run python scripts/validate_plugin.py

if git rev-parse --show-toplevel >/dev/null 2>&1; then
  uv run python scripts/install_git_hooks.py
fi
