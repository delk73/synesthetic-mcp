#!/usr/bin/env bash
set -euo pipefail

# Helper script that builds the image and starts the 'serve' service without tailing logs.
SERVICE=serve

echo "🚀 Building image for '$SERVICE'..."
docker compose build "$SERVICE"

echo "🚀 Starting '$SERVICE' (detached)..."
docker compose up -d "$SERVICE"

echo "✅ MCP is running in background. Use 'docker compose logs -f serve' to tail logs."
