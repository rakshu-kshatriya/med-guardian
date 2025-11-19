import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from advisory_service import get_advisory
from predictor import run_forecast
from example_data import get_latest_trends
from city_data import get_all_cities
from news_ingest import _synthetic_news

app = FastAPI(title="Med Guardian API")

# ------------------------------------------------------
# CORS
# ------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------
# No background tasks. ZERO ingestion. ZERO warnings.
# ------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("Med Guardian backend started (no ingestion).")


# ------------------------------------------------------
# ROUTES
# ------------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/city_data")
async def cities():
    return {"cities": get_all_cities()}


@app.get("/api/trends/latest")
async def trends(city: str, disease: str = "Unknown"):
    return get_latest_trends(city, disease)


@app.get("/api/predictor")
async def predictor(city: str, disease: str = "Unknown"):
    data = get_latest_trends(city, disease)
    df = None
    try:
        import pandas as pd
        df = pd.DataFrame(data["history"])
    except:
        pass
    forecast = run_forecast(df)
    return {"city": city, "disease": disease, "forecast": forecast.to_dict(orient="records")}


@app.get("/api/advisory_service")
async def advisory(city: str, disease: str, aqi: float, temp: float):
    return get_advisory(disease, city, aqi, temp)


@app.get("/api/news_trends")
async def news(city: str, disease: str, limit: int = 5):
    return {"items": _synthetic_news(city, disease, limit)}


@app.get("/")
async def root():
    return {"message": "Med Guardian Backend Running"}


# ------------------------------------------------------
# SSE STREAM (Safe)
# ------------------------------------------------------
@app.get("/api/stream")
async def stream(city: str, disease: str):

    async def events():
        while True:
            await asyncio.sleep(3)
            yield f"event: update\ndata: {_synthetic_news(city, disease, 3)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
