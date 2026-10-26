"""Solar geometry, cast shadows and sky-view factor on a projected DEM."""
from __future__ import annotations

import math
from datetime import datetime, timezone

import numba as nb
import numpy as np


def sun_position(when: datetime, lat_deg: float, lon_deg: float):
    """NOAA low-precision solar position. Returns (elevation, true azimuth) in
    radians; azimuth clockwise from true north. `when` must be tz-aware."""
    t = when.astimezone(timezone.utc)
    doy = t.timetuple().tm_yday
    hour = t.hour + t.minute / 60 + t.second / 3600
    gam = 2 * math.pi / 365 * (doy - 1 + (hour - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(gam) - 0.032077 * math.sin(gam)
                    - 0.014615 * math.cos(2 * gam) - 0.040849 * math.sin(2 * gam))
    decl = (0.006918 - 0.399912 * math.cos(gam) + 0.070257 * math.sin(gam)
            - 0.006758 * math.cos(2 * gam) + 0.000907 * math.sin(2 * gam)
            - 0.002697 * math.cos(3 * gam) + 0.00148 * math.sin(3 * gam))
    tst = hour * 60 + eqt + 4 * lon_deg                  # true solar time [min]
    ha = math.radians(tst / 4 - 180)
    lat = math.radians(lat_deg)
    cz = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(ha)
    zen = math.acos(max(-1.0, min(1.0, cz)))
    az = math.atan2(math.sin(ha), math.cos(ha) * math.sin(lat) - math.tan(decl) * math.cos(lat))
    return math.pi / 2 - zen, (az + math.pi) % (2 * math.pi)


def solar_time_hours(when: datetime, lon_deg: float) -> float:
    """Apparent (true) solar time in hours at longitude lon_deg."""
    t = when.astimezone(timezone.utc)
    doy = t.timetuple().tm_yday
    gam = 2 * math.pi / 365 * (doy - 1 + (t.hour - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(gam) - 0.032077 * math.sin(gam)
                    - 0.014615 * math.cos(2 * gam) - 0.040849 * math.sin(2 * gam))
    return ((t.hour * 60 + t.minute + eqt + 4 * lon_deg) / 60) % 24


def grid_convergence(lon_deg: float, lat0_deg: float = 46.5, lon0_deg: float = 3.0) -> float:
    """Lambert-93 meridian convergence [rad]: true north = grid bearing -gamma."""
    return math.radians((lon_deg - lon0_deg) * math.sin(math.radians(lat0_deg)))


@nb.njit(cache=True, parallel=True)
def shadow_mask(z, res, sun_elev, sun_az_grid, max_dist):
    """True where the cell is in a cast shadow (horizon above the sun)."""
    ny, nx = z.shape
    out = np.zeros((ny, nx), np.bool_)
    if sun_elev <= 0:
        out[:, :] = True
        return out
    tan_e = math.tan(sun_elev)
    sx, sy = math.sin(sun_az_grid), math.cos(sun_az_grid)
    nstep = int(max_dist / res)
    zmax = np.nanmax(z)
    for r in nb.prange(ny):
        for c in range(nx):
            z0 = z[r, c]
            if not np.isfinite(z0):
                continue
            for k in range(1, nstep + 1):
                d = k * res
                if z0 + d * tan_e > zmax:
                    break
                rr = int(round(r - k * sy))
                cc = int(round(c + k * sx))
                if rr < 0 or cc < 0 or rr >= ny or cc >= nx:
                    break
                zz = z[rr, cc]
                if np.isfinite(zz) and zz - z0 > d * tan_e:
                    out[r, c] = True
                    break
    return out


@nb.njit(cache=True, parallel=True)
def sky_view_factor(z, res, n_dir, max_dist):
    """Isotropic sky-view factor ~ mean over azimuths of cos^2(horizon angle)."""
    ny, nx = z.shape
    svf = np.ones((ny, nx), np.float32)
    nstep = int(max_dist / res)
    for r in nb.prange(ny):
        for c in range(nx):
            z0 = z[r, c]
            if not np.isfinite(z0):
                continue
            acc = 0.0
            for a in range(n_dir):
                az = 2 * math.pi * a / n_dir
                sx, sy = math.sin(az), math.cos(az)
                best = 0.0
                for k in range(1, nstep + 1):
                    rr = int(round(r - k * sy))
                    cc = int(round(c + k * sx))
                    if rr < 0 or cc < 0 or rr >= ny or cc >= nx:
                        break
                    zz = z[rr, cc]
                    if np.isfinite(zz):
                        t = (zz - z0) / (k * res)
                        if t > best:
                            best = t
                acc += 1.0 / (1.0 + best * best)    # cos^2(atan(t))
            svf[r, c] = acc / n_dir
    return svf


def incidence_cos(slope, aspect, sun_elev, sun_az_grid):
    """cos of the angle between the sun and the slope normal (clipped at 0)."""
    zen = np.pi / 2 - sun_elev
    ci = np.cos(zen) * np.cos(slope) + np.sin(zen) * np.sin(slope) * np.cos(sun_az_grid - aspect)
    return np.clip(ci, 0, None)
