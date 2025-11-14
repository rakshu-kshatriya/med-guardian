#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "[start-prod] root: $ROOT_DIR"

echo "[start-prod] Frontend already built in Docker → SKIPPING npm install"
echo "[start-prod] Frontend already built in Docker → SKIPPING npm run build"

echo "[start-prod] Installing backend dependencies..."
cd "$ROOT_DIR/backend"
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements-prod.txt

echo "[start-prod] Starting FastAPI server..."
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
