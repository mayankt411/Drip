"""Hash trained weights and result files into data/manifest.csv."""
import sys
from pathlib import Path

from .common import ROOT, log_manifest, sha256


def main(patterns):
    for pat in patterns:
        for p in sorted(ROOT.glob(pat)):
            if p.is_file():
                log_manifest("local:" + str(p.relative_to(ROOT)), "provenance", p.name, "NA", sha256(p), "SUCCESS")
                print(p.relative_to(ROOT))


if __name__ == "__main__":
    main(sys.argv[1:] or ["models/**/*.pt", "results/ml_*.csv", "results/ml_*.json", "data/tanks/cushing_full_registry.csv"])
