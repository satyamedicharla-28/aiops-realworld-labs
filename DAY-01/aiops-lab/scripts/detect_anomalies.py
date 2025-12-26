import os
import time
import requests
import configparser
import numpy as np
from sklearn.ensemble import IsolationForest

# ------------------ Load Config ------------------
config = configparser.ConfigParser()
config.read("scripts/config.ini")

PROM_URL = config["monitoring"]["prometheus_url"]
QUERY = config["monitoring"]["query"]

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")

if not SLACK_WEBHOOK:
    raise RuntimeError("❌ SLACK_WEBHOOK_URL environment variable not set")

# ------------------ Fetch Metric ------------------
def fetch_cpu_usage():
    try:
        response = requests.get(
            f"{PROM_URL}/api/v1/query",
            params={"query": QUERY},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        return float(data["data"]["result"][0]["value"][1])
    except Exception as e:
        print(f"⚠️ Fetch error: {e}")
        return None

# ------------------ Slack Alert ------------------
def alert_slack(message):
    try:
        response = requests.post(
            SLACK_WEBHOOK,
            json={"text": message},
            timeout=5
        )
        response.raise_for_status()
        print("✅ Slack alert sent")
    except Exception as e:
        print(f"⚠️ Slack alert failed: {e}")

# ------------------ Main Logic ------------------
if __name__ == "__main__":
    history = []

    print("🚀 AIOps anomaly detection started...")

    while True:
        cpu = fetch_cpu_usage()
        if cpu is not None:
            history.append(cpu)
            print(f"📊 CPU Usage: {cpu:.2f}%")

            if len(history) >= 10:
                model = IsolationForest(contamination=0.2)
                model.fit(np.array(history).reshape(-1, 1))

                prediction = model.predict([[cpu]])
                if prediction[0] == -1:
                    alert_slack(f"🚨 Anomaly detected! CPU usage = {cpu:.2f}%")

        time.sleep(15)
