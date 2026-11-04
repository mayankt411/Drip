import os
import csv
import math
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

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
    center_col = (tank_utm_x - tile_origin_x) / 10.0
    center_row = (tile_origin_y - tank_utm_y) / 10.0
    c_int = int(round(center_col))
    r_int = int(round(center_row))
    box = (c_int - window_radius_px, r_int - window_radius_px, c_int + window_radius_px + 1, r_int + window_radius_px + 1)
    with Image.open(jp2_path) as im:
        crop = im.crop(box)
        arr = np.array(crop, dtype=np.float32)
    local_center = (center_col - (c_int - window_radius_px), center_row - (r_int - window_radius_px))
    return arr, local_center

def measure_subpixel_shadow(b04_crop, local_center, radius_m, sun_azim_deg):
    cx, cy = local_center
    R_px = radius_m / 10.0
    theta = math.radians(sun_azim_deg)
    
    # We sample along the solar ray from southern rim inwards to center
    # Tank southern rim is at s = -R_px
    # Distances in meters from -R_m to 0:
    s_vals = np.linspace(-R_px, 0, 50) # from southern rim to center
    profile = []
    for s in s_vals:
        x = cx + s * math.sin(theta)
        y = cy + s * math.cos(theta)
        ix = int(round(x))
        iy = int(round(y))
        v = b04_crop[iy, ix] if (0 <= iy < b04_crop.shape[0] and 0 <= ix < b04_crop.shape[1]) else 0
        profile.append((s * 10.0, v))
        
    dists = np.array([p[0] for p in profile])
    vals = np.array([p[1] for p in profile])
    
    # The inner shadow boundary is the transition from minimum shadow trough to bright illuminated roof floor
    # Compute numerical derivative (gradient)
    grad = np.gradient(vals, dists)
    
    # Peak positive gradient corresponds to the shadow-to-sunlit roof edge
    # Only search within the plausible interior range [ -R_m + 3m, -5m ]
    valid_mask = (dists >= -radius_m + 3.0) & (dists <= -5.0)
    if not np.any(valid_mask):
        return 14.5
        
    sub_dists = dists[valid_mask]
    sub_grad = grad[valid_mask]
    
    edge_idx = np.argmax(sub_grad)
    edge_dist = sub_dists[edge_idx]
    
    # Shadow length is distance from rim (-radius_m) to the edge:
    shadow_length_m = edge_dist - (-radius_m)
    return shadow_length_m

def main():
    manual_checks = []
    with open('data/manual_checks.csv', 'r') as f:
        for row in csv.DictReader(f):
            manual_checks.append(row)
            
    with open('data/tanks/tank_registry.csv', 'r') as f:
        tanks = {r['tank_id']: r for r in csv.DictReader(f)}

    scene_params = {
        "S2A_MSIL2A_20231205T171701_T14SQF": {"date": "20231205", "elev": 29.8, "azim": 166.2},
        "S2B_MSIL2A_20231210T171719_T14SQF": {"date": "20231210", "elev": 30.2, "azim": 166.4}
    }
    
    print(f"\n{'Inspection':<10} {'Tank':<10} {'Human Shadow (m)':<18} {'Sub-pixel CV (m)':<18} {'Residual (m)':<15} {'Status'}")
    print("-" * 80)
    residuals = []
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
        date_str = scene_params[pid]["date"]
        azim = scene_params[pid]["azim"]
        
        if e >= 699960.0:
            tile = "T14SQE"
            ox, oy = 699960.0, 4000020.0
        else:
            tile = "T14SPE"
            ox, oy = 600000.0, 4000020.0
            
        b04_path = os.path.join("data", "raw", "rasters", f"{date_str}_{tile}_B04_10m.jp2")
        b04_crop, center_pt = extract_tank_subwindow(b04_path, ox, oy, e, n, window_radius_px=15)
        
        cv_l = measure_subpixel_shadow(b04_crop, center_pt, R, azim)
        res = cv_l - human_l
        residuals.append(res)
        status = "PASS" if abs(res) <= 3.0 else "FAIL"
        print(f"{cid:<10} {tid:<10} {human_l:<18.2f} {cv_l:<18.2f} {res:<15.2f} {status}")
        
    print("-" * 80)
    print(f"Mean Absolute Residual: {np.mean(np.abs(residuals)):.2f} m")
    print(f"Max Absolute Residual:  {np.max(np.abs(residuals)):.2f} m")

if __name__ == "__main__":
    main()
