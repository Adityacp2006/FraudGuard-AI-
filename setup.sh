#!/usr/bin/env bash
# One-shot environment setup for macOS/Linux.
#   chmod +x setup.sh && ./setup.sh
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "==> Creating virtual environment in .venv ..."
"$PYTHON_BIN" -m venv .venv

echo "==> Activating .venv ..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Upgrading pip ..."
pip install --upgrade pip -q

echo "==> Installing requirements.txt ..."
pip install -r requirements.txt -q

echo "==> Installing project in editable mode (so 'hhgoa_fraud' is importable) ..."
pip install -e . -q

if [ ! -f .env ]; then
    echo "==> Creating .env from .env.example ..."
    cp .env.example .env
else
    echo "==> .env already exists, leaving it untouched."
fi

echo ""
echo "Setup complete."
echo "Activate the environment in new shells with: source .venv/bin/activate"
echo "Next: place the HHGOA dataset files under data/, then run:"
echo "  python scripts/00_check_setup.py"
