"""Load the EIA Cushing weekly stocks and match satellite dates to EIA weeks."""
import json
from datetime import date, timedelta

import pandas as pd

from .common import ROOT, cfg, env_credential, log_manifest, sha256


def load_eia(c=None):
    c = c or cfg()
    rows = []
    for rel in c["eia"]["files"]:
        data = json.load(open(ROOT / rel, encoding="utf-8"))["response"]["data"]
        rows += [(r["period"], float(r["value"])) for r in data if r["series"] == c["eia"]["series"]]
    df = pd.DataFrame(rows, columns=["week_end", "eia_mbbl"]).drop_duplicates("week_end")
    df["week_end"] = pd.to_datetime(df["week_end"])
    return df.sort_values("week_end").reset_index(drop=True)


def nearest_week_end(day, week_ends):
    """EIA week ending (a Friday) closest to the acquisition date."""
    day = pd.Timestamp(day).normalize()
    gaps = abs((week_ends - day).days)
    return week_ends[int(gaps.argmin())]


def assign_weeks(dates, eia):
    """Map each acquisition date to its nearest EIA week end (max 3 days away)."""
    ends = pd.DatetimeIndex(eia["week_end"])
    out = []
    for d in pd.to_datetime(dates):
        w = nearest_week_end(d, ends)
        out.append(w if abs((w - d.normalize()).days) <= 3 else pd.NaT)
    return pd.Series(out, index=range(len(out)))


def fetch_eia(start, end, c=None):
    """Optional refresh straight from the EIA v2 API (key from the environment)."""
    import requests
    c = c or cfg()
    url = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
    params = {"api_key": env_credential("EIA_API_KEY"), "frequency": "weekly",
              "data[0]": "value", "facets[series][]": c["eia"]["series"],
              "start": start, "end": end, "sort[0][column]": "period",
              "sort[0][direction]": "asc", "length": 5000}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    out = ROOT / "data" / "raw" / f"eia_cushing_weekly_{start}_{end}.json"
    out.write_text(r.text, encoding="utf-8")
    log_manifest(url, f"series={c['eia']['series']};start={start};end={end}", c["eia"]["series"], "NA", sha256(out), "SUCCESS")
    return out
