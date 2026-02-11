from fastapi import FastAPI, HTTPException
from sklearn.ensemble import IsolationForest
from prometheus_api_client import PrometheusConnect
from prophet import Prophet
import pandas as pd
import joblib
import os
import logging
from datetime import datetime, timedelta

# Suppress Prophet's technical output to keep logs clean for your project
logging.getLogger('prophet').setLevel(logging.WARNING)
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

app = FastAPI(title="AIOps Intelligent Inference Engine")

# 1. PROMETHEUS CONFIGURATION
# Note: The NodePort 30206 is handled by your Ansible 'replace' task
PROMETHEUS_URL = "http://localhost:30206"
prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

# 2. MODEL PATHS
ISO_MODEL_PATH = "/home/ubuntu/aiops-project/models/iso_forest.joblib"
iso_model = None

@app.on_event("startup")
def load_models():
    global iso_model
    if os.path.exists(ISO_MODEL_PATH):
        iso_model = joblib.load(ISO_MODEL_PATH)
        print(f"✅ Isolation Forest loaded from {ISO_MODEL_PATH}")

# --- 1. REACTIVE: CPU ANOMALY DETECTION (For Healer & Dashboard) ---
@app.get("/detect/live")
async def detect_live():
    """Logic remains identical to current working version to ensure Healer doesn't break"""
    if iso_model is None:
        raise HTTPException(status_code=503, detail="Isolation Forest model not loaded")

    try:
        # 30m window for CPU is ideal for detecting sudden spikes
        query = "sum(rate(node_cpu_seconds_total[1m]))[30m:30s]"
        result = prom.custom_query(query=query)

        if not result:
            return {"status": "error", "message": "No CPU data found"}

        df = pd.DataFrame(result[0]['values'], columns=['timestamp', 'value'])
        df['value'] = df['value'].astype(float)
        df['time_formatted'] = df['timestamp'].apply(
            lambda x: datetime.fromtimestamp(float(x)).strftime('%H:%M:%S')
        )

        # Inference: -1 for anomaly, 1 for normal
        df['is_anomaly'] = iso_model.predict(df[['value']])
        anomalies_df = df[df['is_anomaly'] == -1]

        return {
            "status": "success",
            "summary": {
                "total_points": len(df),
                "anomalies_found": len(anomalies_df),
                "current_usage": round(df['value'].iloc[-1], 4)
            },
            "all_metrics": df[['time_formatted', 'value', 'is_anomaly']].to_dict(orient='records'),
            "anomalies": anomalies_df[['timestamp', 'value']].to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 2. PREDICTIVE: MEMORY FORECASTING (Prophet) ---
@app.get("/predict/memory")
async def predict_memory():
    """Forecasts memory leaks over the next 2 hours"""
    try:
        # Pull 6h of history to establish a trend
        query = "node_memory_Active_bytes"
        result = prom.custom_query(query=query + "[6h:5m]")
        
        if not result:
            return {"status": "error", "message": "No memory data found"}

        df = pd.DataFrame(result[0]['values'], columns=['ds', 'y'])
        df['ds'] = pd.to_datetime(df['ds'], unit='s')
        df['y'] = df['y'].astype(float) / (1024 * 1024)  # MB

        # Fit Prophet (Fast Mode)
        m = Prophet(changepoint_prior_scale=0.01, yearly_seasonality=False, weekly_seasonality=False)
        m.fit(df)

        # Predict 2 hours
        future = m.make_future_dataframe(periods=24, freq='5min')
        forecast = m.predict(future)

        forecast_subset = forecast[['ds', 'yhat', 'yhat_upper', 'yhat_lower']].tail(36)
        forecast_subset['time_formatted'] = forecast_subset['ds'].dt.strftime('%H:%M')

        return {
            "status": "success",
            "current_val_mb": round(df['y'].iloc[-1], 2),
            "predicted_val_2h_mb": round(forecast['yhat'].iloc[-1], 2),
            "forecast": forecast_subset[['time_formatted', 'yhat', 'yhat_upper', 'yhat_lower']].to_dict(orient='records')
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 3. PREDICTIVE: DISK CAPACITY FORECASTING (Prophet) ---
@app.get("/predict/disk")
async def predict_disk():
    """Predicts days remaining until disk exhaustion (Critical for storage management)"""
    try:
        # Calculate Percentage Used: (1 - Avail/Size) * 100
        query = '(1 - (node_filesystem_avail_bytes{device=~"/dev/.*"} / node_filesystem_size_bytes{device=~"/dev/.*"})) * 100'
        # Disk moves slowly, so we look at the last 24 hours
        result = prom.custom_query(query=query + "[24h:15m]")
        
        if not result:
            return {"status": "error", "message": "No disk data found"}

        df = pd.DataFrame(result[0]['values'], columns=['ds', 'y'])
        df['ds'] = pd.to_datetime(df['ds'], unit='s')
        df['y'] = df['y'].astype(float)

        # Fit Prophet for long-term trend
        m = Prophet(changepoint_prior_scale=0.01, yearly_seasonality=False)
        m.fit(df)

        # Predict 2 days into the future (hourly resolution)
        future = m.make_future_dataframe(periods=48, freq='H')
        forecast = m.predict(future)

        # Logic to estimate "Days until Full"
        limit_hit = forecast[forecast['yhat'] >= 90] # Warning threshold 90%
        days_remaining = "Safe (>2 days)"
        if not limit_hit.empty:
            eta = limit_hit['ds'].iloc[0]
            remaining_seconds = (eta - datetime.now()).total_seconds()
            days_remaining = f"{round(remaining_seconds / 86400, 1)} days"

        return {
            "status": "success",
            "current_usage_percent": round(df['y'].iloc[-1], 2),
            "days_until_90_percent": days_remaining,
            "forecast": forecast[['ds', 'yhat']].tail(48).to_dict(orient='records')
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- HEALTH CHECK ---
@app.get("/health")
def health():
    return {
        "status": "ok", 
        "iso_model_loaded": iso_model is not None, 
        "prometheus_connected": prom.check_prometheus_connection()
    }
