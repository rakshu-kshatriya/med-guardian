import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# --- Correct imports ---
from advisory_service import get_advisory
from predictor import run_forecast
from city_data import get_all_cities
from example_data import get_latest_trends    # synthetic trends generator
from database import is_mongodb_available
from redis_client import is_redis_available
from news_ingest import fetch_combined_news   # fallback-safe (we catch errors)

app = FastAPI(title="Med Guardian API")
logger = logging.getLogger(__name__)

# ----------------------------------------------------------
# CORS
# ----------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------
# BACKGROUND TASK (DISABLED EXTERNAL INGEST)
# ----------------------------------------------------------
async def background_news_ingest():
    """
    No external providers. Loop stays silent.
    """
    while True:
        await asyncio.sleep(300)
        pass

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_news_ingest())
    logger.info("Background ingest disabled — running synthetic mode.")

# ----------------------------------------------------------
# ROUTES — CITIES
# ----------------------------------------------------------
@app.get("/api/city_data")
async def city_list():
    return {"cities": get_all_cities()}

# ----------------------------------------------------------
# ROUTES — TRENDS (FAKE/SYNTHETIC)
# ----------------------------------------------------------
@app.get("/api/trends/latest")
async def trends_latest(city: str, disease: str = "Unknown"):
    data = get_latest_trends(city, disease)
    return data

# ----------------------------------------------------------
# ROUTES — PREDICTOR
# ----------------------------------------------------------
@app.get("/api/predictor")
async def predictor(city: str, disease: str = "Unknown"):
    """
    Generates synthetic dataset → runs Prophet → fallback LR → returns 30-day forecast
    """
    hist = get_latest_trends(city, disease, days=60)
    df = hist["history"]
    import pandas as pd
    df = pd.DataFrame(df)
    df["ds"] = pd.to_datetime(df["ds"])
    df["y"] = df["y"].astype(int)

    forecast = run_forecast(df)
    return {"city": city, "disease": disease, "forecast": forecast.to_dict(orient="records")}

# ----------------------------------------------------------
# ROUTES — HEALTH ADVISORY
# ----------------------------------------------------------
@app.get("/api/advisory_service")
async def advisory(city: str, disease: str, aqi: float, temp: float):
    return get_advisory(disease, city, aqi, temp)

# ----------------------------------------------------------
# ROUTES — NEWS (SYNTHETIC FALLBACK)
# ----------------------------------------------------------
@app.get("/api/news_trends")
async def news(city: str, disease: str, limit: int = 10):
    """
    Try external providers → if not configured → fallback to synthetic stream.
    """
    try:
        items = await fetch_combined_news(city, disease, limit)
        return {"city": city, "disease": disease, "news": items}
    except Exception:
        # fallback synthetic
        fake = [
            {
                "id": f"{disease}-{city}-{i}",
                "title": f"{disease} updates in {city} — synthetic news item {i}",
                "source": "LocalSynthetic",
                "timestamp": "2024-01-01T00:00:00Z",
                "sentiment": "neutral",
            }
            for i in range(limit)
        ]
        return {"city": city, "disease": disease, "news": fake}

# ----------------------------------------------------------
# SSE STREAM: TRENDS
# ----------------------------------------------------------
@app.get("/api/stream")
async def stream(city: str, disease: str = "Unknown"):
    async def generator():
        while True:
            await asyncio.sleep(4)
            data = get_latest_trends(city, disease)
            yield f"event: update\ndata: {data}\n\n"
    return StreamingResponse(generator(), media_type="text/event-stream")

# ----------------------------------------------------------
# SSE STREAM: NEWS
# ----------------------------------------------------------
@app.get("/api/stream_news")
async def stream_news(city: str, disease: str = "Unknown"):
    async def generator():
        i = 0
        while True:
            await asyncio.sleep(5)
            fake = {
                "id": f"{city}-{disease}-{i}",
                "title": f"{disease} situation update {i} in {city}",
                "source": "LocalSynthetic",
            }
            i += 1
            yield f"event: news\ndata: {fake}\n\n"
    return StreamingResponse(generator(), media_type="text/event-stream")

# ----------------------------------------------------------
# HEALTH CHECK
# ----------------------------------------------------------
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "mongodb": is_mongodb_available(),
        "redis": is_redis_available(),
    }

# ----------------------------------------------------------
# ROOT
# ----------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Med Guardian backend running"}
