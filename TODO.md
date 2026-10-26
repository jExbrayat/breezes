# TODO

Legend: [x] done · [ ] todo · [~] in progress

## Phase 1 — topographic breezes

### Data & terrain
- [x] Copernicus GLO-90 → Lambert-93 200 m grid, cached (`dem.py`)
- [x] Priority-flood, D8 down & up-slope, accumulation, channels, HAND, valley axis
- [x] Sun position, cast shadows, sky-view factor
- [ ] Cache terrain + hypsometry (init currently ~90 s)
- [ ] GLO-30 option for zoomed sub-domains (50–100 m)

### Model
- [x] Clear-sky surface heat flux (incidence, shadows, diffuse, LW × SVF)
- [x] Slope winds, buoyancy-flux scaling, routing-based fetch
- [x] Hypsometric mixed-layer valley-wind model, day + night cold pool, ODE along axis
- [x] First diurnal run (2026-10-26): direction cycle plausible (≈85 % of channels
      up-valley by day / down-valley by night; morning reversal ≈10 h, evening ≈21 h
      solar). **Speeds ~2× too high** (median 6–10 m/s, p95 25–30 m/s).
- [x] Along-valley semi-Lagrangian advection on the D8 network (**motivated by validation**:
      local sign flips in wide basins, e.g. Durance). v0→v1: sign 0.82→0.83, losses vs
      baseline 601→461. Missing term of the momentum eq., not a tuned fix.
- [x] Sourced parameters from `docs/physics_notes.md` (run `v2_sourced_params`):
      f_H 0.30, LW −70, c_slope 0.04, Δz cap 1 km, heat export 0.3, τ_res 4.5 h.
      Afternoon valley median 4.6 m/s (lit. 3–10 ✓), reversal ≈10 h, peak ≈16 h solar ✓.
      Direction score unchanged (0.82) → direction is structural, not parametric.
- [ ] Speed tails still high: valley p95 ≈17 m/s by day, night down-valley median 7–8 m/s
      (lit. core ≈4) → needs mass continuity (below), not more drag
- [ ] Baseline "always up-valley" still wins (0.88 vs 0.82). Model gains on convergences
      (Grésivaudan) but loses on basins (Grenoble/Voreppe cluse) → mass continuity
- [ ] Watershed-aware footprint: restrict lateral mixing to air connected below
      z_m (today a Gaussian footprint leaks across ridges)
- [ ] Mass continuity along the network (narrowing gorges accelerate the wind,
      confluences add flux) — maybe a 2D mass-consistent adjustment (MATHEW/WindNinja-style)
- [ ] Pass / col winds (valley wind crossing a pass toward the hotter side, Maloja type)
- [ ] Ridge convergence lines / thermal triggers from upslope-routing accumulation
- [ ] Sensitivity analysis: σ_valley, channel threshold, γ — report score spread, do not pick the best
- [ ] Seasonal runs (May, July, September) and synoptic-wind caveat

### Scoring criterion (user decision, 2026-10-26)
Per sample: **agree** ≤ 45° off · **opposite** ≥ 135° off · across/calm otherwise.
**Primary goal: opposite = 0** ("evict completely"). Across is tolerated. Legacy "sign" (< 90°) kept for reference.

| run | agree | opposite | legacy sign |
|---|---|---|---|
| naive_up_valley (no physics) | 0.78 | **0.09** | 0.88 |
| v2_sourced_params | 0.71 | **0.12** | 0.82 |

v2 opposite breakdown vs naive: 5.9 % shared (pilots' breeze against the drainage:
convergences, cols → neither model), 6.3 % **new flips caused by the physics** (basins,
footprint leaking across ridges — Alpes du sud 129, Bauges 82, Chablais 59, Chartreuse 59),
3.1 % naive errors fixed by v2 (Vercors 131).
- [ ] Step 1: remove the 6.3 % physics-induced flips without losing the 3.1 % fixes
      (mass continuity / watershed-aware footprint)
- [ ] Step 2: the 5.9 % shared cases (through-valley convergences, pass/col winds)

### Validation (held-out — never tune on it)
- [x] `reference.py`: KML parsed, direction from drawn closed-triangle arrowheads (273/291 lines)
- [x] `validate.py`: agree/opposite/across per sample at 13–16 h solar, per region, + naive baseline
- [x] Naive model as a real run (`run_alps.py --model naive`), viewable in the web app
- [x] `scripts/rescore.py` re-scores saved runs when the criterion changes
- [ ] Look into the line colours in "Alpes du sud et Autres" (blue/pink/purple — meaning?)
- [ ] Second independent set: Météo-France hourly valley stations (see `docs/data_sources.md`)
- [ ] User review session on valleys the user knows → record verdicts in `docs/validation_log.md`

### Rendering
- [x] Static regional PNGs: `scripts/plot_maps.py --tag <run> --hours 8,14,22`
- [x] Localhost viewer `scripts/serve.py` → http://localhost:8000: OSM/IGN/Esri tiles,
      valley arrows, particles, pilots' lines (+ per-hour agreement colouring), hour slider,
      diurnal up/down strip, click popup, run selector, score table. Checked headless, no errors.
- [ ] Viewer: show slope-wind convergence lines / thermal triggers; per-run diff view
- [ ] Optional: publish a static snapshot as a shareable page for the friend

## Phase 2 — surface-contrast ("albedo") breezes
- [ ] Choose data (see `docs/data_sources.md`): ESA WorldCover 10 m, glaciers (RGI 7),
      lakes, seasonal snow, albedo
- [ ] Surface-type rasters → albedo, sensible-heat fraction (Bowen), heat capacity
      (water: ~no daytime sensible heat → lake breezes), glaciers (H<0 by day →
      glacier/katabatic winds in daytime)
- [ ] Re-run the same wind physics with heterogeneous H; diff vs phase 1 = "albedo breezes"
- [ ] Detection: where the phase-2 vs phase-1 difference changes direction or > X m/s
- [ ] Test cases: Annecy, Bourget, Léman, Serre-Ponçon lake breezes; Mont-Blanc glacier winds

## Open questions for the user
- Map style preference? Valleys you want to check first?
- Season/date of reference (the map = summer afternoon thermals?)
