"""Physical parameters. Every value must come from the literature (see
docs/physics_notes.md, "Recommended defaults"), NEVER from fitting the
validation map. [est] = estimate in the notes."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Params:
    # --- constants
    g: float = 9.81
    rho: float = 1.1            # air density at ~1000 m [kg/m3]
    cp: float = 1005.0
    theta0: float = 293.0       # [est]

    # --- radiation / surface energy balance (clear sky)
    S0: float = 1361.0          # Kopp & Lean 2011
    tau_beam: float = 0.75      # clear-sky beam transmissivity at sea level [est]
    diffuse_frac: float = 0.12  # diffuse / extraterrestrial-on-horizontal [est]
    albedo: float = 0.20        # Oke 1987; uniform in phase 1 (phase 2: raster)
    lw_net_clear: float = -70.0 # open site, x sky-view (De Wekker & Whiteman 2006) [est]
    h_frac_day: float = 0.30    # Bowen ~0.5, G = 0.1 Rn (Stull 1988) [est]
    h_frac_night: float = 0.50  # [est]

    # --- stratification
    gamma_day: float = 0.0035   # free-atmosphere dtheta/dz [K/m] [est]
    gamma_night: float = 0.025  # nocturnal valley inversion (De Wekker & Whiteman 2006)

    # --- valley-scale (hypsometric mixed layer) model
    sigma_valley: float = 3000.0  # lateral mixing footprint [m] (~valley half-width) [est]
    chan_area_km2: float = 5.0    # min catchment for a valley-wind channel [est]
    heat_export: float = 0.3      # fraction of valley heat exported at crest (Leukauf et al. 2017)
    tau_residual_h: float = 4.5   # evening residual-heat decay = cooling time scale (De Wekker & Whiteman 2006)
    drag_valley: float = 3.0e-5   # C_D,eff / h = 0.03 / 1000 m [derived, weakest number]
    tau_valley_h: float = 2.0     # linear damping (Giovannini et al. 2017) [est]

    # --- slope winds: u = (|B| dz / c)^(1/3)  (Manins & Sawford 1979 layer eqs)
    c_slope: float = 0.04         # C_D + E (Princevac et al. 2005)
    dz_max_day: float = 1000.0    # height gain capped at CBL depth (Hunt et al. 2003) [est]
    fetch_max_night: float = 3000.0  # [est]
    hand_valley_scale: float = 200.0  # valley-wind weight e-folding with HAND [m] [est]


DEFAULT = Params()
