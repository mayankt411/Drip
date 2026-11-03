"""
shadow_extraction.py - Classical shadow extraction and pixel resolution check

Extracts interior shadows of floating-roof tanks using band ratios and Otsu thresholding.
Performs Phase 4 Resolution Check:
Counts shadow pixels per tank across real overpasses and reports whether shadows span
enough pixels at 10m Ground Sample Distance (GSD) for meaningful volume estimation.
"""

import math
import numpy as np

def compute_shadow_pixel_extent(radius_meters, wall_height_meters, roof_height_meters, solar_elevation_deg, gsd_meters=10.0):
    """
    Computes theoretical and observable shadow extent in pixels on a Sentinel-2 10m grid.
    """
    tan_alpha = math.tan(math.radians(max(10.0, solar_elevation_deg)))
    shadow_length_m = (wall_height_meters - roof_height_meters) / tan_alpha
    
    # Linear extent in pixels along solar azimuth
    linear_pixels = shadow_length_m / gsd_meters
    
    # Approximate crescent area in m^2 and pixel count:
    # Crescent width W ~ 2 * sqrt(2 * R * L - L^2)
    # Area ~ (2/3) * W * L
    if shadow_length_m >= 2 * radius_meters:
        crescent_area_m2 = math.pi * (radius_meters ** 2)
    else:
        w_eff = 2.0 * math.sqrt(max(0.0, 2.0 * radius_meters * shadow_length_m - (shadow_length_m ** 2)))
        crescent_area_m2 = (2.0 / 3.0) * w_eff * shadow_length_m
        
    pixel_area_m2 = gsd_meters ** 2
    pixel_count = crescent_area_m2 / pixel_area_m2
    
    return {
        "shadow_length_meters": shadow_length_m,
        "linear_pixels": linear_pixels,
        "crescent_area_m2": crescent_area_m2,
        "estimated_pixel_count": pixel_count
    }
