#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Building MCP test image..."
docker compose build app

echo "🧪 Running pytest..."
docker compose run --rm app

