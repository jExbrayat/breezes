"""Full French-Alps diurnal run: model -> cached fields -> validation report."""
import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from breezes import arome, dem, model, naive, reference, terrain, validate
from breezes.dem import ROOT

OUT = ROOT / "out"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=float, default=200.0)
    ap.add_argument("--date", default="2026-07-15")
    ap.add_argument("--tag", default="baseline")
    ap.add_argument("--model", choices=["physics", "naive", "arome"], default="physics")
    a = ap.parse_args()

    g = dem.load(res=a.res)
    T = terrain.analyse(g.z, g.res)
    if a.model == "naive":
        m = naive.NaiveModel(g, T, lat=45.3, lon=6.3)
        params = {"speed": m.speed}
    elif a.model == "arome":
        m = arome.AromeModel(g, T, lon=6.3)
        params = {"source": "AROME France HD 10 m wind, composite of clear calm days", "days": m.days}
    else:
        m = model.BreezeModel(g, T, lat=45.3, lon=6.3)
        params = asdict(m.p)
    day = datetime.fromisoformat(a.date).replace(tzinfo=timezone.utc)
    snaps = m.run(day)

    run_dir = OUT / a.tag
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "params.json").write_text(json.dumps(
        {**params, "_model": a.model, "_date": a.date, "_res": a.res}, indent=1))
    np.savez_compressed(run_dir / "fields.npz",
                        solar_hour=np.array([s.solar_hour for s in snaps]),
                        u=np.stack([s.u for s in snaps]).astype(np.float16),
                        v=np.stack([s.v for s in snaps]).astype(np.float16),
                        valley=np.stack([s.valley_speed for s in snaps]).astype(np.float16),
                        H=np.stack([s.H for s in snaps]).astype(np.float16))

    lines = reference.load()
    S = reference.sample(lines)
    aft = [s for s in snaps if 13.0 <= s.solar_hour <= 16.0]
    u = np.mean([s.u for s in aft], 0)
    v = np.mean([s.v for s in aft], 0)
    sc = validate.score(g, T, S, lines, u, v)
    txt = validate.report(sc)
    print(f"afternoon (13-16 h solar, {len(aft)} snapshots)\n{txt}")
    (run_dir / "validation.txt").write_text(txt + "\n")
    (run_dir / "validation.json").write_text(json.dumps(sc, indent=1))


if __name__ == "__main__":
    main()
