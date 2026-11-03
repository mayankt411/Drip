"""
fetch_s2_metadata.py - Query and catalogue all Sentinel-2 L2A granules for Cushing AOI

Queries the CDSE STAC catalog for Sentinel-2 L2A tiles covering the Cushing AOI
between 2021-01-01 and 2023-12-31.
Saves raw catalogue JSON, records SHA-256, and logs all scenes into manifest and exclusions tables.
"""

import os
import sys
import json
import hashlib
from datetime import datetime
import urllib.request
import urllib.parse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Cushing AOI bounding box
# west: -96.85, south: 35.91, east: -96.69, north: 36.05
bbox_str = "-96.85,35.91,-96.69,36.05"
start_date = "2021-01-01T00:00:00Z"
end_date = "2023-12-31T23:59:59Z"

base_url = "https://stac.dataspace.copernicus.eu/v1/collections/sentinel-2-l2a/items"
params = {
    "bbox": bbox_str,
    "datetime": f"{start_date}/{end_date}",
    "limit": 100
}

all_features = []
next_url = f"{base_url}?{urllib.parse.urlencode(params)}"
page = 1

print("Querying CDSE STAC for Sentinel-2 L2A scenes over Cushing...")
while next_url:
    print(f"Fetching page {page}...")
    req = urllib.request.Request(next_url, headers={"User-Agent": "AntigravityResearchPipeline/1.0"})
    with urllib.request.urlopen(req) as resp:
        body = resp.read()
    
    data = json.loads(body.decode("utf-8"))
    features = data.get("features", [])
    all_features.extend(features)
    print(f"Retrieved {len(features)} items on page {page} (Total: {len(all_features)})")
    
    # Check for next link
    next_url = None
    for link in data.get("links", []):
        if link.get("rel") == "next":
            next_url = link.get("href")
            break
    page += 1

raw_out_path = os.path.join(PROJECT_ROOT, "data", "raw", "s2_cushing_stac_2021_2023.json")
raw_json = json.dumps({"type": "FeatureCollection", "features": all_features}, indent=2)
raw_bytes = raw_json.encode("utf-8")

with open(raw_out_path, "wb") as f:
    f.write(raw_bytes)

sha256 = hashlib.sha256(raw_bytes).hexdigest()
retrieval_time = datetime.utcnow().isoformat() + "Z"

# Append to manifest
manifest_path = os.path.join(PROJECT_ROOT, "data", "manifest.csv")
manifest_row = (
    f"https://stac.dataspace.copernicus.eu/v1/collections/sentinel-2-l2a/items,"
    f"{retrieval_time},"
    f"\"bbox={bbox_str};datetime={start_date}/{end_date}\","
    f"SENTINEL-2-L2A-CUSHING-COLLECTION,NA,{sha256},SUCCESS\n"
)
with open(manifest_path, "a") as f:
    f.write(manifest_row)

# Filter by cloud threshold (<= 40%) and log exclusions
exclusions_path = os.path.join(PROJECT_ROOT, "data", "exclusions.csv")
with open(exclusions_path, "a") as exc_file:
    for feat in all_features:
        feat_id = feat.get("id")
        props = feat.get("properties", {})
        cloud_pct = props.get("eo:cloud_cover", 100.0)
        dt = props.get("datetime", "")
        if cloud_pct > 40.0:
            exc_file.write(f"{feat_id},PRODUCT,{dt},CLOUD_COVER_EXCEEDS_THRESHOLD_{cloud_pct:.1f}PCT,cloud_mask\n")

print(f"Processed {len(all_features)} Sentinel-2 scenes. Raw catalog written to {raw_out_path}.")
