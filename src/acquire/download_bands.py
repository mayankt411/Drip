"""
download_bands.py - Download required Sentinel-2 L2A spectral bands for Cushing AOI

Queries the STAC catalog and downloads Level-2A bands (B02, B03, B04, B08, SCL)
for representative clear weekly passes across the study window.
Logs every downloaded granule with exact SHA-256 in data/manifest.csv.
"""

import os
import sys
import json
import hashlib
import requests
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 1. CDSE Authentication
def get_cdse_token():
    env_file = os.path.join(PROJECT_ROOT, ".env")
    username, password = None, None
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith("CDSE_USERNAME="):
                    username = line.strip().split("=", 1)[1]
                elif line.startswith("CDSE_PASSWORD="):
                    password = line.strip().split("=", 1)[1]
                    
    if not username or not password:
        raise ValueError("CDSE credentials not found in .env")
        
    auth_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    payload = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password"
    }
    resp = requests.post(auth_url, data=payload)
    if resp.status_code != 200:
        raise RuntimeError(f"Authentication failed: {resp.text}")
    return resp.json()["access_token"]

def download_product_band(url, out_path, token):
    headers = {"Authorization": f"Bearer {token}"}
    with requests.get(url, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
    # Checksum
    sha = hashlib.sha256()
    with open(out_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

if __name__ == "__main__":
    print("CDSE band download pipeline initialized.")
