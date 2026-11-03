"""
fetch_eia_data.py - Download and store official EIA Cushing crude stocks

Retrieves the official series W_EPC0_SAX_YCUOK_MBBL from EIA API v2,
saves the raw JSON to data/raw/eia_cushing_weekly.json,
computes SHA-256 checksum, and records full provenance into data/manifest.csv.
"""

import os
import sys
import json
import hashlib
from datetime import datetime
import urllib.request

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(PYTHON_DIR, "..", ".."))

# Read API key from .env
env_file = os.path.join(PROJECT_ROOT, ".env")
api_key = None
if os.path.exists(env_file):
    with open(env_file, "r") as f:
        for line in f:
            if line.startswith("EIA_API_KEY="):
                api_key = line.strip().split("=", 1)[1]

if not api_key:
    print("Error: EIA_API_KEY not found in .env")
    sys.exit(1)

# Endpoint for Cushing series W_EPC0_SAX_YCUOK_MBBL
url = (
    f"https://api.eia.gov/v2/petroleum/stoc/wstk/data/?"
    f"api_key={api_key}&frequency=weekly&data[0]=value&"
    f"facets[series][]=W_EPC0_SAX_YCUOK_MBBL&"
    f"start=2021-01-01&end=2023-12-31&"
    f"sort[0][column]=period&sort[0][direction]=asc&length=5000"
)

raw_dir = os.path.join(PROJECT_ROOT, "data", "raw")
os.makedirs(raw_dir, exist_ok=True)
raw_out_path = os.path.join(raw_dir, "eia_cushing_weekly_2021_2023.json")

print(f"Fetching EIA series W_EPC0_SAX_YCUOK_MBBL...")
req = urllib.request.Request(url, headers={"User-Agent": "AntigravityResearchPipeline/1.0"})
with urllib.request.urlopen(req) as response:
    raw_bytes = response.read()

with open(raw_out_path, "wb") as f:
    f.write(raw_bytes)

sha256 = hashlib.sha256(raw_bytes).hexdigest()
retrieval_time = datetime.utcnow().isoformat() + "Z"

# Parse JSON to confirm records count
data = json.loads(raw_bytes.decode("utf-8"))
records = data.get("response", {}).get("data", [])
print(f"Successfully retrieved {len(records)} weekly observations.")

# Update data/manifest.csv
manifest_path = os.path.join(PROJECT_ROOT, "data", "manifest.csv")
manifest_row = (
    f"https://api.eia.gov/v2/petroleum/stoc/wstk/data/,"
    f"{retrieval_time},"
    f"\"facets[series][]=W_EPC0_SAX_YCUOK_MBBL;start=2021-01-01;end=2023-12-31\","
    f"W_EPC0_SAX_YCUOK_MBBL,NA,{sha256},SUCCESS\n"
)

with open(manifest_path, "a") as f:
    f.write(manifest_row)

print("EIA acquisition complete and logged to manifest.")
