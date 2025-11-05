"""
Disease prediction using Prophet with temperature and AQI regressors.
Falls back to linear regression if Prophet fails.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def run_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run Prophet forecast with regressors.
    
    Args:
        df: DataFrame with columns: ds (datetime), y (cases), avg_temp, real_time_aqi
    
    Returns:
        DataFrame with ds, yhat, yhat_lower, yhat_upper
    """
    try:
        from prophet import Prophet
        
        # Ensure ds is datetime
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df['ds']):
            df['ds'] = pd.to_datetime(df['ds'])
        
        # Prepare regressors
        df_reg = df[['ds', 'y', 'avg_temp', 'real_time_aqi']].copy()
        df_reg = df_reg.rename(columns={'y': 'y'})
        
        # Initialize Prophet with regressors
        m = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )
        
        # Add regressors
        m.add_regressor('avg_temp', prior_scale=0.5, mode='multiplicative')
        m.add_regressor('real_time_aqi', prior_scale=0.5, mode='multiplicative')
        
        # Fit model
        m.fit(df_reg)
        
        # Create future dataframe (30 days)
        future = m.make_future_dataframe(periods=30, freq='D')
        
        # Use rolling mean for future regressors (simple approach)
        # Use 7-day rolling average for future predictions
        future_temp = df_reg['avg_temp'].tail(7).mean()
        future_aqi = df_reg['real_time_aqi'].tail(7).mean()
        
        # Add regressors to future dataframe
        # For historical dates, use actual values; for future dates, use rolling mean
        future = future.merge(df_reg[['ds', 'avg_temp', 'real_time_aqi']], on='ds', how='left')
        future['avg_temp'] = future['avg_temp'].fillna(future_temp)
        future['real_time_aqi'] = future['real_time_aqi'].fillna(future_aqi)
        
        # Predict
        forecast = m.predict(future)
        
        # Return full forecast (history + future)
        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        
        # Ensure non-negative predictions
        result['yhat'] = np.maximum(result['yhat'], 0)
        result['yhat_lower'] = np.maximum(result['yhat_lower'], 0)
        result['yhat_upper'] = np.maximum(result['yhat_upper'], 0)
        
        # Return only the forecast period (last 30 days)
        # This will be combined with history in main.py
        forecast_period = result.tail(30).copy()
        
        return forecast_period
        
    except Exception as e:
        logger.warning(f"Prophet forecast failed: {e}. Falling back to linear regression.")
        return _fallback_forecast(df)


def _fallback_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fallback linear regression forecast.
    Uses simple linear trend with seasonal adjustment.
    """
    from sklearn.linear_model import LinearRegression
    
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['ds']):
        df['ds'] = pd.to_datetime(df['ds'])
    
    # Prepare features
    df['days'] = (df['ds'] - df['ds'].min()).dt.days
    df['day_of_year'] = df['ds'].dt.dayofyear
    df['sin_season'] = np.sin(2 * np.pi * df['day_of_year'] / 365.25)
    df['cos_season'] = np.cos(2 * np.pi * df['day_of_year'] / 365.25)
    
    # Features
    X = df[['days', 'avg_temp', 'real_time_aqi', 'sin_season', 'cos_season']].values
    y = df['y'].values
    
    # Fit model
    model = LinearRegression()
    model.fit(X, y)
    
    # Generate future dates
    last_date = df['ds'].max()
    future_dates = [last_date + timedelta(days=i) for i in range(1, 31)]
    
    # Predict future
    future_df = pd.DataFrame({'ds': future_dates})
    future_df['days'] = (future_df['ds'] - df['ds'].min()).dt.days
    future_df['day_of_year'] = future_df['ds'].dt.dayofyear
    future_df['sin_season'] = np.sin(2 * np.pi * future_df['day_of_year'] / 365.25)
    future_df['cos_season'] = np.cos(2 * np.pi * future_df['day_of_year'] / 365.25)
    
    # Use last known values for temp and aqi
    future_df['avg_temp'] = df['avg_temp'].tail(7).mean()
    future_df['real_time_aqi'] = df['real_time_aqi'].tail(7).mean()
    
    X_future = future_df[['days', 'avg_temp', 'real_time_aqi', 'sin_season', 'cos_season']].values
    yhat = model.predict(X_future)
    
    # Calculate confidence intervals (simple approach)
    residuals = y - model.predict(X)
    std_error = np.std(residuals)
    
    result = pd.DataFrame({
        'ds': future_dates,
        'yhat': np.maximum(yhat, 0),
        'yhat_lower': np.maximum(yhat - 1.96 * std_error, 0),
        'yhat_upper': np.maximum(yhat + 1.96 * std_error, 0)
    })
    
    return result

