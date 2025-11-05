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
from backend.predictor import run_forecast 
from backend.advisory_service import get_advisory
from backend.example_data import generate_synthetic_data, get_latest_trends
from backend.database import is_mongodb_available, get_trend_history, save_trend_data
from backend.redis_client import is_redis_available, cache_get, cache_set

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


@app.get("/api/predict")
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


@app.get("/api/advisory")
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
        logger.error(f"Error in /api/advisory: {e}")
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


@app.get("/api/cities")
async def get_cities():
    """Get list of all available cities."""
    return {"cities": CITIES}


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


if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment variable (Railway convention)
    port = int(os.environ.get("PORT", os.environ.get("BACKEND_PORT", "8000")))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
