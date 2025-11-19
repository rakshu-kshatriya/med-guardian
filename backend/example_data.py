"""
Synthetic data generator for disease trends.
Generates realistic temperature, AQI, and case counts.
Used whenever MongoDB does not provide stored data.
Safe for Railway deployment.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from backend.city_data import CITIES
from backend.database import save_trend_data, is_mongodb_available


# ---------------------------------------------------------
# CITY TEMPERATURE HEURISTIC
# ---------------------------------------------------------
def _estimate_base_temperature(lat: float) -> float:
    """Estimate baseline temperature using simple latitude heuristics."""
    if lat > 28:      # North India → cooler
        return 22.0
    elif lat < 12:    # South India → hotter
        return 28.0
    return 25.0       # Central regions


# ---------------------------------------------------------
# SYNTHETIC DATA GENERATOR
# ---------------------------------------------------------
def generate_synthetic_data(
    city: str,
    disease: str = "Unknown",
    days: int = 60,
    start_date: Optional[datetime] = None
) -> pd.DataFrame:
    """Generate realistic synthetic disease trend data."""

    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)

    # Lookup city
    city_data = next((c for c in CITIES if c["city_name"].lower() == city.lower()), None)
    lat = city_data["lat"] if city_data else 20.0
    base_temp = _estimate_base_temperature(lat)

    # Build date range
    dates = [start_date + timedelta(days=i) for i in range(days)]

    # Case count generation
    t = np.arange(days)
    trend = 40 + 0.5 * t             # mild increasing trend
    day_of_year = np.array([d.timetuple().tm_yday for d in dates])

    # Seasonality: monsoon peak
    seasonality = 25 * np.sin(2 * np.pi * day_of_year / 365.25 - 1.2) + 20
    noise = np.random.normal(0, 10, days)

    cases = np.maximum(trend + seasonality + noise, 2).astype(int)

    # Temperature profile
    temp_variation = 5 * np.sin(2 * np.pi * day_of_year / 365.25)
    temp_noise = np.random.normal(0, 1.8, days)
    avg_temp = np.clip(base_temp + temp_variation + temp_noise, 18, 38)

    # AQI profile
    aqi_base = 90
    aqi_seasonal = -25 * np.sin(2 * np.pi * day_of_year / 365.25 + 2.5)
    aqi_noise = np.random.normal(0, 12, days)
    real_time_aqi = np.clip(aqi_base + aqi_seasonal + aqi_noise, 30, 200)

    # Build DataFrame
    df = pd.DataFrame({
        "ds": dates,
        "y": cases,
        "avg_temp": avg_temp.round(2),
        "real_time_aqi": real_time_aqi.round(2)
    })

    # Save only the last row (optional)
    try:
        if is_mongodb_available():
            idx = len(df) - 1
            save_trend_data(
                city=city,
                disease=disease,
                date=dates[idx],
                cases=int(cases[idx]),
                avg_temp=float(avg_temp[idx]),
                real_time_aqi=float(real_time_aqi[idx])
            )
    except Exception:
        # DB errors must not break synthetic data generation
        pass

    return df


# ---------------------------------------------------------
# PUBLIC API: GET LATEST TRENDS
# ---------------------------------------------------------
def get_latest_trends(city: str, disease: str = "Unknown", days: int = 30) -> Dict[str, any]:
    """Return structured trend history for the given city."""

    df = generate_synthetic_data(city, disease, days)

    history: List[Dict[str, any]] = []
    for _, row in df.iterrows():
        history.append({
            "ds": row["ds"].strftime("%Y-%m-%d"),
            "y": int(row["y"]),
            "avg_temp": float(row["avg_temp"]),
            "real_time_aqi": float(row["real_time_aqi"]),
        })

    return {
        "city": city,
        "disease": disease,
        "history": history
    }
