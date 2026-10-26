"""Score model wind directions against the held-out reference map.

Each reference sample is a point + drawn direction. Metrics on the model's
near-surface wind at the sample's cell:
  sign  : fraction with positive along-path component (|angle| < 90 deg)
  hit45 : fraction within 45 deg
  cos   : mean cosine of the angle (calm cells count as 0)
A naive baseline ("always up the nearest valley axis") is scored alongside:
the physics only earns its keep where it beats that baseline.
"""
from __future__ import annotations

import numpy as np

from .dem import Grid
from .terrain import Terrain


def cells(grid: Grid, xy):
    inv = ~grid.transform
    col, row = inv * (xy[:, 0], xy[:, 1])
    r, c = np.floor(row).astype(int), np.floor(col).astype(int)
    ok = (r >= 0) & (c >= 0) & (r < grid.shape[0]) & (c < grid.shape[1])
    return r, c, ok


def _metrics(we, wn, de, dn, calm=0.3):
    sp = np.hypot(we, wn)
    cosang = np.where(sp > calm, (we * de + wn * dn) / np.maximum(sp, 1e-9), 0.0)
    return dict(n=len(cosang), sign=float(np.mean(cosang > 0)),
                hit45=float(np.mean(cosang > np.cos(np.pi / 4))), cos=float(np.mean(cosang)))


def score(grid: Grid, T: Terrain, samples, lines, u, v):
    """samples: rows (line_idx, x, y, de, dn) from reference.sample."""
    r, c, ok = cells(grid, samples[:, 1:3])
    s = samples[ok]
    r, c = r[ok], c[ok]
    de, dn = s[:, 3], s[:, 4]
    tgt = T.tgt[r, c]
    has = tgt >= 0
    up_e = np.where(has, -T.axis_e.ravel()[np.maximum(tgt, 0)], 0)
    up_n = np.where(has, -T.axis_n.ravel()[np.maximum(tgt, 0)], 0)
    regions = np.array([lines[int(i)].region for i in s[:, 0]])
    out = {}
    for reg in ["ALL"] + sorted(set(regions)):
        m = np.ones(len(s), bool) if reg == "ALL" else regions == reg
        out[reg] = dict(model=_metrics(u[r, c][m], v[r, c][m], de[m], dn[m]),
                        baseline=_metrics(up_e[m], up_n[m], de[m], dn[m]))
    return out


def report(scores) -> str:
    rows = [f"{'region':32s} {'n':>5s} | {'model sign':>10s} {'hit45':>6s} {'cos':>6s} | "
            f"{'base sign':>9s} {'hit45':>6s} {'cos':>6s}"]
    for reg, d in scores.items():
        m, b = d["model"], d["baseline"]
        rows.append(f"{reg[:32]:32s} {m['n']:5d} | {m['sign']:10.2f} {m['hit45']:6.2f} {m['cos']:6.2f} | "
                    f"{b['sign']:9.2f} {b['hit45']:6.2f} {b['cos']:6.2f}")
    return "\n".join(rows)
