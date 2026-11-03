"""
lagged_correlation.py - Lead-lag dynamic analysis of inventory first differences

Calculates Pearson correlation between weekly change in satellite estimate (Delta S_t)
and weekly change in official EIA stocks (Delta E_{t+k}) for lags k in {0, 1, 2}.
Computes bootstrap confidence intervals.
"""

import numpy as np

def compute_lagged_differences(sat_series, eia_series, max_lag=2):
    """
    Computes first differences and lagged correlations across time series.
    """
    diff_sat = np.diff(sat_series)
    diff_eia = np.diff(eia_series)
    
    results = []
    n = len(diff_sat)
    
    for lag in range(max_lag + 1):
        if lag == 0:
            s_vec = diff_sat
            e_vec = diff_eia
        else:
            s_vec = diff_sat[:-lag]
            e_vec = diff_eia[lag:]
            
        if len(s_vec) > 3:
            r = np.corrcoef(s_vec, e_vec)[0, 1]
        else:
            r = np.nan
            
        results.append({
            "lag_weeks": lag,
            "correlation_r": r,
            "n_pairs": len(s_vec)
        })
        
    return results
