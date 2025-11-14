#!/usr/bin/env bash
set -euo pipefail

echo "[start-prod] Production start script running..."

# BACKEND DIRECTORY
cd /app/backend

# Upgrade pip safely
python -m pip install --upgrade pip setuptools wheel

# Install backend requirements (if needed)
if [ -f requirements-prod.txt ]; then
    echo "[start-prod] Installing backend requirements..."
    pip install --no-cache-dir -r requirements-prod.txt
fi

# Optional: Install sentry-sdk if DSN provided
if [ -n "${SENTRY_DSN:-}" ]; then
    echo "[start-prod] Installing sentry-sdk..."
    python -m pip install --no-cache-dir sentry-sdk
fi

echo "[start-prod] Starting backend with uvicorn..."
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
