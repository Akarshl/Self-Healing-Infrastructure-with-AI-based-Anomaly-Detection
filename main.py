from fastapi import FastAPI, HTTPException
from sklearn.ensemble import IsolationForest
from prometheus_api_client import PrometheusConnect
from prophet import Prophet
import pandas as pd
import joblib
import os
import logging
from datetime import datetime

# Suppress technical output
logging.getLogger('prophet').setLevel(logging.WARNING)
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

app = FastAPI(title="AIOps Intelligent Inference Engine")

# 1. PROMETHEUS CONFIGURATION
PROMETHEUS_URL = "http://localhost:31173"
prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

# 2. MODEL PATHS
ISO_MODEL_PATH = "/home/ubuntu/aiops-project/models/iso_forest.joblib"
iso_model = None

@app.on_event("startup")
def load_models():
    global iso_model
    if os.path.exists(ISO_MODEL_PATH):
        iso_model = joblib.load(ISO_MODEL_PATH)
        print(f"✅ Isolation Forest loaded successfully")

# --- CPU ANOMALY DETECTION ---
@app.get("/detect/live")
async def detect_live():
    if iso_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        query = "sum(rate(node_cpu_seconds_total[1m]))[30m:30s]"
        result = prom.custom_query(query=query)
        if not result:
            return {"status": "error", "message": "No CPU data"}

        df = pd.DataFrame(result[0]['values'], columns=['timestamp', 'value'])
        df['value'] = df['value'].astype(float)
        df['time_formatted'] = df['timestamp'].apply(lambda x: datetime.fromtimestamp(float(x)).strftime('%H:%M:%S'))
        df['is_anomaly'] = iso_model.predict(df[['value']])
        
        return {
            "status": "success",
            "summary": {"current_usage": round(df['value'].iloc[-1], 4), "anomalies_found": len(df[df['is_anomaly'] == -1])},
            "all_metrics": df[['time_formatted', 'value', 'is_anomaly']].to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- MEMORY FORECASTING ---
@app.get("/predict/memory")
async def predict_memory():
    try:
        query = "node_memory_Active_bytes"
        result = prom.custom_query(query=query + "[10m:30s]")
        if not result: return {"status": "error", "message": "No data"}

        df = pd.DataFrame(result[0]['values'], columns=['ds', 'y'])
        df['ds'] = pd.to_datetime(df['ds'], unit='s')
        df['y'] = df['y'].astype(float) / (1024 * 1024) # MB

        m = Prophet(changepoint_prior_scale=0.01, yearly_seasonality=False, weekly_seasonality=False)
        m.fit(df)
        future = m.make_future_dataframe(periods=24, freq='5min')
        forecast = m.predict(future)
        res = forecast[['ds', 'yhat', 'yhat_upper', 'yhat_lower']].tail(36)
        res['time_formatted'] = res['ds'].dt.strftime('%H:%M')

        return {
            "status": "success",
            "current_val_mb": round(df['y'].iloc[-1], 2),
            "predicted_val_2h_mb": round(forecast['yhat'].iloc[-1], 2),
            "forecast": res.to_dict(orient='records')
        }
    except Exception as e: return {"status": "error", "message": str(e)}

# --- DISK CAPACITY FORECASTING ---
@app.get("/predict/disk")
async def predict_disk():
    try:
        # UNIVERSAL QUERY: Targets root mountpoint to ensure data is found on EC2
        query = '(sum(node_filesystem_size_bytes{mountpoint="/"}) - sum(node_filesystem_avail_bytes{mountpoint="/"})) / sum(node_filesystem_size_bytes{mountpoint="/"}) * 100'
        result = prom.custom_query(query=query + "[10m:30s]")
        if not result: return {"status": "error", "message": "No data"}

        df = pd.DataFrame(result[0]['values'], columns=['ds', 'y'])
        df['ds'] = pd.to_datetime(df['ds'], unit='s')
        df['y'] = df['y'].astype(float)

        m = Prophet(changepoint_prior_scale=0.01, yearly_seasonality=False)
        m.fit(df)
        future = m.make_future_dataframe(periods=48, freq='H')
        forecast = m.predict(future)
        
        limit_hit = forecast[forecast['yhat'] >= 90]
        days = "Safe (>2 days)"
        if not limit_hit.empty:
            days = f"{round((limit_hit['ds'].iloc[0] - datetime.now()).total_seconds() / 86400, 1)} days"

        return {
            "status": "success",
            "current_usage_percent": round(df['y'].iloc[-1], 2),
            "days_until_90_percent": days,
            "forecast": forecast[['ds', 'yhat']].tail(48).to_dict(orient='records')
        }
    except Exception as e: return {"status": "error", "message": str(e)}

@app.get("/health")
def health():
    return {"status": "ok", "prometheus_connected": prom.check_prometheus_connection()}
