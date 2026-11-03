"""
make_figures.py - Generate research figures from results/ outputs
"""

import os
import csv
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
results_dir = os.path.join(PROJECT_ROOT, "results")
weekly_csv = os.path.join(results_dir, "weekly_estimates.csv")

dates_dev = []
eia_dev = []
sat_dev = []

dates_test = []
eia_test = []
sat_test = []

with open(weekly_csv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r["status"] == "VALID_OBSERVATION":
            d = datetime.strptime(r["period"], "%Y-%m-%d")
            eia = float(r["eia_stocks_mbbl"])
            sat = float(r["satellite_stocks_mbbl"])
            if r["split_group"] == "DEVELOPMENT":
                dates_dev.append(d)
                eia_dev.append(eia)
                sat_dev.append(sat)
            else:
                dates_test.append(d)
                eia_test.append(eia)
                sat_test.append(sat)

# Rescale sat for visual alignment using dev coverage scale
cov_scale = (sum(sat_dev) / len(sat_dev)) / (sum(eia_dev) / len(eia_dev))
sat_dev_cal = [s / cov_scale for s in sat_dev]
sat_test_cal = [s / cov_scale for s in sat_test]

# Figure 1: Time Series Validation
plt.figure(figsize=(12, 6))
plt.plot(dates_dev, eia_dev, label="Official EIA Stocks (Development)", color="black", lw=1.5)
plt.scatter(dates_dev, sat_dev_cal, label="Sentinel-2 Estimate (Development)", color="steelblue", s=25, alpha=0.8)

plt.plot(dates_test, eia_test, label="Official EIA Stocks (Locked Test)", color="black", linestyle="--", lw=1.5)
plt.scatter(dates_test, sat_test_cal, label="Sentinel-2 Estimate (Locked Test)", color="crimson", s=30, alpha=0.9)

plt.axvline(datetime.strptime("2022-10-18", "%Y-%m-%d"), color="gray", linestyle=":", lw=2, label="Locked Split Boundary")
plt.title("Sentinel-2 Satellite Crude Oil Estimation vs. Official EIA Weekly Cushing Stocks (2021–2023)", fontsize=13)
plt.xlabel("Date", fontsize=11)
plt.ylabel("Crude Oil Stocks (Thousand Barrels)", fontsize=11)
plt.legend(loc="upper right", frameon=True)
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()

fig1_path = os.path.join(results_dir, "figure1_time_series_validation.png")
plt.savefig(fig1_path, dpi=300)
plt.close()

# Figure 2: Scatter Plot on Test Period
plt.figure(figsize=(7, 7))
plt.scatter(eia_test, sat_test_cal, color="crimson", alpha=0.7, edgecolors="k", s=45, label="Test Weeks (N=44)")
lims = [min(eia_test) - 2000, max(eia_test) + 2000]
plt.plot(lims, lims, "k--", alpha=0.7, label="1:1 Parity")
plt.xlim(lims)
plt.ylim(lims)
plt.title("Locked Test Period: Satellite Estimate vs. EIA Stocks", fontsize=12)
plt.xlabel("Official EIA Cushing Stocks (Thousand Barrels)", fontsize=11)
plt.ylabel("Calibrated Satellite Estimate (Thousand Barrels)", fontsize=11)
plt.legend()
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()

fig2_path = os.path.join(results_dir, "figure2_test_scatter.png")
plt.savefig(fig2_path, dpi=300)
plt.close()

print(f"Generated figures: {fig1_path}, {fig2_path}")
