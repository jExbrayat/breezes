"use strict";
// Alpine Breeze Atlas — localhost viewer for model runs exported by scripts/export_web.py.

const IGN = (layer, fmt) =>
  "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=" + layer +
  "&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=" + fmt;
const BASES = {
  "OpenTopoMap": L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
    subdomains: "abc", maxZoom: 17,
    attribution: "Map data © OpenStreetMap contributors, SRTM · Style © OpenTopoMap (CC-BY-SA)" }),
  "IGN Plan": L.tileLayer(IGN("GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2", "image/png"), {
    maxZoom: 19, attribution: "© IGN – Géoplateforme" }),
  "IGN orthophoto": L.tileLayer(IGN("ORTHOIMAGERY.ORTHOPHOTOS", "image/jpeg"), {
    maxZoom: 19, attribution: "© IGN – Géoplateforme" }),
  "Esri shaded relief": L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}", {
    maxZoom: 13, attribution: "Tiles © Esri" }),
};
const PARTICLE_INK = { dark: "rgba(18, 30, 58, 0.85)", light: "rgba(255, 255, 255, 0.9)" };
const PX_PER_MS = 0.8;           // particle screen speed per frame, per m/s of wind
const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const state = {
  runs: [], meta: null, field: null, valley: null, hour: 0, playTimer: null,
  show: { arrows: true, particles: !REDUCED_MOTION, ref: true, agree: false },
  particleInk: PARTICLE_INK.dark,
};
const $ = (id) => document.getElementById(id);
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

// ------------------------------------------------------------------ map
const map = L.map("map", { zoomAnimation: false, minZoom: 7, maxZoom: 16 }).setView([45.45, 6.15], 9);
Object.values(BASES).forEach((t) => t.setOpacity(0.55));   // faded so winds read on top
BASES["OpenTopoMap"].addTo(map);
L.control.layers(BASES, null, { position: "topright" }).addTo(map);
L.control.scale({ imperial: false }).addTo(map);
map.on("baselayerchange", (e) => {
  state.particleInk = e.name === "IGN orthophoto" ? PARTICLE_INK.light : PARTICLE_INK.dark;
});
map.createPane("particles").style.zIndex = 390;
map.createPane("arrows").style.zIndex = 395;

