import requests
import time
import subprocess
import os

# Configuration
API_BASE = "http://localhost:8000"
CHECK_INTERVAL = 15 
KUBECONFIG = "/home/ubuntu/.kube/config"
KUBECTL_PATH = "/usr/local/bin/kubectl"

def heal():
    print("--- 🛡️ AIOps Multi-Vector Healer Started ---")
    os.environ["KUBECONFIG"] = KUBECONFIG

    while True:
        try:
            # --- 1. CPU REACTION (Isolation Forest) ---
            cpu_res = requests.get(f"{API_BASE}/detect/live", timeout=5)
            if cpu_res.status_code == 200:
                cpu_data = cpu_res.json()
                summary = cpu_data.get("summary", {})
                anomalies = summary.get("anomalies_found", 0)
                
                if anomalies > 0:
                    print(f"!!! [CPU] {anomalies} anomalies detected. Killing anomalous pods...")
                    subprocess.run([KUBECTL_PATH, "delete", "pods", "-l", "app=chaos-worker", "-n", "monitoring", "--now"])
                else:
                    print(f"Status: CPU Healthy ({summary.get('current_usage', 0):.2f})")

            # --- 2. MEMORY PREDICTION (Prophet) ---
            mem_res = requests.get(f"{API_BASE}/predict/memory", timeout=10)
            if mem_res.status_code == 200:
                mem_data = mem_res.json()
                current = mem_data.get("current_val_mb", 0)
                predicted = mem_data.get("predicted_val_2h_mb", 0)
                
                # If memory is predicted to grow by more than 20% in 2 hours (Potential Leak)
                if predicted > (current * 1.2) and current > 0:
                    print(f"🔮 [MEMORY] Predictive Alert: Leak Detected ({current}MB -> {predicted}MB). Restarting Deployment...")
                    subprocess.run([KUBECTL_PATH, "rollout", "restart", "deployment/chaos-spike-generator", "-n", "monitoring"])

            # --- 3. DISK CAPACITY (Prophet) ---
            disk_res = requests.get(f"{API_BASE}/predict/disk", timeout=10)
            if disk_res.status_code == 200:
                disk_data = disk_res.json()
                eta = disk_data.get("days_until_90_percent", "")
                # If the ETA contains "0." it means less than 24 hours remain
                if "0." in str(eta):
                    print(f"⚠️ [DISK] CRITICAL: Storage predicted to hit 90% in {eta}. Log cleanup required.")

        except Exception as e:
            print(f"⚠️ Connection/Logic Error: {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    heal()
