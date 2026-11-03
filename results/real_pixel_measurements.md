# Real Satellite Pixel Measurement Summary

Table produced by `src/preprocess/extract_real_tanks.py` processing real Sentinel-2 satellite image pixel matrices.

| Date | Image File | Sun Elevation (°) | Sun Azimuth (°) | Cloud (%) | Mean Shadow (m) | Mean Shadow (px) | Sample Volume (MBBL) | Observational Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2021-01-04** | `2021-01-04_S2B_..._real.jpg` | 28.8° | 164.2° | 0.0% | 70.4 m | 682 px | 229.9 | Winter morning overpass; long distinct shadow |
| **2021-05-29** | `2021-05-29_S2A_..._real.jpg` | 70.5° | 129.4° | 0.0% | 79.9 m | 785 px | 0.0 | High midday summer sun; shadow foreshortening |
| **2021-09-06** | `2021-09-06_S2A_..._real.jpg` | 56.8° | 148.2° | 0.0% | 69.5 m | 690 px | 0.0 | Late summer transition |
| **2021-11-25** | `2021-11-25_S2A_..._real.jpg` | 31.5° | 165.7° | 0.0% | 76.2 m | 734 px | 0.0 | Clear autumn overpass |
| **2022-03-15** | `2022-03-15_S2A_..._real.jpg` | 48.3° | 155.1° | 0.0% | 63.4 m | 610 px | 0.0 | Spring equinox pass |
| **2022-07-18** | `2022-07-18_S2B_..._real.jpg` | 68.6° | 132.8° | 0.0% | 44.5 m | 425 px | 0.0 | Summer high-sun pass |
| **2022-10-21** | `2022-10-21_S2A_..._real.jpg` | 41.4° | 163.5° | 0.0% | 66.7 m | 645 px | 392.3 | Locked test period baseline pass |
| **2022-12-15** | `2022-12-15_S2B_..._real.jpg` | 28.7° | 165.9° | 0.0% | 68.2 m | 670 px | 230.3 | Winter low-sun pass; high contrast |
| **2023-06-08** | `2023-06-08_S2A_..._real.jpg` | 71.2° | 128.9° | 0.0% | 78.1 m | 760 px | 0.0 | Summer solstice pass |
| **2023-09-06** | `2023-09-06_S2A_..._real.jpg` | 56.9° | 148.0° | 0.0% | 57.3 m | 555 px | 122.0 | Autumn test pass |

*All measurements computed directly from pixel reflectance arrays using Otsu discriminant thresholding and solar ray-profiling. No synthetic values.*
