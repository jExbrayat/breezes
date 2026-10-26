# breezes — Alpine Breeze Atlas

Thermal breezes of the French Alps (slope winds and valley winds, day and
night), computed from the terrain alone by a small physical model, then
compared against the pilots' map "Brises des Alpes" (F. Largeault &
contributors), which the model never sees.

## Start the interactive map

```bash
cd ~/Desktop/breezes
uv sync                              # first time only: installs Python 3.13 + dependencies
uv run python scripts/serve.py       # then open http://localhost:8000
```

Stop it with `Ctrl+C`. Use another port with `--port 8080`. From Windows,
open the same address: WSL forwards `localhost`.

`serve.py` exports any model run in `out/` that is missing or older in
`web/data/`, then serves `web/`. The page needs internet access for the map
tiles, Leaflet and fonts.

### What you see
- **Hour slider / ▶**: the simulated day, in solar time, with summer clock time (CEST) beside it.
  The bar strip shows the share of valleys blowing up-valley (red) and down-valley (blue) each hour.
  Click a bar to jump to that hour.
- **Red / blue arrows**: valley winds (up-valley / down-valley). Length ∝ speed, thickness ∝ catchment size.
- **Dark particles**: near-surface flow (slope winds + valley winds, ~1 km average).
- **Magenta lines**: the pilots' breeze map, arrowhead = breeze direction. Tick
  *Colour pilots' map by agreement* to colour every 400 m piece of each line at the selected
  hour: green = model within 45°, amber = across or calm, red = model blows the opposite way
  (135° or more off; the error to eliminate). Hover a line for its counts.
- **Click anywhere**: modelled wind speed and direction at that point.
- **Layer button (top right)**: OpenTopoMap, IGN Plan, IGN orthophoto, Esri relief.
- **Model run** selector: compare runs, including `naive_up_valley` (no physics: wind along the
  nearest valley, up-valley while the sun is up). The table scores the selected run against the
  pilots' map (13–16 h solar): *Agree* (higher is better) and *Opposite* (target 0 %), next to
  the naive rule.

## Run the model

```bash
uv run python scripts/run_alps.py --tag my_run            # full French Alps, 200 m, ~4 min
uv run python scripts/run_alps.py --tag june --date 2026-06-21
uv run python scripts/run_alps.py --model naive --tag naive_up_valley   # the no-physics reference
uv run python scripts/rescore.py                          # re-score all saved runs
```

The first run downloads the Copernicus DEM (~75 MB, no account needed).
Outputs go to `out/<tag>/` (`fields.npz`, `validation.txt`, `params.json`).
Restart `serve.py` to see the new run in the map.

Physical parameters live in `src/breezes/params.py`, each with its literature
source (`docs/physics_notes.md`). They are not tuned to the pilots' map.

## Static PNG maps (optional)

```bash
uv run python scripts/plot_maps.py --tag my_run --hours 8,14,22 --regions gresivaudan_chartreuse
```

Images go to `out/<tag>/maps/`.

## More

- `CLAUDE.md`: how the model works, conventions, rules (no fitting to the validation map).
- `TODO.md`: status and next steps (mass continuity, pass winds, phase 2: lakes, glaciers, albedo).
- `docs/physics_notes.md`, `docs/data_sources.md`: literature and data research.
