from fastapi import FastAPI, HTTPException
from sklearn.ensemble import IsolationForest
from prometheus_api_client import PrometheusConnect
import pandas as pd
import joblib
import os

app = FastAPI(title="AIOps Real-Time Inference API")

# 1. PROMETHEUS CONFIGURATION
# Ansible will automatically replace this URL with the correct NodePort
PROMETHEUS_URL = "http://localhost:30206"
prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

# Ansible will replace this with the absolute path
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
    """ Fetches live metrics via PromQL subquery and runs anomaly detection """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # 2. PROMETHEUS SUBQUERY FIX
        # Fetches 1 hour of data at 1-minute resolution
        query = "sum(rate(node_cpu_seconds_total[5m]))[1h:1m]"
        result = prom.custom_query(query=query)

        if not result:
            return {"message": "No data found"}

        # 3. DATA EXTRACTION
        values = result[0]['values']
        df = pd.DataFrame(values, columns=['timestamp', 'value'])
        df['value'] = df['value'].astype(float)

        # 4. INFERENCE
        df['anomaly'] = model.predict(df[['value']])
        anomalies = df[df['anomaly'] == -1]

        return {
            "status": "success",
            "data_points_analyzed": len(df),
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies[['timestamp', 'value']].to_dict(orient='records')
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AIOps Error: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}
