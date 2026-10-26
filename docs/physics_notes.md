# Physics notes: thermally driven topographic breezes (French Alps model)

Literature reference for `src/breezes/params.py`. **Tags:** [obs] = observed value in the cited paper; [theory] =
analytical/numerical result of the paper; [derived] = derived here from cited equations (algebra checked, not a
published number); [estimate] = no solid source, judgement call to sensitivity-test. "via Z&W" = quoted from the
Zardi & Whiteman (2013) review, primary paper not checked (full refs in Z&W's bibliography).

Notation: `H` sensible heat flux (W m-2), `Q = H/(rho c_p)` (K m s-1), buoyancy flux `B = g Q/theta0` (m2 s-3),
`gamma = dtheta/dz`, `N^2 = (g/theta0) gamma`, `alpha` slope angle, `x` along-slope fetch, `dz = x sin(alpha)` height
of the cell above the slope foot (day) or below the ridge/source (night). TST = true solar time.

---
## a) Anabatic (upslope) winds

**Layer equations** (Manins & Sawford 1979b; Horst & Doran 1986; Z&W eqs 2.2–2.5), along-slope `s`, slope-normal `n`,
`d` = potential-temperature perturbation:
`du/dt + u du/ds + w du/dn = -(1/rho0) d(p-pa)/ds - g (d/theta0) sin(alpha) - d(u'w')/dn`.

**1. Prandtl (1942) equilibrium profile** (constant K; buoyancy–friction balance plus advection against the
background gradient; works for up- and downslope flow, Defant 1949, Z&W Fig. 2.3):
```
theta'(n) = theta_s exp(-n/l) cos(n/l)        u(n) = theta_s (g/(theta0 N)) Pr^(-1/2) exp(-n/l) sin(n/l)
l = (4 K_m K_h / (N^2 sin^2 alpha))^(1/4)     n_jet = (pi/4) l        u_max = 0.322 u_amp
```
Flux-forced form [derived]: `Q_s = K_h theta_s/l`, so with `Pr = 1`:
`u_max ~= 0.456 B_s / (N^(3/2) K^(1/2) sin^(1/2) alpha)`. Example: `B_s = 3.3e-3`, `N = 0.01`, `K = 1 m2 s-1`,
`alpha = 20 deg` gives `u_max ~= 2.6 m/s`, jet at about 19 m. Very sensitive to K, which is poorly known.

**2. Bulk "hydraulic" law (recommended per-cell form)** [derived]. From the Manins & Sawford (1979b)
layer-averaged equations: steady, neutral ambient, buoyancy balanced by surface plus entrainment (interfacial) drag.
```
d(U h b)/dx = B_s   (heat kept in layer);   b h sin(alpha) = c U^2,  c = C_D + E
=>  U = (B_s x sin(alpha) / c)^(1/3) = (B_s dz / c)^(1/3)
```
Example: `H = 200 W m-2` (`B ~= 5.6e-3`), `dz = 420 m`, `c = 0.038` gives `U ~= 4 m/s` (observed 1–5 m/s).

**3. Hunt, Fernando & Princevac (2003)** [theory+lab]: on long, gentle heated slopes the mean upslope velocity is
`U_M ∝ alpha^(1/3) w*`, with `w* = (B_s h)^(1/3)` and `h` the CBL depth. The speed is set by the CBL depth, not the
slope length. Suggested use [estimate]: by day cap `dz <= h_CBL`, because rising heat leaves the slope layer.

**4. Schumann (1990) LES** [theory]. The steady upslope boundary layer depends only on `alpha` and `z0/H`. Its
scales are consistent with `v* = (B_s/N)^(1/2)`, `H = (B_s/N^3)^(1/2)`, `theta* = Q_s/v*` [derived: these reproduce
the Z&W-quoted 0.58 m/s, 58 m, 0.17 K for 3 K/km and about 0.1 K m s-1]. Steady state is approached through damped
oscillations at `N sin(alpha)`. Wind maxima lie within about 50 m of the ground; the deepest and strongest flows
occur on low-angle slopes.

**Onset.** The morning transition begins "shortly after sunrise, when incoming solar radiation exceeds longwave
loss" (Z&W), so no explicit delay is needed beyond `H(t)` with cast shadows. Adjustment time is about
`2 pi/(N sin alpha)`, i.e. 15–40 min for `N = 0.01`, `alpha = 10–30 deg` [derived].

| Quantity | Value | Range | Source |
|---|---|---|---|
| Max upslope speed | 2–3 m/s | 1–5 m/s | Z&W 2013 (after Whiteman 2000) [obs] |
| Jet height | 20 m | 10–50 m | Z&W 2013 [obs]; Schumann 1990 (<50 m) |
| Upslope flow depth | 100 m | 20–200 m | Z&W 2013 [obs] |
| Temperature excess | 3 K | 2–7 K over 10–100 m | Z&W 2013 [obs] |
| Onset after local sunlight | ~0.5 h | 0.25–1 h | [estimate]; physically: when H > 0 |

Caveats. Real upslope flows are non-stationary, keep growing through the morning, and are disrupted by convection
and winds aloft (Z&W). On slopes steeper than about 20 deg, laboratory upslope flow separates into a rising plume
below the crest (Hocut et al. 2015), a thermal-trigger mechanism. The bulk law keeps all heat in the layer, which
overestimates daytime flow; hence the cap.

---
## b) Katabatic (downslope) winds and cold pools

**Bulk law** [derived from Manins & Sawford 1979b]: `U = (|B_s| x sin(alpha) / c)^(1/3)`, `c = C_D + E`.
Example: `H = -30 W m-2`, `dz = 420 m`, `c = 0.038` gives `U ~= 2.1 m/s`.

Entrainment E: atmospheric fit `E ~= 0.05 Ri^(-0.75)` for `0.15 < Ri < 1.5`, `Ri = b h cos(alpha)/U^2` (Princevac et
al. 2005, Salt Lake Valley); interfacial drag dominates surface drag for `Ri < 0.8`, comparable above. The lab law
`E = (0.08 - 0.1 Ri)/(1 + 5 Ri)` (Ellison & Turner 1959) underestimates natural flows. Briggs (1981) fit (via Princevac
et al. 2005): `E ~= 0.05 (sin alpha)^(2/3)`, i.e. 0.02–0.04 on 10–40 deg slopes, not valid on very low slopes. Manins &
Sawford (1979a): stress against ambient air matters more than surface stress; they quoted `C_D <= 3e-4`.

**Princevac, Hunt & Fernando (2008)** [obs+theory, VTMX]: `U = lambda_u (Delta_b L_H sin alpha)^(1/2)` with
`lambda_u ~= 0.2` for `Ri > 1.5`; on long slopes `h ∝ L_H (tan alpha)^(1/2)`; pulsation period `T0 = 2 pi/(N sin alpha)`.

**Depth.** Temperature-deficit depth is about 0.05 × the vertical drop from the slope top (Horst & Doran 1986). The
jet sits at 30–60% of the inversion depth, and the flow extends several inversion depths higher (Z&W).

**Regimes** (Mahrt 1982, unified scale analysis of the momentum balance). Comparing advection `U^2/L` with
friction `c U^2/h` gives `R = c L/h` [derived]. `R >> 1`: equilibrium flow (buoyancy balances friction, Prandtl-like;
typical of mid-latitude slopes, Z&W). `R << 1`: shooting (advective) flow. On long, gentle slopes the hydrostatic
pressure gradient from the thickening layer opposes buoyancy (Zhong & Whiteman 2008; Princevac et al. 2008). Rising
ambient stability weakens downslope flows; inside a growing valley inversion they detach and converge at its top (Z&W).

**Onset.** Slope flows start almost immediately after cooling begins and peak about 1 h later (McNider & Pielke 1984,
model). On steep Alpine slopes a sharp shading front is followed by a calm period (<0.5 m/s, TKE < 0.05 m2 s-2)
before katabatic onset (Nadeau et al. 2013, Val Ferret).

**Radiative cooling.** Clear-sky net longwave at an open site: `L*_0 ~= -50 to -100 W m-2` [estimate]. Terrain
back-radiation cuts the loss by about 50% versus ridge tops (Olyphant 1986, via Z&W); net loss rises with elevation and
sky-view (Matzinger et al. 2003). Use `L* ~= V_sky L*_0` [estimate, standard approximation]. Valley cooling follows
`H(t)/H_T = 1 - exp(-(t - t0)/tau_c)` (De Wekker & Whiteman 2006):
- `tau_c` ≈ 3.1 h in basins, 3.9–5.5 h in valleys, 5–6 h over plains (7.5 h in a snow-covered valley).
- Summer Colorado valleys: 12–18 K inversion at sunrise over 400–600 m; accumulated nighttime loss 6–8 MJ m-2 per unit
  floor area, or 2.8–3.7 MJ m-2 per unit terrain area. Over a ~10.7 h night the latter is a mean net loss of about
  70–95 W m-2 [derived].
- Longwave flux divergence: up to about -30 K/day locally, roughly 30% of crater cooling (Hoch et al. 2011, via Z&W).

**Cold pools in closed basins.** With no valley-wind export, basins cool fastest and through their full depth, and
downslope flows die later in the night as stability builds (Z&W). Gruenloch (Austria, ~100 m deep): 12 K inversion on
a June night (De Wekker & Whiteman 2006), record minimum -52.6 deg C (Steinacker et al. 2007). Cold air spills over the
lowest pass (Pospichal et al. 2003, via Z&W). Model: fill to spill level (priority-flood), route outflow through the
pass [estimate].

**Glacier winds.** Melting snow/ice keeps `H < 0` even by day, giving a persistent downslope flow: 3–10 m/s at a few
to tens of metres over an Icelandic ice cap (Oerlemans et al. 1999, via Z&W). On a small Alpine glacier (Pasterze),
buoyancy is balanced by friction plus the valley-wind pressure gradient (Van den Broeke 1997).

| Quantity | Value | Range | Source |
|---|---|---|---|
| Max downslope speed | 2 m/s | 1–4 m/s | Z&W 2013 [obs] |
| Jet height | 5 m | 1–15 m (0.6–40 m in Z&W Table 2.1) | Z&W 2013 [obs] |
| Flow depth | 30 m | 3–100 m | Z&W 2013 [obs] |
| Temperature deficit | 4 K | 3–7 K over 1–20 m | Z&W 2013 [obs] |
| Night H on open slopes | -30 W m-2 | -10 to -50 | [estimate] |

Caveats. Steady analytic models wrongly suggest stronger flow on steeper upper slopes; observed flows deepen and
strengthen downslope (Z&W). A cross-flow of 2–3 m/s (e.g. a valley wind) can erase slope flows. Oscillations with
5–90 min periods are common.

---
## c) Valley winds

**Hydrostatic forcing** [theory]. Pressure perturbation at fixed altitude, with an undisturbed reference level
`zr` aloft:
```
p'(z) = -rho0 (g/theta0) Int_z^zr DTheta dz'       F(z) = -(1/rho0) grad_h p' = (g/theta0) grad_h Int_z^zr DTheta dz'
uniform DTheta over D = z_top - z_f, at the floor:  F = (g/theta0) [ D grad(DTheta) + DTheta grad(z_top) ]
mixed layer z_m eroding gamma, DTheta = gamma (z_m - z):  F = (g gamma/theta0) (z_m - z_f) grad(z_m)   [derived]
```
Evaluate gradients at constant height, not along terrain (Haiden 2003 on coordinate errors, via Z&W). In the Adige,
the along-valley growth of pressure amplitude comes from the **increasing depth of the heated layer**, with no
along-valley change in diurnal temperature range (Giovannini et al. 2017). The `grad(z_top)` (depth) term can dominate.

**Topographic amplification factor** (Wagner 1932, via Z&W; Steinacker 1984; Whiteman 1990):
```
TAF = (A_top/V)_valley / (A_top/V)_plain = A_top h / V_valley   (same top area A_top, same depth h)
V-shaped cross-section: TAF = 2; flat-floored or U-shaped: 1 < TAF < 2
Hypsometric (Steinacker 1984): V(z) = Int_zmin^z A(z') dz',  D_eff(z) = V(z)/A_top(z) = h/TAF
Closed volume: DTheta = Q_cum / (rho c_p D_eff)
```
- Stratified generalisation (encroachment; Whiteman & McKee 1982; Stull 1988):
  `Q_cum A_top = rho c_p gamma Int_zf^zm (z_m - z) A(z) dz`. Over flat ground `z_m = (2 Q_cum/(rho c_p gamma))^(1/2)`;
  with an entrainment heat-flux ratio of about 0.2, `z_m` is about 1.18× larger (Stull 1988) [derived].
- Morning: the nocturnal inversion must be removed first,
  `Q_break = rho c_p Int (theta_top - theta(z)) A(z) dz / A_top` (Whiteman & McKee 1982). Colorado valley inversions
  broke up 3–5 h after sunrise (Whiteman 1982).

**Limits of the TAF.** Schmidli & Rotunno (2010): the closed-volume assumption "seldom holds"; advection and
turbulence reduce daytime heating and nighttime cooling, yet the volume effect remains important for along-valley
winds. Schmidli (2013): the volume effect is confirmed as the primary cause of the amplified diurnal range, while the
cross-valley circulation exports heat out of the valley. Rampanelli et al. (2004): heat reaches the core through
compensating subsidence (the "how" of the volume effect). Weigel et al. (2006, Riviera LES): subsidence heating is
comparable to turbulent flux divergence; volume-mean heating 1.5–2e-4 K/s (0.5–0.7 K/h). Leukauf et al. (2017): the
fraction of surface heat exported at crest height falls exponentially with the break-up parameter
`B_u = Q_break/Q_day`, from up to 60% at `B_u ~ 0.1` to under 5% at `B_u > 0.65` (sharp crests).
Model use: `DTheta = (1 - f_exp) Q_cum/(rho c_p D_eff)`.

**Along-valley ODE:** `du/dt = F_par - (C_D,eff/h) |u| u  [ - u/tau ]`, spin-down time `h/(C_D,eff U)`.
Giovannini et al. (2017): wind speed grows **linearly** with the along-valley pressure gradient (quasi-steady
pressure-gradient/friction balance), which supports a linear (Rayleigh) term. Drag, two estimates [derived]:
- Bottom-up: log law `C_D = (kappa/ln(z_r/z0))^2 = 0.003–0.01` (`z_r ~ 100 m`, `z0 = 0.1–1 m`) × wetted-perimeter/width
  factor 1.5–3 gives `C_D,eff ~ 0.005–0.03`.
- Top-down: thermal Δp "up to 5 hPa over 100 km" (Inn, via Z&W) gives a force of 1–4e-3 m s-2; with observed U of
  3–8 m/s, `C_D,eff/h ~ 3–10e-5 m-1` (`C_D,eff ~ 0.03–0.08` at `h ~ 1 km`) or `tau ~ 0.5–2 h`. The gap suggests
  sidewall drag and interfacial shear aloft dominate (shear production peaks aloft in the Riviera; Weigel & Rotach 2004).

Wagner et al. (2015), idealized: a 0.86 deg inclined floor raises up-valley wind about 1.9× (volume effect) and 1.6×
(upslope buoyancy); narrowing by 20 km per 100 km raises it about 2.6×.

| Valley | Observation | Source |
|---|---|---|
| Generic | Valley-centre peak 3–10 m/s; up-valley onset several hours after upslope onset; evening reversal starts at the floor | Z&W 2013 [obs] |
| Inn (AT) | Thermal Δp up to 5 hPa/100 km; valley-exit jet 13 m/s at 200 m AGL | Vergeiner & Dreiseitl 1987; Pamperin & Stilke 1985 (via Z&W) |
| Inn, 19 Aug 2018 | Up-valley ~10–16 UTC (onset ~10:45 TST), ~1000 m deep; ~2 h transition; down-valley from ~18 UTC, jet ≤7.5 m/s at ~200 m AGL | Simonet et al. 2023 [obs] |
| Rhône at Sion (CH) | May–Sep mean max up-valley 8–10 m/s at ~200 m AGL, 15–16 UTC (~15:30–16:30 TST); night down-valley jet 4–8 m/s near 1 km AGL; reversal to ~2 km AGL in summer | Schmid et al. 2020 [obs] |
| Riviera (CH, MAP) | Up-valley jet ~10 m/s near the Bellinzona bend; mixed layer stops growing by ~noon; stable core persists | Weigel & Rotach 2004; Weigel et al. 2006 [obs] |
| Adige (IT) | U linear in along-valley Δp; pressure amplitude grows up-valley | Giovannini et al. 2017 [obs] |
| Dischma (CH) | Classic V-valley wind development; asymmetric sidewall heating | Urfer-Henneberger 1970; Hennemuth 1986 (numbers not checked) |
| Arve / Chamonix (FR) | Winter: weak daytime up-valley, elevated night down-valley jet; summer boundary-layer studies exist | Sabatier et al. 2018; Chemel & Chollet 2006; Brulfert et al. 2005 |
| Grenoble / Isère (FR) | Only wintertime persistent-inversion studies found; no summer valley-wind climatology found | Largeron & Staquet 2016 |

**Timing, clear summer days** [obs, collected from the table]: upslope shortly after local sunlight; up-valley onset
about 3–5.5 h after sunrise, peaking about 15–16 TST; the up-valley wind persists several hours after the surface
energy budget reverses; down-valley regime from around sunset to a few hours after ("several hours after sunset until
about midnight", Z&W).

Caveats. Model intercomparisons show up to 2 h timing spread driven by the surface energy balance (Schmidli et al.
2011). Onset is sensitive to soil moisture even far from the valley (Chow et al. 2006). Cold-air sources at the valley
mouth (lakes) can suppress or reverse the cycle (Z&W).

---
## d) Surface energy budget, sensible heat, albedo

```
R_n = (1-a)[S_b cos(i) b_shadow + D_h V_sky + a_t G (1-V_sky)] + eps_s L_down - eps_s sigma T_s^4
cos(i) = cos(beta) cos(Z) + sin(beta) sin(Z) cos(phi_sun - A)                         (Iqbal 1983)
L_down,slope ~= V_sky eps_a sigma T_a^4 + (1 - V_sky) eps_s sigma T_terrain^4        (Dozier & Frew 1990 framework)
eps_a = 1.24 (e/T)^(1/7)   (e in hPa, T in K; clear sky)                             (Brutsaert 1975)
H = f_H R_n,   f_H = (1 - g_G) Bo/(1 + Bo),   g_G = G/R_n ~ 0.1 by day               [estimate]
```
Daytime sensible flux over complex terrain can be estimated from global radiation on the slope (Matzinger et al.
2003; Rotach & Zardi 2007; via Z&W).

| Surface | Bowen ratio Bo | f_H = H/R_n (day) | Source |
|---|---|---|---|
| Grassland / forest | ~0.5 | ~0.3 | Stull 1988 (typical Bo); f_H [derived] |
| Irrigated / wet meadow | ~0.2 | ~0.15 | Stull 1988 |
| Semi-arid, bare rock, scree | 2–5 | 0.5–0.7 (larger G) | Stull 1988 (semi-arid ~5); rock [estimate] |
| Melting snow or ice | – | H ≤ 0 by day | Z&W (glacier winds) |

Peak H on sunlit slopes on a clear summer day is about 150–300 W m-2 [estimate]; idealized LES runs use about
100–200 W m-2. Measured fluxes are biased low: closure gap 10–40% (Z&W), 28–29% on sloped and flat Stubai meadows
(Hammerle et al. 2007). Inn valley: H lowest on the north-facing sidewall; the Bowen ratio falls through the day
(Lehner et al. 2021; Simonet et al. 2023).

| Albedo by surface | Typical | Range | Source |
|---|---|---|---|
| Short / long grass | 0.23 | 0.16–0.26 | Oke 1987 |
| Deciduous / coniferous forest | 0.18 / 0.10 | 0.15–0.20 / 0.05–0.15 | Oke 1987 |
| Bare rock (dark crystalline / light limestone) | 0.15 / 0.30 | 0.10–0.40 | [estimate] |
| Dry soil / desert | 0.30 | 0.20–0.45 | Oke 1987 |
| Fresh dry snow | 0.85 | 0.75–0.98 | Cuffey & Paterson 2010 |
| Old clean snow / clean wet snow | 0.75 / 0.55 | 0.70–0.85 / 0.46–0.70 | Cuffey & Paterson 2010 |
| Firn | 0.55 | 0.50–0.65 (debris-rich 0.15–0.40) | Cuffey & Paterson 2010 |
| Clean / debris-rich glacier ice | 0.38 / 0.20 | 0.30–0.46 / 0.06–0.30 | Cuffey & Paterson 2010 |
| Water (high / low sun) | 0.06 | 0.03–0.10 / up to ~1 at grazing incidence | Oke 1987 |

Caveats. The Oke, Stull and Cuffey & Paterson numbers are recalled from those standard tables; spot-check them
before Phase 2. Rock albedo is an estimate. f_H is the most uncertain and most influential parameter: it sets timing
as well as speed (Schmidli et al. 2011).

---
## e) Mountain–plain circulation ("Alpine pumping") and pass winds

**Mountain–plain.** Same forcing as (c), applied at massif scale with `D_eff` from the massif hypsometry relative to
the foreland. Early pilot-balloon evidence: Burger & Ekhart (1937) and Ekhart (1948), via Z&W. VERTIKATOR, south
Bavaria (Lugauer & Winkler 2005; Weissmann et al. 2005): inflow 1–4 m/s, up to 1500 m deep, reaching about 80 km
(lidar) to 100 km (Danube, climatology) into the foreland; strongest when daily global radiation exceeds about
20 MJ m-2 and winds aloft are weak (via Z&W); rising branch about 0.05–0.10 m/s. Phase delay of up to 3 h with
distance from the Alps; 0.5–1.5 m/s near Munich in simulations (Graf et al. 2016). Venting: about 30% of the Alpine
boundary-layer mass rises above 2500 m per hour in daytime (Henne et al. 2005). Rockies, timing only: inflow→outflow
19–02 MST, outflow→inflow 06–11 MST (Bossert et al. 1989, via Z&W). The reversal lags the valley winds because of the
larger air mass (Z&W).

**Pass / col winds** [derived from the hydrostatic relation in (c)]. At pass height `z_p`, the side with more heating
*above* `z_p` has lower pressure:
`F_pass = (g/theta0)(I_2 - I_1)/L`, with `I_k = Int_{z_p}^{zr} DTheta_k dz`. With encroachment,
`I = gamma (z_m - z_p)^2/2` when `z_m > z_p`; there is no forcing while the mixed layer stays below the pass.

Supporting cases: a thermally induced plain-to-basin wind crosses a mountain range (Kimura & Kuwagata 1993); flow enters
a basin over the ridge once pressure differences exist above ridge level, the inside/outside gradient matters only
through gaps (De Wekker et al. 1998). **Maloja wind** (Wagner 1938; Gross 1985; Z&W): the Bergell (Bregaglia)
up-valley wind overflows the Maloja Pass and blows *down* the Upper Engadine by day, explained by local topography (the
Bergell ridgelines extend beyond the pass). **Ora del Garda**: cool lake-valley air (up to 6 m/s) crosses a saddle into
the Adige in early afternoon (Laiti et al. 2014; Wagner 1938). At night, basin cold air drains through the lowest pass
(Pospichal et al. 2003, via Z&W).

Caveat. Pass flows also carry momentum (the Maloja wind is partly inertia of a strong valley wind). `F_pass` gives
the sign; speeds need the momentum ODE along the through-valley path.

---
## f) Confluences and convergence of valley-wind systems

From Z&W (tributary section): by day, up-valley flow divides at each tributary junction; at night, down-valley flows
merge. Mass balance at junctions can force closed circulations with enhanced subsidence or ascent over the junction
(Freytag 1988; Zängl 2004). Tributaries can supply more drainage than a sidewall and pulse (surges) when blocked by the
main-valley cold flow (Coulter et al. 1989, 1991; Porch et al. 1991). Inn daytime up-valley mass flux *diverges* along
the valley (Vergeiner 1983; Zängl 2004).

Mass balance [derived]: `w_conv ~= (Sum_i U_i h_i W_i)/A_junction`; expect ascent where up-valley flows converge
(drainage divides, pass saddles) and descent over night-time confluences. Documented anomalies: at the Ora del Garda /
Adige junction, cold saddle outflow undercuts the Adige up-valley wind and splits into up-valley flow north and
down-valley flow south of the junction (Z&W Fig. 2.11; Laiti et al. 2014). In the Riviera, curvature at the
Bellinzona bend drives an "anti-thermal" secondary circulation with w ~ 0.5–1 m/s (Weigel & Rotach 2004; Weigel et
al. 2006).

French paragliding sources: I could **not** find or verify G. Briffe, "Brises et confluences des Alpes du Sud", or any
peer-reviewed study of breeze confluences in the French Alps (Durance–Ubaye, Isère–Drac, Arve). Treat confluence
behaviour as an emergent model output.

---
## Recommended defaults for our model

| Parameter | Symbol | Default | Range | Source |
|---|---|---|---|---|
| Solar constant | S0 | 1361 W m-2 | – | Kopp & Lean 2011 |
| Albedo (Phase 1, uniform) | a | 0.20 | 0.15–0.25 | Oke 1987 (grass/forest/crops) |
| Surface emissivity | eps_s | 0.97 | 0.95–0.99 | Oke 1987 |
| Clear-sky atmospheric emissivity | eps_a | Brutsaert formula | – | Brutsaert 1975 |
| Clear-night net LW, open site | L*_0 | -70 W m-2 | -50 to -100 | [estimate]; consistent with De Wekker & Whiteman 2006 |
| Sky-view scaling of LW loss | – | L* = V_sky L*_0 | – | Dozier & Frew 1990 framework [estimate] |
| Sensible fraction, day | f_H | 0.30 | 0.20–0.50 | Bo ~0.5 (Stull 1988), G = 0.1 R_n [estimate] |
| Sensible fraction, night | f_Hn | 0.5 | 0.3–0.7 | [estimate] |
| Reference potential temperature | theta0 | 293 K | 283–303 | [estimate] |
| Free-atmosphere stability (day) | gamma | 3.5 K km-1 | 3–5 | ISA gives 3.3; Schumann 1990 uses 3 [estimate] |
| Nocturnal valley inversion gradient | Gamma_n | 25 K km-1 | 15–40 | 12–18 K over 400–600 m (De Wekker & Whiteman 2006, Colorado) |
| Nocturnal cooling time constant | tau_c | 4.5 h | 3–8 h | De Wekker & Whiteman 2006 |
| Evening residual heat decay | tau_res | = tau_c | 3–8 h | [derived] from De Wekker & Whiteman 2006 |
| Slope surface drag | C_D | 0.01 | 0.003–0.02 | log law [derived]; Princevac et al. 2005 |
| Slope entrainment | E | 0.05 (sin alpha)^(2/3) | 0.005–0.1 | Briggs 1981 via Princevac et al. 2005 |
| Slope-flow drag sum | c | 0.04 | 0.01–0.1 | C_D + E [derived] |
| Daytime fetch cap | dz_max | h_CBL ~ 1 km | 0.5–1.5 km | motivated by Hunt et al. 2003 [estimate] |
| Katabatic depth | h_k | 0.05 dz_top | – | Horst & Doran 1986 |
| Katabatic coefficient (alternative law) | lambda_u | 0.2 | 0.2–1 (low Ri) | Princevac et al. 2008 |
| Slope-flow adjustment period | T_s | 2 pi/(N sin alpha) | 15–40 min | Schumann 1990; Princevac et al. 2008 |
| Prandtl eddy diffusivity (day / night) | K | 1 / 0.1 m2 s-1 | 0.3–5 / 0.02–0.5 | [estimate] |
| TAF (V-shaped reference) | TAF | 2 | 1–3 | Whiteman 1990; compute from DEM hypsometry |
| Valley heat export at crest | f_exp | 0.3 | 0.05–0.6 | Leukauf et al. 2017 |
| Valley-wind layer depth | h | valley depth (crest – floor) | 0.5–2 km | Simonet et al. 2023; Schmid et al. 2020 [obs] |
| Valley effective drag | C_D,eff | 0.03 | 0.005–0.08 | [derived], bottom-up vs top-down |
| Optional linear damping | tau | 2 h | 0.5–6 h | Giovannini et al. 2017 (linear law) [estimate] |
| Up-valley / down-valley core speed (check only) | U | 5 / 4 m/s | 3–10 / 2–8 | Z&W 2013; Schmid et al. 2020 |
| Mountain–plain speed / depth / reach (check only) | – | 1.5 m/s / 1.5 km / 100 km | 1–4 m/s / 1–2 km / 80–100 km | Weissmann et al. 2005; Lugauer & Winkler 2005 |

---
## References (DOIs verified via Crossref unless noted)
Brutsaert 1975, Water Resour. Res. 11:742, doi:10.1029/WR011i005p00742 · Brulfert et al. 2005, ACP 5:2341,
doi:10.5194/acp-5-2341-2005 · Chemel & Chollet 2006, BLM 119:239, doi:10.1007/s10546-005-9026-4 · Chow et al. 2006,
JAMC 45:63, doi:10.1175/JAM2322.1 · Cuffey & Paterson 2010, *The Physics of Glaciers* 4th ed., Academic Press ·
De Wekker & Whiteman 2006, JAMC 45:813, doi:10.1175/JAM2378.1 · De Wekker et al. 1998, JAM 37:606,
doi:10.1175/1520-0450(1998)037<0606:ANSOTT>2.0.CO;2 · Dozier & Frew 1990, IEEE TGRS 28:963, doi:10.1109/36.58986 ·
Fernando, Princevac, Hunt & Dumitrescu (c. 2006), AMS preprint 5.4, https://ams.confex.com/ams/pdfpapers/114619.pdf ·
Giovannini et al. 2017, QJRMS 143:2389, doi:10.1002/qj.3092 · Graf et al. 2016, Front. Earth Sci. 4:5,
doi:10.3389/feart.2016.00005 · Gross 1985, Beitr. Phys. Atmos. 58:441 (not read) · Hammerle et al. 2007, BLM 122:397,
doi:10.1007/s10546-006-9109-x · Henne et al. 2005, JAM 44:620, doi:10.1175/JAM2217.1 · Hennemuth 1986, BLM 36:371,
doi:10.1007/BF00118338 · Hocut et al. 2015, JFM 775:266, doi:10.1017/jfm.2015.298 · Hoch et al. 2011, JAMC 50:2473,
doi:10.1175/JAMC-D-11-083.1 · Horst & Doran 1986, BLM 34:263, doi:10.1007/BF00122382 · Hunt, Fernando & Princevac
2003, JAS 60:2169, doi:10.1175/1520-0469(2003)060<2169:UTDFOG>2.0.CO;2 · Iqbal 1983, *An Introduction to Solar
Radiation*, Academic Press · Kimura & Kuwagata 1993, JAM 32:1538, doi:10.1175/1520-0450(1993)032<1538:TIWPFP>2.0.CO;2 ·
Kopp & Lean 2011, GRL 38:L01706, doi:10.1029/2010GL045777 (not Crossref-checked) · Laiti et al. 2014, ACP 14:9771,
doi:10.5194/acp-14-9771-2014 · Largeron & Staquet 2016, Front. Earth Sci. 4:70, doi:10.3389/feart.2016.00070 ·
Lehner et al. 2021, QJRMS 147:2173, doi:10.1002/qj.4016 · Leukauf, Gohm & Rotach 2017, JAMC 56:2711,
doi:10.1175/JAMC-D-16-0378.1 · Lugauer & Winkler 2005, Meteorol. Z. 14:15, doi:10.1127/0941-2948/2005/0014-0015 ·
Mahrt 1982, JAS 39:2701, doi:10.1175/1520-0469(1982)039<2701:MBOGF>2.0.CO;2 · Manins & Sawford 1979a, QJRMS 105:1011,
doi:10.1002/qj.49710544618; 1979b, JAS 36:619, doi:10.1175/1520-0469(1979)036<0619:AMOKW>2.0.CO;2 · Matzinger et al.
2003, QJRMS 129:877, doi:10.1256/qj.02.44 · McNider & Pielke 1984, JCAM 23:1441, doi:10.1175/0733-3021-23.10.1441 ·
Nadeau et al. 2013, QJRMS 139:607, doi:10.1002/qj.1985 · Oke 1987, *Boundary Layer Climates* 2nd ed., Methuen
(reprint doi:10.4324/9780203407219) · Prandtl 1942, *Führer durch die Strömungslehre*, Vieweg · Princevac, Fernando &
Whiteman 2005, JFM 533:259, doi:10.1017/S0022112005004441 · Princevac, Hunt & Fernando 2008, JAS 65:627,
doi:10.1175/2007JAS2110.1 · Rampanelli, Zardi & Rotunno 2004, JAS 61:3097, doi:10.1175/JAS-3354.1 · Sabatier et al.
2018, Atmosphere 9:118, doi:10.3390/atmos9040118 · Schmid et al. 2020, Atmosphere 11:54, doi:10.3390/atmos11010054 ·
Schmidli 2013, JAS 70:4041, doi:10.1175/JAS-D-13-083.1 · Schmidli & Rotunno 2010, JAS 67:3033,
doi:10.1175/2010JAS3473.1 · Schmidli et al. 2011, MWR 139:1389, doi:10.1175/2010MWR3523.1 · Schumann 1990, QJRMS
116:637, doi:10.1002/qj.49711649307 · Simonet, Oettl & Lehner 2023, BLM 189:251, doi:10.1007/s10546-023-00835-9 ·
Steinacker 1984, Contrib. Atmos. Phys. 57:64 (not read) · Steinacker et al. 2007, BAMS 88:701,
doi:10.1175/BAMS-88-5-701 · Stull 1988, *An Introduction to Boundary Layer Meteorology*, Kluwer,
doi:10.1007/978-94-009-3027-8 · Urfer-Henneberger 1970, Arch. Meteor. Geophys. Bioklim. B 18:21,
doi:10.1007/BF02245866 · Van den Broeke 1997, BLM 83:183, doi:10.1023/A:1000268825998 · Vergeiner 1987
("An elementary valley wind model"; not read), MAP 36:255, doi:10.1007/BF01045153 · Vergeiner & Dreiseitl 1987, MAP
36:264, doi:10.1007/BF01045154 · Wagner, Gohm & Rotach 2015, ACP 15:6589, doi:10.5194/acp-15-6589-2015 · Weigel &
Rotach 2004, QJRMS 130:2605, doi:10.1256/qj.03.214 · Weigel et al. 2006, JAMC 45:87, doi:10.1175/JAM2323.1 ·
Weissmann et al. 2005, MWR 133:3095, doi:10.1175/MWR3012.1 · Whiteman 1982, JAM 21:270,
doi:10.1175/1520-0450(1982)021<0270:BOTIID>2.0.CO;2 · Whiteman & McKee 1982, JAM 21:290,
doi:10.1175/1520-0450(1982)021<0290:BOTIID>2.0.CO;2 · Whiteman 1990, Meteor. Monogr. 23(45):5,
doi:10.1007/978-1-935704-25-6_2 · Whiteman 2000, *Mountain Meteorology*, OUP, doi:10.1093/oso/9780195132717.001.0001 ·
Zängl 2004, MAP 87:241, doi:10.1007/s00703-003-0056-5 · Zardi & Whiteman 2013 ("Z&W"), in *Mountain Weather Research
and Forecasting*, Springer, 35–119, doi:10.1007/978-94-007-4098-3_2 · Zhong & Whiteman 2008, JAMC 47:2039,
doi:10.1175/2007JAMC1670.1
