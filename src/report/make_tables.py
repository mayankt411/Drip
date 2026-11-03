"""
make_tables.py - Generate formatted results tables from code outputs
"""

import os
import csv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
results_dir = os.path.join(PROJECT_ROOT, "results")

# 1. Main Metrics Table
metrics_file = os.path.join(results_dir, "metrics.csv")
table1_path = os.path.join(results_dir, "table1_main_metrics.md")
if os.path.exists(metrics_file):
    with open(metrics_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    with open(table1_path, "w", encoding="utf-8") as f:
        f.write("# Table 1: Primary Estimation Metrics (Locked Test Period)\n\n")
        f.write("| Metric | Value | Unit | Period | Notes |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for r in rows:
            f.write(f"| {r['metric']} | {r['value']} | {r['unit']} | {r['period']} | {r['evaluation_notes']} |\n")

# 2. Stratified Metrics Table
strat_file = os.path.join(results_dir, "stratified_metrics.csv")
table2_path = os.path.join(results_dir, "table2_stratified_metrics.md")
if os.path.exists(strat_file):
    with open(strat_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    with open(table2_path, "w", encoding="utf-8") as f:
        f.write("# Table 2: Error Stratified by Atmospheric Quality (Locked Test Period)\n\n")
        f.write("| Stratum Type | Stratum Level | N (Weeks) | Mean MAPE (%) | Mean MAE (MBBL) |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for r in rows:
            f.write(f"| {r['stratum_type']} | {r['stratum_level']} | {r['n_weeks']} | {r['mean_mape_percent']}% | {r['mean_mae_mbbl']} |\n")

# 3. Lagged Correlation Table
lag_file = os.path.join(results_dir, "lagged_correlation.csv")
table3_path = os.path.join(results_dir, "table3_lagged_correlation.md")
if os.path.exists(lag_file):
    with open(lag_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    with open(table3_path, "w", encoding="utf-8") as f:
        f.write("# Table 3: Lagged Correlation of First Differences\n\n")
        f.write("| Lag (Weeks) | Correlation (r) | Pair Count | Statistical Interpretation |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for r in rows:
            f.write(f"| {r['lag_weeks']} | {r['correlation_r']} | {r['n_pairs']} | {r.get('statistical_interpretation', '')} |\n")

print(f"Generated tables: {table1_path}, {table2_path}, {table3_path}")
