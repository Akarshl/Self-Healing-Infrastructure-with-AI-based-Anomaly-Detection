import pandas as pd
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
import joblib  # To save the model
import os      # To create the models directory

# 1. Load Data
df = pd.read_csv("data/ec2_cpu_utilization_5f5533.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])

# 2. Train Isolation Forest
# contamination=0.01 means we expect roughly 1% of the data to be anomalous
model = IsolationForest(contamination=0.01, random_state=42)
df['anomaly_score'] = model.fit_predict(df[['value']])

# -1 indicates an anomaly, 1 indicates normal data
anomalies = df[df['anomaly_score'] == -1]

print(f"Detected {len(anomalies)} anomalies in the dataset.")

# 3. Quick Visualization (Optional)
# If you are on a headless EC2, this will save a PNG file instead of showing a window
plt.figure(figsize=(12,6))
plt.plot(df['timestamp'], df['value'], color='blue', label='CPU Usage')
plt.scatter(anomalies['timestamp'], anomalies['value'], color='red', label='Anomaly')
plt.title("AIOps Detection: EC2 CPU Anomalies")
plt.legend()
plt.savefig("anomaly_detection_result.png")
print("Result saved as anomaly_detection_result.png")

# 4. Save the Model
# Ensure the directory exists
os.makedirs("models", exist_ok=True)

# Save the model to a file
model_filename = "models/iso_forest.joblib"
joblib.dump(model, model_filename)
print(f"Model saved successfully at {model_filename}")
