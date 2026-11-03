"""
geometry.py - Shadow Geometry and Tank Volume Conversions

Implements the physical principles detailed in Part 3 of the study:
d = (H - h) / tan(alpha)
h = H - L * tan(alpha)
V = pi * r^2 * (h - h_empty)
"""

import math

# Standard conversion: 1 cubic meter = 6.28981077 U.S. petroleum barrels (ASTM D1250 / API standard)
BARRELS_PER_CUBIC_METER = 6.28981077

def shadow_length_to_roof_height(wall_height_m, shadow_length_m, solar_elevation_deg):
    """
    Computes floating-roof height above tank floor from measured shadow length.
    
    h = H - L * tan(alpha)
    where:
    H = wall height (m)
    L = shadow length along solar azimuth (m)
    alpha = solar elevation angle (degrees)
    """
    if solar_elevation_deg <= 0 or solar_elevation_deg >= 90:
        raise ValueError(f"Solar elevation must be in (0, 90) degrees, got {solar_elevation_deg}")
    
    alpha_rad = math.radians(solar_elevation_deg)
    h = wall_height_m - shadow_length_m * math.tan(alpha_rad)
    return max(0.0, min(wall_height_m, h))

def compute_liquid_volume(radius_m, roof_height_m, h_empty_m=1.5):
    """
    Computes crude oil liquid volume in barrels.
    
    V_m3 = pi * r^2 * (h - h_empty)
    V_bbl = V_m3 * 6.28981077
    """
    effective_height = max(0.0, roof_height_m - h_empty_m)
    volume_m3 = math.pi * (radius_m ** 2) * effective_height
    volume_bbl = volume_m3 * BARRELS_PER_CUBIC_METER
    return volume_bbl
