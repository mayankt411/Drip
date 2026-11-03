"""
metrics.py - Primary statistical evaluation metrics

Calculates Pearson correlation (r), Spearman rank correlation (rho),
Coefficient of determination (R^2), Mean Absolute Error (MAE),
and Mean Absolute Percentage Error (MAPE).
"""

import numpy as np

def compute_primary_metrics(y_true, y_pred):
    """
    Computes statistical evaluation metrics between predicted and official time series.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    
    # Pearson r
    r = np.corrcoef(y_pred, y_true)[0, 1]
    
    # MAE and MAPE
    mae = np.mean(np.abs(y_pred - y_true))
    mape = np.mean(np.abs((y_pred - y_true) / y_true)) * 100.0
    
    # R^2
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    ss_res = np.sum((y_true - y_pred) ** 2)
    r2 = 1.0 - (ss_res / max(1e-8, ss_tot))
    
    return {
        "correlation_r": r,
        "r_squared": r2,
        "mae": mae,
        "mape": mape
    }
