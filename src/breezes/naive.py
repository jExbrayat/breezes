"""Naive reference model — no physics, the bar to beat.

The breeze blows along the nearest valley axis at a fixed speed: up-valley
while the sun is up, down-valley otherwise. Every cell takes the axis of the
drainage cell it drains to (same as the baseline in validate.score), so its
afternoon score equals that baseline exactly.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np

from . import solar
from .dem import Grid
from .model import Snapshot
from .terrain import Terrain


@dataclass
class NaiveModel:
    grid: Grid
    terrain: Terrain
    lat: float
    lon: float
    speed: float = 3.0

    def __post_init__(self):
        T = self.terrain
        tgt = T.tgt.ravel()
        ok = tgt >= 0
        t0 = np.maximum(tgt, 0)
        # up-valley unit vector of the nearest drainage cell, per cell
        self.up_e = np.where(ok, -T.axis_e.ravel()[t0], 0).reshape(self.grid.shape).astype(np.float32)
        self.up_n = np.where(ok, -T.axis_n.ravel()[t0], 0).reshape(self.grid.shape).astype(np.float32)
        self.chan = T.chan

    def run(self, day: datetime, **_):
        """Hourly snapshots for the UTC calendar day `day`."""
        t0 = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        zeros = np.zeros(self.grid.shape, np.float32)
        out = []
        for h in range(24):
            t = t0 + timedelta(hours=h)
            elev, _ = solar.sun_position(t, self.lat, self.lon)
            sgn = 1.0 if elev > 0 else -1.0
            valley = np.where(self.chan, sgn * self.speed, np.nan).astype(np.float32)
            out.append(Snapshot(time=t, solar_hour=solar.solar_time_hours(t, self.lon), H=zeros,
                                slope_u=zeros, slope_v=zeros, valley_speed=valley,
                                u=sgn * self.speed * self.up_e, v=sgn * self.speed * self.up_n,
                                z_m=zeros, z_c=zeros))
        return out
