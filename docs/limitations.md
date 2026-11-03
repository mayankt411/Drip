# Limitations of the Study

1. **Spatial Resolution Constraint (10m Native Sentinel-2 Grid):**
   A standard 80-meter diameter floating-roof tank occupies only ~8 pixels across in Sentinel-2 bands B02, B03, B04, and B08. An internal shadow length of 3–5 meters represents less than half a pixel, making shadow boundary localization subject to substantial discretization uncertainty unless sub-pixel interpolation or high solar zenith angles are present.

2. **Hub Registry vs. Official EIA Scope Mismatch:**
   EIA series `WCRSTUS1` aggregates total commercial crude storage across all operating terminals in the Cushing hub (~70–90 million barrels nominal capacity). The satellite registry observes an identified subset of floating-roof tanks. Satellite totals represent a sample coverage fraction, not universal hub inventory, and cannot be rescaled without calibrated development models.

3. **Fixed-Roof & Underground Tank Invisibility:**
   Fixed-roof tanks do not exhibit variable interior shadows as liquid levels fluctuate. Crude stored in fixed-roof vessels or underground manifold piping remains unobservable via optical shadow geometry.

4. **Cloud Occlusion & Temporal Gaps:**
   Persistent cloud cover in Oklahoma (particularly during spring convective weather) causes weeks with missing or corrupted observations, inducing survivorship bias towards clear-sky conditions.
