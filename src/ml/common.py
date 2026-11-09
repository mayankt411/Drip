"""Shared helpers: config, hashing, manifest rows, credentials from the environment."""
import csv
import hashlib
import os
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "manifest.csv"


def cfg(path="configs/ml.yaml"):
    with open(ROOT / path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def aoi(c=None):
    c = c or cfg()
    with open(ROOT / c["aoi_config"], encoding="utf-8") as f:
        return yaml.safe_load(f)["bounding_box"]


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def log_manifest(source, query, item, cloud, checksum, status, manifest=MANIFEST):
    new = not Path(manifest).exists()
    with open(manifest, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(["source_url_or_endpoint", "retrieval_time_utc", "query_params",
                        "product_id_or_series", "cloud_cover", "sha256_checksum", "status"])
        w.writerow([source, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    query, item, cloud, checksum, status])


def seed_all(seed):
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def env_credential(name):
    """Read a credential from the environment or a local .env. Never print it."""
    if os.environ.get(name):
        return os.environ[name]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[7:]
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError(f"{name} is not set; put it in your environment or a local .env (gitignored)")


def in_range(date, start, end):
    return str(start) <= str(date)[:10] <= str(end)
