import requests
import time
import subprocess
import os

# Configuration
API_URL = "http://localhost:8000/detect/live"
CHECK_INTERVAL = 15  # Wait 15s between checks to allow Prometheus to update
KUBECONFIG = "/home/ubuntu/.kube/config"

def heal():
    print("--- AIOps Remediation Engine Started ---")
    os.environ["KUBECONFIG"] = KUBECONFIG

    while True:
        try:
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                anomalies = data.get("anomalies_detected", 0)
                
                if anomalies > 0:
                    print(f"!!! ALERT: {anomalies} anomalies detected. Triggering Healing...")
                    
                    # ACTION: Delete pods by label selector (app=chaos-worker)
                    # The Deployment will automatically recreate these pods.
                    result = subprocess.run(
                        ["kubectl", "delete", "pods", "-l", "app=chaos-worker", "-n", "monitoring", "--now"],
                        capture_output=True, text=True
                    )
                    
                    if result.returncode == 0:
                        print("SUCCESS: Anomalous pods deleted. Deployment will restart them.")
                    else:
                        print(f"REMEDIATION ERROR: {result.stderr}")
                else:
                    print("Status: Cluster Healthy.")
            else:
                print(f"API Error: {response.status_code}")

        except Exception as e:
            print(f"Connection Error: {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    heal()
