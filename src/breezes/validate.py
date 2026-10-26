"""Score model wind directions against the held-out reference map.

Each reference sample is a point + drawn direction. The model's near-surface
wind at the sample's cell is classified as
  agree    : within AGREE_DEG of the drawn direction           (good enough)
  opposite : within 180 - OPPOSITE_DEG of the reverse direction (the error to eliminate)
  across   : anything in between, or calm (< CALM m/s)          (not counted as an error)
Legacy metrics kept for comparison: sign (|angle| < 90 deg), cos (mean cosine).
A naive baseline ("always up the nearest valley axis") is scored alongside.
"""
from __future__ import annotations

import numpy as np

from .dem import Grid
from .terrain import Terrain

AGREE_DEG = 45.0
OPPOSITE_DEG = 135.0
CALM = 0.3


def cells(grid: Grid, xy):
    inv = ~grid.transform
    col, row = inv * (xy[:, 0], xy[:, 1])
    r, c = np.floor(row).astype(int), np.floor(col).astype(int)
    ok = (r >= 0) & (c >= 0) & (r < grid.shape[0]) & (c < grid.shape[1])
    return r, c, ok


def classify(we, wn, de, dn, calm=CALM):
    """Per-sample class: 1 agree, 0 across/calm, -1 opposite."""
    sp = np.hypot(we, wn)
    cosang = (we * de + wn * dn) / np.maximum(sp, 1e-9)
    cls = np.zeros(len(sp), np.int8)
    cls[(sp > calm) & (cosang >= np.cos(np.radians(AGREE_DEG)))] = 1
    cls[(sp > calm) & (cosang <= np.cos(np.radians(OPPOSITE_DEG)))] = -1
    return cls


def _metrics(we, wn, de, dn, calm=CALM):
    sp = np.hypot(we, wn)
    cosang = np.where(sp > calm, (we * de + wn * dn) / np.maximum(sp, 1e-9), 0.0)
    cls = classify(we, wn, de, dn, calm)
    return dict(n=len(cls), agree=float(np.mean(cls == 1)), opposite=float(np.mean(cls == -1)),
                across=float(np.mean(cls == 0)), sign=float(np.mean(cosang > 0)),
                cos=float(np.mean(cosang)))


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
    rows = [f"{'':32s} {'':>5s} | {'---- model ----':^20s} | {'---- naive ----':^20s}",
            f"{'region':32s} {'n':>5s} | {'agree':>6s} {'OPPOS':>6s} {'sign':>6s} | "
            f"{'agree':>6s} {'OPPOS':>6s} {'sign':>6s}"]
    for reg, d in scores.items():
        m, b = d["model"], d["baseline"]
        rows.append(f"{reg[:32]:32s} {m['n']:5d} | {m['agree']:6.2f} {m['opposite']:6.2f} {m['sign']:6.2f} | "
                    f"{b['agree']:6.2f} {b['opposite']:6.2f} {b['sign']:6.2f}")
    rows.append(f"agree: within {AGREE_DEG:g} deg · OPPOS: >= {OPPOSITE_DEG:g} deg off (target 0) · "
                f"sign: legacy < 90 deg")
    return "\n".join(rows)
