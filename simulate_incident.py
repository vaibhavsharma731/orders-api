"""
sample/simulate_incident.py

Quick helper script to simulate incidents on your running sample service.
Usage:
  python simulate_incident.py db_exhaustion
  python simulate_incident.py memory_leak
  python simulate_incident.py bad_deployment
  python simulate_incident.py reset
"""

import sys
import urllib.request
import json

TARGET_URL = "http://localhost:8080"

SCENARIOS = {
    "db_exhaustion": "/chaos/db-exhaustion",
    "memory_leak": "/chaos/memory-leak",
    "bad_deployment": "/chaos/bad-deployment",
    "reset": "/chaos/reset"
}

def trigger_scenario(scenario_name: str):
    endpoint = SCENARIOS.get(scenario_name)
    if not endpoint:
        print(f"Unknown scenario '{scenario_name}'. Valid options: {list(SCENARIOS.keys())}")
        return

    url = f"{TARGET_URL}{endpoint}"
    print(f"[*] Sending chaos trigger to {url} ...")
    try:
        req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            print(f"[✓] Success: {data}")
            print("\n🚨 Incident is now LIVE! Now open AegisAI dashboard and click 'Run AegisAI Investigation'.")
    except Exception as e:
        print(f"[!] Error triggering scenario: {e}")
        print("    Make sure your sample service is running: python app.py")

if __name__ == "__main__":
    scenario = sys.argv[1] if len(sys.argv) > 1 else "db_exhaustion"
    trigger_scenario(scenario)
