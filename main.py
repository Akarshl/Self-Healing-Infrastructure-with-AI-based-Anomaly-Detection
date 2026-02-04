from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.ensemble import IsolationForest
from prometheus_api_client import PrometheusConnect
from prometheus_api_client.utils import parse_datetime
import pandas as pd
import joblib
import os

app = FastAPI(title="AIOps Real-Time Inference API")

# 1. PROMETHEUS CONFIGURATION
# This is the internal DNS name created by your Helm chart
PROMETHEUS_URL = "http://prometheus-kube-prometheus-prometheus.monitoring.svc:9090"
prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

MODEL_PATH = "models/iso_forest.joblib"
model = None

@app.on_event("startup")
def load_model():
    global model
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print("Model loaded successfully.")

@app.get("/detect/live")
async def detect_live():
    """ Fetches live metrics from Prometheus and runs anomaly detection """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Fetch last 1 hour of CPU Rate data
        # 'sum(rate(node_cpu_seconds_total[5m]))' gives us the average CPU usage
        metric_data = prom.get_metric_range_data(
            metric_name="sum(rate(node_cpu_seconds_total[5m]))",
            start_time=parse_datetime("1h"),
            end_time=parse_datetime("now")
        )

        if not metric_data:
            return {"message": "No metrics found in Prometheus for the last hour"}

        # Convert Prometheus format to DataFrame
        # Prometheus returns [timestamp, value]
        values = metric_data[0]['values']
        df = pd.DataFrame(values, columns=['timestamp', 'value'])
        df['value'] = df['value'].astype(float)

        # Run Inference
        df['anomaly'] = model.predict(df[['value']])
        
        # Filter for anomalies (-1)
        anomalies = df[df['anomaly'] == -1]

        return {
            "status": "success",
            "data_points_analyzed": len(df),
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies[['timestamp', 'value']].to_dict(orient='records')
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Prometheus: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok"}
