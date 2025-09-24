#!/usr/bin/env bash
set -euo pipefail

SERVICE=serve
SOCKET_PATH="${MCP_SOCKET_PATH:-/tmp/mcp.sock}"

echo "🛑 Stopping '$SERVICE'..."
docker compose stop "$SERVICE" >/dev/null 2>&1 || true

echo "🧹 Removing '$SERVICE' container..."
docker compose rm -f "$SERVICE" >/dev/null 2>&1 || true

# Clean up socket file if it exists
if [ -S "$SOCKET_PATH" ]; then
  echo "🧽 Cleaning up leftover socket at $SOCKET_PATH"
  rm -f "$SOCKET_PATH"
fi

echo "✅ MCP shutdown complete."