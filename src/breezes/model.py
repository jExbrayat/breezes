"""Thermally driven topographic breezes (phase 1: uniform surface properties).

Three components, all diagnosed from terrain + solar forcing:

1. Surface sensible heat flux H(x,t): clear-sky beam on the slope with cast
   shadows, diffuse x sky-view, net longwave x sky-view.
2. Slope winds (local, fast): u = (B x sin a / c)^(1/3) along the fall line,
   upslope by day (fetch from upslope routing), downslope by night (fetch from
   downslope routing).
3. Valley winds (valley scale, lagged): a hypsometric mixed-layer model.
   Heat accumulated over a footprint fills the air volume below each level, so
   the mixed-layer top z_m(x) rises faster where there is less air (narrow
   valleys; generalised topographic amplification factor). Hydrostatics then
   gives, at valley-floor height z_f, the along-valley force
       F = (g gamma / theta0) (z_m - z_f) grad z_m           (day)
       F = -(g Gamma_n / theta0) (z_c - z_f) grad z_c        (night cold pool)
   which drives a damped momentum ODE along the valley axis.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import numba as nb
import numpy as np
from scipy import ndimage

from . import solar
from .dem import PROC, Grid
from .params import DEFAULT, Params
from .terrain import Terrain

HOUR = 3600.0


@nb.njit(cache=True)
def _advect_along_network(u, cidx, pos, rec, donor, hop, dt):
    """Semi-Lagrangian advection of the along-axis wind on the D8 network.
    u > 0 = down-valley: departure point lies upstream (walk the main-stem
    donor); u < 0: departure lies downstream (walk the receiver)."""
    out = np.empty_like(u)
    for k in range(cidx.size):
        steps = int(abs(u[k]) * dt / hop + 0.5)
        j = cidx[k]
        for _ in range(steps):
            nxt = donor[j] if u[k] > 0 else rec[j]
            if nxt < 0 or pos[nxt] < 0:
                break
            j = nxt
        out[k] = u[pos[j]]
    return out


def _fill_nan_nearest(a):
    mask = np.isnan(a)
    if not mask.any():
        return a
    idx = ndimage.distance_transform_edt(mask, return_distances=False, return_indices=True)
    return a[tuple(idx)]


class Hypsometry:
    """Precomputed footprint volumes V_k(x) = K * max(L_k - z, 0)^2 / 2 on a
    coarse grid, used to invert heat content -> mixed-layer top height."""

    def __init__(self, z, res, sigma, coarse=5, dz=25.0):
        zf = _fill_nan_nearest(z.astype(np.float64))
        self.coarse = coarse
        self.levels = np.arange(np.floor(zf.min() / dz) * dz, zf.max() + 3000 + dz, dz)
        s = sigma / res
        key = f"{z.shape[0]}x{z.shape[1]}_{res:g}_{sigma:g}_{coarse}_{dz:g}_{np.nansum(z):.6e}"
        cache = PROC / f"hyps_{key}.npy"
        if cache.exists():
            self.V = np.load(cache)
        else:
            self.V = np.stack([
                ndimage.gaussian_filter(np.maximum(L - zf, 0.0) ** 2 / 2, s, mode="nearest")[::coarse, ::coarse]
                for L in self.levels]).astype(np.float32)
            PROC.mkdir(parents=True, exist_ok=True)
            np.save(cache, self.V)
        self.sigma_cells = s
        self.shape = z.shape

    def top(self, heat, k_strat):
        """Level where k_strat * V(level) = smoothed heat (k = rho cp gamma)."""
        qs = ndimage.gaussian_filter(heat, self.sigma_cells, mode="nearest")[::self.coarse, ::self.coarse]
        target = np.maximum(qs / k_strat, 1e-6)            # no heat -> top at local floor
        n = (self.V < target[None]).sum(0)                 # levels below the crossing
        n = np.clip(n, 1, len(self.levels) - 1)
        i0 = n - 1
        v0 = np.take_along_axis(self.V, i0[None], 0)[0]
        v1 = np.take_along_axis(self.V, n[None], 0)[0]
        f = np.clip((target - v0) / np.maximum(v1 - v0, 1e-9), 0, 1)
        top_c = self.levels[i0] + f * (self.levels[1] - self.levels[0])
        zoom = (self.shape[0] / top_c.shape[0], self.shape[1] / top_c.shape[1])
        return ndimage.zoom(top_c, zoom, order=1)[:self.shape[0], :self.shape[1]]


@dataclass
class Snapshot:
    time: datetime
    solar_hour: float
    H: np.ndarray            # surface sensible heat flux [W/m2]
    slope_u: np.ndarray      # slope-wind components east/north [m/s]
    slope_v: np.ndarray
    valley_speed: np.ndarray # signed along-axis valley wind on channels (+ = up-valley)
    u: np.ndarray            # composite near-surface wind east/north [m/s]
    v: np.ndarray
    z_m: np.ndarray          # daytime mixed-layer top [m]
    z_c: np.ndarray          # nocturnal cold-pool top [m]


@dataclass
class BreezeModel:
    grid: Grid
    terrain: Terrain
    lat: float
    lon: float
    p: Params = field(default_factory=lambda: DEFAULT)

    def __post_init__(self):
        T, p = self.terrain, self.p
        self.valid = np.isfinite(self.grid.z)
        self.zc = _fill_nan_nearest(self.grid.z.astype(np.float64))
        self.svf = solar.sky_view_factor(self.grid.z, self.grid.res, 16, 10000.0)
        self.hyps = Hypsometry(self.grid.z, self.grid.res, p.sigma_valley)
        self.gconv = solar.grid_convergence(self.lon)
        # fall-line unit vector (pointing downslope), east/north
        self.fall_e = np.sin(T.aspect)
        self.fall_n = np.cos(T.aspect)
        self.sin_slope = np.sin(T.slope)
        # height gain along the slope-flow path: day capped at the CBL depth
        self.dz_day = np.minimum(T.fetch_up * self.sin_slope, p.dz_max_day)
        self.dz_night = np.minimum(T.area / self.grid.res, p.fetch_max_night) * self.sin_slope
        self.zfloor = np.nan_to_num(T.filled)
        self.chan_idx = np.flatnonzero(T.chan.ravel())
        self.chan_pos = np.full(self.grid.z.size, -1, np.int64)
        self.chan_pos[self.chan_idx] = np.arange(self.chan_idx.size)

    # ---------------------------------------------------------------- forcing
    def heat_flux(self, when: datetime):
        p, T = self.p, self.terrain
        elev, az_true = solar.sun_position(when, self.lat, self.lon)
        az = az_true + self.gconv          # true -> grid bearing (true north = -gamma)
        lw = p.lw_net_clear * self.svf
        if elev <= 0:
            rn = lw
        else:
            doy = when.timetuple().tm_yday
            s0 = p.S0 * (1 + 0.033 * math.cos(2 * math.pi * doy / 365))
            # air mass with altitude (pressure) correction
            m = 1.0 / (math.sin(elev) + 0.50572 * (math.degrees(elev) + 6.07995) ** -1.6364)
            pr = np.exp(-self.zc / 8434.5)
            beam = s0 * p.tau_beam ** (m * pr)
            shade = solar.shadow_mask(self.grid.z, self.grid.res, elev, az, 40000.0)
            ci = solar.incidence_cos(T.slope, T.aspect, elev, az)
            direct = np.where(shade, 0.0, beam * ci)
            diffuse = p.diffuse_frac * s0 * math.sin(elev) * self.svf
            rn = (1 - p.albedo) * (direct + diffuse) + lw
        H = np.where(rn > 0, p.h_frac_day * rn, p.h_frac_night * rn)
        return H.astype(np.float32), elev

    # ------------------------------------------------------------ slope winds
    def slope_wind(self, H):
        p = self.p
        B = p.g * H / (p.rho * p.cp * p.theta0)          # buoyancy flux [m2/s3]
        dz = np.where(B > 0, self.dz_day, self.dz_night)
        mag = np.cbrt(np.abs(B) * dz / p.c_slope)
        sign = np.where(B > 0, -1.0, 1.0)                 # day: against fall line
        return sign * mag * self.fall_e, sign * mag * self.fall_n

    # ----------------------------------------------------------- valley force
    def valley_force(self, Qd, Qn):
        p = self.p
        res = self.grid.res
        k = p.g / p.theta0
        zm = self.hyps.top(Qd, p.rho * p.cp * p.gamma_day)
        zc = self.hyps.top(-Qn, p.rho * p.cp * p.gamma_night)
        gy_m, gx_m = np.gradient(zm, res)
        gy_c, gx_c = np.gradient(zc, res)
        dm = np.maximum(zm - self.zfloor, 0)
        dc = np.maximum(zc - self.zfloor, 0)
        Fe = k * (p.gamma_day * dm * gx_m - p.gamma_night * dc * gx_c)
        Fn = k * (p.gamma_day * dm * -gy_m - p.gamma_night * dc * -gy_c)
        return Fe, Fn, zm, zc

    # -------------------------------------------------------------- time loop
    def run(self, day: datetime, dt_min: float = 15.0, spinup_days: int = 1,
            out_every_min: float = 60.0):
        """Integrate from midnight (UTC) `spinup_days` before `day`; return
        hourly snapshots for `day` (UTC calendar day)."""
        p, T = self.p, self.terrain
        dt = dt_min * 60.0
        t = datetime(day.year, day.month, day.day, tzinfo=timezone.utc) - timedelta(days=spinup_days)
        t_end = t + timedelta(days=spinup_days + 1)
        Qd = np.zeros(self.grid.shape)
        Qn = np.zeros(self.grid.shape)
        uv = np.zeros(self.chan_idx.size)               # along-axis valley wind (+ down-valley)
        ax_e = T.axis_e.ravel()[self.chan_idx]
        ax_n = T.axis_n.ravel()[self.chan_idx]
        decay_res = math.exp(-dt / (p.tau_residual_h * HOUR))
        out, every = [], int(round(out_every_min / dt_min))
        step = 0
        while t < t_end:
            H, elev = self.heat_flux(t)
            H64 = np.where(self.valid, H, H[self.valid].mean()).astype(np.float64)
            # morning heat first erodes the cold pool, then feeds the mixed layer
            heat_in = H64 * dt
            pos = np.maximum(heat_in, 0)
            erode = np.minimum(pos, -Qn)
            Qn = Qn + np.minimum(heat_in, 0) + erode
            Qd = Qd + (1 - p.heat_export) * (pos - erode)
            Qd = np.where(heat_in < 0, Qd * decay_res, Qd)
            Fe, Fn, zm, zc = self.valley_force(Qd, Qn)
            Fa = Fe.ravel()[self.chan_idx] * ax_e + Fn.ravel()[self.chan_idx] * ax_n
            # advection along the valley, then semi-implicit forcing + damping
            uv = _advect_along_network(uv, self.chan_idx, self.chan_pos, T.rec, T.donor,
                                       1.2 * self.grid.res, dt)
            uv = (uv + dt * Fa) / (1 + dt * (p.drag_valley * np.abs(uv) + 1 / (p.tau_valley_h * HOUR)))
            if t >= t_end - timedelta(days=1) and step % every == 0:
                out.append(self._snapshot(t, H, uv, zm, zc))
            t += timedelta(seconds=dt)
            step += 1
        return out

    def _snapshot(self, t, H, uv, zm, zc):
        T, p = self.terrain, self.p
        su, sv = self.slope_wind(H)
        chan_speed = np.full(self.grid.z.size, np.nan, np.float32)
        chan_speed[self.chan_idx] = uv
        # spread the valley wind from each thalweg to the cells draining to it
        tgt = T.tgt.ravel()
        ok = tgt >= 0
        vs = np.zeros(self.grid.z.size)
        vs[ok] = np.nan_to_num(chan_speed[tgt[ok]])
        ve = vs * np.where(ok, T.axis_e.ravel()[np.maximum(tgt, 0)], 0)
        vn = vs * np.where(ok, T.axis_n.ravel()[np.maximum(tgt, 0)], 0)
        w = np.exp(-np.nan_to_num(T.hand, nan=1e4) / p.hand_valley_scale).ravel()
        u = (w * ve + (1 - w) * su.ravel()).reshape(self.grid.shape)
        v = (w * vn + (1 - w) * sv.ravel()).reshape(self.grid.shape)
        return Snapshot(time=t, solar_hour=solar.solar_time_hours(t, self.lon), H=H,
                        slope_u=su.astype(np.float32), slope_v=sv.astype(np.float32),
                        valley_speed=(-chan_speed).reshape(self.grid.shape),
                        u=u.astype(np.float32), v=v.astype(np.float32),
                        z_m=zm.astype(np.float32), z_c=zc.astype(np.float32))
