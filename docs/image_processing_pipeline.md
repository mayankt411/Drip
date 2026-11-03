# Computer Vision and Image Processing Architecture

This document details the exact pixel-level remote sensing and digital image processing pipeline implemented in `src/preprocess/image_processing.py`.

---

## 1. Pixel-Level Pipeline Stages

```
Sentinel-2 L2A Granules (B02, B03, B04, B08, SCL)
                         │
                         ▼
           [ Stage 1: Radiometric Masking ]
   • Scene Classification Layer (SCL) Filtering
   • Cloud, Cirrus & Cloud Shadow Pixel Rejection
                         │
                         ▼
        [ Stage 2: Tank ROI Cropping & Geo-Transform ]
   • Bounding Box extraction around center (x0, y0)
   • Metric Ground Sample Distance: GSD = 10.0m
                         │
                         ▼
     [ Stage 3: Multispectral Contrast Enhancement ]
   • Near-Infrared / Red Band Ratio & Shadow Index
   • Bimodal histogram contrast normalization
                         │
                         ▼
       [ Stage 4: Optimal Otsu Thresholding ]
   • Maximizes between-class variance:
       σ_b²(t) = w_0(t) * w_1(t) * [μ_0(t) - μ_1(t)]²
   • Isolates low-reflectance interior shadow pixels
                         │
                         ▼
     [ Stage 5: Mathematical Morphology (Opening) ]
   • 3x3 Cross-kernel Erosion: removes salt-and-pepper noise
   • 3x3 Cross-kernel Dilation: closes internal voids
   • Isolates contiguous crescent shadow polygon
                         │
                         ▼
    [ Stage 6: Directional Radon / Ray Profiling ]
   • Constrains ray direction along solar azimuth:
       θ_shadow = (θ_sun + 180°) mod 360°
   • Sub-pixel edge localization along radial profile
                         │
                         ▼
          Metric Shadow Length (L_meters)
```

---

## 2. Key Image Processing Algorithms Implemented

### A. Otsu Global Thresholding (`otsu_threshold`)
- Calculates the zeroth and first-order cumulative moments of the ROI pixel histogram:
  $$w_0(t) = \sum_{i=0}^t p(i), \quad w_1(t) = 1 - w_0(t)$$
  $$\mu_0(t) = \sum_{i=0}^t \frac{i \cdot p(i)}{w_0(t)}, \quad \mu_1(t) = \sum_{i=t+1}^{L-1} \frac{i \cdot p(i)}{w_1(t)}$$
- Automatically finds the optimal cut point separating the dark interior wall shadow from the higher-albedo painted pontoon roof.

### B. Morphological Cleaning (`morphological_clean`)
- Applies structural morphological opening:
  $$A \circ B = (A \ominus B) \oplus B$$
- Strips off false shadow speckles caused by rust, standing rainwater patches, or pontoon ladder hardware on the roof surface.

### C. Directional Ray-Casting Profiler (`extract_shadow_profile`)
- Rather than calculating generic bounding boxes, the algorithm casts a discrete ray from the tank wall inward along the exact optical illumination vector:
  $$\vec{r}(s) = \left( x_c + s \cdot \sin(\theta_{\text{shadow}}), \; y_c - s \cdot \cos(\theta_{\text{shadow}}) \right)$$
- Measures the precise metric distance from the outer tank perimeter to the shadow boundary.

---

## 3. Unit Test Verification
The image processing suite is verified in `tests/test_image_processing.py`:
- `test_otsu_thresholding_bimodal`: Verified on synthetic bimodal distributions.
- `test_morphological_clean_removes_isolated_pixels`: Verifies 100% elimination of 1-pixel noise artifacts.
- `test_directional_ray_casting`: Verifies sub-pixel radial profiling along solar azimuth rays.
