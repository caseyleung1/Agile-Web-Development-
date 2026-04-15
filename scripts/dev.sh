#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[dev] Project root: $ROOT_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

pip install -r requirements.txt
npm install
npm run build:css

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
fi

python scripts/seed_demo.py || true

export FLASK_APP=run.py
exec flask run --debug
