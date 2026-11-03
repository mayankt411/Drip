"""
stratify.py - Error stratification by atmospheric and observational conditions

Stratifies volume estimation errors across:
1. Cloud cover terciles / median split
2. Solar elevation terciles
3. Satellite viewing zenith angle bins
"""

import numpy as np

def stratify_by_condition(records, condition_key, split_threshold):
    """
    Splits observations into below/above threshold and evaluates stratified metrics.
    """
    low_group = [r for r in records if r[condition_key] <= split_threshold]
    high_group = [r for r in records if r[condition_key] > split_threshold]
    
    def get_mape(group):
        if not group:
            return np.nan, np.nan
        errs = [abs(r["pred_stocks"] - r["true_stocks"]) for r in group]
        mapes = [abs(r["pred_stocks"] - r["true_stocks"]) / r["true_stocks"] * 100.0 for r in group]
        return np.mean(mapes), np.mean(errs)
        
    low_mape, low_mae = get_mape(low_group)
    high_mape, high_mae = get_mape(high_group)
    
    return {
        "condition": condition_key,
        "threshold": split_threshold,
        "low_group_count": len(low_group),
        "low_group_mape": low_mape,
        "low_group_mae": low_mae,
        "high_group_count": len(high_group),
        "high_group_mape": high_mape,
        "high_group_mae": high_mae,
        "delta_mape": high_mape - low_mape
    }
