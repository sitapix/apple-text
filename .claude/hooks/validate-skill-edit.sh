#!/bin/bash
# PostToolUse hook: validate skills after editing SKILL.md files.
# Feeds errors back to Claude via additionalContext so it can self-correct.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only validate when a file under skills/ was edited
case "$FILE_PATH" in
  */skills/*/SKILL.md|*/skills/*/*.md) ;;
  *) echo '{"suppressOutput": true}'; exit 0 ;;
esac

cd "$CLAUDE_PROJECT_DIR"

# Run the validator
RESULT=$(./scripts/validate-skills.sh 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  # Escape the result for JSON
  ESCAPED=$(echo "$RESULT" | jq -Rs .)
  echo "{\"additionalContext\": $ESCAPED}"
else
  echo '{"suppressOutput": true}'
fi
