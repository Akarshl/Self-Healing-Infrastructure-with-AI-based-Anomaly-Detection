from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.ensemble import IsolationForest
import pandas as pd
import joblib
import os

app = FastAPI(title="AIOps Anomaly Detection API")

# Path to save/load your model
MODEL_PATH = "models/iso_forest.joblib"

# Define the data structure for incoming requests
class MetricPoint(BaseModel):
    timestamp: str
    value: float

class MetricBatch(BaseModel):
    metrics: list[MetricPoint]

# Global model variable
model = None

@app.on_event("startup")
def load_model():
    global model
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print("Model loaded successfully.")
    else:
        # Fallback: Initialize and train a basic model if none exists
        # In production, you would train this on your Kaggle/Prometheus baseline
        print("No pre-trained model found. Initializing new model...")
        model = IsolationForest(contamination=0.01, random_state=42)

@app.post("/detect")
async def detect_anomalies(batch: MetricBatch):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not initialized")
    
    # Convert incoming JSON to DataFrame
    data = pd.DataFrame([m.dict() for m in batch.metrics])
    
    # Run Inference
    # predict() returns -1 for anomalies and 1 for normal data
    preds = model.predict(data[['value']])
    
    anomalies = []
    for i, pred in enumerate(preds):
        if pred == -1:
            anomalies.append(batch.metrics[i])
            
    return {
        "total_processed": len(batch.metrics),
        "anomalies_found": len(anomalies),
        "anomalies": anomalies
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": model is not None}
