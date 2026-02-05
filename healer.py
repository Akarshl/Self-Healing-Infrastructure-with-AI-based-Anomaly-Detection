import requests
import time
import subprocess
import os

# Configuration
API_URL = "http://localhost:8000/detect/live"
CHECK_INTERVAL = 15 
KUBECONFIG = "/home/ubuntu/.kube/config"
KUBECTL_PATH = "/usr/local/bin/kubectl"

def heal():
    print("--- AIOps Remediation Engine Started ---")
    os.environ["KUBECONFIG"] = KUBECONFIG

    while True:
        try:
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # FIXED: Access the nested summary dictionary
                summary = data.get("summary", {})
                anomalies = summary.get("anomalies_found", 0)
                
                if anomalies > 0:
                    print(f"!!! ALERT: {anomalies} anomalies detected by AI. Triggering Healing...")
                    
                    result = subprocess.run(
                        [KUBECTL_PATH, "delete", "pods", "-l", "app=chaos-worker", "-n", "monitoring", "--now"],
                        capture_output=True, text=True
                    )
                    
                    if result.returncode == 0:
                        print("SUCCESS: Anomalous pods deleted. Deployment will restart them.")
                    else:
                        print(f"REMEDIATION ERROR: {result.stderr}")
                else:
                    current_usage = summary.get("current_usage", 0)
                    print(f"Status: Cluster Healthy. (Current Load: {current_usage:.2f})")
            else:
                print(f"API Error: {response.status_code}")

        except Exception as e:
            print(f"Connection Error: {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    heal()
