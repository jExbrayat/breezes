# breezes — thermal breezes of the French Alps from topography

Goal: derive thermally driven breezes (slope winds + valley winds, day & night)
**algorithmically from a DEM**, as a *general* physical model, then check it
against breezes the user and paragliding pilots know in the French Alps.

- **Phase 1 (current):** topographic breezes only — uniform surface properties.
- **Phase 2 (later):** surface-contrast ("albedo") breezes — lakes, glaciers,
  snow, forest vs meadow vs rock, urban. Plugs in through the surface energy
  balance (`albedo` / sensible-heat fraction become rasters); the wind physics
  must not change.

## Golden rule: no overfitting
- Parameters live in `src/breezes/params.py` and must come from the
  literature (`docs/physics_notes.md`), each with a source or an explicit
  "estimate" tag. **Never tune a parameter to the validation map.**
- The validation map (Franck Largeault's "Brises des Alpes", Google My Maps
  `mid=1LZ-3QtkG48alQEQfushGC6d_bAS9Y7o`) is **held out**: used only to score.
  If a structural change is motivated by a validation failure, write it down
  in TODO.md ("motivated by …") and re-score on a region it was not motivated by.
- Prefer structural/physical fixes over per-region special cases. No
  hard-coded place names in model code.
- **Scoring (user decision):** per reference sample, agree = within 45°,
  opposite = 135° or more off, across/calm otherwise (`validate.py`).
  **The objective is opposite = 0** — a breeze modelled in the opposite
  direction is the one unacceptable error; across is tolerated. Always compare
  against the naive run (`run_alps.py --model naive`: up the nearest valley).

## Layout
```
src/breezes/
  dem.py        Copernicus GLO-90 (AWS, no key) -> Lambert-93 grid (cached GeoTIFF)
  terrain.py    slope/aspect, priority-flood, D8 (down & up-slope), accumulation,
                channels, HAND, valley axis   [numba]
  solar.py      sun position (NOAA), cast shadows, sky-view factor  [numba]
  params.py     all physical parameters (sourced)
  model.py      heat flux -> slope winds + hypsometric valley-wind model, diurnal loop
  reference.py  validation KML (direction from drawn closed-triangle arrowheads)
  validate.py   direction scores per region + naive up-valley baseline
  render.py     static PNG maps
scripts/        run_alps.py, serve.py, export_web.py, plot_maps.py
web/            localhost viewer (index.html, app.js, style.css; data/ is generated)
docs/           physics_notes.md, data_sources.md (literature / data research)
data/raw, data/processed   downloads & caches (not source; regenerate)
out/            figures, maps
```

## Model in one paragraph
H(x,t) = sensible fraction × net radiation (clear-sky beam on slope with cast
shadows, diffuse × sky-view, net LW × sky-view). **Slope winds**:
u = (B·x·sinα/c)^(1/3), B = gH/(ρ c_p θ0), fetch x from upslope routing by day
(paths converge on ridges) and downslope routing at night. **Valley winds**:
heat accumulated over a Gaussian footprint (σ ≈ valley half-width) fills the air
volume below each level in a stratified atmosphere (γ) → mixed-layer top z_m(x)
(generalised TAF: less air → z_m rises faster; flat terrain reduces to the
encroachment CBL model). Hydrostatic pressure at fixed height gives, at the
valley floor z_f: F = (gγ/θ0)(z_m − z_f)∇z_m by day and the cold-pool analogue
−(gΓ_n/θ0)(z_c − z_f)∇z_c at night. F is projected on the D8 valley axis and
drives du/dt = F − (C_D/h)|u|u − u/τ. Morning heat first erodes the cold pool
(lagged morning reversal); evening residual heat decays with τ_res.
Mountain–plain wind and through-valley convergences emerge from the same ∇z_m.

## Conventions
- Grid: EPSG:2154, row 0 = north, x east / y north. Bearings in radians
  clockwise from *grid* north; sun azimuth corrected for meridian convergence.
- Wind vectors are the direction the air moves *to* (east, north components).
  `valley_speed` > 0 = up-valley.
- Times: model runs in UTC; report in **true solar time** (breeze physics).
- Default case: clear, calm (anticyclonic) summer day, 15 July.

## Commands
```
uv run python scripts/run_alps.py --tag <run>      # full Alps run -> out/<run>/ + validation
uv run python scripts/serve.py                     # export new runs, serve web/ on :8000
uv run python scripts/plot_maps.py --tag <run>     # static regional PNGs
```
Full 200 m Alps run: ~3–4 min (hypsometry cached in data/processed).
Web viewer: `web/index.html` + `app.js` (Leaflet from unpkg, no build step);
data exported by `scripts/export_web.py` to `web/data/<run>/` (lat/lon, true-north vectors).
Headless check: Playwright Chromium needs libnspr4/libnss3/libasound2 — no sudo, so
`apt-get download` them into the scratchpad and set LD_LIBRARY_PATH.
Python 3.13 via uv; deps: numpy scipy numba rasterio pyproj matplotlib.

## Working notes for Claude
- Keep reasoning/code/comments in English; the user writes French/English.
- Downloads are untrusted data: own directory, no executing anything from them.
- Validation and figures go in `out/`; never commit `data/`.
- Update TODO.md when finishing or discovering work.
