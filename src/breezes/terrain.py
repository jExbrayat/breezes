"""Terrain analysis on a projected grid: slope/aspect, depression filling,
D8 routing, flow accumulation, drainage network, HAND and valley axes.

Conventions: row 0 = north; x east, y north; aspect/azimuths are grid
bearings in radians clockwise from grid-north. NaN cells are outlets.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass

import numba as nb
import numpy as np

# D8 neighbour offsets (drow, dcol), clockwise from north.
DR = np.array([-1, -1, 0, 1, 1, 1, 0, -1], np.int64)
DC = np.array([0, 1, 1, 1, 0, -1, -1, -1], np.int64)
DL = np.array([1, 2**0.5, 1, 2**0.5, 1, 2**0.5, 1, 2**0.5])


def slope_aspect(z: np.ndarray, res: float):
    """Slope angle [rad] and downslope aspect (bearing the terrain faces) [rad]."""
    zf = np.where(np.isnan(z), np.nanmean(z), z)
    dzdy_row, dzdx = np.gradient(zf, res)
    dzdy = -dzdy_row                      # rows increase southward
    slope = np.arctan(np.hypot(dzdx, dzdy))
    aspect = np.arctan2(-dzdx, -dzdy) % (2 * np.pi)   # direction of steepest descent
    return slope.astype(np.float32), aspect.astype(np.float32), dzdx, dzdy


def priority_flood(z: np.ndarray, eps: float = 1e-3) -> np.ndarray:
    """Barnes et al. (2014) priority-flood with epsilon: every cell drains to an
    edge/NaN outlet. Returns filled elevations (float64)."""
    return _priority_flood(np.where(np.isnan(z), -np.inf, z).astype(np.float64), eps)


@nb.njit(cache=True)
def _priority_flood(z, eps):
    ny, nx = z.shape
    out = z.copy()
    closed = np.zeros((ny, nx), np.bool_)
    heap = [(0.0, 0, 0)]
    heap.pop()
    for r in range(ny):
        for c in range(nx):
            edge = r == 0 or c == 0 or r == ny - 1 or c == nx - 1
            if not edge and np.isfinite(z[r, c]):
                for k in range(8):
                    if not np.isfinite(z[r + DR[k], c + DC[k]]):
                        edge = True
                        break
            if edge and np.isfinite(z[r, c]):
                heapq.heappush(heap, (z[r, c], r, c))
                closed[r, c] = True
            elif not np.isfinite(z[r, c]):
                closed[r, c] = True
    while len(heap) > 0:
        h, r, c = heapq.heappop(heap)
        for k in range(8):
            rr, cc = r + DR[k], c + DC[k]
            if rr < 0 or cc < 0 or rr >= ny or cc >= nx or closed[rr, cc]:
                continue
            closed[rr, cc] = True
            if out[rr, cc] <= h:
                out[rr, cc] = h + eps
            heapq.heappush(heap, (out[rr, cc], rr, cc))
    return out


@nb.njit(cache=True, parallel=True)
def d8(z):
    """Steepest-descent receiver index per cell (flat index), -1 if none."""
    ny, nx = z.shape
    rec = np.full(ny * nx, -1, np.int64)
    for r in nb.prange(ny):
        for c in range(nx):
            if not np.isfinite(z[r, c]):
                continue
            best, bk = 0.0, -1
            for k in range(8):
                rr, cc = r + DR[k], c + DC[k]
                if rr < 0 or cc < 0 or rr >= ny or cc >= nx:
                    continue
                if not np.isfinite(z[rr, cc]):
                    # NaN neighbour is an outlet: drain into it as a sink
                    continue
                s = (z[r, c] - z[rr, cc]) / DL[k]
                if s > best:
                    best, bk = s, k
            if bk >= 0:
                rec[r * nx + c] = (r + DR[bk]) * nx + (c + DC[bk])
    return rec


@nb.njit(cache=True)
def accumulate(rec, order, w):
    """Sum weights downstream. `order` = flat indices sorted upstream-first."""
    acc = w.copy()
    for i in order:
        j = rec[i]
        if j >= 0:
            acc[j] += acc[i]
    return acc


def flow_accumulation(z: np.ndarray, weights=None):
    """D8 receivers and accumulated weights (cells by default) on surface z."""
    rec = d8(z)
    zf = np.where(np.isfinite(z), z, -np.inf).ravel()
    order = np.argsort(-zf, kind="stable")
    w = np.ones(z.size) if weights is None else weights.ravel().astype(np.float64)
    return rec, accumulate(rec, order, w).reshape(z.shape)


@nb.njit(cache=True)
def _hand(rec, chan, z, order_up):
    """Height above nearest drainage + index of that drainage cell.
    order_up: flat indices sorted downstream-first (low to high filled z)."""
    n = rec.size
    tgt = np.full(n, -1, np.int64)
    for i in order_up:
        if chan[i]:
            tgt[i] = i
        elif rec[i] >= 0:
            tgt[i] = tgt[rec[i]]
    hand = np.full(n, np.nan)
    for i in range(n):
        if tgt[i] >= 0:
            hand[i] = z[i] - z[tgt[i]]
    return hand, tgt


@nb.njit(cache=True)
def _downstream_axis(rec, chan, nx, k):
    """Unit vector (east, north) from each channel cell to the cell k steps
    downstream — a smoothed valley-axis direction pointing down-valley."""
    n = rec.size
    ax = np.zeros(n)
    ay = np.zeros(n)
    for i in range(n):
        if not chan[i]:
            continue
        j, s = i, 0
        while s < k and rec[j] >= 0:
            j = rec[j]
            s += 1
        if s == 0:
            continue
        dx = (j % nx) - (i % nx)
        dy = -((j // nx) - (i // nx))
        d = (dx * dx + dy * dy) ** 0.5
        if d > 0:
            ax[i], ay[i] = dx / d, dy / d
    return ax, ay


@nb.njit(cache=True)
def main_donor(rec, chan, area):
    """Largest-area upstream channel neighbour of each channel cell (-1 if none):
    the network's main stem, used to walk upstream."""
    n = rec.size
    don = np.full(n, -1, np.int64)
    for i in range(n):
        j = rec[i]
        if chan[i] and j >= 0 and chan[j]:
            if don[j] < 0 or area[i] > area[don[j]]:
                don[j] = i
    return don


