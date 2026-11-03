"""
reproduce_test.py - Clean execution test verifying bitwise reproducibility of results
"""

import os
import sys
import hashlib
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
results_dir = os.path.join(PROJECT_ROOT, "results")
metrics_csv = os.path.join(results_dir, "metrics.csv")

# Record checksum of current metrics
with open(metrics_csv, "rb") as f:
    orig_hash = hashlib.sha256(f.read()).hexdigest()

print(f"Initial metrics.csv SHA-256: {orig_hash}")

# Re-run pipeline script
python_exe = r"C:\Program Files\KiCad\10.0\bin\python.exe"
proc = subprocess.run([python_exe, "src/evaluate/run_phase7_evaluation.py"], cwd=PROJECT_ROOT, capture_output=True, text=True)
if proc.returncode != 0:
    print("Error during re-execution:", proc.stderr)
    sys.exit(1)

with open(metrics_csv, "rb") as f:
    new_hash = hashlib.sha256(f.read()).hexdigest()

print(f"Re-run metrics.csv SHA-256:  {new_hash}")

if orig_hash == new_hash:
    print("SUCCESS: metrics.csv reproduced bitwise identically.")
else:
    print("MISMATCH: Checksums differ.")
    sys.exit(1)
