"""Export model runs (out/<tag>/fields.npz) for the localhost map viewer.

Writes, per run, web/data/<tag>/:
  meta.json   hours, valley-arrow positions/axes, pilots' lines + sample geometry, scores
  field.bin   int8 [hour][u|v][row][col] near-surface wind on a lat/lon grid, m/s * FIELD_SCALE
  valley.bin  int8 [hour][arrow] signed valley wind, m/s * 10 (+ = up-valley)
  samples.bin int8 [hour][sample] class of each pilots'-line sample: 1 agree, 0 across/calm, -1 opposite
and web/data/runs.json listing all exported runs.
All vectors are rotated from Lambert-93 grid north to true north (Web Mercator
is conformal, so true east/north = screen right/up).
"""
import argparse
import json
from datetime import datetime, timedelta, timezone

import numpy as np
from pyproj import Transformer
from scipy import ndimage

from breezes import dem, reference, terrain, validate
from breezes.dem import ALPS_BBOX, CRS, ROOT

WEB = ROOT / "web"
FIELD_SCALE = 4          # int8 units per m/s in field.bin (0.25 m/s steps, max ±31 m/s)
SAMPLE_HALF_M = 200.0    # half-length of the drawn piece of pilots' line per sample (samples every 400 m)
FORMAT = 2               # bump when the export layout changes; serve.py re-exports older runs
DLAT, DLON = 0.01, 0.014  # ~1.1 km particle grid

TO93 = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
TO84 = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True)


def north_angle(lon, lat):
    """Grid bearing of true north at (lon, lat) [rad]."""
    x0, y0 = TO93.transform(lon, lat)
    x1, y1 = TO93.transform(lon, lat + 0.001)
    return np.arctan2(np.subtract(x1, x0), np.subtract(y1, y0))


def to_true(e, n, theta):
    """Rotate grid-frame vector components to true east/north."""
    c, s = np.cos(theta), np.sin(theta)
    return e * c - n * s, n * c + e * s


def grid_index(g, x, y):
    """Fractional (row, col) of projected points in the 200 m grid (cell centres)."""
    col = (x - g.transform.c) / g.res - 0.5
    row = (g.transform.f - y) / g.res - 0.5
    return row, col


def field_latlon(g, u, v, smooth_cells=5):
    lon0, lat0, lon1, lat1 = ALPS_BBOX
    lats = np.arange(lat1, lat0, -DLAT)
    lons = np.arange(lon0, lon1, DLON)
    LON, LAT = np.meshgrid(lons, lats)
    X, Y = TO93.transform(LON, LAT)
    R, C = grid_index(g, X, Y)
    theta = north_angle(LON, LAT)
    out = np.zeros((u.shape[0], 2, len(lats), len(lons)), np.int8)
    for h in range(u.shape[0]):
        uh = ndimage.uniform_filter(np.nan_to_num(u[h].astype(np.float32)), smooth_cells)
        vh = ndimage.uniform_filter(np.nan_to_num(v[h].astype(np.float32)), smooth_cells)
        us = ndimage.map_coordinates(uh, [R, C], order=1, cval=0.0)
        vs = ndimage.map_coordinates(vh, [R, C], order=1, cval=0.0)
        ue, vn = to_true(us, vs, theta)
        out[h, 0] = np.clip(np.round(ue * FIELD_SCALE), -127, 127)
        out[h, 1] = np.clip(np.round(vn * FIELD_SCALE), -127, 127)
    return out, dict(lat0=float(lats[0]), lon0=float(lons[0]), dlat=DLAT, dlon=DLON,
                     ny=len(lats), nx=len(lons), scale=FIELD_SCALE)


