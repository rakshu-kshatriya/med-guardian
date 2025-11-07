"""
FastAPI backend for Med Guardian - Disease prediction and advisory system.
Now configured to serve the Next.js static build automatically for Railway deployment.
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import pandas as pd
from datetime import datetime, timedelta
import logging
import asyncio
import json
import random
import os

from backend.city_data import CITIES, get_city_by_name
from backend.predictor import run_forecast
from backend.advisory_service import get_advisory
from backend.example_data import generate_synthetic_data, get_latest_trends
from backend.database import is_mongodb_available, get_trend_history, save_trend_data, save_news_item
from backend.redis_client import is_redis_available, cache_get, cache_set
from backend.news_ingest import fetch_combined_news, METRIC_NEWS_SAVED
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Load .env (optional for local dev)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Runtime config
MONGO_URI = os.getenv("MONGO_URI")
REDIS_URL = os.getenv("REDIS_URL")
SENTRY_DSN = os.getenv("SENTRY_DSN")

# Background ingestion
NEWS_INGEST_INTERVAL = int(os.environ.get("NEWS_INGEST_INTERVAL", "300"))
NEWS_CACHE_TTL = int(os.environ.get("NEWS_CACHE_TTL", "180"))
INGEST_CITIES = os.environ.get("INGEST_CITIES")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Med Guardian API", version="1.0.0")

# --- Sentry Setup (optional) ---
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
            _experiments={"profiles_sample_rate": float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0"))}
        )
        app = SentryAsgiMiddleware(app)
        logger.info("Sentry initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Detect Frontend Build Path ---
# For Next.js exported builds, the static output is usually in frontend/out
possible_paths = [
    os.path.join(os.path.dirname(__file__), "../frontend/out"),
    os.path.join(os.path.dirname(__file__), "../frontend/dist"),
    "/app/frontend/out",
    "/app/frontend/dist",
]
frontend_build_path = None
for p in possible_paths:
    abs_path = os.path.abspath(p)
    if os.path.exists(abs_path):
        frontend_build_path = abs_path
        logger.info(f"Frontend build found at: {frontend_build_path}")
        break

if frontend_build_path:
    static_path = os.path.join(frontend_build_path, "_next")
    if os.path.exists(static_path):
        app.mount("/_next", StaticFiles(directory=static_path), name="_next")
    app.mount("/static", StaticFiles(directory=frontend_build_path), name="static")

# --- Core API Endpoints (unchanged) ---
# [Keep your /api/trends/latest, /api/predictor, /api/advisory_service, etc. exactly as-is]

# (You can keep your API route definitions unchanged from the version you shared)

# --- Root + Frontend Fallback ---
@app.get("/")
def serve_index():
    """Serve Next.js index.html (exported build)."""
    if frontend_build_path:
        index_path = os.path.join(frontend_build_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    return {"message": "Med Guardian API", "note": "Frontend not built yet"}

@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    """Catch-all route to serve React/Next.js frontend for client-side routing."""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    if frontend_build_path:
        index_path = os.path.join(frontend_build_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend not available")

# --- Health ---
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "mongodb": is_mongodb_available(),
        "redis": is_redis_available(),
    }

# --- Background News Loop ---
async def _run_news_ingest_loop(stop_event: asyncio.Event):
    logger.info("Starting background news ingest loop")
    cities = [c["city_name"] for c in CITIES[:5]]
    diseases = ["flu", "dengue", "covid"]

    while not stop_event.is_set():
        for city in cities:
            for disease in diseases:
                try:
                    items = await fetch_combined_news(city, disease, limit=10)
                    cache_key = f"news:{city}:{disease}"
                    if is_redis_available():
                        cache_set(cache_key, {"items": items}, ttl=NEWS_CACHE_TTL)
                except Exception as e:
                    logger.warning(f"Ingest failed for {city}/{disease}: {e}")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=NEWS_INGEST_INTERVAL)
        except asyncio.TimeoutError:
            continue

@app.on_event("startup")
async def startup_event():
    try:
        app.state.stop_event = asyncio.Event()
        app.state.ingest_task = asyncio.create_task(_run_news_ingest_loop(app.state.stop_event))
        logger.info("Background ingest started.")
    except Exception as e:
        logger.warning(f"Startup task failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    try:
        if hasattr(app.state, "stop_event"):
            app.state.stop_event.set()
        if hasattr(app.state, "ingest_task"):
            await app.state.ingest_task
    except Exception:
        pass

# --- Run Uvicorn ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
