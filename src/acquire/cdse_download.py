"""
cdse_download.py - Copernicus Data Space Ecosystem (CDSE) S2 L2A Acquisition

Acquires Sentinel-2 Level-2A surface reflectance products intersecting the Cushing AOI.
Logs full provenance into data/manifest.csv and records any exclusions into data/exclusions.csv.
"""

import os
import hashlib
import requests
from datetime import datetime
import yaml

def get_manifest_row(url, query_params, product_id, cloud_cover, checksum, status):
    return {
        "source_url_or_endpoint": url,
        "retrieval_time_utc": datetime.utcnow().isoformat() + "Z",
        "query_params": query_params,
        "product_id_or_series": product_id,
        "cloud_cover": cloud_cover,
        "sha256_checksum": checksum,
        "status": status
    }

def calculate_sha256(filepath):
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()

def search_cdse_stac(bbox, start_date, end_date):
    """
    Search Sentinel-2 L2A via CDSE STAC API.
    """
    stac_endpoint = "https://catalogue.dataspace.copernicus.eu/stac/search"
    payload = {
        "collections": ["SENTINEL-2"],
        "bbox": [bbox['west'], bbox['south'], bbox['east'], bbox['north']],
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "query": {
            "processingLevel": {"eq": "S2MSI2A"}
        },
        "limit": 100
    }
    return stac_endpoint, payload
