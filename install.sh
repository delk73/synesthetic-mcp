#!/usr/bin/env bash
set -euo pipefail

# Ensure we start clean
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate

# Always upgrade pip
pip install --upgrade pip

# Install from pinned requirements
pip install -r requirements.txt

echo "✅ Environment ready. Activate with: source .venv/bin/activate"