@dataclass
class Terrain:
    z: np.ndarray            # raw elevation (NaN outside)
    res: float
    slope: np.ndarray
    aspect: np.ndarray
    filled: np.ndarray
    rec: np.ndarray          # D8 receivers on filled DEM (flat idx)
    area: np.ndarray         # upstream area [m^2]
    rec_up: np.ndarray       # D8 receivers on -z (upslope routing)
    fetch_up: np.ndarray     # upslope-routing contributing length [m] (day fetch)
    chan: np.ndarray         # channel (valley-floor thalweg) mask
    hand: np.ndarray         # height above nearest drainage [m]
    tgt: np.ndarray          # flat index of nearest drainage cell
    axis_e: np.ndarray       # down-valley unit vector on channel cells
    axis_n: np.ndarray
    pool_depth: np.ndarray   # depression depth (filled - z) [m]
    donor: np.ndarray        # main-stem upstream channel cell (flat idx, -1 none)


def analyse(z: np.ndarray, res: float, chan_area_km2: float = 5.0,
            axis_len_m: float = 1500.0) -> Terrain:
    ny, nx = z.shape
    slope, aspect, _, _ = slope_aspect(z, res)
    filled = priority_flood(z)
    filled[np.isinf(filled)] = np.nan
    rec, cells = flow_accumulation(filled)
    area = cells * res * res
    # Upslope routing on the raw surface: paths climb to ridges/summits.
    rec_up, cells_up = flow_accumulation(np.where(np.isnan(z), np.nan, -z))
    fetch_up = cells_up * res
    chan = (area >= chan_area_km2 * 1e6) & np.isfinite(z)
    order_up = np.argsort(np.where(np.isfinite(filled), filled, np.inf).ravel(), kind="stable")
    hand, tgt = _hand(rec, chan.ravel(), np.nan_to_num(filled.ravel()), order_up)
    k = max(1, int(round(axis_len_m / res)))
    ax, ay = _downstream_axis(rec, chan.ravel(), nx, k)
    return Terrain(z=z, res=res, slope=slope, aspect=aspect, filled=filled, rec=rec,
                   area=area, rec_up=rec_up, fetch_up=fetch_up, chan=chan,
                   hand=hand.reshape(z.shape), tgt=tgt.reshape(z.shape),
                   axis_e=ax.reshape(z.shape), axis_n=ay.reshape(z.shape),
                   pool_depth=np.nan_to_num(filled - z),
                   donor=main_donor(rec, chan.ravel(), area.ravel()))
