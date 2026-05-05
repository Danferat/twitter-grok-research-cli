#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python 3, then run this script again."
  exit 1
fi

echo "Project root: $ROOT_DIR"
echo "Using Python: $($PYTHON_BIN --version)"

if [ ! -d ".venv" ]; then
  echo "Creating local virtual environment: .venv"
  "$PYTHON_BIN" -m venv .venv
else
  echo "Local virtual environment already exists: .venv"
fi

# shellcheck disable=SC1091
source ".venv/bin/activate"

echo "Preparing Python environment..."
python -m pip install --upgrade pip >/dev/null
if [ -s "requirements.txt" ]; then
  python -m pip install -r requirements.txt
fi

mkdir -p data/runs

if [ ! -f ".env" ]; then
  cp ".env.example" ".env"
  ENV_CREATED="yes"
else
  ENV_CREATED="no"
fi

echo "Running local tests..."
python -m unittest discover -s tests -v

echo
echo "Setup complete."
echo
if [ "$ENV_CREATED" = "yes" ]; then
  echo "A new .env file was created here:"
else
  echo "Your existing .env file is here:"
fi
echo "$ROOT_DIR/.env"
echo
echo "Open that file and replace the placeholder values:"
echo
echo "X_BEARER_TOKEN=your_x_api_bearer_token_here"
echo "XAI_API_KEY=your_xai_api_key_here"
echo "XAI_MODEL=grok-4.20-0309-reasoning"
echo
echo "Use X_BEARER_TOKEN for Twitter-only search."
echo "Use XAI_API_KEY for Grok-only search."
echo
echo "After adding keys, test with:"
echo "source .venv/bin/activate"
echo "python -m twitter_research --help"
echo "python -m twitter_research plan-query \"why is PUMP token down this week?\""
