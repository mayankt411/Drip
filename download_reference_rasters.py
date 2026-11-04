import os
import io
import json
import csv
import math
import hashlib
import requests
from PIL import Image
from src.acquire.download_bands import get_cdse_token

def wgs84_to_utm14n(lat, lon):
    a = 6378137.0
    f = 1 / 298.257223563
    b = a * (1 - f)
    e = math.sqrt(1 - (b * b) / (a * a))
    e_prime_sq = (e * e) / (1 - e * e)
    k0 = 0.9996
    lon0 = -99.0 * math.pi / 180.0
    lat_rad = lat * math.pi / 180.0
    lon_rad = lon * math.pi / 180.0
    N = a / math.sqrt(1 - e * e * math.sin(lat_rad) ** 2)
    T = math.tan(lat_rad) ** 2
    C = e_prime_sq * math.cos(lat_rad) ** 2
    A = (lon_rad - lon0) * math.cos(lat_rad)
    M = a * ((1 - e**2/4 - 3*e**4/64 - 5*e**6/256) * lat_rad
             - (3*e**2/8 + 3*e**4/32 + 45*e**6/1024) * math.sin(2*lat_rad)
             + (15*e**4/256 + 45*e**6/1024) * math.sin(4*lat_rad)
             - (35*e**6/3072) * math.sin(6*lat_rad))
    easting = k0 * N * (A + (1 - T + C) * A**3 / 6 + (5 - 18*T + T**2 + 72*C - 58*e_prime_sq) * A**5 / 120) + 500000.0
    northing = k0 * (M + N * math.tan(lat_rad) * (A**2 / 2 + (5 - T + 9*C + 4*C**2) * A**4 / 24 + (61 - 58*T + T**2 + 600*C - 330*e_prime_sq) * A**6 / 720))
    return easting, northing

def get_band_url(stac_data, date_str, tile, band_key):
    for f in stac_data.get('features', []):
        fid = f.get('id', '')
        if date_str in fid and tile in fid:
            assets = f.get('assets', {})
            return assets.get(band_key, {}).get('alternate', {}).get('https', {}).get('href')
    return None

def download_and_crop(token, url, save_path):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    if os.path.exists(save_path):
        print(f"Already exists: {save_path}")
        return
    print(f"Downloading full band: {url}")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, stream=True)
    resp.raise_for_status()
    tmp_path = save_path + ".tmp"
    with open(tmp_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1048576):
            f.write(chunk)
    os.replace(tmp_path, save_path)
    print(f"Saved: {save_path} ({os.path.getsize(save_path) / 1024 / 1024:.1f} MB)")

def main():
    token = get_cdse_token()
    with open('data/raw/s2_cushing_stac_2021_2023.json', 'r') as f:
        stac_data = json.load(f)

    # We need 2023-12-05 (S2A) and 2023-12-10 (S2B), tiles T14SQE and T14SPE
    scenes = [
        ("20231205", "T14SQE"),
        ("20231205", "T14SPE"),
        ("20231210", "T14SQE"),
        ("20231210", "T14SPE")
    ]
    
    bands = ["B04_10m", "B08_10m"]
    
    for date_str, tile in scenes:
        for band in bands:
            url = get_band_url(stac_data, date_str, tile, band)
            if not url:
                print(f"Warning: No URL for {date_str} {tile} {band}")
                continue
            out_file = os.path.join("data", "raw", "rasters", f"{date_str}_{tile}_{band}.jp2")
            download_and_crop(token, url, out_file)

if __name__ == "__main__":
    main()
