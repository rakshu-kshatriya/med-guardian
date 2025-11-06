"""
FastAPI backend for Med Guardian - Disease prediction and advisory system.
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
# Load .env early so local env files are respected (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
from backend.predictor import run_forecast 
from backend.advisory_service import get_advisory
from backend.example_data import generate_synthetic_data, get_latest_trends
from backend.database import is_mongodb_available, get_trend_history, save_trend_data
from backend.redis_client import is_redis_available, cache_get, cache_set
from backend.news_ingest import fetch_combined_news, METRIC_NEWS_SAVED
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from backend.database import save_news_item

# Background ingestion / caching configuration
NEWS_INGEST_INTERVAL = int(os.environ.get("NEWS_INGEST_INTERVAL", "300"))  # seconds
NEWS_CACHE_TTL = int(os.environ.get("NEWS_CACHE_TTL", "180"))  # seconds
INGEST_CITIES = os.environ.get("INGEST_CITIES")  # comma-separated city names (optional)


def _news_cache_key(city: str, disease: str, limit: int) -> str:
    return f"news:{city.lower()}:{disease.lower()}:{limit}"


async def _run_news_ingest_loop(stop_event: asyncio.Event):
    """Background task: periodically fetch and cache news for configured cities/diseases."""
    logger.info("Starting background news ingest loop")

    # Determine cities to ingest: either from INGEST_CITIES env or top 5 from CITIES
    if INGEST_CITIES:
        cities_to_ingest = [c.strip() for c in INGEST_CITIES.split(",") if c.strip()]
    else:
        # Pick top 5 cities from available list
        cities_to_ingest = [c["city_name"] for c in CITIES[:5]]

    diseases_to_ingest = ["flu", "dengue", "covid"]

    while not stop_event.is_set():
        for city in cities_to_ingest:
            for disease in diseases_to_ingest:
                try:
                    # Try to fetch from external providers; if they are not configured,
                    # fetch_combined_news will raise and we'll skip to synthetic fallback.
                    items = []
                    try:
                        items = await fetch_combined_news(city, disease, limit=10)
                        source = "external"
                    except Exception as e:
                        # Do not spam logs; log at debug level for expected fallback.
                        logger.debug(f"Background ingest: external providers unavailable: {e}. Generating synthetic items.")
                        # Fallback to synthetic generator
                        from backend.example_data import get_latest_trends
                        # Convert trends history into simple news-like items
                        trends = get_latest_trends(city, disease, days=7)
                        items = []
                        for idx, h in enumerate(trends.get("history", [])[:10]):
                            items.append({
                                "id": f"synthetic-{city}-{disease}-{idx}",
                                "title": f"{disease} cases in {city}: {h.get('y')}",
                                "source": "synthetic",
                                "sentiment": "neutral",
                                "timestamp": h.get("ds") + "T00:00:00Z",
                                "link": None,
                            })
                        source = "synthetic"

                    # Cache results in Redis if available
                    cache_key = _news_cache_key(city, disease, 10)
                    if is_redis_available():
                        cache_set(cache_key, {"items": items, "source": source}, ttl=NEWS_CACHE_TTL)
                        logger.debug(f"Cached news for {city}/{disease} -> {cache_key}")
                    # Persist to MongoDB for historical analytics if available
                    if is_mongodb_available():
                        try:
                            for it in items:
                                saved = save_news_item(it)
                                if saved:
                                    try:
                                        METRIC_NEWS_SAVED.inc()
                                    except Exception:
                                        pass
                        except Exception as e:
                            logger.warning(f"Failed to save news items to MongoDB: {e}")
                except Exception as e:
                    logger.warning(f"Error in background ingest for {city}/{disease}: {e}")

        # Wait for configured interval or until stop
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=NEWS_INGEST_INTERVAL)
        except asyncio.TimeoutError:
            continue


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Med Guardian API", version="1.0.0")

# Get port from environment variable (Railway uses PORT, fallback to 8000)
PORT = int(os.environ.get("PORT", os.environ.get("BACKEND_PORT", "8000")))

# CORS middleware - allow all origins in production (Railway handles this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Railway will handle CORS properly
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from frontend build
# Handle both local development and Docker paths
possible_paths = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist"),  # From backend/ -> ../frontend/dist
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"),  # Relative from backend/
    "/app/frontend/dist",  # Docker absolute path
    os.path.join("/app", "frontend", "dist"),  # Docker alternative
]

frontend_dist_path = None
for path in possible_paths:
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        frontend_dist_path = abs_path
        logger.info(f"Frontend dist found at: {frontend_dist_path}")
        break

if frontend_dist_path is None:
    logger.warning("Frontend dist directory not found. Frontend will not be served.")

if frontend_dist_path and os.path.exists(frontend_dist_path):
    assets_path = os.path.join(frontend_dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    app.mount("/static", StaticFiles(directory=frontend_dist_path), name="static")


@app.get("/api/trends/latest")
async def get_trends_latest(
    city: str = Query(..., description="City name"),
    disease: str = Query("Unknown", description="Disease name")
):
    """
    Get latest 30 days of disease trend data for a city.
    Uses MongoDB if available, otherwise synthetic data.
    """
    try:
        # Validate city
        city_data = get_city_by_name(city)
        if not city_data:
            raise HTTPException(status_code=404, detail=f"City '{city}' not found")
        
        # Check Redis cache first
        cache_key = f"trends:{city}:{disease}:latest"
        if is_redis_available():
            cached = cache_get(cache_key)
            if cached:
                logger.info(f"Cache hit for {cache_key}")
                return cached
        
        # Try MongoDB first
        if is_mongodb_available():
            history = get_trend_history(city, disease, days=30)
            if history:
                result = {
                    "city": city,
                    "disease": disease,
                    "history": history,
                    "source": "mongodb"
                }
                # Cache for 5 minutes
                if is_redis_available():
                    cache_set(cache_key, result, ttl=300)
                return result
        
        # Fallback to synthetic data
        trends = get_latest_trends(city, disease, days=30)
        trends["source"] = "synthetic"
        
        # Cache synthetic data for 1 minute
        if is_redis_available():
            cache_set(cache_key, trends, ttl=60)
        
        return trends
        
    except Exception as e:
        logger.error(f"Error in /api/trends/latest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/predictor")
async def get_predict(
    city: str = Query(..., description="City name"),
    disease: str = Query("Unknown", description="Disease name")
):
    """Get disease prediction for next 30 days."""
    try:
        city_data = get_city_by_name(city)
        if not city_data:
            raise HTTPException(status_code=404, detail=f"City '{city}' not found")

        df = generate_synthetic_data(city, disease, days=60)
        df_history = df.tail(30).copy()
        forecast_df = run_forecast(df)

        result = []
        for _, row in df_history.iterrows():
            result.append({
                "ds": row["ds"].strftime("%Y-%m-%d"),
                "y": int(row["y"]),
                "yhat": None,
                "yhat_lower": None,
                "yhat_upper": None
            })
        for _, row in forecast_df.iterrows():
            result.append({
                "ds": row["ds"].strftime("%Y-%m-%d"),
                "y": None,
                "yhat": float(row["yhat"]),
                "yhat_lower": float(row["yhat_lower"]),
                "yhat_upper": float(row["yhat_upper"])
            })

        return {"city": city, "disease": disease, "data": result}

    except Exception as e:
        logger.error(f"Error in /api/predict: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/advisory_service")
async def get_advisory_endpoint(
    city: str = Query(..., description="City name"),
    disease: str = Query(..., description="Disease name"),
    aqi: float = Query(..., description="Air Quality Index"),
    temp: float = Query(..., description="Average temperature")
):
    """Get AI-generated health advisory for a disease in a city."""
    try:
        city_data = get_city_by_name(city)
        if not city_data:
            raise HTTPException(status_code=404, detail=f"City '{city}' not found")

        advisory = get_advisory(disease, city, aqi, temp)
        return advisory

    except Exception as e:
        logger.error(f"Error in /api/advisory_servive: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/directions")
async def get_directions(
    origin_city: str = Query(..., description="Origin city"),
    destination_city: str = Query(..., description="Destination city")
):
    """Mock Google Directions API-like response."""
    try:
        origin = get_city_by_name(origin_city)
        destination = get_city_by_name(destination_city)
        if not origin:
            raise HTTPException(status_code=404, detail=f"Origin '{origin_city}' not found")
        if not destination:
            raise HTTPException(status_code=404, detail=f"Destination '{destination_city}' not found")

        import math
        lat1, lon1 = math.radians(origin["lat"]), math.radians(origin["lng"])
        lat2, lon2 = math.radians(destination["lat"]), math.radians(destination["lng"])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance_km = 6371 * c
        duration_seconds = int((distance_km / 60) * 3600)
        duration_mins = duration_seconds // 60

        def encode_polyline(points):
            return "|".join([f"{p['lat']:.6f},{p['lng']:.6f}" for p in points])

        num_points = max(3, int(distance_km / 100))
        waypoints = [
            {"lat": origin["lat"] + (destination["lat"] - origin["lat"]) * i / num_points,
             "lng": origin["lng"] + (destination["lng"] - origin["lng"]) * i / num_points}
            for i in range(num_points + 1)
        ]
        polyline_encoded = encode_polyline(waypoints)

        steps = [{
            "distance": {"text": f"{distance_km:.1f} km", "value": int(distance_km * 1000)},
            "duration": {"text": f"{duration_mins} mins", "value": duration_seconds},
            "polyline": {"points": polyline_encoded},
            "html_instructions": f"Travel from {origin_city} to {destination_city}"
        }]

        return {
            "routes": [{
                "bounds": {
                    "northeast": {"lat": max(origin["lat"], destination["lat"]), "lng": max(origin["lng"], destination["lng"])},
                    "southwest": {"lat": min(origin["lat"], destination["lat"]), "lng": min(origin["lng"], destination["lng"])}
                },
                "legs": [{
                    "start_address": f"{origin_city}, {origin['state']}, India",
                    "end_address": f"{destination_city}, {destination['state']}, India",
                    "steps": steps,
                    "duration": {"text": f"{duration_mins} mins", "value": duration_seconds},
                    "distance": {"text": f"{distance_km:.1f} km", "value": int(distance_km * 1000)}
                }]
            }]
        }

    except Exception as e:
        logger.error(f"Error in /api/directions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news_trends")
async def get_news_trends(
    city: str = Query(..., description="City name"),
    disease: str = Query("Unknown", description="Disease name"),
    limit: int = Query(10, description="Max number of news items")
):
    """Return synthetic news and social media trend items related to a disease and city."""
    try:
        city_data = get_city_by_name(city)
        if not city_data:
            raise HTTPException(status_code=404, detail=f"City '{city}' not found")
        # Check Redis cache first
        cache_key = _news_cache_key(city, disease, min(limit, 50))
        cached = None
        if is_redis_available():
            try:
                cached = cache_get(cache_key)
            except Exception:
                cached = None

        if cached:
            logger.debug(f"Cache hit for {cache_key}")
            # cached expected shape: {"items": [...], "source": "external"|"synthetic"}
            return {"city": city, "disease": disease, "items": cached.get("items", []), "source": cached.get("source", "cache")}

        # Try to fetch from configured external providers (NewsAPI / Twitter). If not configured
        # or an error occurs, fall back to synthetic generated items.
        try:
            items = await fetch_combined_news(city, disease, limit=min(limit, 50))
            result = {"city": city, "disease": disease, "items": items, "source": "external"}
            # Cache if Redis available
            if is_redis_available():
                cache_set(cache_key, {"items": items, "source": "external"}, ttl=NEWS_CACHE_TTL)
            return result
        except Exception as e:
            logger.info(f"External news providers unavailable or failed: {e}. Falling back to synthetic data.")

        base_trends = [
            f"Spike in {disease} cases reported in {city}",
            f"Hospitals in {city} see rise in {disease} admissions",
            f"Public health advisory issued for {disease} in {city}",
            f"Local schools in {city} close due to {disease} outbreak",
            f"Social media warnings about {disease} spread in {city}"
        ]

        sources = ["NewsDaily", "HealthWatch", "LocalTimes", "Tweet", "FBPost"]

        items = []
        import random
        from datetime import datetime, timedelta

        for i in range(min(limit, 50)):
            minutes_ago = random.randint(1, 120)
            ts = (datetime.utcnow() - timedelta(minutes=minutes_ago)).isoformat() + "Z"
            title = random.choice(base_trends)
            source = random.choice(sources)
            sentiment = random.choice(["neutral", "concern", "alarm", "advisory"])
            items.append({
                "id": f"news-{i}-{minutes_ago}",
                "title": title,
                "source": source,
                "sentiment": sentiment,
                "timestamp": ts,
                "link": None,
            })

        return {"city": city, "disease": disease, "items": items, "source": "synthetic"}

    except Exception as e:
        logger.error(f"Error in /api/news_trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


    @app.get("/api/data_sources")
    async def get_data_sources(
        city: str = Query(..., description="City name"),
        disease: str = Query("Unknown", description="Disease name"),
        rows: int = Query(1000, description="Number of rows to return")
    ):
        """Return a CSV-like payload (JSON rows) containing recent synthetic or stored trend rows.
        This endpoint is intended for the frontend Data Sources page to download a 1000 row dataset.
        """
        try:
            # Validate city
            city_data = get_city_by_name(city)
            if not city_data:
                raise HTTPException(status_code=404, detail=f"City '{city}' not found")

            # If MongoDB has historical records, try to pull from it
            if is_mongodb_available():
                try:
                    history = get_trend_history(city, disease, days=rows)
                    # Convert to rows: date, cases, avg_temp, real_time_aqi
                    rows_out = []
                    for h in history:
                        rows_out.append([h.get('ds'), h.get('y'), h.get('avg_temp', None), h.get('real_time_aqi', None)])
                    return {"rows": rows_out, "source": "mongodb"}
                except Exception:
                    # Fallback to synthetic generator
                    pass

            # Fallback to synthetic data generator
            from backend.example_data import generate_synthetic_data
            df = generate_synthetic_data(city, disease, days=rows)
            rows_out = []
            for _, row in df.iterrows():
                rows_out.append([row['ds'].strftime('%Y-%m-%d'), int(row['y']), float(row['avg_temp']), float(row['real_time_aqi'])])

            return {"rows": rows_out, "source": "synthetic"}
        except Exception as e:
            logger.error(f"Error in /api/data_sources: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stream_news")
async def stream_news(
    city: str = Query(..., description="City name"),
    disease: str = Query("Unknown", description="Disease name")
):
    """SSE endpoint that streams synthetic social/news trend items periodically."""
    async def news_generator():
        # If external providers are configured, periodically fetch recent items and stream them.
        try:
            while True:
                try:
                    items = await fetch_combined_news(city, disease, limit=5)
                    for it in items:
                        yield f"event: news\ndata: {json.dumps(it)}\n\n"
                    await asyncio.sleep(12)
                    continue
                except Exception as e:
                    logger.info(f"Streaming external news failed: {e}. Switching to synthetic stream.")
                    # Fall through to synthetic generator below

                import random
                from datetime import datetime
                sources = ["NewsDaily", "HealthWatch", "LocalTimes", "Tweet", "FBPost"]
                templates = [
                    f"New reports of {{disease}} in {{city}} — hospitals monitoring situation.",
                    f"Residents in {{city}} share concerns about rising {{disease}} cases on social media.",
                    f"Public health officials in {{city}} advise precautions for {{disease}}.",
                    f"Local clinic in {{city}} reports clusters of {{disease}} cases."
                ]

                while True:
                    now = datetime.utcnow()
                    title = random.choice(templates).format(disease=disease, city=city)
                    item = {
                        "id": f"news-{int(now.timestamp())}-{random.randint(1,1000)}",
                        "title": title,
                        "source": random.choice(sources),
                        "sentiment": random.choice(["neutral", "concern", "alarm", "advisory"]),
                        "timestamp": now.isoformat() + "Z",
                    }

                    yield f"event: news\ndata: {json.dumps(item)}\n\n"
                    await asyncio.sleep(12)

        except Exception as e:
            logger.error(f"Error in SSE news stream: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(news_generator(), media_type="text/event-stream")


@app.get("/api/stream")
async def stream_updates(
    city: str = Query(..., description="City name"),
    disease: str = Query("Unknown", description="Disease name")
):
    """SSE endpoint for real-time disease trend updates."""
    async def event_generator():
        try:
            trends = get_latest_trends(city, disease, days=30)
            base_cases = trends["history"][-1]["y"] if trends["history"] else 100

            while True:
                change = random.randint(-5, 10)
                new_cases = max(0, base_cases + change)
                base_cases = new_cases
                now = datetime.now()

                temp = 25.0 + random.uniform(-2, 2)
                aqi = 80.0 + random.uniform(-10, 10)

                data = {
                    "timestamp": now.isoformat(),
                    "city": city,
                    "disease": disease,
                    "cases": new_cases,
                    "avg_temp": round(temp, 2),
                    "real_time_aqi": round(aqi, 2)
                }

                yield f"event: update\ndata: {json.dumps(data)}\n\n"
                await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/city_data")
async def get_cities():
    """Get list of all available cities."""
    return {"cities": CITIES}


@app.get('/metrics')
async def metrics():
    """Prometheus metrics endpoint."""
    try:
        data = generate_latest()
        return StreamingResponse(iter([data]), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway and monitoring."""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "mongodb": is_mongodb_available(),
            "redis": is_redis_available()
        }
    }
    
    return health_status


