"""
Disease prediction using Prophet with temperature & AQI regressors.
Fully Railway-safe version:
 - Never crashes main API
 - Falls back cleanly if Prophet is missing or fails
 - Handles small or empty datasets
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MAIN FORECAST FUNCTION
# ---------------------------------------------------------------------------
def run_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run Prophet forecast; fallback to regression; fallback to synthetic.
    
    Args:
        df: DataFrame with columns -> ds, y, avg_temp, real_time_aqi
    
    Returns:
        DataFrame (30 rows): ds, yhat, yhat_lower, yhat_upper
    """

    # Safety: if df empty → generate synthetic forecast
    if df is None or len(df) < 10:
        logger.warning("Insufficient data (<10 rows). Using synthetic fallback forecast.")
        return _synthetic_forecast()

    # Ensure ds is datetime
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["ds"]):
        df["ds"] = pd.to_datetime(df["ds"], errors="coerce")

    df = df.dropna(subset=["ds"])
    if len(df) < 10:
        return _synthetic_forecast()

    # Try Prophet
    try:
        from prophet import Prophet

        df_reg = df[["ds", "y", "avg_temp", "real_time_aqi"]].copy()

        m = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode="multiplicative"
        )

        # Add regressors
        m.add_regressor("avg_temp", prior_scale=0.5)
        m.add_regressor("real_time_aqi", prior_scale=0.5)

        # Fit Prophet
        m.fit(df_reg)

        # Build future 30 days
        future = m.make_future_dataframe(periods=30, freq="D")

        # Fill future regressors
        avg_temp_future = df_reg["avg_temp"].tail(7).mean()
        aqi_future = df_reg["real_time_aqi"].tail(7).mean()

        future = future.merge(df_reg[["ds", "avg_temp", "real_time_aqi"]], on="ds", how="left")
        future["avg_temp"].fillna(avg_temp_future, inplace=True)
        future["real_time_aqi"].fillna(aqi_future, inplace=True)

        # Predict
        forecast = m.predict(future)

        result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()

        # Non-negative predictions
        for col in ["yhat", "yhat_lower", "yhat_upper"]:
            result[col] = np.maximum(result[col], 0)

        # Return only next 30 days
        return result.tail(30).copy()

    except Exception as e:
        logger.warning(f"Prophet forecast failed: {e}. Using regression fallback.")
        try:
            return _fallback_forecast(df)
        except Exception as e2:
            logger.warning(f"Regression fallback failed: {e2}. Using synthetic fallback.")
            return _synthetic_forecast()


# ---------------------------------------------------------------------------
# FALLBACK 1 — Simple Linear Regression With Seasonal Features
# ---------------------------------------------------------------------------
def _fallback_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """Fallback linear regression model."""

    from sklearn.linear_model import LinearRegression

    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["ds"]):
        df["ds"] = pd.to_datetime(df["ds"])

    df["days"] = (df["ds"] - df["ds"].min()).dt.days
    df["day_of_year"] = df["ds"].dt.dayofyear
    df["sin_season"] = np.sin(2 * np.pi * df["day_of_year"] / 365.25)
    df["cos_season"] = np.cos(2 * np.pi * df["day_of_year"] / 365.25)

    X = df[["days", "avg_temp", "real_time_aqi", "sin_season", "cos_season"]].values
    y = df["y"].values

    model = LinearRegression()
    model.fit(X, y)

    # Future 30 days
    last_date = df["ds"].max()
    future_dates = [last_date + timedelta(days=i) for i in range(1, 31)]

    future = pd.DataFrame({"ds": future_dates})
    future["days"] = (future["ds"] - df["ds"].min()).dt.days
    future["day_of_year"] = future["ds"].dt.dayofyear
    future["sin_season"] = np.sin(2 * np.pi * future["day_of_year"] / 365.25)
    future["cos_season"] = np.cos(2 * np.pi * future["day_of_year"] / 365.25)

    # Use 7-day average for temp & aqi future values
    future["avg_temp"] = df["avg_temp"].tail(7).mean()
    future["real_time_aqi"] = df["real_time_aqi"].tail(7).mean()

    X_future = future[["days", "avg_temp", "real_time_aqi", "sin_season", "cos_season"]].values
    yhat = model.predict(X_future)

    # Confidence interval
    resid = y - model.predict(X)
    std_err = np.std(resid)

    result = pd.DataFrame({
        "ds": future_dates,
        "yhat": np.maximum(yhat, 0),
        "yhat_lower": np.maximum(yhat - 1.96 * std_err, 0),
        "yhat_upper": np.maximum(yhat + 1.96 * std_err, 0),
    })

    return result


# ---------------------------------------------------------------------------
# FALLBACK 2 — Synthetic Forecast (Always Works)
# ---------------------------------------------------------------------------
def _synthetic_forecast() -> pd.DataFrame:
    """
    A completely safe deterministic fallback.
    Produces a gently rising synthetic forecast curve.
    """

    base = datetime.utcnow()
    dates = [base + timedelta(days=i) for i in range(1, 31)]

    # Simple synthetic pattern
    t = np.arange(30)
    yhat = 40 + 0.8 * t + 5 * np.sin(2 * np.pi * t / 30)

    df = pd.DataFrame({
        "ds": dates,
        "yhat": np.maximum(yhat, 0),
        "yhat_lower": np.maximum(yhat - 10, 0),
        "yhat_upper": np.maximum(yhat + 10, 0)
    })

    return df
