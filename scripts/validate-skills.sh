#!/bin/bash
# Validate Apple Text skills for common regressions.
# Runs as a pre-commit hook or standalone: ./scripts/validate-skills.sh

cd "$(git rev-parse --show-toplevel)"

tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT

for skill_dir in skills/*/; do
  skill=$(basename "$skill_dir")
  md="$skill_dir/SKILL.md"
  [ -f "$md" ] || continue

  # 1. No YAML multiline descriptions
  if grep -q '^description: >$' "$md" 2>/dev/null; then
    echo "FAIL [$skill]: YAML multiline description (use single-line)" >> "$tmpfile"
  fi

  # 2. Quick Decision section exists
  if ! grep -q '## Quick Decision' "$md" 2>/dev/null; then
    echo "FAIL [$skill]: missing ## Quick Decision section" >> "$tmpfile"
  fi

  # 3. Description under 1024 chars
  desc=$(sed -n '/^description:/{ s/^description: *//; s/^"//; s/"$//; p; }' "$md" | head -1)
  if [ ${#desc} -gt 1024 ]; then
    echo "FAIL [$skill]: description is ${#desc} chars (max 1024)" >> "$tmpfile"
  fi

  # 4. /skill cross-references resolve
  for ref in $(grep -oh '/skill [a-z0-9-]*' "$md" 2>/dev/null | sed 's|/skill ||'); do
    if [ ! -f "skills/$ref/SKILL.md" ]; then
      echo "FAIL [$skill]: broken cross-reference /skill $ref" >> "$tmpfile"
    fi
  done

  # 5. Relative .md file references resolve
  for ref in $(grep -oE '\]\([a-zA-Z0-9_-]+\.md\)' "$md" 2>/dev/null | sed 's/\](//;s/)//'); do
    if [ ! -f "$skill_dir/$ref" ]; then
      echo "FAIL [$skill]: broken file reference $ref" >> "$tmpfile"
    fi
  done
done

if [ -s "$tmpfile" ]; then
  cat "$tmpfile"
  count=$(wc -l < "$tmpfile" | tr -d ' ')
  echo ""
  echo "Skill validation failed with $count error(s)."
  exit 1
else
  echo "All skills valid."
fi
