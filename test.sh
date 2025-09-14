#!/bin/bash
set -euo pipefail

echo 'Building MCP container image...'
docker compose build

echo 'Running pytest (container will remain)...'
docker compose up --build --exit-code-from app

echo '✅ MCP tests passed'
