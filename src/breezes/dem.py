"""DEM acquisition: Copernicus GLO-90 tiles from AWS (no key), mosaicked and
reprojected to Lambert-93 (EPSG:2154) on a regular grid."""
from __future__ import annotations

import math
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject, transform_bounds

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "dem"
PROC = ROOT / "data" / "processed"

TILE_URL = ("https://copernicus-dem-90m.s3.amazonaws.com/"
            "Copernicus_DSM_COG_30_{ns}{lat:02d}_00_{ew}{lon:03d}_00_DEM/"
            "Copernicus_DSM_COG_30_{ns}{lat:02d}_00_{ew}{lon:03d}_00_DEM.tif")

CRS = "EPSG:2154"

# French Alps + margins (Rhône plain to the W, Po-side ridges to the E).
ALPS_BBOX = (4.6, 43.3, 7.9, 46.6)  # lon_min, lat_min, lon_max, lat_max


@dataclass
class Grid:
    """A DEM on a regular projected grid. Row 0 is the northern edge."""
    z: np.ndarray            # elevation [m], float32, NaN = no data
    transform: rasterio.Affine
    crs: str = CRS

    @property
    def res(self) -> float:
        return self.transform.a

    @property
    def shape(self):
        return self.z.shape

    def xy(self):
        """Cell-centre coordinates (x 1-D, y 1-D) in the grid CRS."""
        ny, nx = self.z.shape
        x = self.transform.c + (np.arange(nx) + 0.5) * self.transform.a
        y = self.transform.f + (np.arange(ny) + 0.5) * self.transform.e
        return x, y


def _tile_path(lat: int, lon: int) -> Path:
    ns, ew = ("N" if lat >= 0 else "S"), ("E" if lon >= 0 else "W")
    return RAW / f"cop90_{ns}{abs(lat):02d}_{ew}{abs(lon):03d}.tif"


def fetch_tiles(bbox=ALPS_BBOX) -> list[Path]:
    lon0, lat0, lon1, lat1 = bbox
    RAW.mkdir(parents=True, exist_ok=True)
    paths = []
    for lat in range(math.floor(lat0), math.ceil(lat1)):
        for lon in range(math.floor(lon0), math.ceil(lon1)):
            p = _tile_path(lat, lon)
            if not p.exists():
                url = TILE_URL.format(ns="N" if lat >= 0 else "S", lat=abs(lat),
                                      ew="E" if lon >= 0 else "W", lon=abs(lon))
                try:
                    urllib.request.urlretrieve(url, p)
                except urllib.error.HTTPError as e:  # sea-only tiles do not exist
                    if e.code in (403, 404):
                        continue
                    raise
            paths.append(p)
    return paths


def load(bbox=ALPS_BBOX, res: float = 200.0) -> Grid:
    """Mosaic + reproject to Lambert-93 at `res` metres. Cached as GeoTIFF."""
    key = "_".join(f"{v:g}" for v in bbox)
    out = PROC / f"dem_l93_{int(res)}m_{key}.tif"
    if out.exists():
        with rasterio.open(out) as ds:
            z = ds.read(1).astype(np.float32)
            z[z == ds.nodata] = np.nan
            return Grid(z, ds.transform)

    srcs = [rasterio.open(p) for p in fetch_tiles(bbox)]
    mosaic, mtrans = merge(srcs, bounds=bbox)
    src_crs = srcs[0].crs
    for s in srcs:
        s.close()

    x0, y0, x1, y1 = transform_bounds("EPSG:4326", CRS, *bbox)
    x0, y0 = math.floor(x0 / res) * res, math.floor(y0 / res) * res
    x1, y1 = math.ceil(x1 / res) * res, math.ceil(y1 / res) * res
    nx, ny = int((x1 - x0) / res), int((y1 - y0) / res)
    transform = from_origin(x0, y1, res, res)
    z = np.full((ny, nx), np.nan, np.float32)
    reproject(mosaic[0].astype(np.float32), z, src_transform=mtrans, src_crs=src_crs,
              dst_transform=transform, dst_crs=CRS, resampling=Resampling.average,
              src_nodata=np.nan, dst_nodata=np.nan)
    # Copernicus DSM uses 0 m on sea; treat the Mediterranean as sea level, keep it.
    PROC.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out, "w", driver="GTiff", height=ny, width=nx, count=1,
                       dtype="float32", crs=CRS, transform=transform, nodata=-9999,
                       compress="deflate") as ds:
        ds.write(np.where(np.isnan(z), -9999, z), 1)
    return Grid(z, transform)
