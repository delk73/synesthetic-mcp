#!/usr/bin/env bash
set -euo pipefail

SCHEMAS_DIR=${SYN_SCHEMAS_DIR:-/app/libs/synesthetic-schemas}

echo "🚀 Starting MCP server container with schemas at $SCHEMAS_DIR"
docker run --rm -it \
  --name synesthetic-mcp-serve \
  -e SYN_SCHEMAS_DIR=$SCHEMAS_DIR \
  synesthetic-mcp \
  python -m mcp
