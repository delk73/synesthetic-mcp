#!/bin/bash
set -euo pipefail

# Ensure schemas are checked out
git submodule update --init --recursive

# Optional backend preflight
if [ -n "${SYN_BACKEND_URL:-}" ]; then
  echo "Checking backend: $SYN_BACKEND_URL/health"
  curl -sf --max-time 3 "$SYN_BACKEND_URL/health" || {
    echo "Backend not reachable"; exit 1;
  }
fi

./test.sh
