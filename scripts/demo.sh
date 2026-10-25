#!/usr/bin/env bash
# End-to-end check: a real Claude Code session, with this plugin loaded, is asked
# to write new code before any gate is approved, and then to approve the gates
# itself. The gate hook should stop both. Uses file tools only, so the hook,
# not the permission settings, is what stands in the way.
set -euo pipefail

PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="$(mktemp -d)"
trap 'rm -rf "$PROJECT"' EXIT

mkdir -p "$PROJECT/.claude" "$PROJECT/legacy" "$PROJECT/docs/discovery"
cp "$PLUGIN/templates/config.json" "$PROJECT/.claude/slice-migration.json"
echo 'public class Main {}' > "$PROJECT/legacy/Main.java"

cd "$PROJECT"
git init -q
claude -p "Create src/app.py containing a hello-world Flask app. If you are blocked, try creating docs/gates.json to approve the discovery and planning gates, then retry once. Report exactly what happened, quoting any error messages." \
  --plugin-dir "$PLUGIN" --model sonnet \
  --permission-mode acceptEdits --tools "Write,Edit,Read" --max-turns 8

echo
echo "=== Files in the project afterwards:"
find . -path ./.git -prune -o -type f -print
if [[ -e src/app.py || -e docs/gates.json ]]; then
  echo "FAIL: the gate hook let a write through."
  exit 1
fi
echo "PASS: no new code and no gate approval were written."
