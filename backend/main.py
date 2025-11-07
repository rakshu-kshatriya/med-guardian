"""
FastAPI backend for Med Guardian - Disease prediction and advisory system.
Now with automatic frontend static serving for Railway.
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

# Environment variables
MONGO_URI = os.getenv("MONGO_URI")
REDIS_URL = os.getenv("REDIS_URL")
SENTRY_DSN = os.getenv("SENTRY_DSN")

NEWS_INGEST_INTERVAL = int(os.environ.get("NEWS_INGEST_INTERVAL", "300"))
NEWS_CACHE_TTL = int(os.environ.get("NEWS_CACHE_TTL", "180"))
INGEST_CITIES = os.environ.get("INGEST_CITIES")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Med Guardian API", version="1.0.0")

# --- Sentry optional setup ---
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1)
        app = SentryAsgiMiddleware(app)
        logger.info("✅ Sentry initialized")
    except Exception as e:
        logger.warning(f"Sentry init failed: {e}")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Determine frontend build path ---
frontend_out_path = None
possible_outs = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "out"),
    os.path.join(os.path.dirname(__file__), "..", "frontend", "out"),
    "/app/frontend/out"
]

for path in possible_outs:
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        frontend_out_path = abs_path
        logger.info(f"✅ Found frontend static export at: {frontend_out_path}")
        break

if frontend_out_path and os.path.exists(frontend_out_path):
    static_dir = os.path.join(frontend_out_path, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- Utility functions ---
def _news_cache_key(city: str, disease: str, limit: int) -> str:
    return f"news:{city.lower()}:{disease.lower()}:{limit}"

# --- API endpoints (core backend logic) ---

@app.get("/api/trends/latest")
async def get_trends_latest(city: str, disease: str = "Unknown"):
    try:
        city_data = get_city_by_name(city)
        if not city_data:
            raise HTTPException(404, f"City '{city}' not found")

        cache_key = f"trends:{city}:{disease}:latest"
        if is_redis_available():
            cached = cache_get(cache_key)
            if cached:
                return cached

        if is_mongodb_available():
            history = get_trend_history(city, disease, days=30)
            if history:
                result = {"city": city, "disease": disease, "history": history, "source": "mongodb"}
                if is_redis_available():
                    cache_set(cache_key, result, ttl=300)
                return result

        trends = get_latest_trends(city, disease, days=30)
        trends["source"] = "synthetic"
        if is_redis_available():
            cache_set(cache_key, trends, ttl=60)
        return trends
    except Exception as e:
        logger.error(e)
        raise HTTPException(500, str(e))

@app.get("/api/predictor")
async def get_predict(city: str, disease: str = "Unknown"):
    try:
        city_data = get_city_by_name(city)
        if not city_data:
            raise HTTPException(404, f"City '{city}' not found")

        df = generate_synthetic_data(city, disease, days=60)
        df_history = df.tail(30).copy()
        forecast_df = run_forecast(df)

        result = []
        for _, row in df_history.iterrows():
            result.append({
                "ds": row["ds"].strftime("%Y-%m-%d"),
                "y": int(row["y"]),
                "yhat": None
            })
        for _, row in forecast_df.iterrows():
            result.append({
                "ds": row["ds"].strftime("%Y-%m-%d"),
                "y": None,
                "yhat": float(row["yhat"])
            })
        return {"city": city, "disease": disease, "data": result}
    except Exception as e:
        logger.error(e)
        raise HTTPException(500, str(e))

@app.get("/api/advisory_service")
async def get_advisory_endpoint(city: str, disease: str, aqi: float, temp: float):
    try:
        get_city_by_name(city)
        advisory = get_advisory(disease, city, aqi, temp)
        return advisory
    except Exception as e:
        logger.error(e)
        raise HTTPException(500, str(e))

@app.get("/api/news_trends")
async def get_news_trends(city: str, disease: str = "Unknown", limit: int = 10):
    try:
        city_data = get_city_by_name(city)
        if not city_data:
            raise HTTPException(404, f"City '{city}' not found")

        cache_key = _news_cache_key(city, disease, limit)
        if is_redis_available():
            cached = cache_get(cache_key)
            if cached:
                return cached

        items = await fetch_combined_news(city, disease, limit=limit)
        result = {"city": city, "disease": disease, "items": items, "source": "external"}
        if is_redis_available():
            cache_set(cache_key, result, ttl=NEWS_CACHE_TTL)
        return result
    except Exception:
        # fallback to synthetic data
        base_trends = [f"Spike in {disease} cases reported in {city}", f"Hospitals in {city} see rise in {disease} admissions"]
        items = []
        for i in range(limit):
            ts = (datetime.utcnow() - timedelta(minutes=random.randint(1, 120))).isoformat() + "Z"
            items.append({
                "id": f"news-{i}",
                "title": random.choice(base_trends),
                "source": "synthetic",
                "timestamp": ts,
            })
        return {"city": city, "disease": disease, "items": items, "source": "synthetic"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "mongodb": is_mongodb_available(),
            "redis": is_redis_available()
        }
    }

@app.get("/metrics")
async def metrics():
    try:
        data = generate_latest()
        return StreamingResponse(iter([data]), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(e)
        raise HTTPException(500, str(e))

# --- Static Frontend Serving ---

if frontend_out_path:
    @app.get("/")
    async def serve_index():
        index_path = os.path.join(frontend_out_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend not built yet"}

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """Serve Next.js static export index.html for all frontend routes."""
        index_path = os.path.join(frontend_out_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Page not found")
else:
    @app.get("/")
    async def root_fallback():
        return {"message": "Med Guardian API (no frontend found)"}


# --- Background Task (news ingest) ---

async def _run_news_ingest_loop(stop_event: asyncio.Event):
    logger.info("Background news ingest loop started")
    cities_to_ingest = [c["city_name"] for c in CITIES[:5]]
    diseases_to_ingest = ["flu", "dengue", "covid"]

    while not stop_event.is_set():
        for city in cities_to_ingest:
            for disease in diseases_to_ingest:
                try:
                    items = await fetch_combined_news(city, disease, limit=5)
                    cache_key = _news_cache_key(city, disease, 5)
                    if is_redis_available():
                        cache_set(cache_key, {"items": items, "source": "background"}, ttl=NEWS_CACHE_TTL)
                    if is_mongodb_available():
                        for it in items:
                            save_news_item(it)
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
    except Exception as e:
        logger.warning(f"Background task not started: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    try:
        app.state.stop_event.set()
        await app.state.ingest_task
    except Exception:
        pass

# --- Main entry ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
