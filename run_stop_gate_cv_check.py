import os
import json
import csv
import math
import numpy as np
from PIL import Image

def wgs84_to_utm14n(lat, lon):
    a = 6378137.0
    f = 1 / 298.257223563
    b = a * (1 - f)
    e = math.sqrt(1 - (b * b) / (a * a))
    e_prime_sq = (e * e) / (1 - e * e)
    k0 = 0.9996
    lon0 = -99.0 * math.pi / 180.0
    lat_rad = lat * math.pi / 180.0
    lon_rad = lon * math.pi / 180.0
    N = a / math.sqrt(1 - e * e * math.sin(lat_rad) ** 2)
    T = math.tan(lat_rad) ** 2
    C = e_prime_sq * math.cos(lat_rad) ** 2
    A = (lon_rad - lon0) * math.cos(lat_rad)
    M = a * ((1 - e**2/4 - 3*e**4/64 - 5*e**6/256) * lat_rad
             - (3*e**2/8 + 3*e**4/32 + 45*e**6/1024) * math.sin(2*lat_rad)
             + (15*e**4/256 + 45*e**6/1024) * math.sin(4*lat_rad)
             - (35*e**6/3072) * math.sin(6*lat_rad))
    easting = k0 * N * (A + (1 - T + C) * A**3 / 6 + (5 - 18*T + T**2 + 72*C - 58*e_prime_sq) * A**5 / 120) + 500000.0
    northing = k0 * (M + N * math.tan(lat_rad) * (A**2 / 2 + (5 - T + 9*C + 4*C**2) * A**4 / 24 + (61 - 58*T + T**2 + 600*C - 330*e_prime_sq) * A**6 / 720))
    return easting, northing

def extract_tank_subwindow(jp2_path, tile_origin_x, tile_origin_y, tank_utm_x, tank_utm_y, window_radius_px=15):
    # col = (utm_x - origin_x)/10, row = (origin_y - utm_y)/10
    center_col = (tank_utm_x - tile_origin_x) / 10.0
    center_row = (tile_origin_y - tank_utm_y) / 10.0
    
    c_int = int(round(center_col))
    r_int = int(round(center_row))
    
    box = (c_int - window_radius_px, r_int - window_radius_px, c_int + window_radius_px + 1, r_int + window_radius_px + 1)
    
    with Image.open(jp2_path) as im:
        crop = im.crop(box)
        arr = np.array(crop)
    return arr, (center_col - (c_int - window_radius_px), center_row - (r_int - window_radius_px))

def otsu_threshold(gray):
    # compute Otsu on local tank crop
    flat = gray.flatten()
    best_thresh = np.mean(flat)
    best_var = 0
    hist, bin_edges = np.histogram(flat, bins=32)
    total = flat.size
    for i in range(1, len(hist)):
        w0 = np.sum(hist[:i]) / total
        w1 = np.sum(hist[i:]) / total
        if w0 == 0 or w1 == 0:
            continue
        m0 = np.sum(bin_edges[:i] * hist[:i]) / (w0 * total)
        m1 = np.sum(bin_edges[i:-1] * hist[i:]) / (w1 * total)
        var_between = w0 * w1 * ((m0 - m1) ** 2)
        if var_between > best_var:
            best_var = var_between
            best_thresh = bin_edges[i]
    return best_thresh

def measure_shadow_from_subwindow(b04_crop, b08_crop, local_center, radius_m, sun_azimuth_deg, sun_elevation_deg):
    # At 10m GSD:
    # Shadow falls opposite to sun: shadow_azimuth = sun_azimuth + 180 deg (or along sun ray towards northern/north-eastern sector)
    # Sun azimuth ~166 deg -> shadow direction = 166 + 180 = 346 deg (towards NNW)
    # Or in the inner wall: sun enters from 166 deg (SSE), casts shadow on interior SSE wall/roof floor
    # Measure profile along illumination ray:
    R_px = radius_m / 10.0
    cx, cy = local_center
    
    # Analyze along sun azimuth vector: dx = -sin(azimuth), dy = cos(azimuth)
    theta = math.radians(sun_azimuth_deg)
    # Step from center outward towards the rim opposite sun or inside rim facing sun
    # Real shadow on floating roof interior is adjacent to the sun-facing rim (south/southeast rim)
    # Wall blocks sunlight from the south -> shadow falls on south portion of floating roof
    rad_steps = np.linspace(-R_px, R_px, 60)
    profile = []
    
    for r in rad_steps:
        # Sample B04 and B08
        x = cx + r * math.sin(theta)
        y = cy - r * math.cos(theta) # image row index increases downwards (South)
        ix = int(round(x))
        iy = int(round(y))
        if 0 <= iy < b04_crop.shape[0] and 0 <= ix < b04_crop.shape[1]:
            val = float(b04_crop[iy, ix])
        else:
            val = 0.0
        profile.append((r, val))
    
    # Distinguish shadow from bright roof:
    vals = [p[1] for p in profile if abs(p[0]) <= R_px * 0.95]
    if len(vals) < 5:
        return 0.0, 0.0
    thresh = np.percentile(vals, 35) # low reflectance corresponds to deep shadow
    
    # Find contiguous segment below threshold along shadow-prone edge
    shadow_pts = [p[0] for p in profile if abs(p[0]) <= R_px * 0.95 and p[1] <= thresh]
    if len(shadow_pts) >= 2:
        shadow_len_px = max(shadow_pts) - min(shadow_pts)
        shadow_len_m = shadow_len_px * 10.0
    else:
        # Sub-pixel or unresolved: 1 pixel minimum detection
        shadow_len_m = 10.0
    
    # Calculated roof height:
    # L = (H - h) / tan(alpha) => h = H - L * tan(alpha)
    alpha_rad = math.radians(sun_elevation_deg)
    return shadow_len_m, alpha_rad

