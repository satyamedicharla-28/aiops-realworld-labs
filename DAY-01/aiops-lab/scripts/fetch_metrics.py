# Copyright (c) 2025 Rajinikanth Vadla
# All rights reserved.

import requests
import pandas as pd
import time
import os
import configparser

# -------------------------------
# FIX: Load config relative to script
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")

if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"❌ config.ini not found at {CONFIG_PATH}")

config = configparser.ConfigParser()
config.read(CONFIG_PATH)

PROM_URL = config["monitoring"]["prometheus_url"]
QUERY = config["monitoring"]["query"]

# Guardrail (never allow Docker DNS on host)
if "prometheus:9090" in PROM_URL:
    raise RuntimeError("❌ WRONG CONFIG LOADED — prometheus:9090 detected")

print(f"✅ Using Prometheus URL: {PROM_URL}")

def fetch_historical(hours=1):
    try:
        end = int(time.time())
        start = end - hours * 3600

        response = requests.get(
            f"{PROM_URL}/api/v1/query_range",
            params={
                "query": QUERY,
                "start": start,
                "end": end,
                "step": "60s"
            },
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

        if not data["data"]["result"]:
            raise ValueError("❌ No metrics returned — check node_exporter")

        points = data["data"]["result"][0]["values"]

        df = pd.DataFrame(points, columns=["timestamp", "cpu_usage"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df["cpu_usage"] = df["cpu_usage"].astype(float)

        output_file = os.path.join(BASE_DIR, "cpu_metrics.csv")
        df.to_csv(output_file, index=False)

        print(f"✅ Saved {len(df)} metrics to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fetch_historical(hours=6)
