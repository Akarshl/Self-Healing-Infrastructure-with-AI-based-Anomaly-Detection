import pandas as pd
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
import joblib
import os

# Use absolute paths to avoid directory confusion during automation
BASE_DIR = "/home/ubuntu/aiops-project"
DATA_PATH = os.path.join(BASE_DIR, "data", "ec2_cpu_utilization_5f5533.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_FILE = os.path.join(MODEL_DIR, "iso_forest.joblib")

# 1. Load Data
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Missing CSV at {DATA_PATH}")

df = pd.read_csv(DATA_PATH)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# 2. Train Isolation Forest
model = IsolationForest(contamination=0.01, random_state=42)
df['anomaly_score'] = model.fit_predict(df[['value']])

# 3. Save the Model
os.makedirs(MODEL_DIR, exist_ok=True)
joblib.dump(model, MODEL_FILE)
print(f"Model saved successfully at {MODEL_FILE}")

# 4. Save Visualization
plt.figure(figsize=(12,6))
plt.plot(df['timestamp'], df['value'], color='blue', label='CPU Usage')
anomalies = df[df['anomaly_score'] == -1]
plt.scatter(anomalies['timestamp'], anomalies['value'], color='red', label='Anomaly')
plt.savefig(os.path.join(BASE_DIR, "anomaly_detection_result.png"))
