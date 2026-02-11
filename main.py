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
# Locked to 31173 via Ansible automation
PROMETHEUS_URL = "http://localhost:31173"
prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

# 2. MODEL PATHS
# Path is managed by Ansible to be absolute
ISO_MODEL_PATH = "/home/ubuntu/aiops-project/models/iso_forest.joblib"
iso_model = None

@app.on_event("startup")
def load_models():
    global iso_model
    if os.path.exists(ISO_MODEL_PATH):
        iso_model = joblib.load(ISO_MODEL_PATH)
        print(f"✅ Isolation Forest loaded from {ISO_MODEL_PATH}")

# --- 1. REACTIVE: CPU ANOMALY DETECTION (Isolation Forest) ---
@app.get("/detect/live")
async def detect_live():
    """Fetches real-time CPU metrics for anomaly detection and remediation"""
    if iso_model is None:
        raise HTTPException(status_code=503, detail="Isolation Forest model not loaded")

    try:
        # Window for CPU spikes
        query = "sum(rate(node_cpu_seconds_total[1m]))[30m:30s]"
        result = prom.custom_query(query=query)

        if not result:
            return {"status": "error", "message": "No CPU data found"}

        df = pd.DataFrame(result[0]['values'], columns=['timestamp', 'value'])
        df['value'] = df['value'].astype(float)
        df['time_formatted'] = df['timestamp'].apply(
            lambda x: datetime.fromtimestamp(float(x)).strftime('%H:%M:%S')
        )

        # Inference: -1 = Anomaly, 1 = Normal
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
    """Predicts memory usage trends to identify slow leaks before OOM occurs"""
    try:
        query = "node_memory_Active_bytes"
        result = prom.custom_query(query=query + "[6h:5m]")
        
        if not result:
            return {"status": "error", "message": "No memory data found"}

        df = pd.DataFrame(result[0]['values'], columns=['ds', 'y'])
        df['ds'] = pd.to_datetime(df['ds'], unit='s')
        df['y'] = df['y'].astype(float) / (1024 * 1024)  # MB

        # Fast Prophet fit
        m = Prophet(changepoint_prior_scale=0.01, yearly_seasonality=False, weekly_seasonality=False)
        m.fit(df)

        # Forecast 2 hours
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
    """Forecasts disk exhaustion using NVMe/Root device metrics"""
    try:
        # Using the specific device identified via manual curl
        query = '(node_filesystem_size_bytes{device="/dev/root"} - node_filesystem_avail_bytes{device="/dev/root"}) / node_filesystem_size_bytes{device="/dev/root"} * 100'
        result = prom.custom_query(query=query + "[24h:15m]")
        
        if not result:
            return {"status": "error", "message": "No disk data found"}

        df = pd.DataFrame(result[0]['values'], columns=['ds', 'y'])
        df['ds'] = pd.to_datetime(df['ds'], unit='s')
        df['y'] = df['y'].astype(float)

        m = Prophet(changepoint_prior_scale=0.01, yearly_seasonality=False)
        m.fit(df)

        # Forecast 2 days (hourly)
        future = m.make_future_dataframe(periods=48, freq='H')
        forecast = m.predict(future)

        limit_hit = forecast[forecast['yhat'] >= 90]
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
