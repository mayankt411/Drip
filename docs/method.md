# Methodology: Physical and Geometric Principles

## 1. Floating-Roof Tank Geometry

A floating-roof crude oil storage tank features an open-top cylindrical shell of height $H$ and internal radius $r$. A pontoon roof floats on top of the stored crude oil at height $h$ above the floor.

When illuminated by sunlight at solar elevation angle $\alpha$, the upper rim of the tank wall casts an interior shadow onto the sunken floating roof.

$$\tan(\alpha) = \frac{H - h}{L}$$

Solving for roof height $h$:
$$h = H - L \cdot \tan(\alpha)$$

where:
- $H$: Tank shell height (meters), documented per tank in `data/tanks/tank_registry.csv` (typically 16.5m–19.0m at Cushing).
- $h$: Pontoon roof elevation above tank floor (meters).
- $L$: Interior shadow length along the solar azimuth direction (meters).
- $\alpha$: Solar elevation angle at sensing time over the AOI center.

## 2. Liquid Volume Conversion

Crude oil volume $V$ is given by:

$$V = \pi \cdot r^2 \cdot \max(0, h - h_{\text{empty}})$$

Converted to 42-gallon U.S. petroleum barrels:
$$V_{\text{bbl}} = V \cdot 6.28981077$$

Constant reference: ASTM D1250 / API MPMS Chapter 11.1 standard conversion factor ($1\text{ m}^3 = 6.28981077\text{ bbl}$).

## 3. Solar and Viewing Angles
- **Solar Azimuth:** Shadow displacement lies in direction $\theta_{\text{shadow}} = (\theta_{\text{sun}} + 180^\circ) \pmod{360^\circ}$. Measurements must be sampled along this specific ray.
- **Satellite Zenith Angle:** High off-nadir viewing causes foreshortening. S2 tile viewing zenith angles are logged per acquisition to test for systematic skew.
