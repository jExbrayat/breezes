"""AROME baseline — operational NWP 10 m wind, used as a model to compare against.

Composite of clear, calm July days (scripts/fetch_arome.py) taken as if it were
the idealised calm day of the physics model. The 0.01 deg lat/lon field is
interpolated bilinearly to the 200 m Lambert-93 grid (no added detail: AROME HD
is ~1.3 km) and rotated from true north to grid north. valley_speed is the
projection on the D8 valley axis, on channels.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from pyproj import Transformer
from scipy import ndimage

from . import solar
from .dem import CRS, PROC, Grid
from .model import Snapshot
from .terrain import Terrain

COMPOSITE = PROC / "arome_hd_composite.npz"


@dataclass
class AromeModel:
    grid: Grid
    terrain: Terrain
    lon: float
    path: Path = COMPOSITE

    def __post_init__(self):
        A = np.load(self.path)
        self.days = [str(d) for d in A["days"]]
        self.U, self.V = A["u"], A["v"]
        lat, lon = A["lat"], A["lon"]
        x, y = self.grid.xy()
        X, Y = np.meshgrid(x, y)
        to84 = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True)
        LON, LAT = to84.transform(X, Y)
        self.idx = [(LAT - lat[0]) / (lat[1] - lat[0]), (LON - lon[0]) / (lon[1] - lon[0])]
        # grid bearing of true north, per cell
        to93 = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
        x1, y1 = to93.transform(LON, LAT + 0.001)
        th = np.arctan2(x1 - X, y1 - Y)
        self.cos, self.sin = np.cos(th).astype(np.float32), np.sin(th).astype(np.float32)

    def run(self, day: datetime, **_):
        """Hourly snapshots; UTC hours of the composite placed on calendar day `day`."""
        T = self.terrain
        t0 = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        zeros = np.zeros(self.grid.shape, np.float32)
        out = []
        for h in range(24):
            t = t0 + timedelta(hours=h)
            ue = ndimage.map_coordinates(self.U[h], self.idx, order=1, mode="nearest").astype(np.float32)
            vn = ndimage.map_coordinates(self.V[h], self.idx, order=1, mode="nearest").astype(np.float32)
            u = ue * self.cos + vn * self.sin           # true -> grid frame
            v = vn * self.cos - ue * self.sin
            valley = np.where(T.chan, -(u * T.axis_e + v * T.axis_n), np.nan).astype(np.float32)
            out.append(Snapshot(time=t, solar_hour=solar.solar_time_hours(t, self.lon), H=zeros,
                                slope_u=zeros, slope_v=zeros, valley_speed=valley, u=u, v=v,
                                z_m=zeros, z_c=zeros))
        return out
