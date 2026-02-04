import requests
import time
import subprocess

API_URL = "http://localhost:8000/detect/live"

def heal():
    print("AIOps Healer started. Monitoring for anomalies...")
    while True:
        try:
            response = requests.get(API_URL)
            data = response.json()
            
            if data.get("anomalies_detected", 0) > 0:
                print(f"!!! ANOMALY DETECTED: {data['anomalies_detected']} points. Triggering healing...")
                
                # Remediation Action: Delete the chaos pod causing the spike
                subprocess.run(["kubectl", "delete", "pod", "cpu-chaos-test", "-n", "monitoring"])
                print("Healing complete: Chaos pod removed.")
                
            else:
                print("System healthy...")
                
        except Exception as e:
            print(f"Waiting for API to be ready... {e}")
            
        time.sleep(10) # Check every 10 seconds

if __name__ == "__main__":
    heal()