def valley_arrows(g, T, valley, min_area_km2=10.0, spacing_m=1000.0):
    """One arrow per spacing_m bin of the channel network, largest catchment first."""
    rr, cc = np.nonzero(T.chan & (T.area > min_area_km2 * 1e6))
    order = np.argsort(-T.area[rr, cc], kind="stable")
    rr, cc = rr[order], cc[order]
    k = spacing_m / g.res
    bins = (rr // k).astype(np.int64) * 100000 + (cc // k).astype(np.int64)
    _, first = np.unique(bins, return_index=True)
    first = np.sort(first)                      # keep largest-catchment-first order
    rr, cc = rr[first], cc[first]
    x, y = g.xy()
    lon, lat = TO84.transform(x[cc], y[rr])
    ae, an = to_true(T.axis_e[rr, cc], T.axis_n[rr, cc], north_angle(lon, lat))
    sp = np.clip(np.round(np.nan_to_num(valley[:, rr, cc].astype(np.float32)) * 10), -127, 127).astype(np.int8)
    arrows = dict(n=int(len(rr)), lat=np.round(lat, 5).tolist(), lon=np.round(lon, 5).tolist(),
                  ae=np.round(ae, 3).tolist(), an=np.round(an, 3).tolist(),
                  logA=np.round(np.log10(T.area[rr, cc] / 1e6), 2).tolist())
    return arrows, sp


def export(tag, g, T, lines, samples):
    run = ROOT / "out" / tag
    F = np.load(run / "fields.npz")
    order = np.argsort(F["solar_hour"])
    sh = F["solar_hour"][order]
    u, v, valley = F["u"][order], F["v"][order], F["valley"][order]
    params = json.loads((run / "params.json").read_text()) if (run / "params.json").exists() else {}
    date = params.get("_date", "2026-07-15")
    day = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    cest = [(day + timedelta(hours=int(i) + 2)).strftime("%H:%M") for i in order]

    # per-hour class of every reference sample: 1 agree, 0 across/calm, -1 opposite
    r, c, ok = validate.cells(g, samples[:, 1:3])
    S, r, c = samples[ok], r[ok], c[ok]
    classes = np.stack([validate.classify(u[h].astype(np.float32)[r, c], v[h].astype(np.float32)[r, c],
                                          S[:, 3], S[:, 4]) for h in range(len(sh))])
    ref, ref_index = [], {}
    for i, L in enumerate(lines):
        if not L.head_ok:
            continue
        ref_index[i] = len(ref)
        ref.append(dict(name=L.name, region=L.region,
                        coords=[[round(la, 5), round(lo, 5)] for lo, la in L.lonlat]))
    half = SAMPLE_HALF_M
    lo0, la0 = TO84.transform(S[:, 1] - S[:, 3] * half, S[:, 2] - S[:, 4] * half)
    lo1, la1 = TO84.transform(S[:, 1] + S[:, 3] * half, S[:, 2] + S[:, 4] * half)
    sample_meta = dict(n=int(len(S)), line=[ref_index[int(i)] for i in S[:, 0]],
                       lat0=np.round(la0, 5).tolist(), lon0=np.round(lo0, 5).tolist(),
                       lat1=np.round(la1, 5).tolist(), lon1=np.round(lo1, 5).tolist())

    aft = (sh >= 13) & (sh <= 16)
    scores = validate.score(g, T, samples, lines, u[aft].astype(np.float32).mean(0),
                            v[aft].astype(np.float32).mean(0))

    field, fmeta = field_latlon(g, u, v)
    arrows, vsp = valley_arrows(g, T, valley)
    d = WEB / "data" / tag
    d.mkdir(parents=True, exist_ok=True)
    field.tofile(d / "field.bin")
    vsp.tofile(d / "valley.bin")
    classes.astype(np.int8).tofile(d / "samples.bin")
    meta = dict(format=FORMAT, tag=tag, date=date, hours=[round(float(h), 2) for h in sh], cest=cest,
                field=fmeta, arrows=arrows, ref=ref, samples=sample_meta, scores=scores, params=params,
                criteria=dict(agree_deg=validate.AGREE_DEG, opposite_deg=validate.OPPOSITE_DEG,
                              calm=validate.CALM))
    (d / "meta.json").write_text(json.dumps(meta, separators=(",", ":")))
    return scores["ALL"]


def write_index():
    runs = []
    for m in sorted((WEB / "data").glob("*/meta.json")):
        meta = json.loads(m.read_text())
        src = ROOT / "out" / meta["tag"] / "fields.npz"
        s = meta["scores"]["ALL"]["model"]
        runs.append(dict(tag=meta["tag"], date=meta["date"], model=meta["params"].get("_model", "physics"),
                         agree=s.get("agree"), opposite=s.get("opposite"), sign=s["sign"],
                         mtime=(src if src.exists() else m).stat().st_mtime))
    runs.sort(key=lambda r: -r["mtime"])        # most recent model run first
    (WEB / "data" / "runs.json").write_text(json.dumps(runs, indent=1))
    return runs


def main(tags=None):
    if tags is None:
        ap = argparse.ArgumentParser()
        ap.add_argument("tags", nargs="*", help="run tags in out/ (default: all runs)")
        tags = ap.parse_args().tags
    if not tags:
        tags = sorted(p.parent.name for p in (ROOT / "out").glob("*/fields.npz"))
    g = dem.load(res=200)
    T = terrain.analyse(g.z, g.res)
    lines = reference.load()
    samples = reference.sample(lines)
    for tag in tags:
        m = export(tag, g, T, lines, samples)["model"]
        print(f"exported {tag}: agree {m['agree']:.2f}, opposite {m['opposite']:.2f}")
    write_index()


if __name__ == "__main__":
    main()
