"""
analyze_acquisition.py - Summarize acquisition counts, weekly distribution, and exclusions
"""

import json
import os
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 1. EIA Data
eia_path = os.path.join(PROJECT_ROOT, "data", "raw", "eia_cushing_weekly_2021_2023.json")
with open(eia_path, "r", encoding="utf-8") as f:
    eia_data = json.load(f)
eia_records = eia_data.get("response", {}).get("data", [])

# 2. S2 Data
s2_path = os.path.join(PROJECT_ROOT, "data", "raw", "s2_cushing_stac_2021_2023.json")
with open(s2_path, "r", encoding="utf-8") as f:
    s2_data = json.load(f)
s2_features = s2_data.get("features", [])

usable_s2 = [f for f in s2_features if f["properties"].get("eo:cloud_cover", 100.0) <= 40.0]
excluded_s2 = [f for f in s2_features if f["properties"].get("eo:cloud_cover", 100.0) > 40.0]

# Group by ISO calendar week (YYYY-WW)
weekly_s2 = defaultdict(list)
for f in usable_s2:
    dt_str = f["properties"]["datetime"][:10]
    dt = datetime.strptime(dt_str, "%Y-%m-%d")
    iso_week = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
    weekly_s2[iso_week].append(f)

weekly_eia = {}
for r in eia_records:
    dt = datetime.strptime(r["period"], "%Y-%m-%d")
    iso_week = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
    weekly_eia[iso_week] = r

all_weeks = sorted(list(weekly_eia.keys()))
weeks_with_usable_s2 = [w for w in all_weeks if len(weekly_s2[w]) > 0]
weeks_without_s2 = [w for w in all_weeks if len(weekly_s2[w]) == 0]

print("=== Phase 1 Acquisition Summary ===")
print(f"Total Official EIA Weekly Observations (2021-2023): {len(eia_records)}")
print(f"Total Sentinel-2 L2A Granules Retrieved: {len(s2_features)}")
print(f"Usable S2 Granules (Cloud Cover <= 40%): {len(usable_s2)}")
print(f"Excluded S2 Granules (Cloud Cover > 40%): {len(excluded_s2)}")
print(f"Total Study Calendar Weeks: {len(all_weeks)}")
print(f"Calendar Weeks with >= 1 Usable S2 Overpass: {len(weeks_with_usable_s2)} ({len(weeks_with_usable_s2)/len(all_weeks)*100:.1f}%)")
print(f"Calendar Weeks Completely Blocked by Clouds: {len(weeks_without_s2)} ({len(weeks_without_s2)/len(all_weeks)*100:.1f}%)")
