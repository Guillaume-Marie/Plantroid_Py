# Plantroid – Technical Reference

*A detailed walk‑through of the algorithms and scientific assumptions behind the Plantroid\_Py code base.*

> Audience: researchers with expertise in plant ecophysiology, process‑based modelling and Python development.

---

## Table of contents

1. [Scope & philosophy](#1-scope--philosophy)
2. [Numerical framework](#2-numerical-framework)
3. [Environment sub‑model](#3-environment-sub-model)
4. [Plant state & parameters](#4-plant-state--parameters)
5. [Process equations](#5-process-equations)

   * 5.1 Photosynthesis & water cost
   * 5.2 Leaf energy balance & stomatal regulation
   * 5.3 Root absorption & nutrient dynamics
   * 5.4 Maintenance respiration & reserve buffering
   * 5.5 Biomass allocation & growth
   * 5.6 Phenology & life‑cycle strategies
6. [Resource accounting & mortality rules](#6-resource-accounting--mortality-rules)
7. [Species database & parameter provenance](#7-species-database--parameter-provenance)
8. [Numerical stability & performance](#8-numerical-stability--performance)
9. [Known limitations](#9-known-limitations)
10. [Bibliographic references](#10-bibliographic-references)

---

## 1. Scope & philosophy

Plantroid targets *conceptual clarity* rather than fine‑grained realism. The guiding design choices are:

| Principle                  | Code manifestation                                                                                                                                                                         |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Parsimony**              | Flat dictionaries (`Plant`, `Environment`, `history`) avoid deep OOP hierarchies; only 5 biomass pools & 3 resource currencies (sugar, water, nutrients).                                  |
| **Algorithm over algebra** | Each process is a short Python function whose output feeds the next; no implicit solvers except the scalar root $f\bigl(T_{leaf}\bigr)=0$ in `functions_BE.leaf_energy_balance_plantroid`. |
| **Hourly resolution**      | Coarse enough for desktop speed, fine enough to capture diurnal leaf temperature and stomatal swings.                                                                                      |

---

## 2. Numerical framework

* **Time step** $Δt = 1\,\mathrm{h}$ set in `global_constants.DT` ( $3600\,\mathrm{s}$ ).
* **Integrator** – explicit forward Euler; the sequence is hard‑wired in `time_loop.run_simulation_collect_data`:

```text
update_environment()  →  photosynthesis()  →  nutrient_absorption()
→ compute_max_transpiration_capacity()  →  leaf_energy_balance()
→ costs & respiration  →  allocate_biomass()  →  manage_phenology()
→ history_update()
```

If any critical pool becomes negative, `functions.check_for_negatives` flags the plant as dead and stops the loop.

---

## 3. Environment sub‑model

Implemented in **`Environnement_def.py`**.

| Variable        | Symbol    | Driver equation                                                         | Notes                                               |
| --------------- | --------- | ----------------------------------------------------------------------- | --------------------------------------------------- |
| Air temperature | $T_{air}$ | Seasonal sine (amplitude `T_amp_seasonal`) + diurnal sine + white noise | °C                                                  |
| PAR/shortwave   | $S$       | Scaled to clearness index; attenuated by solar zenith $\cos θ$          | W m⁻²                                               |
| Long‑wave       | $L↓$      | Stefan–Boltzmann from $T_{air}$ minus emissivity window                 | W m⁻²                                               |
| RH              | $h$       | Sinusoidally linked to $T_{air}$                                        | %                                                   |
| Wind            | $u$       | Daily triangular wave                                                   | m s⁻¹                                               |
| Soil water      | $θ$       | Bucket model: $θ_{t+1}=θ_t+P−E_t−D$                                     | *P* from random storms; *E* == actual transpiration |

All parameters are overridable via the `Environment` dict.

---

## 4. Plant state & parameters

### 4.1 Biomass pools (g dry mass)

| Key         | Biological meaning                | Used in                                          |
| ----------- | --------------------------------- | ------------------------------------------------ |
| `transport` | xylem, phloem, supportive tissues | Transport capacity, maximum height (future work) |
| `photo`     | leaves / needles                  | Light capture, transpiration                     |
| `absorp`    | absorbing roots                   | Soil exploration & water uptake                  |
| `stock`     | non‑structural reserves           | Buffering of C & nutrients                       |
| `repro`     | flowers, fruits, seeds            | Fitness proxy                                    |

### 4.2 Fluxes & costs

All fluxes are stored per cycle in `Plant["flux_in"]`, `Plant["cost"]`, then zeroed at each call to `post_process_success` / `post_process_resist`.

### 4.3 Parameter provenance

Species‑level traits (SLA, $T_{opt}$, leaf albedo, C\:N ratios, …) are loaded from `species_db` via `Plant_def.set_plant_species`. Default entries come from peer‑reviewed compilations (see §7).

---

## 5. Process equations

### 5.1 Photosynthesis & water cost  (`functions.photosynthesis`)

```python
absorbed = PAR * cos(leaf_angle) * (1 - albedo)
power_W = absorbed * SLA_max * slai
T_lim  = max(0, 1 - temp_sens * |T_leaf - T_opt|)
A_pot  = power_W * watt_to_sugar_coeff * T_lim * nutrient_index
A_real = A_pot * (CO2/400) * stomatal_conductance
C_gain = A_real * biomass_photo * Δt
```

*Assumptions*

* Light‑use efficiency is linear with absorbed energy.
* Temperature response is triangular with slope `temp_photo_sensitivity`.
* The CO₂ factor normalises to 400 ppm (pre‑industrial baseline).
* Sugar formation costs water at a fixed stoichiometric ratio
  $\mathrm{H₂O:C₆H₁₂O₆}=11.5$ (`Gl.RATIO_H2O_C6H12O6`).

### 5.2 Leaf energy balance & stomatal regulation  (`functions_BE.leaf_energy_balance_plantroid`)

The leaf temperature $T_L$ is solved from

$R_n(T_L) \;−\; H(T_L) \;−\; λE(T_L) = 0$

where

* $R_n$ – net radiation with geometry factor $\cos(θ)$,
* $H$ – sensible heat via forced convection over an ellipse of size `leaf_size`,
* $λE$ – latent heat **limited** by `Plant["max_transpiration_capacity"]`.

The stomatal conductance is reduced when `max_transpiration_capacity` is lower than potential demand, inducing *coupled* regulation of $λE$ and photosynthesis.

### 5.3 Root absorption & nutrient dynamics  (`functions.nutrient_absorption`)

Nutrient influx is proportional to root‑explored soil volume and the soil nutrient index. A Michaelis–Menten saturation avoids infinite uptake when soil is rich.

### 5.4 Maintenance respiration & reserve buffering  (`functions.ensure_maintenance_sugar`, `functions.refill_reserve`)

* Maintenance cost scales with active biomass and health state.
* If photosynthesis is insufficient, the `stock` pool is catabolised.
* Below a critical reserve ratio the plant health `health_state` decays (see §6).

### 5.5 Biomass allocation & growth  (`functions.allocate_biomass`)

```python
ratio = Plant["ratio_alloc"]  # dict with five keys
for pool, frac in ratio.items():
    Plant["biomass"][pool] += new_biomass * frac
```

`ratio_alloc` is dynamic and can be altered by stress modules (e.g. more root investment when `soil_water_index` < threshold).

Growth consumes sugar, water and nutrients according to pool‑specific construction costs (`cost_coeff_*`).

### 5.6 Phenology & life‑cycle strategies  (`functions.manage_phenology`)

State machine with nodes *seed / vegetative / reserve / dormancy / reproduction / senescence*. Transition triggers include:

* 7‑day mean $T_{air}$ below `T_dormancy`,
* integrated photoperiod < `P_crit`,
* slope of sugar over the last `n` hours becoming negative (`slope_last_hours`).

Annual, biannual or perennial branches share the same code but differ in transition permissions.

---

## 6. Resource accounting & mortality rules

`functions.post_process_resist` compares **costs** vs **fluxes**.

* If any resource balance is negative after using reserves → pool‑specific damage.
* Health $H ∈ [0,1]$ degrades at rate proportional to unmet maintenance; if $H < H_{crit}$ the organ is destroyed via `destroy_biomass`.
* Total biomass < `biomass_min_alive` ⇒ `Plant["alive"] = False`.

---

## 7. Species database & parameter provenance

| Trait                    | Symbol    | Units  | Default source        |
| ------------------------ | --------- | ------ | --------------------- |
| Specific leaf area       | SLA\_max  | m² g⁻¹ | Poorter *et al.* 2009 |
| Optimal leaf T           | $T_{opt}$ | °C     | Medlyn *et al.* 2002  |
| Stomatal slope           | $g₁$      | –      | Leuning 1995          |
| Construction cost (root) | $c_r$     | gC g⁻¹ | Penning de Vries 1975 |

*(Full table in `Plant_def.species_db`)*

---

## 8. Numerical stability & performance

* All fluxes are bounded by `max_transpiration_capacity` and `compute_available_water`, preventing runaway evaporation.
* Only one non‑linear solve (leaf T) per hour ⇒ <10 µs on a modern CPU.
* Entire 3‑year perennial run (26 k cycles) completes in \~0.7 s on Intel i7‑1185G.

---

## 9. Known limitations

1. No carboxylation kinetics (Rubisco) – CO₂ enters linearly.
2. Soil is a single bucket; no capillary rise or drainage profile.
3. Nitrogen and phosphorus merged into a single “nutrient” currency.
4. No size‑dependent hydraulics; height is implicit.

---

## 10. Bibliographic references

* Leuning R. (1995). *A critical appraisal of a combined stomatal–photosynthesis model.*
* Medlyn B.E. *et al.* (2002). *Temperature response of parameters of a biochemically based model of photosynthesis.*
* Penman H.L. (1948). *Natural evaporation from open water, bare soil and grass.*
* Penning de Vries F.W\.T. (1975). *The cost of maintenance processes in plant cells.*
* Poorter H. *et al.* (2009). *Causes and consequences of variation in leaf mass per area (LMA): a meta‑analysis.*

---

*Document version: v1.0 – May 2025*
