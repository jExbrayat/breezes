"""Held-out validation set: the hand-drawn breeze map (KML export of Google My
Maps "Brises des Alpes"). Lines are drawn tail -> tip and end with a drawn
closed-triangle arrowhead: ..., tip, barb1, barb2, tip. We keep the shaft."""
from __future__ import annotations

import math
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from pyproj import Transformer

from .dem import CRS, ROOT

KML_URL = "https://www.google.com/maps/d/kml?mid=1LZ-3QtkG48alQEQfushGC6d_bAS9Y7o&forcekml=1"
KML_PATH = ROOT / "data" / "raw" / "reference" / "brises_des_alpes.kml"
NS = {"k": "http://www.opengis.net/kml/2.2"}


@dataclass
class RefLine:
    region: str
    name: str
    color: str
    lonlat: np.ndarray       # shaft vertices, tail -> tip (N, 2)
    xy: np.ndarray           # same in Lambert-93
    head_ok: bool            # arrowhead found and pointing forward


def fetch(path: Path = KML_PATH) -> Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(KML_URL, path)
    return path


def _km(a, b):
    return math.hypot((a[0] - b[0]) * 111.32 * math.cos(math.radians(a[1])), (a[1] - b[1]) * 110.57)


def _strip_head(P):
    """Return (shaft, ok). Head = closed triangle: P[-4]=tip, P[-3], P[-2]=barbs, P[-1]~tip."""
    if len(P) >= 5 and _km(P[-4], P[-1]) < 0.05:
        tip, b1, b2 = P[-4], P[-3], P[-2]
        shaft = P[:-3]
        d = np.subtract(tip, shaft[-2])
        back = np.subtract((np.add(b1, b2)) / 2, tip)
        return shaft, float(np.dot(d, back)) < 0
    return P, False


def load() -> list[RefLine]:
    root = ET.parse(fetch()).getroot()
    to_l93 = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    out = []
    for folder in root.find("k:Document", NS).findall("k:Folder", NS):
        region = folder.findtext("k:name", namespaces=NS).strip()
        for pm in folder.findall(".//k:Placemark", NS):
            ls = pm.find(".//k:LineString/k:coordinates", NS)
            if ls is None:
                continue
            P = [tuple(map(float, c.split(",")[:2])) for c in ls.text.split()]
            shaft, ok = _strip_head(P)
            ll = np.array(shaft)
            x, y = to_l93.transform(ll[:, 0], ll[:, 1])
            style = (pm.findtext("k:styleUrl", namespaces=NS) or "").split("-")
            out.append(RefLine(region=region, name=(pm.findtext("k:name", namespaces=NS) or "").strip(),
                               color=style[1] if len(style) > 1 else "", lonlat=ll,
                               xy=np.column_stack([x, y]), head_ok=ok))
    return out


def sample(lines: list[RefLine], step_m: float = 400.0):
    """Points every `step_m` along each shaft with the drawn direction (unit e/n)."""
    rows = []
    for i, L in enumerate(lines):
        if not L.head_ok:
            continue
        for a, b in zip(L.xy[:-1], L.xy[1:]):
            seg = b - a
            n = np.hypot(*seg)
            if n < 1:
                continue
            k = max(1, int(n // step_m))
            for t in (np.arange(k) + 0.5) / k:
                p = a + t * seg
                rows.append((i, p[0], p[1], seg[0] / n, seg[1] / n))
    return np.array(rows)
