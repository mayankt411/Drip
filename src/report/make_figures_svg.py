"""
make_figures_svg.py - Generate research figures as standalone SVG vector graphics
"""

import os
import csv
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
results_dir = os.path.join(PROJECT_ROOT, "results")
weekly_csv = os.path.join(results_dir, "weekly_estimates.csv")

dates_dev, eia_dev, sat_dev = [], [], []
dates_test, eia_test, sat_test = [], [], []

with open(weekly_csv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r["status"] == "VALID_OBSERVATION":
            d = datetime.strptime(r["period"], "%Y-%m-%d")
            eia = float(r["eia_stocks_mbbl"])
            sat_raw = float(r["raw_sample_stocks_mbbl"])
            sat_cal = float(r["calibrated_stocks_mbbl"])
            if r["split_group"] == "DEVELOPMENT":
                dates_dev.append(d)
                eia_dev.append(eia)
                sat_dev.append(sat_cal)
            else:
                dates_test.append(d)
                eia_test.append(eia)
                sat_test.append(sat_cal)

sat_dev_cal = sat_dev
sat_test_cal = sat_test

# Render Figure 1: Time Series as SVG
all_dates = dates_dev + dates_test
min_d, max_d = min(all_dates), max(all_dates)
all_vals = eia_dev + eia_test + sat_dev_cal + sat_test_cal
min_v, max_v = min(all_vals) * 0.95, max(all_vals) * 1.05

width, height = 900, 450
pad_l, pad_r, pad_t, pad_b = 70, 40, 50, 50

def get_x(d):
    frac = (d - min_d).total_seconds() / (max_d - min_d).total_seconds()
    return pad_l + frac * (width - pad_l - pad_r)

def get_y(v):
    frac = (v - min_v) / (max_v - min_v)
    return height - pad_b - frac * (height - pad_t - pad_b)

svg_lines = []
svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">')
svg_lines.append(f'<rect width="{width}" height="{height}" fill="#ffffff"/>')

# Grid lines
for y_val in [20000, 30000, 40000, 50000, 60000]:
    if min_v <= y_val <= max_v:
        y_px = get_y(y_val)
        svg_lines.append(f'<line x1="{pad_l}" y1="{y_px}" x2="{width-pad_r}" y2="{y_px}" stroke="#e2e8f0" stroke-dasharray="4"/>')
        svg_lines.append(f'<text x="{pad_l-10}" y="{y_px+4}" font-family="sans-serif" font-size="10" text-anchor="end" fill="#64748b">{y_val//1000}M</text>')

# Split line
split_x = get_x(datetime.strptime("2022-10-18", "%Y-%m-%d"))
svg_lines.append(f'<line x1="{split_x}" y1="{pad_t}" x2="{split_x}" y2="{height-pad_b}" stroke="#94a3b8" stroke-width="2" stroke-dasharray="5"/>')
svg_lines.append(f'<text x="{split_x+5}" y="{pad_t+20}" font-family="sans-serif" font-size="11" fill="#64748b">Locked Test Split</text>')

# Plot EIA lines
eia_pts_dev = " ".join([f"{get_x(d):.1f},{get_y(v):.1f}" for d, v in zip(dates_dev, eia_dev)])
eia_pts_test = " ".join([f"{get_x(d):.1f},{get_y(v):.1f}" for d, v in zip(dates_test, eia_test)])
svg_lines.append(f'<polyline points="{eia_pts_dev}" fill="none" stroke="#0f172a" stroke-width="2"/>')
svg_lines.append(f'<polyline points="{eia_pts_test}" fill="none" stroke="#0f172a" stroke-width="2" stroke-dasharray="4"/>')

# Plot Sat Points
for d, v in zip(dates_dev, sat_dev_cal):
    svg_lines.append(f'<circle cx="{get_x(d):.1f}" cy="{get_y(v):.1f}" r="3" fill="#2563eb" opacity="0.8"/>')

for d, v in zip(dates_test, sat_test_cal):
    svg_lines.append(f'<circle cx="{get_x(d):.1f}" cy="{get_y(v):.1f}" r="3.5" fill="#dc2626" opacity="0.9"/>')

# Title & Legend
svg_lines.append(f'<text x="{width/2}" y="30" font-family="sans-serif" font-size="14" font-weight="bold" text-anchor="middle" fill="#0f172a">Sentinel-2 Satellite Estimates vs. Official EIA Weekly Cushing Stocks (2021–2023)</text>')
svg_lines.append(f'<circle cx="{width-240}" cy="20" r="3.5" fill="#2563eb"/><text x="{width-230}" y="24" font-family="sans-serif" font-size="10" fill="#334155">Dev Satellite</text>')
svg_lines.append(f'<circle cx="{width-150}" cy="20" r="3.5" fill="#dc2626"/><text x="{width-140}" y="24" font-family="sans-serif" font-size="10" fill="#334155">Test Satellite</text>')
svg_lines.append(f'<line x1="{width-70}" y1="20" x2="{width-45}" y2="20" stroke="#0f172a" stroke-width="2"/><text x="{width-40}" y="24" font-family="sans-serif" font-size="10" fill="#334155">EIA</text>')

svg_lines.append('</svg>')

fig1_path = os.path.join(results_dir, "figure1_time_series_validation.svg")
with open(fig1_path, "w", encoding="utf-8") as f:
    f.write("\n".join(svg_lines))

print(f"Generated vector graphic: {fig1_path}")
