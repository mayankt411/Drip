"""Build the Cushing tank registry from OpenStreetMap storage_tank footprints.

Needs internet (Overpass). Capacity is NOT in OSM for most tanks, so the registry
carries diameter and a footprint-area weight only; volumes stay in relative units.
"""
import json
import re

import numpy as np
import pandas as pd
import requests
from pyproj import Transformer
from scipy.cluster.hierarchy import fcluster, linkage

from .common import ROOT, aoi, cfg, log_manifest, sha256

RAW = ROOT / "data" / "raw" / "osm_storage_tanks_cushing.json"
OUT = ROOT / "data" / "tanks" / "cushing_full_registry.csv"


def parse_diameter(tag):
    if tag is None:
        return None
    m = re.match(r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*(m|meter|metre|meters)?\s*$", str(tag))
    return float(m.group(1).replace(",", ".")) if m else None


def polygon_stats(latlon, to_utm):
    """Area-equivalent diameter and centroid (UTM) of a closed footprint."""
    xy = np.array([to_utm.transform(lon, lat) for lat, lon in latlon])
    x, y = xy[:, 0], xy[:, 1]
    cross = x[:-1] * y[1:] - x[1:] * y[:-1]
    area = 0.5 * cross.sum()
    if abs(area) < 1e-6:
        return None
    cx = ((x[:-1] + x[1:]) * cross).sum() / (6 * area)
    cy = ((y[:-1] + y[1:]) * cross).sum() / (6 * area)
    return 2 * np.sqrt(abs(area) / np.pi), cx, cy


def assign_clusters(xy, link_m):
    """Single-linkage terminals: tanks closer than link_m end up in one cluster."""
    if len(xy) == 1:
        return np.array([1])
    return fcluster(linkage(xy, method="single"), t=link_m, criterion="distance")


def split_clusters(df, share):
    """Hold out the south-east clusters until about `share` of the tanks are held out."""
    g = df.groupby("cluster").agg(x=("x_utm", "mean"), y=("y_utm", "mean"), n=("tank_id", "size"))
    g["score"] = (g.x - df.x_utm.median()) - (g.y - df.y_utm.median())
    held, total = [], 0
    for cid, row in g.sort_values("score", ascending=False).iterrows():
        if total >= share * len(df):
            break
        held.append(cid)
        total += row.n
    return np.where(df.cluster.isin(held), "heldout", "train")


def query_overpass(c):
    b = aoi(c)
    q = (f'[out:json][timeout:180];way["man_made"="storage_tank"]'
         f'({b["south"]},{b["west"]},{b["north"]},{b["east"]});out geom tags;')
    head = {"User-Agent": "cushing-storage-study/1.0 (academic research)", "Accept": "*/*"}
    urls = [c["registry"]["overpass_url"], "https://overpass.private.coffee/api/interpreter"]
    for url in urls:
        r = requests.post(url, data={"data": q}, headers=head, timeout=240)
        if r.ok:
            break
        print(f"overpass {url} returned {r.status_code}")
    r.raise_for_status()
    RAW.write_text(r.text, encoding="utf-8")
    log_manifest(c["registry"]["overpass_url"], q, "osm_storage_tanks_cushing", "NA", sha256(RAW), "SUCCESS")
    return r.json()


def build(raw, c):
    to_utm = Transformer.from_crs("EPSG:4326", c["utm_crs"], always_xy=True)
    to_ll = Transformer.from_crs(c["utm_crs"], "EPSG:4326", always_xy=True)
    rows = []
    for el in raw["elements"]:
        geom = el.get("geometry") or []
        if len(geom) < 4:
            continue
        s = polygon_stats([(p["lat"], p["lon"]) for p in geom], to_utm)
        if s is None:
            continue
        d_eq, cx, cy = s
        tags = el.get("tags", {})
        d_tag = parse_diameter(tags.get("diameter"))
        lon, lat = to_ll.transform(cx, cy)
        rows.append({"tank_id": f"OSM_{el['id']}", "osm_id": el["id"], "latitude": lat, "longitude": lon,
                     "x_utm": cx, "y_utm": cy, "diameter_m": d_tag or d_eq,
                     "diameter_source": "tag" if d_tag else "footprint",
                     "content": tags.get("content", ""), "operator": tags.get("operator", ""),
                     "capacity_tag": tags.get("capacity", ""), "roof_shape": tags.get("roof:shape", "")})
    df = pd.DataFrame(rows)
    df = df[df.diameter_m >= c["registry"]["min_diameter_m"]].reset_index(drop=True)
    df["cluster"] = assign_clusters(df[["x_utm", "y_utm"]].to_numpy(), c["registry"]["cluster_link_m"])
    df["split"] = split_clusters(df, c["registry"]["heldout_share"])
    df["area_weight_m2"] = np.pi * (df.diameter_m / 2) ** 2
    return df


def main():
    c = cfg()
    df = build(query_overpass(c), c)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    log_manifest("derived:osm_storage_tanks_cushing.json", "registry.build", OUT.name, "NA", sha256(OUT), "SUCCESS")
    print(len(df), "tanks,", df.cluster.nunique(), "clusters,", (df.split == "heldout").sum(), "held out")


if __name__ == "__main__":
    main()
