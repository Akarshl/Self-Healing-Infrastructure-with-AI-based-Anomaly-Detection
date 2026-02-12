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
            # CPU
            cpu_res = requests.get(f"{API_BASE}/detect/live", timeout=5).json()
            if cpu_res.get("status") == "success" and cpu_res["summary"].get("anomalies_found", 0) > 0:
                print("!!! [CPU] Anomaly. Killing pods...")
                subprocess.run([KUBECTL_PATH, "delete", "pods", "-l", "app=chaos-worker", "-n", "monitoring", "--now"])

            # MEMORY
            mem_res = requests.get(f"{API_BASE}/predict/memory", timeout=10).json()
            if mem_res.get("status") == "success":
                if mem_res.get("predicted_val_2h_mb", 0) > (mem_res.get("current_val_mb", 0) * 1.2):
                    print("🔮 [MEMORY] Predicted Leak. Restarting Deployment...")
                    subprocess.run([KUBECTL_PATH, "rollout", "restart", "deployment/chaos-spike-generator", "-n", "monitoring"])

            # DISK
            disk_res = requests.get(f"{API_BASE}/predict/disk", timeout=10).json()
            if disk_res.get("status") == "success" and disk_res.get("current_usage_percent", 0) > 70:
                print("⚠️ [DISK] High Usage. Triggering cleanup restart...")
                subprocess.run([KUBECTL_PATH, "rollout", "restart", "deployment/chaos-spike-generator", "-n", "monitoring"])

        except Exception as e: print(f"⚠️ Loop Error: {e}")
        time.sleep(15)

if __name__ == "__main__": heal()
