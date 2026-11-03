"""
volume.py - Conversion of measured roof height to liquid storage volume

Calculates individual tank crude volumes and hub aggregations
using API/ASTM MPMS Chapter 11.1 standard conversion factor.
"""

import math

BARRELS_PER_M3 = 6.28981077

def tank_volume_barrels(radius_m, roof_height_m, h_empty_m=1.5):
    """
    Computes crude oil volume in standard 42-gallon barrels.
    V = pi * r^2 * max(0, h - h_empty) * 6.28981
    """
    eff_height = max(0.0, roof_height_m - h_empty_m)
    vol_m3 = math.pi * (radius_m ** 2) * eff_height
    return vol_m3 * BARRELS_PER_M3

def aggregate_hub_volume_mbbl(tank_volumes_bbl):
    """
    Aggregates list of tank volumes into thousand barrels (MBBL).
    """
    return sum(tank_volumes_bbl) / 1000.0