@app.get("/")
async def root():
    """Serve frontend index.html."""
    if frontend_dist_path:
        index_path = os.path.join(frontend_dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    return {"message": "Med Guardian API", "version": "1.0.0", "note": "Frontend not built"}


@app.get("/{path:path}")
async def serve_frontend(path: str):
    """Serve frontend for all non-API routes."""
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    if frontend_dist_path:
        index_path = os.path.join(frontend_dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="Frontend not available")


# Background ingest task management
@app.on_event("startup")
async def startup_event():
    # Start background news ingest loop only if we have something to do:
    # - Redis or Mongo available for caching/persistence, or
    # - External providers configured (NEWSAPI_KEY/TWITTER_BEARER_TOKEN)
    try:
        providers_configured = bool(os.environ.get("NEWSAPI_KEY") or os.environ.get("TWITTER_BEARER_TOKEN"))
        if not (is_redis_available() or is_mongodb_available() or providers_configured):
            logger.info("Skipping background news ingest: no Redis/Mongo/providers configured")
            return

        # Avoid creating multiple tasks if hot-reload triggers startup twice
        if getattr(app.state, "_news_ingest_task", None):
            logger.debug("Background news ingest task already running; skipping creation")
            return

        app.state._news_ingest_stop = asyncio.Event()
        app.state._news_ingest_task = asyncio.create_task(_run_news_ingest_loop(app.state._news_ingest_stop))
        logger.info("Background news ingest task started")
    except Exception as e:
        logger.warning(f"Failed to start background ingest task: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        if hasattr(app.state, "_news_ingest_stop") and app.state._news_ingest_stop:
            app.state._news_ingest_stop.set()
        if hasattr(app.state, "_news_ingest_task") and app.state._news_ingest_task:
            await app.state._news_ingest_task
    except Exception:
        pass


if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment variable (Railway convention)
    port = int(os.environ.get("PORT", os.environ.get("BACKEND_PORT", "8000")))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
