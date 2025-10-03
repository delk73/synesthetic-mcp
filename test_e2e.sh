#!/usr/bin/env bash
set -euo pipefail

MCP="python -m mcp"
TMP_OUT="$(mktemp)"

# Run all E2E scenarios, capture stdout into $TMP_OUT
{
  # list_schemas
  echo '{"jsonrpc":"2.0","id":1,"method":"list_schemas","params":{}}' \
    | $MCP 2>stderr.log

  # oversized payload
  python - <<'EOF' | $MCP 2>stderr.log
import json
payload = {
  "jsonrpc": "2.0",
  "id": 2,
  "method": "validate_asset",
  "params": {
    "asset": {"$schema": "jsonschema/synesthetic-asset.schema.json", "blob": "x" * 1200000}
  }
}
print(json.dumps(payload))
EOF

  # missing schema
  echo '{"jsonrpc":"2.0","id":3,"method":"validate_asset","params":{"asset":{"id":"dummy"}}}' \
    | $MCP 2>stderr.log

  # unsupported method
  echo '{"jsonrpc":"2.0","id":4,"method":"no_such_method","params":{}}' \
    | $MCP 2>stderr.log
} >"$TMP_OUT"

# Compare with golden file
diff -u tests/fixtures/e2e_golden.jsonl "$TMP_OUT"

echo "E2E test passed (output matches golden)."
