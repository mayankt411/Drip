"""
test_geometry.py - Unit tests for physical and geometric volume formulas
"""

import math
import pytest
from src.measure.geometry import shadow_length_to_roof_height, compute_liquid_volume, BARRELS_PER_CUBIC_METER

def test_shadow_length_to_roof_height_formula_check():
    # If solar elevation is 45 degrees, tan(45) = 1.0
    # Wall height H = 18m, shadow L = 5m -> h = 18 - 5 * 1.0 = 13m
    h = shadow_length_to_roof_height(wall_height_m=18.0, shadow_length_m=5.0, solar_elevation_deg=45.0)
    assert math.isclose(h, 13.0, rel_tol=1e-5)

def test_compute_liquid_volume_formula_check():
    # Radius r = 10m, roof_height = 11.5m, h_empty = 1.5m -> effective height = 10m
    # Area = pi * 10^2 = 100 * pi m^2
    # Volume m3 = 1000 * pi m^3
    # Volume bbl = 1000 * pi * 6.28981077
    expected_bbl = 1000.0 * math.pi * BARRELS_PER_CUBIC_METER
    calculated_bbl = compute_liquid_volume(radius_m=10.0, roof_height_m=11.5, h_empty_m=1.5)
    assert math.isclose(calculated_bbl, expected_bbl, rel_tol=1e-5)

def test_negative_elevation_raises_error():
    with pytest.raises(ValueError):
        shadow_length_to_roof_height(wall_height_m=18.0, shadow_length_m=5.0, solar_elevation_deg=-10.0)
