#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "[start-prod] root: $ROOT_DIR"

echo "[start-prod] Frontend already built during Docker build — skipping npm install"

echo "[start-prod] Installing backend requirements (if needed)..."
cd "$ROOT_DIR/backend"

if [ -f requirements-prod.txt ]; then
  python -m pip install --upgrade pip setuptools wheel
  pip install --no-cache-dir -r requirements-prod.txt
elif [ -f requirements.txt ]; then
  python -m pip install --upgrade pip setuptools wheel
  pip install --no-cache-dir -r requirements.txt
fi

echo "[start-prod] Starting FastAPI server..."
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
