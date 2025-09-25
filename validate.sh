#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Validating MCP setup..."

# Config
HOST="${MCP_HOST:-localhost}"
PORT="${MCP_PORT:-8765}"

# 1. Ping MCP directly
echo "➡️  Sending list_schemas request to MCP at $HOST:$PORT"
printf '{"jsonrpc":"2.0","id":1,"method":"list_schemas"}\n' \
  | nc "$HOST" "$PORT" \
  | tee /tmp/mcp_validate_ping.json

if grep -q '"result"' /tmp/mcp_validate_ping.json; then
  echo "✅ MCP responded with schemas"
else
  echo "❌ MCP did not return schemas"
  exit 1
fi

# 2. Run Labs generate (requires labs installed / in repo)
echo "➡️  Running Labs generate test"
MCP_ENDPOINT=tcp MCP_HOST=$HOST MCP_PORT=$PORT LABS_FAIL_FAST=1 \
python -m labs.cli generate --prompt "hello world shader test"

# 3. Check output logs
echo "➡️  Checking Labs output logs"
tail -n 5 meta/output/labs/experiments/*.jsonl || {
  echo "❌ No Labs output found"
  exit 1
}

echo "✅ Validation complete: MCP + Labs pipeline is working"
