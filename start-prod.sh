#!/usr/bin/env bash
set -euo pipefail

echo "[start-prod] Med Guardian production start"
echo "[start-prod] Frontend is already built inside Docker image"
echo "[start-prod] Skipping npm build (not available in runtime container)"

echo "[start-prod] Starting FastAPI backend..."
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
