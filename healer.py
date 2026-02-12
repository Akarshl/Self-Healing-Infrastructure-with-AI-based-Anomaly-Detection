import requests
import time
import subprocess
import os

# --- Configuration ---
API_BASE = "http://localhost:8000"
KUBECONFIG = "/home/ubuntu/.kube/config"
KUBECTL_PATH = "/usr/local/bin/kubectl"

def heal():
    print("--- 🛡️ AIOps Multi-Vector Healer Started ---")
    # Ensure the environment knows where the Kubeconfig is located
    os.environ["KUBECONFIG"] = KUBECONFIG

    while True:
        try:
            # 1. CPU Spike Reaction (Isolation Forest - Reactive)
            # Detects immediate anomalies in CPU usage
            cpu_res = requests.get(f"{API_BASE}/detect/live", timeout=5).json()
            if cpu_res.get("status") == "success":
                summary = cpu_res.get("summary", {})
                anoms = summary.get("anomalies_found", 0)
                if anoms > 0:
                    print(f"!!! [CPU] {anoms} anomalies detected. Killing anomalous pods...")
                    subprocess.run([
                        KUBECTL_PATH, "delete", "pods", 
                        "-l", "app=chaos-worker", 
                        "-n", "monitoring", "--now"
                    ], capture_output=True)

            # 2. Memory Leak Prediction (Prophet - Predictive)
            # Triggers if memory is forecasted to grow >20% in the next 2 hours
            mem_res = requests.get(f"{API_BASE}/predict/memory", timeout=10).json()
            if mem_res.get("status") == "success":
                curr = mem_res.get("current_val_mb", 0)
                pred = mem_res.get("predicted_val_2h_mb", 0)
                
                if curr > 0 and pred > (curr * 1.2):
                    print(f"🔮 [MEMORY] Predictive Alert: Leak trend detected ({curr}MB -> {pred}MB). Restarting Deployment...")
                    subprocess.run([
                        KUBECTL_PATH, "rollout", "restart", 
                        "deployment/chaos-spike-generator", 
                        "-n", "monitoring"
                    ], capture_output=True)

            # 3. Disk Capacity Management (Prophet - Strategic)
            # Triggers if disk is predicted to hit 90% in less than 24 hours
            disk_res = requests.get(f"{API_BASE}/predict/disk", timeout=10).json()
            if disk_res.get("status") == "success":
                eta = disk_res.get("days_until_90_percent", "")
                # ETA containing "0." implies less than 1 day remaining
                if "0." in str(eta) or "Critical" in str(eta):
                    print(f"⚠️ [DISK] CRITICAL: Storage predicted full in {eta}. Triggering automated cleanup...")
                    # Add your cleanup commands here, for example:
                    # subprocess.run([KUBECTL_PATH, "delete", "evicted", "pods", "--all-namespaces"])

        except Exception as e:
            print(f"⚠️ Healer Loop Error: {e}")

        # Sync interval: 15 seconds matches the dashboard refresh rate
        time.sleep(15)

if __name__ == "__main__":
    heal()
