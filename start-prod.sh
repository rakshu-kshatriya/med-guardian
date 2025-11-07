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

# Optional: if SENTRY_DSN is provided at runtime, install sentry-sdk if not already present.
# This allows using Sentry without baking it into the image. Set SENTRY_INSTALL_ON_STARTUP=false
# to skip runtime installation and rely on a baked-in image instead.
if [ -n "${SENTRY_DSN:-}" ]; then
  SENTRY_INSTALL_ON_STARTUP=${SENTRY_INSTALL_ON_STARTUP:-true}
  if [ "$SENTRY_INSTALL_ON_STARTUP" != "false" ]; then
    echo "[start-prod] SENTRY_DSN detected; ensuring sentry-sdk is available..."
    # Check if sentry_sdk is importable; if not, install it.
    python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('sentry_sdk') else 1)" || {
      echo "[start-prod] sentry-sdk not found; installing sentry-sdk..."
      python -m pip install --no-cache-dir sentry-sdk
    }
  else
    echo "[start-prod] SENTRY_DSN set but SENTRY_INSTALL_ON_STARTUP=false; skipping runtime install"
  fi
fi

echo "[start-prod] Starting uvicorn backend..."
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
