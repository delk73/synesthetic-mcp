#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Synesthetic MCP setup (inside nix develop)..."

# Ensure we're in the same directory as this script
cd "$(dirname "$0")"

# Optional: clean slate if RESET_ENV=1
if [[ "${RESET_ENV:-0}" == "1" ]]; then
  echo "🧹 Resetting environment..."
  rm -rf .venv/ poetry.lock requirements.txt
  poetry cache clear pypi --all || true
  pip cache purge || true
fi

# Ensure Poetry venv exists
if [[ ! -d .venv ]]; then
  poetry env use python3.11
fi

# Try Poetry install with timeout (120s)
echo "📦 Installing dependencies via Poetry..."
if timeout 120s poetry install --sync -vvv; then
  echo "✅ Poetry install completed"
else
  echo "⚠️ Poetry install hung — falling back to pip"
  poetry export -f requirements.txt --without-hashes -o requirements.txt
  .venv/bin/pip install -r requirements.txt
fi

echo "🎉 Environment ready. Activate with: source .venv/bin/activate"
