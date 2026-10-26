"""AROME baseline: composite 10 m wind of clear, calm July days (historical runs).

1. Day screening — Open-Meteo historical-forecast API (no key), AROME France 2.5 km
   (`meteofrance_arome_france`, which has 700 hPa + cloud). 700 hPa / cloud are
   archived only from 2024. Selection is fixed *before* looking at any score
   (estimate thresholds for a "thermally driven day": weak synoptic forcing at
   crest level, clear sky, dry):
     median over SCREEN_POINTS of the 06-16 UTC mean of
     700 hPa wind < 5 m/s, cloud cover < 20 %, daily precipitation < 0.5 mm.
2. 10 m wind — AROME France HD 1.3 km (0.01 deg lat/lon), from Open-Meteo's
   open-data S3 archive (.om files, 108 h x whole France, ~200 MB each, anonymous
   HTTPS). Whole files are cached in data/raw/arome/om/ (remote partial reads are
   far slower) and the Alps window is read locally. Verified cell-for-cell
   against the API.
3. Composite: per UTC hour, mean u, v over the selected days ("as if these days
   were the idealised calm day" that the physics model simulates).

Output: data/processed/arome_hd_composite.npz
  lat (ny,), lon (nx,), hour_utc (24,), u, v (24, ny, nx) true east/north [m/s], days
and data/raw/arome/days.json (screening table).
Run: uv run --group arome python scripts/fetch_arome.py
"""
import argparse
import json
import time
import urllib.request

import numpy as np

from breezes.dem import ALPS_BBOX, ROOT

API = "https://historical-forecast-api.open-meteo.com/v1/forecast"
S3 = "https://openmeteo.s3.amazonaws.com/data/meteofrance_arome_france_hd/"
RAW = ROOT / "data" / "raw" / "arome"
OUT = ROOT / "data" / "processed" / "arome_hd_composite.npz"
SCREEN_MODEL = "meteofrance_arome_france"
# spread over the French Alps, north to south (lat, lon)
SCREEN_POINTS = [(46.2, 6.5), (45.9, 6.9), (45.6, 6.2), (45.3, 6.6), (45.2, 5.8),
                 (44.9, 6.6), (44.5, 6.2), (44.1, 6.9)]
MAX_U700 = 5.0       # m/s   (estimate)
MAX_CLOUD = 20.0     # %     (estimate)
MAX_PRECIP = 0.5     # mm/day (estimate)
# AROME HD grid in the S3 archive (static/meta.json): regular 0.01 deg, south-west origin
LAT0, LON0, D, NX = 37.5, -12.0, 0.01, 2801
MARGIN = 0.05        # deg around ALPS_BBOX


def get(params: dict):
    url = API + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                d = json.load(r)
            return d if isinstance(d, list) else [d]
        except Exception as e:  # rate limit / transient
            print(f"  retry {attempt + 1}: {e}")
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(url[:200])


def screen(years):
    rows = []
    lat = ",".join(str(p[0]) for p in SCREEN_POINTS)
    lon = ",".join(str(p[1]) for p in SCREEN_POINTS)
    for y in years:
        d = get(dict(latitude=lat, longitude=lon, start_date=f"{y}-07-01", end_date=f"{y}-07-31",
                     hourly="wind_speed_700hPa,cloud_cover,precipitation", models=SCREEN_MODEL,
                     timezone="UTC", wind_speed_unit="ms", cell_selection="nearest"))
        t = np.array(d[0]["hourly"]["time"], "datetime64[h]")
        arr = {k: np.array([p["hourly"][k] for p in d], float) for k in
               ["wind_speed_700hPa", "cloud_cover", "precipitation"]}
        for day in np.unique(t.astype("datetime64[D]")):
            m = t.astype("datetime64[D]") == day
            hd = m & (t.astype(int) % 24 >= 6) & (t.astype(int) % 24 <= 16)
            if np.isnan(arr["wind_speed_700hPa"][:, hd]).all():
                continue                       # not archived (2023)
            r = dict(day=str(day),
                     u700=float(np.nanmedian(np.nanmean(arr["wind_speed_700hPa"][:, hd], 1))),
                     cloud=float(np.nanmedian(np.nanmean(arr["cloud_cover"][:, hd], 1))),
                     precip=float(np.nanmedian(np.nansum(arr["precipitation"][:, m], 1))))
            r["selected"] = bool(r["u700"] < MAX_U700 and r["cloud"] < MAX_CLOUD and r["precip"] < MAX_PRECIP)
            rows.append(r)
    return rows


def window():
    lon0, lat0, lon1, lat1 = ALPS_BBOX
    r0, r1 = int((lat0 - MARGIN - LAT0) / D), int(np.ceil((lat1 + MARGIN - LAT0) / D)) + 1
    c0, c1 = int((lon0 - MARGIN - LON0) / D), int(np.ceil((lon1 + MARGIN - LON0) / D)) + 1
    return r0, r1, c0, c1


def chunk_file(var, chunk):
    path = RAW / "om" / f"{var}_{chunk}.om"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".part")
        urllib.request.urlretrieve(f"{S3}{var}/chunk_{chunk}.om", tmp)
        tmp.rename(path)
    return path


def read_day(var, day, r0, r1, c0, c1):
    """(24, rows, cols) of `var` for UTC calendar day `day`, rows south -> north."""
    from omfiles import OmFileReader
    h0 = int(np.datetime64(day, "h").astype(int))
    out = np.empty((24, r1 - r0, c1 - c0), np.float32)
    lo, hi = r0 * NX, (r1 - 1) * NX + NX       # whole rows: one contiguous read per file
    for chunk in sorted({(h0 + k) // 108 for k in range(24)}):
        f = OmFileReader.from_path(str(chunk_file(var, chunk)))
        ks = [k for k in range(24) if (h0 + k) // 108 == chunk]
        t0 = h0 + ks[0] - chunk * 108
        if len(f.shape) == 3:                   # newer files (2025-): (lat, lon, time)
            a = f.read_array((slice(r0, r1), slice(c0, c1), slice(t0, t0 + len(ks))))
        else:                                   # older files: (lat * lon, time)
            a = f.read_array((slice(lo, hi), slice(t0, t0 + len(ks))))
            a = a.reshape(r1 - r0, NX, len(ks))[:, c0:c1]
        out[ks] = a.transpose(2, 0, 1)
        f.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=[2024, 2025])
    ap.add_argument("--screen-only", action="store_true")
    a = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    rows = screen(a.years)
    (RAW / "days.json").write_text(json.dumps(rows, indent=1))
    days = [r["day"] for r in rows if r["selected"]]
    for r in rows:
        print(f"{r['day']}  u700 {r['u700']:4.1f} m/s  cloud {r['cloud']:5.1f} %  "
              f"precip {r['precip']:4.1f} mm  {'SELECTED' if r['selected'] else ''}")
    print(f"{len(days)} days selected: {days}")
    if a.screen_only or not days:
        return

    r0, r1, c0, c1 = window()
    su = np.zeros((24, r1 - r0, c1 - c0)); sv = np.zeros_like(su)
    for day in days:
        t = time.time()
        su += read_day("wind_u_component_10m", day, r0, r1, c0, c1)
        sv += read_day("wind_v_component_10m", day, r0, r1, c0, c1)
        print(f"  {day} read in {time.time() - t:.0f} s")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT, lat=LAT0 + D * np.arange(r0, r1), lon=LON0 + D * np.arange(c0, c1),
                        hour_utc=np.arange(24), u=(su / len(days)).astype(np.float32),
                        v=(sv / len(days)).astype(np.float32), days=np.array(days))
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
