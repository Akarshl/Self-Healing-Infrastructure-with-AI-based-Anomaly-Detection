from fastapi import FastAPI, HTTPException
from sklearn.ensemble import IsolationForest
from prometheus_api_client import PrometheusConnect
import pandas as pd
import joblib
import os
from datetime import datetime

app = FastAPI(title="AIOps Real-Time Inference API")

# 1. PROMETHEUS CONFIGURATION
PROMETHEUS_URL = "http://localhost:30206"
prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

# 2. MODEL CONFIGURATION
MODEL_PATH = "/home/ubuntu/aiops-project/models/iso_forest.joblib"
model = None

@app.on_event("startup")
def load_model():
    global model
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print(f"Model loaded successfully from {MODEL_PATH}")

@app.get("/detect/live")
async def detect_live():
    """ Fetches metrics, runs inference, and returns rich data for the dashboard """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Fetch 30 minutes of data at 30-second resolution for a smoother graph
        query = "sum(rate(node_cpu_seconds_total[1m]))[30m:30s]"
        result = prom.custom_query(query=query)

        if not result:
            return {"status": "error", "message": "No data found"}

        # 3. DATA EXTRACTION & PREPROCESSING
        values = result[0]['values']
        df = pd.DataFrame(values, columns=['timestamp', 'value'])
        df['value'] = df['value'].astype(float)
        
        # Convert Unix timestamp to readable format for the dashboard
        df['time_formatted'] = df['timestamp'].apply(
            lambda x: datetime.fromtimestamp(float(x)).strftime('%H:%M:%S')
        )

        # 4. INFERENCE (Isolation Forest)
        # -1 = Anomaly, 1 = Normal
        df['is_anomaly'] = model.predict(df[['value']])
        
        # Filter for the Healer
        anomalies_df = df[df['is_anomaly'] == -1]

        return {
            "status": "success",
            "summary": {
                "total_points": len(df),
                "anomalies_found": len(anomalies_df),
                "current_usage": df['value'].iloc[-1]
            },
            # 'all_metrics' used by Streamlit Dashboard
            "all_metrics": df[['time_formatted', 'value', 'is_anomaly']].to_dict(orient='records'),
            # 'anomalies' used by Healer Script
            "anomalies": anomalies_df[['timestamp', 'value']].to_dict(orient='records')
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AIOps Error: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None, "prometheus_connected": prom.check_prometheus_connection()}