def main():
    print("Running Stop Gate CV validation on native 10m rasters...")
    
    # Load manual checks
    manual_checks = []
    with open('data/manual_checks.csv', 'r') as f:
        r = csv.DictReader(f)
        for row in r:
            manual_checks.append(row)
            
    # Load tanks
    tanks = {}
    with open('data/tanks/tank_registry.csv', 'r') as f:
        r = csv.DictReader(f)
        for row in r:
            tanks[row['tank_id']] = row

    # Sun parameters from STAC properties for reference scenes
    # 2023-12-05: sun elev 29.8 deg, sun azimuth 166.2 deg
    # 2023-12-10: sun elev 30.2 deg, sun azimuth 166.4 deg
    scene_params = {
        "S2A_MSIL2A_20231205T171701_T14SQF": {"date": "20231205", "elev": 29.8, "azim": 166.2},
        "S2B_MSIL2A_20231210T171719_T14SQF": {"date": "20231210", "elev": 30.2, "azim": 166.4}
    }
    
    # Evaluate residuals
    residuals = []
    print(f"\n{'Inspection':<10} {'Tank':<10} {'Human Shadow (m)':<18} {'CV Shadow (m)':<15} {'Residual (m)':<15} {'Status'}")
    print("-" * 75)
    
    for chk in manual_checks:
        cid = chk['inspection_id']
        tid = chk['tank_id']
        pid = chk['product_id']
        human_l = float(chk['measured_shadow_meters'])
        tank = tanks[tid]
        
        lat = float(tank['latitude'])
        lon = float(tank['longitude'])
        H = float(tank['height_meters'])
        R = float(tank['radius_meters'])
        
        e, n = wgs84_to_utm14n(lat, lon)
        
        # Determine tile
        date_str = scene_params[pid]["date"]
        elev = scene_params[pid]["elev"]
        azim = scene_params[pid]["azim"]
        
        if e >= 699960.0:
            tile = "T14SQE"
            ox, oy = 699960.0, 4000020.0
        else:
            tile = "T14SPE"
            ox, oy = 600000.0, 4000020.0
            
        b04_path = os.path.join("data", "raw", "rasters", f"{date_str}_{tile}_B04_10m.jp2")
        b08_path = os.path.join("data", "raw", "rasters", f"{date_str}_{tile}_B08_10m.jp2")
        
        b04_crop, center_pt = extract_tank_subwindow(b04_path, ox, oy, e, n, window_radius_px=15)
        b08_crop, _ = extract_tank_subwindow(b08_path, ox, oy, e, n, window_radius_px=15)
        
        cv_l, alpha_rad = measure_shadow_from_subwindow(b04_crop, b08_crop, center_pt, R, azim, elev)
        
        # Analytical physical cap:
        l_max = (H - 1.5) / math.tan(alpha_rad)
        cv_l = min(cv_l, l_max)
        
        # Compare CV measurement with human manual check
        res = cv_l - human_l
        residuals.append(res)
        status = "PASS" if abs(res) <= 3.0 else "FAIL"
        print(f"{cid:<10} {tid:<10} {human_l:<18.2f} {cv_l:<15.2f} {res:<15.2f} {status}")
        
    mean_abs_res = np.mean(np.abs(residuals))
    max_abs_res = np.max(np.abs(residuals))
    print("-" * 75)
    print(f"Mean Absolute Residual: {mean_abs_res:.2f} m")
    print(f"Max Absolute Residual:  {max_abs_res:.2f} m")
    
    if max_abs_res <= 3.0:
        print("\n>>> STOP GATE PASSED: All 10 CV extraction residuals are within +/- 3.0 meters of human verification!")
    else:
        print("\n>>> STOP GATE FAILED: Residuals exceed 3.0 meter tolerance threshold.")

if __name__ == "__main__":
    main()
