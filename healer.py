import requests
import time
import subprocess
import os

API_BASE = "http://localhost:8000"
KUBECONFIG = "/home/ubuntu/.kube/config"
KUBECTL_PATH = "/usr/local/bin/kubectl"

def heal():
    print("--- 🛡️ AIOps Multi-Vector Healer Started ---")
    os.environ["KUBECONFIG"] = KUBECONFIG
    while True:
        try:
            # CPU (Reactive)
            cpu_res = requests.get(f"{API_BASE}/detect/live", timeout=15).json()
            if cpu_res.get("status") == "success" and cpu_res["summary"].get("anomalies_found", 0) > 0:
                print("!!! [CPU] Anomaly. Killing pods...")
                subprocess.run([KUBECTL_PATH, "delete", "pods", "-l", "app=chaos-worker", "-n", "monitoring", "--now"])

            # Memory (Predictive)
            mem_res = requests.get(f"{API_BASE}/predict/memory", timeout=25).json()
            if mem_res.get("status") == "success" and mem_res.get("predicted_val_2h_mb", 0) > (mem_res.get("current_val_mb", 0) * 1.2):
                print("🔮 [MEMORY] Predicted Leak. Restarting Deployment...")
                subprocess.run([KUBECTL_PATH, "rollout", "restart", "deployment/chaos-spike-generator", "-n", "monitoring"])

            # Disk (Strategic)
            disk_res = requests.get(f"{API_BASE}/predict/disk", timeout=25).json()
            if disk_res.get("status") == "success" and disk_res.get("current_usage_percent", 0) > 70:
                print(f"⚠️ [DISK] High Usage ({disk_res['current_usage_percent']}%). Triggering Cleanup...")
                subprocess.run([KUBECTL_PATH, "rollout", "restart", "deployment/chaos-spike-generator", "-n", "monitoring"])

        except Exception as e: print(f"⚠️ Healer Loop Error: {e}")
        time.sleep(30)

if __name__ == "__main__": heal()