// A canvas pinned to the map container, redrawn on view changes.
const CanvasLayer = L.Layer.extend({
  initialize(pane, draw) { this._paneName = pane; this._draw = draw; },
  onAdd(m) {
    this.canvas = L.DomUtil.create("canvas", "", m.getPane(this._paneName));
    this.canvas.style.pointerEvents = "none";
    this.ctx = this.canvas.getContext("2d");
    m.on("move zoom resize viewreset", this.reset, this);
    this.reset();
  },
  onRemove(m) { L.DomUtil.remove(this.canvas); m.off("move zoom resize viewreset", this.reset, this); },
  reset() {
    const s = map.getSize(), dpr = window.devicePixelRatio || 1;
    if (this.w !== s.x || this.h !== s.y) {
      this.w = s.x; this.h = s.y;
      this.canvas.width = s.x * dpr; this.canvas.height = s.y * dpr;
      this.canvas.style.width = s.x + "px"; this.canvas.style.height = s.y + "px";
      this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    L.DomUtil.setPosition(this.canvas, map.containerPointToLayerPoint([0, 0]));
    this._draw(this.ctx, this.w, this.h);
  },
});

// ------------------------------------------------------------ field sampling
function sampleField(lon, lat) {
  const f = state.meta.field, fi = (f.lat0 - lat) / f.dlat, fj = (lon - f.lon0) / f.dlon;
  if (!(fi >= 0 && fj >= 0 && fi < f.ny - 1 && fj < f.nx - 1)) return null;
  const i0 = fi | 0, j0 = fj | 0, a = fi - i0, b = fj - j0, nn = f.nx * f.ny;
  const base = state.hour * 2 * nn + i0 * f.nx + j0, F = state.field;
  const bil = (k) => ((F[k] * (1 - b) + F[k + 1] * b) * (1 - a) +
                      (F[k + f.nx] * (1 - b) + F[k + f.nx + 1] * b) * a) / f.scale;
  return [bil(base), bil(base + nn)];
}

// ------------------------------------------------------------ valley arrows
function drawArrows(ctx, w, h) {
  ctx.clearRect(0, 0, w, h);
  if (!state.show.arrows || !state.meta) return;
  const A = state.meta.arrows, off = state.hour * A.n, z = map.getZoom();
  const minLogA = z <= 8 ? 2.4 : z <= 9 ? 1.7 : z <= 10 ? 1.3 : 1.0;
  const bounds = map.getBounds().pad(0.05), bin = 26, taken = new Set();
  const up = css("--up"), down = css("--down");
  for (let k = 0; k < A.n; k++) {                       // largest catchments first
    if (A.logA[k] < minLogA || !bounds.contains([A.lat[k], A.lon[k]])) continue;
    const p = map.latLngToContainerPoint([A.lat[k], A.lon[k]]);
    const key = ((p.x / bin) | 0) + "," + ((p.y / bin) | 0);
    if (taken.has(key)) continue;
    taken.add(key);
    const s = state.valley[off + k] / 10;
    if (Math.abs(s) < 0.3) {
      ctx.fillStyle = "rgba(90,90,90,0.6)";
      ctx.beginPath(); ctx.arc(p.x, p.y, 1.8, 0, 2 * Math.PI); ctx.fill();
      continue;
    }
    const sg = Math.sign(s), de = -A.ae[k] * sg, dn = -A.an[k] * sg;   // up-valley = -axis
    const len = Math.min(36, 7 + 2.4 * Math.abs(s)), lw = 1.2 + 0.8 * Math.max(0, A.logA[k] - 1);
    const x0 = p.x - de * len / 2, y0 = p.y + dn * len / 2, x1 = p.x + de * len / 2, y1 = p.y - dn * len / 2;
    const hs = 3 + lw * 1.6;
    const head = () => {
      ctx.beginPath();
      ctx.moveTo(x1 + de * hs * 0.6, y1 - dn * hs * 0.6);
      ctx.lineTo(x1 - de * hs + dn * hs * 0.6, y1 + dn * hs + de * hs * 0.6);
      ctx.lineTo(x1 - de * hs - dn * hs * 0.6, y1 + dn * hs - de * hs * 0.6);
      ctx.closePath();
    };
    ctx.lineCap = "round";
    ctx.strokeStyle = "rgba(255,255,255,0.85)"; ctx.lineWidth = lw + 2.4;
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
    head(); ctx.lineWidth = 2.4; ctx.stroke();
    ctx.strokeStyle = ctx.fillStyle = s > 0 ? up : down; ctx.lineWidth = lw;
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
    head(); ctx.fill();
  }
}

// ---------------------------------------------------------------- particles
const P = { list: [], lonW: 0, lonE: 0, latOfY: null, w: 0, h: 0, moving: false };
function seed(p) {
  p.x = Math.random() * P.w; p.y = Math.random() * P.h;
  p.age = 0; p.life = 40 + Math.random() * 90;
}
function resetParticles(ctx, w, h) {
  ctx.clearRect(0, 0, w, h);
  P.w = w; P.h = h;
  P.lonW = map.containerPointToLatLng([0, 0]).lng;
  P.lonE = map.containerPointToLatLng([w, 0]).lng;
  P.latOfY = new Float64Array(h + 1);
  for (let y = 0; y <= h; y++) P.latOfY[y] = map.containerPointToLatLng([0, y]).lat;
  const n = Math.min(5000, Math.round((w * h) / 450));
  while (P.list.length < n) { const p = {}; seed(p); P.list.push(p); }
  P.list.length = n;
  P.list.forEach(seed);
}
function stepParticles() {
  requestAnimationFrame(stepParticles);
  const layer = particleLayer, ctx = layer.ctx;
  if (!state.meta || !state.show.particles || P.moving || !P.latOfY) return;
  ctx.globalCompositeOperation = "destination-in";
  ctx.fillStyle = "rgba(0,0,0,0.95)";
  ctx.fillRect(0, 0, P.w, P.h);
  ctx.globalCompositeOperation = "source-over";
  ctx.strokeStyle = state.particleInk; ctx.lineWidth = 1.6;
  ctx.beginPath();
  for (const p of P.list) {
    const yi = p.y | 0;
    const uv = (yi >= 0 && yi <= P.h && p.x >= 0 && p.x <= P.w)
      ? sampleField(P.lonW + (p.x / P.w) * (P.lonE - P.lonW), P.latOfY[yi]) : null;
    if (!uv || ++p.age > p.life || Math.hypot(uv[0], uv[1]) < 0.15) { seed(p); continue; }
    const nx = p.x + uv[0] * PX_PER_MS, ny = p.y - uv[1] * PX_PER_MS;
    ctx.moveTo(p.x, p.y); ctx.lineTo(nx, ny);
    p.x = nx; p.y = ny;
  }
  ctx.stroke();
}

const arrowLayer = new CanvasLayer("arrows", drawArrows);
const particleLayer = new CanvasLayer("particles", resetParticles);
arrowLayer.addTo(map);
particleLayer.addTo(map);
map.on("movestart", () => { P.moving = true; particleLayer.ctx.clearRect(0, 0, P.w, P.h); });
map.on("moveend", () => { P.moving = false; particleLayer.reset(); });
requestAnimationFrame(stepParticles);

// ------------------------------------------------------------ pilots' lines
// Each line is sampled every 400 m; each sample is classed per hour:
// 1 agree (within 45°), 0 across or calm, -1 opposite (135° or more off).
const refGroup = L.layerGroup().addTo(map);
const sampleGroup = L.layerGroup();
const sampleRenderer = L.canvas({ padding: 0.3 });
let refItems = [], sampleSegs = [];
const sampleClass = (k) => state.samples[state.hour * state.meta.samples.n + k];
const classColor = (c) => (c === 1 ? css("--good") : c === -1 ? css("--bad") : css("--mid"));
function refTooltip(item) {
  let agree = 0, across = 0, opp = 0;
  for (const k of item.samples) {
    const c = sampleClass(k);
    if (c === 1) agree++; else if (c === -1) opp++; else across++;
  }
  const n = item.samples.length;
  const crit = state.meta.criteria;
  return `<div class="ref-tip"><b>${item.line.name || "(unnamed)"}</b><br>${item.line.region}<br>` +
    `At ${$("clock-solar").textContent} solar, ${n} points:<br>` +
    `<span class="good">${agree} agree</span> (≤ ${crit.agree_deg}°) · ${across} across/calm · ` +
    `<span class="bad">${opp} opposite</span> (≥ ${crit.opposite_deg}°)</div>`;
}
function arrowHead(coords) {
  const tip = map.latLngToLayerPoint(coords[coords.length - 1]);
  const prev = map.latLngToLayerPoint(coords[coords.length - 2]);
  const d = tip.subtract(prev), n = Math.hypot(d.x, d.y) || 1, ux = d.x / n, uy = d.y / n, s = 11;
  const pts = [[tip.x + ux * 3, tip.y + uy * 3],
               [tip.x - ux * s + uy * s * 0.55, tip.y - uy * s - ux * s * 0.55],
               [tip.x - ux * s - uy * s * 0.55, tip.y - uy * s + ux * s * 0.55]];
  return pts.map((q) => map.layerPointToLatLng(q));
}
function buildRef() {
  refGroup.clearLayers();
  sampleGroup.clearLayers();
  refItems = state.meta.ref.map((line) => {
    const item = { line, samples: [] };
    item.casing = L.polyline(line.coords, { color: "#1b1b1b", weight: 6, opacity: 0.55, interactive: false });
    item.main = L.polyline(line.coords, { color: css("--ref"), weight: 3.2, opacity: 1 });
    item.head = L.polygon(arrowHead(line.coords), { color: "#1b1b1b", weight: 1.2, fillColor: css("--ref"),
                                                   fillOpacity: 1, interactive: false });
    item.main.bindTooltip(() => refTooltip(item), { sticky: true });
    [item.casing, item.main, item.head].forEach((l) => refGroup.addLayer(l));
    return item;
  });
  const S = state.meta.samples;
  sampleSegs = [];
  for (let k = 0; k < S.n; k++) {
    refItems[S.line[k]].samples.push(k);
    const seg = L.polyline([[S.lat0[k], S.lon0[k]], [S.lat1[k], S.lon1[k]]],
      { renderer: sampleRenderer, weight: 5, opacity: 1, lineCap: "butt", interactive: false });
    sampleSegs.push(seg);
    sampleGroup.addLayer(seg);
  }
  styleRef();
}
function styleRef() {
  const agree = state.show.agree;
  for (const it of refItems) {
    it.main.setStyle({ color: agree ? "#1b1b1b" : css("--ref"), weight: agree ? 1.5 : 3.2 });
    it.casing.setStyle({ opacity: agree ? 0 : 0.55 });
    it.head.setStyle({ fillColor: agree ? "#1b1b1b" : css("--ref") });
  }
  if (agree) {
    sampleSegs.forEach((seg, k) => seg.setStyle({ color: classColor(sampleClass(k)) }));
    if (state.show.ref) sampleGroup.addTo(map);
  } else {
    sampleGroup.remove();
  }
}
map.on("zoomend", () => refItems.forEach((it) => it.head.setLatLngs(arrowHead(it.line.coords))));

// ------------------------------------------------------------ time controls
const fmtClock = (h) => {
  const m = Math.round(h * 60) % 1440;
  return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0");
};
function setHour(i) {
  const H = state.meta.hours.length;
  state.hour = ((i % H) + H) % H;
  $("hour").value = state.hour;
  $("clock-solar").textContent = fmtClock(state.meta.hours[state.hour]);
  $("clock-cest").textContent = state.meta.cest[state.hour] + " CEST";
  arrowLayer.reset();
  styleRef();
  drawCycle();
}
let cycleStats = null;
function computeCycle() {
  const A = state.meta.arrows, H = state.meta.hours.length;
  cycleStats = [];
  for (let h = 0; h < H; h++) {
    let up = 0, down = 0, n = 0;
    for (let k = 0; k < A.n; k++) {
      if (A.logA[k] < 1.3) continue;
      const s = state.valley[h * A.n + k] / 10;
      n++; if (s > 0.3) up++; else if (s < -0.3) down++;
    }
    cycleStats.push([up / n, down / n]);
  }
}
function drawCycle() {
  const cv = $("cycle"), dpr = window.devicePixelRatio || 1, w = cv.clientWidth, h = 64;
  cv.width = w * dpr; cv.height = h * dpr;
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  if (!cycleStats) return;
  const H = cycleStats.length, bw = w / H, mid = 27, amp = 24;
  ctx.fillStyle = css("--line"); ctx.fillRect(0, mid, w, 1);
  cycleStats.forEach(([u, d], i) => {
    ctx.globalAlpha = i === state.hour ? 1 : 0.55;
    ctx.fillStyle = css("--up"); ctx.fillRect(i * bw + 1, mid - u * amp, bw - 2, u * amp);
    ctx.fillStyle = css("--down"); ctx.fillRect(i * bw + 1, mid + 1, bw - 2, d * amp);
  });
  ctx.globalAlpha = 1;
  ctx.strokeStyle = css("--fg"); ctx.lineWidth = 1.5;
  ctx.strokeRect(state.hour * bw + 0.5, 1, bw - 1, mid + amp + 2);
  ctx.fillStyle = css("--dim"); ctx.font = "11px 'IBM Plex Mono', monospace"; ctx.textAlign = "center";
  [0, 6, 12, 18].forEach((t) => {
    const i = state.meta.hours.findIndex((x) => Math.round(x) === t);
    if (i >= 0) ctx.fillText(t + "h", i * bw + bw / 2, h - 2);
  });
}
$("cycle").addEventListener("click", (e) => {
  const r = e.currentTarget.getBoundingClientRect();
  setHour(Math.floor(((e.clientX - r.left) / r.width) * state.meta.hours.length));
});
$("hour").addEventListener("input", (e) => setHour(+e.target.value));
$("play").addEventListener("click", () => {
  const btn = $("play");
  if (state.playTimer) {
    clearInterval(state.playTimer); state.playTimer = null;
    btn.textContent = "▶"; btn.classList.remove("playing"); btn.setAttribute("aria-label", "Play the day");
  } else {
    state.playTimer = setInterval(() => setHour(state.hour + 1), 1100);
    btn.textContent = "❚❚"; btn.classList.add("playing"); btn.setAttribute("aria-label", "Pause");
  }
});

// ------------------------------------------------------------ layer toggles
function bindToggle(id, key, onChange) {
  const el = $(id);
  el.checked = state.show[key];
  el.addEventListener("change", () => { state.show[key] = el.checked; onChange(); });
}
bindToggle("show-arrows", "arrows", () => arrowLayer.reset());
bindToggle("show-particles", "particles", () => particleLayer.reset());
bindToggle("show-ref", "ref", () => {
  if (state.show.ref) refGroup.addTo(map); else refGroup.remove();
  styleRef();
  if (!state.show.ref) sampleGroup.remove();
});
bindToggle("show-agree", "agree", styleRef);

$("collapse").addEventListener("click", () => {
  $("panel").classList.add("collapsed"); $("expand").hidden = false; map.invalidateSize();
});
$("expand").addEventListener("click", () => {
  $("panel").classList.remove("collapsed"); $("expand").hidden = true; map.invalidateSize();
});

// ------------------------------------------------------------ click popup
const COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
map.on("click", (e) => {
  if (!state.meta) return;
  const uv = sampleField(e.latlng.lng, e.latlng.lat);
  let html;
  if (!uv) html = "Outside the model domain.";
  else {
    const sp = Math.hypot(uv[0], uv[1]);
    if (sp < 0.3) html = `Calm (< 0.3 m/s) at ${fmtClock(state.meta.hours[state.hour])} solar.`;
    else {
      const to = (Math.atan2(uv[0], uv[1]) * 180 / Math.PI + 360) % 360;
      const from = COMPASS[Math.round(((to + 180) % 360) / 22.5) % 16];
      html = `<b>${sp.toFixed(1)} m/s</b> from <b>${from}</b> (blowing toward ${COMPASS[Math.round(to / 22.5) % 16]})` +
        `<br><span class="dim">near-surface flow, ~1 km average, ${fmtClock(state.meta.hours[state.hour])} solar</span>`;
    }
  }
  L.popup({ className: "wind-popup" }).setLatLng(e.latlng).setContent(html).openOn(map);
});

// ------------------------------------------------------------ scores
function renderScores() {
  const tb = document.querySelector("#scores tbody");
  tb.innerHTML = "";
  const S = state.meta.scores;
  const keys = ["ALL", ...Object.keys(S).filter((k) => k !== "ALL").sort()];
  const pct = (x) => Math.round(x * 100) + "%";
  const isNaive = state.meta.params._model === "naive";
  for (const k of keys) {
    const m = S[k].model, b = S[k].baseline;
    // higher agree is better; lower opposite is better
    const ca = isNaive ? "" : m.agree > b.agree + 0.01 ? "win" : m.agree < b.agree - 0.01 ? "lose" : "";
    const co = isNaive ? "" : m.opposite < b.opposite - 0.01 ? "win" : m.opposite > b.opposite + 0.01 ? "lose" : "";
    const tr = document.createElement("tr");
    if (k === "ALL") tr.className = "all";
    tr.innerHTML = `<td>${k === "ALL" ? "All regions" : k}</td><td class="num">${m.n}</td>` +
      `<td class="num"><span class="${ca}">${pct(m.agree)}</span></td><td class="num dim">${pct(b.agree)}</td>` +
      `<td class="num"><span class="${co}">${pct(m.opposite)}</span></td><td class="num dim">${pct(b.opposite)}</td>`;
    tb.appendChild(tr);
  }
}

// ------------------------------------------------------------ loading
async function loadRun(tag) {
  const base = `data/${tag}/`;
  const [meta, field, valley, samples] = await Promise.all([
    fetch(base + "meta.json").then((r) => r.json()),
    fetch(base + "field.bin").then((r) => r.arrayBuffer()),
    fetch(base + "valley.bin").then((r) => r.arrayBuffer()),
    fetch(base + "samples.bin").then((r) => r.arrayBuffer()),
  ]);
  state.meta = meta; state.field = new Int8Array(field); state.valley = new Int8Array(valley);
  state.samples = new Int8Array(samples);
  const kind = meta.params._model;
  $("run-date").textContent = kind === "naive"
    ? `Naive rule, no physics: along the nearest valley, up-valley while the sun is up · ${meta.date}`
    : kind === "arome"
    ? `AROME HD (1.3 km) 10 m wind · mean of ${meta.params.days.length} clear calm July days: ${meta.params.days.join(", ")}`
    : `Physical model · simulated day ${meta.date} · clear sky, no synoptic wind`;
  $("hour").max = meta.hours.length - 1;
  computeCycle();
  renderScores();
  buildRef();
  if (!state.show.ref) refGroup.remove();
  let best = 0;
  meta.hours.forEach((h, i) => { if (Math.abs(h - 14.3) < Math.abs(meta.hours[best] - 14.3)) best = i; });
  setHour(state.loadedOnce ? state.hour : best);       // keep the hour when switching runs
  state.loadedOnce = true;
  particleLayer.reset();
}

async function init() {
  try {
    state.runs = await fetch("data/runs.json").then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); });
  } catch (err) {
    $("run-date").textContent = location.protocol === "file:"
      ? "Open this page through the local server: uv run python scripts/serve.py"
      : "No exported runs found. Run: uv run python scripts/serve.py";
    return;
  }
  const sel = $("run");
  for (const r of state.runs) {
    const o = document.createElement("option");
    o.value = r.tag;
    o.textContent = `${r.tag} · agree ${Math.round(r.agree * 100)}% · opposite ${Math.round(r.opposite * 100)}%`;
    sel.appendChild(o);
  }
  sel.addEventListener("change", () => loadRun(sel.value));
  if (state.runs.length) await loadRun(state.runs[0].tag);
}
window.addEventListener("resize", drawCycle);
init();
