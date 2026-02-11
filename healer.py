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
            # 1. CPU REACTION (Isolation Forest)
            cpu_res = requests.get(f"{API_BASE}/detect/live", timeout=5)
            if cpu_res.status_code == 200:
                cpu_data = cpu_res.json()
                summary = cpu_data.get("summary", {})
                if summary.get("anomalies_found", 0) > 0:
                    print(f"!!! [CPU] Anomaly detected ({summary['current_usage']}). Killing pods...")
                    subprocess.run([KUBECTL_PATH, "delete", "pods", "-l", "app=chaos-worker", "-n", "monitoring", "--now"])
                else:
                    print(f"Status: CPU Healthy ({summary.get('current_usage', 0):.2f})")

            # 2. MEMORY PREDICTION (Prophet)
            mem_res = requests.get(f"{API_BASE}/predict/memory", timeout=10)
            if mem_res.status_code == 200:
                mem_data = mem_res.json()
                curr = mem_data.get("current_val_mb", 0)
                pred = mem_data.get("predicted_val_2h_mb", 0)
                
                # If memory is predicted to grow >25% in 2 hours
                if pred > (curr * 1.25) and curr > 0:
                    print(f"🔮 [MEMORY] Predictive Alert: Leak detected ({curr}MB -> {pred}MB). Restarting Deployment...")
                    subprocess.run([KUBECTL_PATH, "rollout", "restart", "deployment/chaos-spike-generator", "-n", "monitoring"])

            # 3. DISK CAPACITY (Prophet)
            disk_res = requests.get(f"{API_BASE}/predict/disk", timeout=10)
            if disk_res.status_code == 200:
                disk_data = disk_res.json()
                eta = disk_data.get("days_until_90_percent", "")
                if "0." in str(eta): # Less than 1 day remains
                    print(f"⚠️ [DISK] CRITICAL: Storage predicted full in {eta}. Cleanup triggered.")

        except Exception as e:
            print(f"⚠️ Healer Loop Error: {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    heal()
