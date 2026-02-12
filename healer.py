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
            # 1. CPU Reaction
            cpu_res = requests.get(f"{API_BASE}/detect/live", timeout=5).json()
            if cpu_res.get("status") == "success":
                anoms = cpu_res["summary"].get("anomalies_found", 0)
                if anoms > 0:
                    print(f"!!! [CPU] Anomaly detected. Killing pods...")
                    subprocess.run([KUBECTL_PATH, "delete", "pods", "-l", "app=chaos-worker", "-n", "monitoring", "--now"])

            # 2. Memory Prediction
            mem_res = requests.get(f"{API_BASE}/predict/memory", timeout=10).json()
            if mem_res.get("status") == "success":
                curr = mem_res.get("current_val_mb", 0)
                pred = mem_res.get("predicted_val_2h_mb", 0)
                if pred > (curr * 1.2) and curr > 0:
                    print(f"🔮 [MEMORY] Predicted Leak trend. Restarting Deployment...")
                    subprocess.run([KUBECTL_PATH, "rollout", "restart", "deployment/chaos-spike-generator", "-n", "monitoring"])

            # 3. Disk Management
            disk_res = requests.get(f"{API_BASE}/predict/disk", timeout=10).json()
            if disk_res.get("status") == "success":
                eta = disk_res.get("days_until_90_percent", "")
                if "0." in str(eta) or "Critical" in str(eta):
                    print(f"⚠️ [DISK] CRITICAL: Storage predicted full in {eta}. Triggering cleanup...")

        except Exception as e:
            print(f"⚠️ Loop Error: {e}")
        time.sleep(15)

if __name__ == "__main__":
    heal()
