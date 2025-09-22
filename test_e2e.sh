#!/usr/bin/env bash
set -euo pipefail

MCP="python -m mcp"

echo "== E2E: list_schemas =="
echo '{"jsonrpc":"2.0","id":1,"method":"list_schemas","params":{}}' \
  | $MCP 2>stderr.log

echo "== E2E: oversized payload =="
python - <<'EOF' | $MCP 2>stderr.log
import json, sys
payload = {"jsonrpc":"2.0","id":2,"method":"validate_asset","params":{"asset":{"blob":"x"*1200000},"schema":"nested-synesthetic-asset"}}
print(json.dumps(payload))
EOF

echo "== E2E: missing schema =="
echo '{"jsonrpc":"2.0","id":3,"method":"validate_asset","params":{"asset":{"id":"dummy"}}}' \
  | $MCP 2>stderr.log

echo "== E2E: unsupported method =="
echo '{"jsonrpc":"2.0","id":4,"method":"no_such_method","params":{}}' \
  | $MCP 2>stderr.log
