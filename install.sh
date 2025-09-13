# install.sh
#!/usr/bin/env bash
set -euo pipefail

# clean out stray venv
rm -rf .venv

# install pinned deps
pip install -r requirements.txt

# install this repo editable
pip install -e .
