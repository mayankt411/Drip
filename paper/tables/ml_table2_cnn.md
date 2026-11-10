**Table 2**

*Hub-Level CNN Training and Per-Tank Validation Status*

| Item | Value |
|:--|--:|
| Training dates (fit / inner validation) | 47 / 12 |
| Ensemble seeds | 5 |
| Best inner-validation MSE, standardized (mean over seeds) | 0.049 |
| Per-tank fill MAE, RMSE, R² (H2) | not testable |

*Note.* No per-tank fill-level labels exist, so the network is trained against hub-level EIA stocks only and H2 is not tested. MSE is on z-scored EIA stocks.
