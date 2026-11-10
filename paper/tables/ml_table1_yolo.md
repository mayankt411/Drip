**Table 1**

*Tank Detection on Held-Out Terminals (Test Dates 2023–2024)*

| Metric | Value | Pre-specified threshold |
|:--|--:|--:|
| Precision | 0.900 | ≥ 0.80 |
| Recall | 0.903 | n/a |
| mAP@50 | 0.876 | ≥ 0.85 |
| mAP@50–95 | 0.453 | n/a |
| Test images / labelled tanks | 620 / 18047 | n/a |

*Note.* Precision and recall are at the deployment confidence threshold; mAP uses all thresholds. Labels come from OpenStreetMap footprints, so they are noisy; detections of tanks missing from OSM count as false positives.
