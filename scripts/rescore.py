"""Re-score saved runs (out/<tag>/fields.npz) with the current validation metrics."""
import argparse
import json

import numpy as np

from breezes import dem, reference, terrain, validate
from breezes.dem import ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tags", nargs="*", help="run tags (default: all runs in out/)")
    tags = ap.parse_args().tags or sorted(p.parent.name for p in (ROOT / "out").glob("*/fields.npz"))
    g = dem.load(res=200)
    T = terrain.analyse(g.z, g.res)
    lines = reference.load()
    S = reference.sample(lines)
    summary = []
    for tag in tags:
        run = ROOT / "out" / tag
        F = np.load(run / "fields.npz")
        aft = (F["solar_hour"] >= 13) & (F["solar_hour"] <= 16)
        u = F["u"][aft].astype(np.float32).mean(0)
        v = F["v"][aft].astype(np.float32).mean(0)
        sc = validate.score(g, T, S, lines, u, v)
        (run / "validation.txt").write_text(validate.report(sc) + "\n")
        (run / "validation.json").write_text(json.dumps(sc, indent=1))
        m = sc["ALL"]["model"]
        summary.append(f"{tag:24s} agree {m['agree']:.2f}  opposite {m['opposite']:.2f}  "
                       f"across/calm {m['across']:.2f}  (legacy sign {m['sign']:.2f})")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
