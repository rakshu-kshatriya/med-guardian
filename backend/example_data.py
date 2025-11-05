"""
Synthetic data generator for disease trends.
Generates plausible cases, temperature, and AQI data with seasonality and noise.
Falls back to this when MongoDB is not available.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from city_data import CITIES
from database import save_trend_data

def generate_synthetic_data(
    city: str,
    disease: str = "Unknown",
    days: int = 60,
    start_date: datetime = None
) -> pd.DataFrame:
    """
    Generate synthetic disease trend data for a city.
    
    Args:
        city: City name
        disease: Disease name
        days: Number of days to generate
        start_date: Start date (defaults to days ago from today)
    
    Returns:
        DataFrame with columns: ds, y (cases), avg_temp, real_time_aqi
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)
    
    # Get city data for base temperature (latitude affects climate)
    city_data = next((c for c in CITIES if c["city_name"].lower() == city.lower()), None)
    base_temp = 25.0  # Default
    if city_data:
        # Approximate temperature based on latitude (rough heuristic)
        lat = city_data["lat"]
        if lat > 28:  # North India
            base_temp = 22.0
        elif lat < 12:  # South India
            base_temp = 28.0
        else:
            base_temp = 25.0
    
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # Generate cases with seasonality and trend
    t = np.arange(days)
    # Base trend (slight upward)
    trend = 50 + 0.5 * t
    # Seasonal component (sinusoidal, peaks in monsoon/post-monsoon)
    day_of_year = np.array([d.timetuple().tm_yday for d in dates])
    seasonality = 30 * np.sin(2 * np.pi * day_of_year / 365.25 - np.pi/2) + 20
    # Random noise
    noise = np.random.normal(0, 10, days)
    cases = np.maximum(trend + seasonality + noise, 0).astype(int)
    
    # Generate temperature (realistic range for India)
    temp_base = base_temp
    temp_variation = 5 * np.sin(2 * np.pi * day_of_year / 365.25)
    temp_noise = np.random.normal(0, 2, days)
    avg_temp = np.clip(temp_base + temp_variation + temp_noise, 18.0, 38.0)
    
    # Generate AQI (Air Quality Index, 0-500 scale)
    # Higher in winter months, lower in monsoon
    aqi_base = 80
    aqi_seasonal = -20 * np.sin(2 * np.pi * day_of_year / 365.25 + np.pi)
    aqi_noise = np.random.normal(0, 15, days)
    real_time_aqi = np.clip(aqi_base + aqi_seasonal + aqi_noise, 30, 200)
    
    df = pd.DataFrame({
        "ds": dates,
        "y": cases,
        "avg_temp": avg_temp.round(2),
        "real_time_aqi": real_time_aqi.round(2)
    })
    
    # Save to MongoDB if available (save latest data point)
    if len(dates) > 0:
        try:
            from database import is_mongodb_available
            if is_mongodb_available():
                latest_idx = len(df) - 1
                save_trend_data(
                    city=city,
                    disease=disease,
                    date=dates[latest_idx],
                    cases=int(cases[latest_idx]),
                    avg_temp=float(avg_temp[latest_idx]),
                    real_time_aqi=float(real_time_aqi[latest_idx])
                )
        except Exception as e:
            # Silently fail - synthetic data generation should not depend on DB
            pass
    
    return df

def get_latest_trends(city: str, disease: str = "Unknown", days: int = 30) -> dict:
    """
    Get latest trend data for a city.
    
    Returns:
        Dict with city, disease, and history array
    """
    df = generate_synthetic_data(city, disease, days)
    
    history = []
    for _, row in df.iterrows():
        history.append({
            "ds": row["ds"].strftime("%Y-%m-%d"),
            "y": int(row["y"]),
            "avg_temp": float(row["avg_temp"]),
            "real_time_aqi": float(row["real_time_aqi"])
        })
    
    return {
        "city": city,
        "disease": disease,
        "history": history
    }

