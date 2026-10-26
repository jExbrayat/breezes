"""Regional PNG maps of a saved run: hillshade, model valley winds (red = up-valley,
blue = down-valley), slope winds (grey), pilots' reference map (yellow)."""
import argparse

import numpy as np

from breezes import dem, reference, render, terrain
from breezes.dem import ROOT

REGIONS = {  # lon_min, lat_min, lon_max, lat_max
    "gresivaudan_chartreuse": (5.55, 45.10, 6.20, 45.60),
    "bauges_annecy": (5.85, 45.50, 6.45, 45.95),
    "chablais_arve": (6.20, 45.85, 7.00, 46.40),
    "tarentaise_maurienne": (6.20, 45.15, 7.05, 45.75),
    "vercors_diois": (5.15, 44.55, 5.80, 45.25),
    "oisans_ecrins": (5.85, 44.75, 6.70, 45.20),
    "durance_ubaye": (5.75, 44.10, 6.95, 44.95),
    "alps_overview": (4.70, 43.40, 7.80, 46.50),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1_advection")
    ap.add_argument("--hours", default="14", help="solar hours, comma-separated, e.g. 8,11,14,17,22")
    ap.add_argument("--regions", default=",".join(REGIONS))
    a = ap.parse_args()

    g = dem.load(res=200)
    T = terrain.analyse(g.z, g.res)
    F = np.load(ROOT / "out" / a.tag / "fields.npz")
    sh = F["solar_hour"]
    lines = reference.load()
    out = ROOT / "out" / a.tag / "maps"
    out.mkdir(parents=True, exist_ok=True)
    for h in [float(x) for x in a.hours.split(",")]:
        i = int(np.argmin(np.abs(sh - h)))
        valley = F["valley"][i].astype(np.float32)
        u, v = F["u"][i].astype(np.float32), F["v"][i].astype(np.float32)
        for name in a.regions.split(","):
            bb = REGIONS[name]
            overview = name == "alps_overview"
            path = out / f"{name}_{sh[i]:04.1f}h.png"
            render.plot_region(g, T, valley, u, v, bb,
                               f"{a.tag} — {name} — {sh[i]:.1f} h solar time, 15 July, clear calm day",
                               path, lines, slope_every=12 if overview else 4,
                               min_area_km2=300.0 if overview else 20.0)
            print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
