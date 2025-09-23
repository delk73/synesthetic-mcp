#!/usr/bin/env bash
set -euo pipefail

SERVICE=serve

echo "🚀 Building image for '$SERVICE'..."
docker compose build "$SERVICE"

echo "🚀 Running '$SERVICE' (foreground)..."
# Run interactively so you can see logs, and container exits cleanly
docker compose run --rm "$SERVICE"
