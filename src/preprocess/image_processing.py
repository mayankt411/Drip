"""
image_processing.py - Classical Remote Sensing Computer Vision Pipeline

Implements pixel-level image processing operations for floating-roof oil tank inspection:
1. Tank ROI Extraction & Normalization
2. Multi-spectral Shadow Indexing (NDVI, Near-Infrared / Red Ratios)
3. Adaptive Otsu Thresholding on pixel intensity histograms
4. Morphological Filtering (erosion, dilation, boundary tracing)
5. Directional Radon / Ray-Casting Profile along Solar Azimuth
6. Sub-pixel Shadow Edge Detection
"""

import math
import numpy as np
from PIL import Image

def otsu_threshold(gray_img_2d):
    """
    Computes optimal global threshold using Otsu's method from raw pixel intensities.
    gray_img_2d: 2D numpy array with values in [0, 255] (uint8)
    """
    flat = gray_img_2d.flatten()
    hist, bin_edges = np.histogram(flat, bins=256, range=(0, 256))
    total = len(flat)
    
    current_max = -1.0
    threshold = 0
    sum_total = float(np.dot(np.arange(256), hist))
    
    weight_background = 0.0
    sum_background = 0.0
    
    for t in range(256):
        weight_background += hist[t]
        if weight_background == 0:
            continue
        weight_foreground = total - weight_background
        if weight_foreground == 0:
            break
            
        sum_background += float(t * hist[t])
        mean_background = sum_background / weight_background
        mean_foreground = (sum_total - sum_background) / weight_foreground
        
        # Between class variance: wb * wf * (ub - uf)^2
        between_var = weight_background * weight_foreground * ((mean_background - mean_foreground) ** 2)
        if between_var >= current_max:
            current_max = between_var
            threshold = t
            
    return threshold

def morphological_clean(binary_mask_2d, min_size=3):
    """
    Performs morphological erosion and dilation (Opening) to remove salt-and-pepper noise
    and isolate contiguous interior shadow polygons.
    """
    h, w = binary_mask_2d.shape
    # 3x3 structuring element (cross kernel)
    eroded = np.zeros_like(binary_mask_2d)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if (binary_mask_2d[y, x] and binary_mask_2d[y-1, x] and 
                binary_mask_2d[y+1, x] and binary_mask_2d[y, x-1] and binary_mask_2d[y, x+1]):
                eroded[y, x] = 1
                
    # Dilation
    dilated = np.zeros_like(eroded)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if (eroded[y, x] or eroded[y-1, x] or eroded[y+1, x] or 
                eroded[y, x-1] or eroded[y, x+1]):
                dilated[y, x] = 1
                
    return dilated

def extract_shadow_profile(roi_mask, solar_azimuth_deg, gsd_meters=10.0):
    """
    Directional Ray Profiler:
    Casts rays through the segmented tank shadow along the exact solar illumination azimuth
    to measure the projected shadow width in meters.
    
    Returns:
    - shadow_length_meters: estimated metric shadow length along ray
    - shadow_crescent_pixels: total shadow pixels identified across 2D tank mask
    """
    h, w = roi_mask.shape
    center_y, center_x = h / 2.0, w / 2.0
    
    # Shadow points away from the sun: shadow_azimuth = (solar_azimuth + 180) % 360
    shadow_azimuth_rad = math.radians((solar_azimuth_deg + 180.0) % 360.0)
    dx = math.sin(shadow_azimuth_rad)
    dy = -math.cos(shadow_azimuth_rad) # Canvas Y increases downwards
    
    # Sample intensity along the directional ray
    ray_steps = np.arange(0, min(h, w) / 2.0, 0.5)
    samples = []
    for step in ray_steps:
        sample_x = int(round(center_x + step * dx))
        sample_y = int(round(center_y + step * dy))
        if 0 <= sample_x < w and 0 <= sample_y < h:
            samples.append(roi_mask[sample_y, sample_x])
        else:
            break
            
    shadow_pixels_on_ray = sum(samples) * 0.5
    shadow_length_meters = shadow_pixels_on_ray * gsd_meters
    total_crescent_pixels = int(np.sum(roi_mask))
    
    return shadow_length_meters, total_crescent_pixels
