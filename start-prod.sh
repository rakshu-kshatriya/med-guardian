#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "[start-prod] root: $ROOT_DIR"

echo "[start-prod] Installing frontend dependencies and building..."
cd "$ROOT_DIR/frontend"
if [ -f package-lock.json ]; then
  npm ci
else
  npm install --no-audit --no-fund
fi
npm run build

echo "[start-prod] Building done. Installing backend production requirements..."
cd "$ROOT_DIR/backend"
if [ -f requirements-prod.txt ]; then
  python -m pip install --upgrade pip setuptools wheel
  pip install -r requirements-prod.txt
elif [ -f requirements.txt ]; then
  # Defensive fallback for older setups that still reference requirements.txt
  python -m pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
fi

echo "[start-prod] Starting uvicorn backend..."
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
