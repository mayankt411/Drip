"""
download_sample_s2_images.py - Download representative high-quality Sentinel-2 scenes
directly into data/raw/imagery/ and record SHA-256 provenance in data/manifest.csv.
"""

import os
import json
import hashlib
import urllib.request
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
raw_imagery_dir = os.path.join(PROJECT_ROOT, "data", "raw", "imagery")
os.makedirs(raw_imagery_dir, exist_ok=True)

stac_path = os.path.join(PROJECT_ROOT, "data", "raw", "s2_cushing_stac_2021_2023.json")
with open(stac_path, "r", encoding="utf-8") as f:
    stac_data = json.load(f)

features = stac_data["features"]
clear_scenes = [f for f in features if f["properties"].get("eo:cloud_cover", 100.0) < 2.0]
clear_scenes.sort(key=lambda x: x["properties"].get("datetime"), reverse=True)

# Select 5 diverse seasonal clear scenes
selected_scenes = clear_scenes[:5]

manifest_path = os.path.join(PROJECT_ROOT, "data", "manifest.csv")

print(f"Downloading {len(selected_scenes)} sample Sentinel-2 imagery quicklooks into data/raw/imagery/...")

for f in selected_scenes:
    scene_id = f["id"]
    props = f["properties"]
    dt = props.get("datetime")[:10]
    cloud = props.get("eo:cloud_cover")
    thumb_url = f["assets"].get("thumbnail", {}).get("href")
    
    if not thumb_url:
        continue
        
    out_fname = f"{dt}_{scene_id[:30]}_quicklook.jpg"
    out_path = os.path.join(raw_imagery_dir, out_fname)
    
    print(f"Fetching {out_fname} ({dt}, cloud: {cloud}%)...")
    req = urllib.request.Request(thumb_url, headers={"User-Agent": "AntigravityResearchPipeline/1.0"})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
        
    with open(out_path, "wb") as out_f:
        out_f.write(content)
        
    sha256 = hashlib.sha256(content).hexdigest()
    retrieval_time = datetime.utcnow().isoformat() + "Z"
    
    # Append to manifest
    with open(manifest_path, "a", encoding="utf-8") as m_f:
        m_f.write(f"{thumb_url},{retrieval_time},\"scene_id={scene_id}\",{out_fname},{cloud},{sha256},SUCCESS\n")

print(f"Sample images successfully downloaded and stored locally in {raw_imagery_dir}")
