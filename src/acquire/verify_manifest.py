"""Check data/manifest.csv checksums against the files in this checkout.

Text files are also tried with CRLF line endings, because some manifest
rows were hashed on a Windows working copy. Rasters are gitignored, so
they are reported as not present unless you download them.
"""
import csv
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEX = re.compile(r"^[0-9a-f]{64}$")


def digests(path):
    raw = path.read_bytes()
    found = {hashlib.sha256(raw).hexdigest()}
    if path.suffix in (".json", ".csv", ".md", ".txt"):
        found.add(hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest())
    return found


def main():
    counts = {"match": 0, "mismatch": 0, "absent": 0}
    with open(ROOT / "data/manifest.csv", newline="", encoding="utf-8") as f:
        for row in list(csv.reader(f))[1:]:
            sha = next((c for c in row if HEX.match(c)), None)
            path = ROOT / row[0]
            if sha is None or not row[0].startswith("data/") and not row[0].startswith("results/"):
                continue
            if not path.exists():
                counts["absent"] += 1
            elif sha in digests(path):
                counts["match"] += 1
            else:
                counts["mismatch"] += 1
                print("MISMATCH", row[0])
    print(counts)


if __name__ == "__main__":
    main()
