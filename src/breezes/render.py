"""Static maps: hillshade + valley winds on the network + slope-wind arrows +
reference (held-out) arrows."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource
from pyproj import Transformer

from .dem import CRS, Grid
from .terrain import Terrain

UP, DOWN = "#d6402b", "#2b6fd6"     # up-valley warm, down-valley cool


def _window(grid: Grid, lonlat_bbox):
    tr = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    lon0, lat0, lon1, lat1 = lonlat_bbox
    xs, ys = tr.transform([lon0, lon1, lon0, lon1], [lat0, lat0, lat1, lat1])
    inv = ~grid.transform
    cols, rows = zip(*[inv * (x, y) for x, y in zip(xs, ys)])
    r0, r1 = max(0, int(min(rows))), min(grid.shape[0], int(max(rows)) + 1)
    c0, c1 = max(0, int(min(cols))), min(grid.shape[1], int(max(cols)) + 1)
    return slice(r0, r1), slice(c0, c1)


def plot_region(grid: Grid, T: Terrain, valley, su, sv, lonlat_bbox, title, path,
                ref_lines=None, slope_every=4, min_area_km2=20.0):
    rs, cs = _window(grid, lonlat_bbox)
    z = grid.z[rs, cs]
    x, y = grid.xy()
    x, y = x[cs], y[rs]
    ext = (x[0], x[-1], y[-1], y[0])
    fig, ax = plt.subplots(figsize=(11, 11 * z.shape[0] / z.shape[1] + 0.6), dpi=130)
    ls = LightSource(azdeg=315, altdeg=40)
    hs = ls.hillshade(np.nan_to_num(z, nan=0), vert_exag=2, dx=grid.res, dy=grid.res)
    ax.imshow(hs, cmap="gray", extent=ext, vmin=0, vmax=1.1, alpha=0.9)
    ax.imshow(np.ma.masked_invalid(z), cmap="terrain", extent=ext, alpha=0.25, vmin=0, vmax=4000)

    # slope winds (thin grey arrows)
    k = slope_every
    X, Y = np.meshgrid(x[::k], y[::k])
    U, V = su[rs, cs][::k, ::k], sv[rs, cs][::k, ::k]
    ax.quiver(X, Y, U, V, color="#333", alpha=0.35, scale=120, width=0.0012, headwidth=4)

    # valley winds on the network, sampled as arrows
    vv = valley[rs, cs]
    area = T.area[rs, cs]
    ae, an = T.axis_e[rs, cs], T.axis_n[rs, cs]
    sel = np.isfinite(vv) & (area > min_area_km2 * 1e6)
    rr, cc = np.nonzero(sel)
    keep = ((rr // 6 + cc // 6) % 2 == 0) & (rr % 3 == 0) & (cc % 3 == 0)
    rr, cc = rr[keep], cc[keep]
    s = vv[rr, cc]
    de, dn = -ae[rr, cc] * s, -an[rr, cc] * s          # + valley = up-valley = -axis
    col = np.where(s > 0, UP, DOWN)
    a_km2 = area[rr, cc] / 1e6
    for lo, hi, w in [(0, 100, 0.0018), (100, 1000, 0.0026), (1000, np.inf, 0.0036)]:
        m = (a_km2 >= lo) & (a_km2 < hi)
        if m.any():
            ax.quiver(x[cc[m]], y[rr[m]], de[m], dn[m], color=col[m], scale=150, width=w,
                      headwidth=3.5, alpha=0.95, zorder=4)

    if ref_lines is not None:
        for L in ref_lines:
            if not L.head_ok:
                continue
            ax.plot(L.xy[:, 0], L.xy[:, 1], color="black", lw=2.6, alpha=0.8, zorder=5)
            ax.plot(L.xy[:, 0], L.xy[:, 1], color="#ffd400", lw=1.4, alpha=0.95, zorder=6)
            a, b = L.xy[-2], L.xy[-1]
            ax.annotate("", xy=b, xytext=a + 0.3 * (b - a),
                        arrowprops=dict(arrowstyle="-|>", color="#ffd400", lw=1.4,
                                        mutation_scale=16), zorder=7)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=11)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], color=UP, lw=3, label="model: up-valley"),
                       Line2D([], [], color=DOWN, lw=3, label="model: down-valley"),
                       Line2D([], [], color="#333", lw=1, alpha=0.5, label="model: slope wind"),
                       Line2D([], [], color="#ffd400", lw=2.5, label="reference map (pilots)")],
              loc="lower right", fontsize=8, framealpha=0.85)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
