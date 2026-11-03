"""
test_image_processing.py - Unit test suite for computer vision algorithms
"""

import numpy as np
from src.preprocess.image_processing import otsu_threshold, morphological_clean, extract_shadow_profile

def test_otsu_thresholding_bimodal():
    # Construct synthetic bimodal test image (shadow vs brightly lit roof)
    img = np.zeros((20, 20), dtype=np.uint8)
    img[:10, :] = 40  # Shadow class (dark)
    img[10:, :] = 180 # Lit roof class (bright)
    
    thresh = otsu_threshold(img)
    # The optimal separation between 40 and 180 should lie between 40 and 180
    assert 40 < thresh < 180

def test_morphological_clean_removes_isolated_pixels():
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[2, 2] = 1 # Isolated salt noise
    mask[5:8, 5:8] = 1 # Solid 3x3 block
    
    cleaned = morphological_clean(mask)
    assert cleaned[2, 2] == 0 # Salt noise removed
    assert cleaned[6, 6] == 1 # Central core preserved

def test_directional_ray_casting():
    # 20x20 mask with a 4-pixel shadow along the horizontal right direction
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[10, 10:14] = 1 # Horizontal segment
    
    # Sun azimuth 270 (West) -> shadow points East (90 deg)
    length_m, count = extract_shadow_profile(mask, solar_azimuth_deg=270.0, gsd_meters=10.0)
    assert count >= 4
    assert length_m > 0
