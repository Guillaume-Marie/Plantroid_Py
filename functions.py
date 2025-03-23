# functions.py
"""
General physiological, growth, and resource-management functions for the Plantroid model.
Comments and docstrings are in English, while function/variable names remain in French
to preserve compatibility with other modules.
"""

import global_constants as Gl
import history_def as Hi
import Environnement_def as Ev
import global_constants as Gl
import math
import numpy as np


###############################################
#           PLANT HEALTH AND CHECKS           #
###############################################

def check_for_negatives(Plant, Env, time):
    """
    Verifies if any plant biomass or flux is negative.
    If found, prints an error and sets Plant["alive"] = False.

    Parameters
    ----------
    Plant : dict
        Main plant dictionary including biomass and flux states.
    Env : dict
        Environment dictionary, in case some debug info is needed.
    time : int or float
        Current simulation time (hours).

    Returns
    -------
    bool
        True if a negative was found (plant is set to dead), False otherwise.
    """

    # 1) Check biomass compartments
    for compartment, val in Plant["biomass"].items():
        if val < -1e-12:
            print("====================================================")
            print(f"ERROR: Negative biomass detected at t={time} h!")
            print(f"Compartment '{compartment}' = {val:.5f}")
            print("Diagnostic info:")
            print(f"  - biomasse totale: {Plant['biomass_total']:.5f}")
            print(f"  - photo: {Plant['biomass']['photo']:.5f}")
            print(f"  - absorp: {Plant['biomass']['absorp']:.5f}")
            print(f"  - support: {Plant['biomass']['support']:.5f}")
            print(f"  - repro: {Plant['biomass']['repro']:.5f}")
            print(f"  - flux_in sugar: {Plant['flux_in']['sugar']:.5f}")
            print(f"  - flux_in water: {Plant['flux_in']['water']:.5f}")
            print(f"  - flux_in nutrient: {Plant['flux_in']['nutrient']:.5f}")
            print(f"  - reserve sugar: {Plant['reserve']['sugar']:.5f}")
            print(f"  - reserve water: {Plant['reserve']['water']:.5f}")
            print(f"  - reserve nutrient: {Plant['reserve']['nutrient']:.5f}")
            print(f"  - phenology_stage: {Plant['phenology_stage']}")
            print(f"  - health_state: {Plant['health_state']}")
            print("====================================================")
            Plant["alive"] = False
            return True

    # 2) Check flux_in
    for flux_name, val in Plant["flux_in"].items():
        if val < -1e-12:
            print("====================================================")
            print(f"ERROR: Negative flux detected at t={time} h!")
            print(f"Flux '{flux_name}' = {val:.5f}")
            print("Diagnostic info:")
            print(f"  - biomass total: {Plant['biomass_total']:.5f}")
            print(f"  - photo: {Plant['biomass']['photo']:.5f}")
            print(f"  - absorp: {Plant['biomass']['absorp']:.5f}")
            print(f"  - support: {Plant['biomass']['support']:.5f}")
            print(f"  - repro: {Plant['biomass']['repro']:.5f}")
            print(f"  - flux_in sugar: {Plant['flux_in']['sugar']:.5f}")
            print(f"  - flux_in water: {Plant['flux_in']['water']:.5f}")
            print(f"  - flux_in nutrient: {Plant['flux_in']['nutrient']:.5f}")
            print(f"  - reserve sugar: {Plant['reserve']['sugar']:.5f}")
            print(f"  - reserve water: {Plant['reserve']['water']:.5f}")
            print(f"  - reserve nutrient: {Plant['reserve']['nutrient']:.5f}")
            print(f"  - phenology_stage: {Plant['phenology_stage']}")
            print(f"  - health_state: {Plant['health_state']}")
            print("====================================================")
            Plant["alive"] = False
            return True

    return False  # no negatives found


def degrade_health_state(Plant):
    """
    Decreases the plant health by 1 unit. If health goes below 0, increments dying_state_count.
    """
    Plant["health_state"] -= 1
    if Plant["health_state"] < 0:
        Plant["dying_state_count"] += 1
    else:
        Plant["dying_state_count"] = 0


def restore_health(Plant):
    """
    Increases the plant health by 1 unit, capped at 100.
    """
    if Plant["health_state"] < 100:
        Plant["health_state"] += 1


def destroy_biomass(Plant, Env, which_biomass, process, damage_factor=None):
    """
    Destroys a fraction of the specified biomass compartment and adds it to necromass.
    Optionally recovers some water/nutrients (if a more detailed model is used).

    Parameters
    ----------
    Plant : dict
    Env : dict
    which_biomass : str
        A key in Plant["biomass"] (e.g. "photo", "support", "absorp", "necromass")
    process : str or None
        The name of the process causing destruction, if applicable (else None).
    damage_factor : float
        Fraction of biomass to destroy. If None, defaults to Gl.delta_adapt.
    """

    if damage_factor is None:
        damage_factor = Gl.delta_adapt

    lost = Plant["biomass"][which_biomass] * damage_factor
    Plant["biomass"][which_biomass] -= lost

    if which_biomass in ["necromass", "repro"]:
        Env["litter"]["necromass"] += lost
    else:
        Plant["biomass"]["necromass"] += lost

    # Potential partial re-translocation (not fully implemented here).
    # For example, if "nutrient" or "water" is recovered, you could adjust Plant["reserve"] or Env.

    update_biomass_total(Plant)


###############################################
#            MAINTENANCE AND RESERVES         #
###############################################

def ensure_maintenance_sugar(Plant, Env):
    """
    Checks if the plant has enough sugar for maintenance. If not, performs
    a "cannibalization" by destroying some living biomass to recover sugar.

    Parameters
    ----------
    Plant : dict
    Env : dict
    """
    needed_sugar = Plant["cost"]["maintenance"]["sugar"]
    available_sugar = Plant["flux_in"]["sugar"] + Plant["reserve"]["sugar"]
    shortfall = needed_sugar - available_sugar
    if shortfall <= 0:
        return  # enough sugar, no action

    # Otherwise, destroy biomass to recover sugar
    compartments_order = ["photo", "absorp", "support"]  # priority for cannibalization
    mass_to_destroy = shortfall / Plant["cannibal_ratio"]

    for comp in compartments_order:
        if mass_to_destroy <= 0:
            break
        if Plant["biomass"][comp] > 0:
            can_destroy = Plant["biomass"][comp] * 0.05
            destroy_here = min(can_destroy, mass_to_destroy)

            Plant["biomass"][comp] -= destroy_here
            if comp in ["necromass", "repro"]:
                Env["litter"]["necromass"] += destroy_here
            else:
                Plant["biomass"]["necromass"] += destroy_here

            sugar_recovered = destroy_here * Plant["cannibal_ratio"]
            Plant["flux_in"]["sugar"] += sugar_recovered
            mass_to_destroy -= destroy_here

    update_biomass_total(Plant)

    remaining_shortfall = (
        Plant["cost"]["maintenance"]["sugar"] - (Plant["flux_in"]["sugar"] + Plant["reserve"]["sugar"])
    )
    # If there's still not enough sugar even after cannibalization, we could degrade health
    if remaining_shortfall > 0:
        pass
        # degrade_health_state(Plant) # optional approach


def refill_reserve(Plant, rsc):
    """
    Transfers all of flux_in[rsc] into Plant["reserve"][rsc], up to a certain logic limit.
    """
    if rsc == "water" and Plant["reserve"][rsc] >= Plant["biomass_total"]:
        return

    if Plant["flux_in"][rsc] >= 0.0:
        usable_in = Plant["flux_in"][rsc] * Gl.delta_adapt
        Plant["flux_in"][rsc] -= usable_in
        Plant["reserve"][rsc] += usable_in
    else:
        print("Error in refill_reserve: flux_in is negative for", rsc, Plant["flux_in"][rsc])


###############################################
#        GROWTH RATE AND PHOTOSYNTHESIS       #
###############################################

def calculate_potential_new_biomass(Plant, bm_total):
    """
    Uses a monomolecular growth form:
      new_biomass = bm_total * (r_max / (1 + alpha * bm_total))

    Parameters
    ----------
    Plant : dict
    bm_total : float
        Current total living biomass of the plant.

    Returns
    -------
    float
        Potential new biomass growth for this timestep.
    """
    r_max = Plant["r_max"]
    alpha = Plant["alpha"]
    return bm_total * (r_max / (1.0 + alpha * bm_total))


def photosynthesis(Plant, Env):
    """
    Computes photosynthesis, updating flux_in["sugar"] based on light absorption,
    temperature, and stomatal conditions.

    Also calculates water cost for sugar formation.

    Parameters
    ----------
    Plant : dict
    Env : dict
    """
    cos_theta = max(0.0, math.cos(Plant["leaf_angle"]))
    absorbed_solar = Env["atmos"]["light"] * cos_theta * (1.0 - Plant["leaf_albedo"])

    # Power absorbed J/s/gLeaf
    power_absorbed = absorbed_solar * Plant["sla_max"] * Plant["slai"]

    # Temperature limitation
    temp_diff = abs(Plant["temperature"]["photo"] - Plant["T_optim"])
    temp_lim = max(0.0, 1.0 - Plant["temp_photo_sensitivity"] * temp_diff)

    # Potential flux gC6H12O6/s/gLeaf
    c6_flux_pot = (power_absorbed *
                   Plant["watt_to_sugar_coeff"] *
                   temp_lim *
                   Plant["nutrient_index"])

    # CO2 factor
    cf = Env["atmos"]["Co2"] / 400.0

    # Stomatal conductance factor
    c6_flux = c6_flux_pot * cf * Plant["stomatal_conductance"] * Plant["nutrient_index"]

    # Convert flux to total sugar per hour (gC6H12O6 / hour)
    Plant["flux_in"]["sugar"] = c6_flux * Plant["biomass"]["photo"] * Gl.DT

    # Water cost of forming sugar
    Plant["cost"]["transpiration"]["water"] += Plant["flux_in"]["sugar"] * Gl.RATIO_H2O_C6H12O6

    # Diagnostics
    Plant["diag"]["raw_sugar_flux"] = power_absorbed * Plant["watt_to_sugar_coeff"]
    Plant["diag"]["pot_sugar"] = c6_flux
    Plant["diag"]["actual_sugar"] = Plant["flux_in"]["sugar"]


def nutrient_absorption(Plant, Env):
    """
    Calculates how much water and nutrients the plant takes from the soil,
    based on the transpiration water need, soil available water, and
    a water_nutrient_coeff that translates water uptake into nutrient uptake.

    Parameters
    ----------
    Plant : dict
    Env : dict
    """
    water_needed = Plant["cost"]["transpiration"]["water"]
    if water_needed <= 0.0:
        return

    water_in_soil = Env["soil"]["water"]
    if water_in_soil <= 0.0:
        return

    water_absorbed = min(water_needed, water_in_soil)

    soil_nutrient_total = Env["soil"]["nutrient"]
    soil_water = Env["soil"]["water"]
    if soil_water > 0:
        Env["soil"]["nutrient_concentration"] = soil_nutrient_total / soil_water
    else:
        Env["soil"]["nutrient_concentration"] = 0.0

    nutrients_pot_absorbed = (
        water_absorbed *
        Env["soil"]["nutrient_concentration"] *
        Plant["water_nutrient_coeff"]
    )
    nutrients_absorbed = min(nutrients_pot_absorbed, Env["soil"]["nutrient"])

    Plant["flux_in"]["nutrient"] += nutrients_absorbed
    Env["soil"]["water"] -= water_absorbed
    Env["soil"]["nutrient"] -= nutrients_absorbed

    if "diag" not in Plant:
        Plant["diag"] = {}
    Plant["diag"]["nutrient_absorption"] = {
        "water_absorbed": water_absorbed,
        "nutrients_absorbed": nutrients_absorbed,
        "nutrient_concentration": Env["soil"].get("nutrient_concentration", 0.0)
    }


###############################################
#        STOMATAL, ROOT, AND TRANSPIRATION    #
###############################################

def compute_stomatal_area(Plant):
    """
    Computes an approximate stomatal pore area factor for the leaf
    (stomatal_density * total leaf area).

    Returns
    -------
    float
        Dimensionless area fraction or area factor.
    """
    return (Plant["stomatal_density"] *
            Plant["biomass"]["photo"] *
            Plant["sla_max"] *
            Plant["slai"])


def compute_stomatal_conductance_max(Plant):
    """
    Calculates the maximum possible stomatal conductance (m/s)
    based on the fraction of pore area and simplified diffusion.

    Returns
    -------
    float
        Max stomatal conductance in m/s.
    """
    area_fraction = compute_stomatal_area(Plant)
    g_stomatal_max = area_fraction * (Gl.D_H2O / Gl.pore_depth)
    return g_stomatal_max


def compute_root_explored_volume(Plant, Env):
    """
    Calculates the volume of soil explored by the root system
    based on the absorp biomass and a constant k_root.

    Returns
    -------
    float
        Explored volume in cm³, clamped to Env["soil_volume"]*1e6.
    """
    explored_volume = Plant["biomass"]["absorp"] * Gl.k_root
    return min(explored_volume, Env["soil_volume"] * 1e6)


def compute_available_water(Plant, Env):
    """
    Calculates how much water is available to the plant from the portion of soil
    that the roots explore.

    Returns
    -------
    float
        Amount of water (g) that can be accessed by the plant.
    """
    explored_volume = compute_root_explored_volume(Plant, Env)
    soil_moisture = Env["soil"]["water"] / (Env["soil_volume"] * 1e6)
    available_water = explored_volume * soil_moisture
    return min(available_water, Env["soil"]["water"])

import math

def compute_cell_water_draw(Plant):
    """
    Calcule la quantité d'eau mobilisable en puisant dans la réserve cellulaire,
    de façon progressive. Plus on est proche de la limite (min_cell_water), 
    moins on peut puiser facilement.

    Paramètres
    ----------
    Plant : dict
      - Plant["biomass_total"] (g) : biomasse totale
      - Plant["reserve"]["water"] (g) : réserve d'eau interne dans les cellules
    max_ratio : float
      Proportion maximale d’eau cellulaire qui peut être consommée 
      (ex: 0.15 => 15% de la biomasse).
    smoothing_factor : float
      Contrôle la "vitesse" de saturation exponentielle 
      (plus il est petit, plus la courbe est lente => on pioche peu dès qu'on se rapproche du min).

    Retour
    ------
    draw_possible : float
      Quantité d’eau mobilisable (g), calculée de manière dégressive.
    """
    biomass = Plant["biomass_total"]
    water_reserve = Plant["reserve"]["water"]

    # Seuil minimal d’eau = 15% de la biomasse (par défaut),
    # en dessous duquel on considère la plante en flétrissement sévère.
    min_cell_water = Plant["max_turgor_loss_frac"] * biomass

    delta = water_reserve - min_cell_water
    if delta <= 0.0:
        # La réserve est déjà sous le seuil
        return 0.0

    # Approche exponentielle : 
    #   ratio = 1 - exp(- (delta / (smoothing_factor * min_cell_water)) )
    #   draw = delta * ratio
    # =>  - si delta est très petit, ratio ~ delta/... => draw << delta 
    #     - si delta est grand, ratio -> 1 => draw ~ delta
    alpha = 0.2 * min_cell_water
    ratio = 1.0 - math.exp(- delta / alpha)  
    draw_possible = delta * ratio

    return draw_possible

def compute_max_transpiration_capacity(Plant, Env):
    """
    Calculates the plant's maximum transpiration capacity (in g of water per cycle),
    determined by stomatal, support transport, and soil water availability.

    The limiting pool sets the maximum possible transpiration:
    - photo : limited by stomatal conduction
    - support : limited by transport capacity
    - soil : limited by available water in the soil

    The result is stored in Plant["max_transpiration_capacity"] and
    the limiting pool in Plant["transp_limit_pool"].
    """
    gs = compute_stomatal_conductance_max(Plant) * Plant["stomatal_conductance"]
    photo_capacity = gs * Gl.D_H2O * Gl.VPD * Gl.DT

    support_capacity = (
        Plant["biomass"]["support"] * Plant["support_transport_coeff"] * Gl.DT
    )
    
    soil_capacity = compute_available_water(Plant, Env)  

    capacities = {
        "photo": photo_capacity,
        "support": support_capacity,
        "soil": soil_capacity
    }
    min_capacity = min(capacities.values())
    limiting_pool = min(capacities, key=capacities.get)

    Plant["max_transpiration_capacity"] = min_capacity
    Plant["transp_limit_pool"] = limiting_pool


###############################################
#         PROCESS SUCCESS OR FAILURE          #
###############################################

def post_process_success(Plant, Env, process):
    """
    Called when resources are sufficient for a process (maintenance, extension, reproduction).
    Pays the cost, updates compartments, and can restore health.
    """
    if process == "maintenance":
        pay_cost(Plant, Env, process)
    elif process == "extension":
        allocate_biomass(Plant, Plant["new_biomass"])
        pay_cost(Plant, Env, process)
        restore_health(Plant)
    elif process == "reproduction":
        allocate_biomass(Plant,Plant["new_biomass"])
        pay_cost(Plant, Env, process)
        restore_health(Plant)


def post_process_resist(Plant, Env, process):
    """
    Called when the plant is partially resisting the resource shortage (after drawing reserves).
    """
    if process == "maintenance":
        pay_cost(Plant, Env, process)
    elif process == "extension":
        allocate_biomass(Plant, Plant["new_biomass"])
        pay_cost(Plant, Env, process)
        adjust_success_cycle(Plant, "extension")
        restore_health(Plant)
    elif process == "reproduction":
        allocate_biomass(Plant,Plant["new_biomass"])
        pay_cost(Plant, Env, process)
        adjust_success_cycle(Plant, "reproduction")
        restore_health(Plant)


def post_process_fail(Plant, Env, process):
    """
    Called when resources remain insufficient (after adjusting cost and reserves).
    The process fails or is partially canceled.
    """
    if process == "maintenance":
        pay_cost(Plant, Env, process)
        degrade_health_state(Plant)
        ensure_maintenance_sugar(Plant, Env)

    elif process == "extension":
        adjust_success_cycle(Plant, "extension")
        if Plant["success_cycle"]["extension"] > 0:
            pay_cost(Plant, Env, process)
            allocate_biomass(Plant, Plant["new_biomass"])

    elif process == "reproduction":
        adjust_success_cycle(Plant, "reproduction")
        #if Plant["success_cycle"]["reproduction"] > 0:
        #    pay_cost(Plant, Env, process)
        #    allocate_biomass(Plant,Plant["new_biomass"])


###############################################
#        MAIN PROCESS HANDLER / COST          #
###############################################

def handle_process(Plant, Env, process):
    """
    Verifies resource availability for a process, tries to use reserves,
    possibly adjusts the cost, then decides if it succeeds, partially succeeds,
    or fails. Calls post_process_{success,resist,fail} accordingly.
    """
    if resources_available(Plant, process):
        update_stress_history(Plant, process)
        post_process_success(Plant, Env, process)
        return

    draw_from_reserves(Plant, process)
    if resources_available(Plant, process):
        update_stress_history(Plant, process)
        post_process_resist(Plant, Env, process)
        return

    adjust_cost(Plant, Env, process)
    update_stress_history(Plant, process)
    if resources_available(Plant, process):
        post_process_resist(Plant, Env, process)
    else:
        post_process_fail(Plant, Env, process)


def resources_available(Plant, process):
    """
    Checks if flux_in is sufficient to cover the cost for a given process.
    """
    return (
        Plant["flux_in"]["sugar"] >= Plant["cost"][process]["sugar"]
        and Plant["flux_in"]["nutrient"] >= Plant["cost"][process]["nutrient"]
        and Plant["flux_in"]["water"] >= Plant["cost"][process]["water"]
    )


def pay_cost(Plant, Env, process):
    """
    Deducts the process cost from the flux_in, or sugar alone in case of maintenance.
    """
    if process in ["extension", "reproduction"]:
        Plant["flux_in"]["sugar"] -= Plant["cost"][process]["sugar"]
        Plant["flux_in"]["nutrient"] -= Plant["cost"][process]["nutrient"]
        Plant["flux_in"]["water"] -= Plant["cost"][process]["water"]
    elif process == "maintenance":
        Plant["flux_in"]["sugar"] -= Plant["cost"][process]["sugar"]


def calculate_cost(Plant, Env, process):
    """
    Fills Plant["cost"][process] with the estimated resource costs for that process.

    - Maintenance: proportional to biomass_total and time
    - Extension: depends on new_biomass
    - Reproduction: depends on reproduction_ref
    """
    if process == "reproduction":
        for r in Gl.resource:
            cost_factor = Plant["cost_params"][process]["unique"][r]
            Plant["cost"][process][r] = cost_factor * Plant["new_biomass"] * Plant["ratio_allocation"]["repro"] 

    elif process == "maintenance":
        cost_factor = Plant["cost_params"][process]["unique"]["sugar"]
        Plant["cost"][process]["sugar"] = cost_factor * Gl.DT * Plant["biomass_total"]

    else:  # extension
        for bf in Gl.biomass_function:
            for r in Gl.resource:
                cost_factor = Plant["cost_params"]["extension"][bf][r]
                Plant["cost"][process][r] += cost_factor * Plant["new_biomass"] * Plant["ratio_allocation"][bf] 


def adjust_cost(Plant, Env, process):
    """
    If not enough resources or capacity, we reduce the cost (and new_biomass) accordingly.
    """
    Plant["adjusted_used"][process] = True

    if process == "extension":
        limiting_bio = Plant["new_biomass"]
        for bf in Gl.biomass_function:
            for r in Gl.resource:
                denom = Plant["cost_params"]["extension"][bf][r]
                if denom > 0:
                    max_bio = Plant["flux_in"][r] / denom if denom != 0 else 0
                    if max_bio < limiting_bio:
                        limiting_bio = max_bio

        Plant["new_biomass"] = limiting_bio
        # Recompute cost with updated new_biomass
        for bf in Gl.biomass_function:
            for r in Gl.resource:
                cost_factor = Plant["cost_params"]["extension"][bf][r]
                Plant["cost"][process][r] = cost_factor * Plant["new_biomass"]

    elif process == "reproduction":
        limiting_bio = float('inf')
        for r in Gl.resource:
            denom = Plant["cost_params"][process]["unique"][r]
            if denom > 0:
                max_bio = Plant["flux_in"][r] / denom
                if max_bio < limiting_bio:
                    limiting_bio = max_bio

        if limiting_bio < Plant["new_biomass"]:
            Plant["new_biomass"] = limiting_bio

        for r in Gl.resource:
            cost_factor = Plant["cost_params"][process]["unique"][r]
            Plant["cost"][process][r] = cost_factor * limiting_bio

    elif process == "maintenance":
        pass  # generally only sugar cost, handled by cannibalization if needed


def draw_from_reserves(Plant, process):
    """
    Tries to cover the shortfall of flux_in by drawing from the internal reserves.
    """
    for r in Gl.resource:
        shortfall = Plant["cost"][process][r] - Plant["flux_in"][r]
        if shortfall > 0 and Plant["reserve"][r] > 0:
            transfer = min(shortfall, Plant["reserve"][r])
            Plant["reserve"][r] -= transfer
            Plant["flux_in"][r] += transfer

    Plant["reserve_used"][process] = True


def compute_stress(Plant, process):
    """
    Computes a stress measure (0..1) for maintenance (sugar) or transpiration (water).

    Parameters
    ----------
    Plant : dict
    process : str

    Returns
    -------
    (float, str)
        (stress_value, resource_name) e.g. (0.5, "sugar")
    """
    if process == "maintenance":
        sugar_available = Plant["flux_in"]["sugar"] + Plant["reserve"]["sugar"]
        needed = Plant["cost"]["maintenance"]["sugar"]
        if needed <= 0:
            return (0.0, "sugar")
        ratio_available = sugar_available / needed
        stress = 1.0 - min(1.0, ratio_available / Gl.N)
        return (stress, "sugar")

    elif process == "transpiration":
        water_available = Plant["reserve"]["water"]
        needed = Plant["cost"]["maintenance"]["water"]
        if needed <= 0:
            return (0.0, "water")
        ratio_available = water_available / needed
        stress = 1.0 - min(1.0, ratio_available / Gl.N)
        return (stress, "water")

    return (0.0, "")


def update_success_history(Plant, process):
    """
    Appends the current success_cycle[process] to the success_history[process].
    """
    sc = Plant["success_cycle"].get(process, 0.0)
    Plant["success_history"][process].append(sc)
    Plant["success_history"][process] = Gl.keep_last_N(Plant["success_history"][process], Gl.N)


def update_stress_history(Plant, process):
    """
    Appends a stress measure to the appropriate stress_history for sugar or water.
    """
    if process in ["maintenance", "transpiration"]:
        cycle_stress, rsc = compute_stress(Plant, process)
        Plant["stress_history"][rsc].append(cycle_stress)
        Plant["stress_history"][rsc] = Gl.keep_last_N(Plant["stress_history"][rsc], Gl.N)


###############################################
#        PHENOLOGY AND BIOMASS ALLOCATION     #
###############################################

def adapt_leaf_structure(Plant, Env):
    """
    Adjusts SLAI based on the light level in Env.
    If light < 300, decrease SLAI; if light > 800, increase SLAI.
    """
    if Env["atmos"]["light"] < 300:
        Plant["slai"] = max(0.01, Plant["slai"] - Gl.delta_adapt)
    elif Env["atmos"]["light"] > 800:
        Plant["slai"] = min(1.0, Plant["slai"] + Gl.delta_adapt)


def adapt_leaf_nutrient(Plant):
    """
    Simplified approach to adapt the plant's nutrient index and cost parameters
    if it experiences nutrient stress.
    """
    Plant["nutrient_index"] = max(0.1, Plant["nutrient_index"] - Gl.delta_adapt)
    Plant["cost_params"]["extension"]["photo"]["nutrient"] = max(
        0.001,
        Plant["cost_params"]["extension"]["photo"]["nutrient"] - Gl.delta_adapt
    )
    Plant["cost_params"]["extension"]["absorp"]["nutrient"] = max(
        0.001,
        Plant["cost_params"]["extension"]["absorp"]["nutrient"] - Gl.delta_adapt
    )
    Plant["cost_params"]["extension"]["support"]["nutrient"] = max(
        0.001,
        Plant["cost_params"]["extension"]["support"]["nutrient"] - Gl.delta_adapt
    )


def adapt_water_supply(Plant, Env):
    """
    Reallocates biomass investment in case of chronic water stress.
    Shifts ratio_allocation to favor root or support, etc.
    """
    if Plant["transp_limit_pool"] == "soil":
        # More root allocation
        if Plant["ratio_allocation"]["absorp"] <= 0.8:
            Plant["ratio_allocation"]["support"] = max(Plant["ratio_allocation"]["support"] - Gl.delta_adapt / 2, 0.0)
            Plant["ratio_allocation"]["absorp"] += Gl.delta_adapt
            Plant["ratio_allocation"]["photo"] = max(Plant["ratio_allocation"]["photo"] - Gl.delta_adapt / 2, 0.0)

    elif Plant["transp_limit_pool"] == "support":
        if Plant["ratio_allocation"]["support"] <= 0.8:
            Plant["ratio_allocation"]["support"] += Gl.delta_adapt
            Plant["ratio_allocation"]["absorp"] = max(Plant["ratio_allocation"]["absorp"] - Gl.delta_adapt / 2, 0.0)
            Plant["ratio_allocation"]["photo"] = max(Plant["ratio_allocation"]["photo"] - Gl.delta_adapt / 2, 0.0)

    elif Plant["transp_limit_pool"] == "photo":
        if Plant["ratio_allocation"]["photo"] <= 0.8:
            Plant["ratio_allocation"]["support"] = max(Plant["ratio_allocation"]["support"] - Gl.delta_adapt / 2, 0.0)
            Plant["ratio_allocation"]["photo"] += Gl.delta_adapt
            Plant["ratio_allocation"]["absorp"] = max(Plant["ratio_allocation"]["absorp"] - Gl.delta_adapt / 2, 0.0)
        adapt_leaf_structure(Plant, Env)

    check_allocation(Plant)


def adapt_for_reproduction(Plant):
    """
    Increases the ratio of biomass allocated to reproduction, up to alloc_repro_max.
    Decreases other allocations proportionally.
    """
    if Plant["ratio_allocation"]["repro"] <= Plant["alloc_repro_max"]:
        change = Plant["alloc_change_rate"]
        Plant["ratio_allocation"]["support"] = max(Plant["ratio_allocation"]["support"] - change / 3, 0.0)
        Plant["ratio_allocation"]["photo"] = max(Plant["ratio_allocation"]["photo"] - change / 3, 0.0)
        Plant["ratio_allocation"]["absorp"] = max(Plant["ratio_allocation"]["absorp"] - change / 3, 0.0)
        Plant["ratio_allocation"]["repro"] += change
    check_allocation(Plant)


def adapt_nutrient_supply(Plant):
    """
    Reallocation to root compartments in case of nutrient stress, plus adjusting leaf nutrient index.
    """
    if Plant["ratio_allocation"]["absorp"] <= 0.8:
        Plant["ratio_allocation"]["support"] = max(Plant["ratio_allocation"]["support"] - Gl.delta_adapt / 2, 0.0)
        Plant["ratio_allocation"]["absorp"] += Gl.delta_adapt
        Plant["ratio_allocation"]["photo"] = max(Plant["ratio_allocation"]["photo"] - Gl.delta_adapt / 2, 0.0)
        adapt_leaf_nutrient(Plant)
    check_allocation(Plant)


def dessication(Plant, Env, day):
    """
    If the plant enters dessication stage, biomass in certain compartments is destroyed
    (especially for annual or biannual). Perennials might only lose partial support.
    """
    if Plant["growth_type"] == "annual":
        destroy_biomass(Plant, Env, "support", "extension", Plant["dessication_rate"])
        destroy_biomass(Plant, Env, "absorp", "extension", Plant["dessication_rate"])
        destroy_biomass(Plant, Env, "photo", "extension", Plant["dessication_rate"])
    elif Plant["growth_type"] == "perennial":
        destroy_biomass(Plant, Env, "support", "extension", Plant["support_turnover"])
        destroy_biomass(Plant, Env, "absorp", "extension", Plant["dessication_rate"])
        destroy_biomass(Plant, Env, "photo", "extension", Plant["dessication_rate"])
    elif Plant["growth_type"] == "biannual" and day < 365:
        destroy_biomass(Plant, Env, "photo", "extension", Plant["dessication_rate"])
        destroy_biomass(Plant, Env, "absorp", "extension", Plant["dessication_rate"])        
        destroy_biomass(Plant, Env, "support", "extension", Plant["support_turnover"])
    elif Plant["growth_type"] == "biannual" and day > 365:
        destroy_biomass(Plant, Env, "photo", "extension", Plant["dessication_rate"])   
        destroy_biomass(Plant, Env, "absorp", "extension", Plant["dessication_rate"])
        destroy_biomass(Plant, Env, "support", "extension", Plant["dessication_rate"])

def update_biomass_total(Plant):
    """
    Recalculates the total living biomass (sum of support, photo, absorp).
    necromass is not included in biomass_total.
    """
    Plant["biomass_total"] = (
        Plant["biomass"]["support"] +
        Plant["biomass"]["photo"] +
        Plant["biomass"]["absorp"]
    )


def allocate_biomass(Plant, nb):
    """
    Distributes 'nb' (new biomass) among support, photo, absorp, and repro compartments
    according to ratio_allocation.

    Parameters
    ----------
    Plant : dict
    nb : float
        Additional biomass to allocate.
    """
    ra = Plant["ratio_allocation"]
    add_support = nb * ra["support"]
    add_photo = nb * ra["photo"]
    add_absorp = nb * ra["absorp"]
    add_repro = nb * ra["repro"]

    Plant["biomass"]["support"] += add_support
    Plant["biomass"]["photo"] += add_photo
    Plant["biomass"]["absorp"] += add_absorp
    Plant["biomass"]["repro"] += add_repro

    update_biomass_total(Plant)


def adjust_success_cycle(Plant, process):
    """
    success_cycle = new_biomass / (max_biomass) as a rough measure of process success.

    Parameters
    ----------
    Plant : dict
    process : str
    """
    expected = Plant["max_biomass"]
    if expected > 0:
        Plant["success_cycle"][process] = Plant["new_biomass"] / expected
    else:
        Plant["success_cycle"][process] = 0.0


def phenology_annual(Plant, Env, day_index, daily_min_temps):
    photoperiod_today = Ev.calc_daily_photoperiod(day_index)
    photoperiod_yesterday = Ev.calc_daily_photoperiod(day_index - 1)
    sugar_slope = slope_last_hours(Hi.history["reserve_sugar"], nb_hours=24 * 3)
    
    # Germination check
    if Plant["phenology_stage"] in ["seed", "dormancy"]:
        if len(daily_min_temps) >= 7 and all(t > 3.0 for t in daily_min_temps[-7:]):
            Plant["phenology_stage"] = "vegetative"
        else:
            pass
        return

    # Switch to reproduction if sugar slope is negative
    if ((sugar_slope < -1e-4 or photoperiod_today > 15.5) and
        Plant["phenology_stage"] != "reproduction"):
            Plant["reproduction_ref"] = Plant["biomass_total"]
            Plant["phenology_stage"] = "reproduction"
            return


def phenology_biannual(Plant, Env, day_index, daily_min_temps):
    photoperiod_today = Ev.calc_daily_photoperiod(day_index)
    photoperiod_yesterday = Ev.calc_daily_photoperiod(day_index - 1)
    sugar_slope = slope_last_hours(Hi.history["reserve_sugar"], nb_hours=24 * 4)
    photo_slope = slope_last_hours(Hi.history["pot_sugar"], nb_hours=24 * 4)
    mean_sugar = np.mean(Hi.history["reserve_sugar"][-24 * 3:])

    # Germination check
    if Plant["phenology_stage"] in ["seed"]:
        if len(daily_min_temps) >= 7 and all(t > 3.0 for t in daily_min_temps[-7:]):
            Plant["phenology_stage"] = "vegetative"
        return
    
    if Plant["phenology_stage"] in ["dormancy"] and day_index > 365:
        if len(daily_min_temps) >= 7 and all(t > 3.0 for t in daily_min_temps[-7:]):
            Plant["phenology_stage"] = "reproduction"
        return
   
    # optimize reserve build-up
    if (photo_slope < -1e-9 and 
        photoperiod_today < photoperiod_yesterday and
        Plant["phenology_stage"] == "vegetative"):

        Plant["phenology_stage"] = "making_reserve"
        return
    
    if (day_index < 365 and sugar_slope < -1e-9 and
        Plant["phenology_stage"] == "making_reserve"):
        Plant["phenology_stage"] = "dessication"
        return
    
    # End-of-life dessication
    if Plant["biomass"]["photo"] < 0.001 and Plant["phenology_stage"] == "dessication":
        Plant["phenology_stage"] = "dormancy"
        Plant["ratio_allocation"] = {"photo": 0.05, "support": 0.1, "absorp": 0.05, "repro": 0.8}
        check_allocation(Plant)

def phenology_perennial(Plant, Env, day_index, daily_min_temps):
    photoperiod_today = Ev.calc_daily_photoperiod(day_index)
    photoperiod_yesterday = Ev.calc_daily_photoperiod(day_index - 1)
    sugar_slope = slope_last_hours(Hi.history["reserve_sugar"], nb_hours=24 * 3)

    # Germination check
    if Plant["phenology_stage"] in ["seed", "dormancy"]:
        if len(daily_min_temps) >= 7 and all(t > 3.0 for t in daily_min_temps[-7:]):
            Plant["phenology_stage"] = "vegetative"
        return
    
    if (Plant["growth_type"] == "biannual" and 
        day_index > 365 and 
        Plant["phenology_stage"] == "vegetative"):
            Plant["phenology_stage"] = "reproduction"
            return

    # Switch to reproduction if sugar slope is negative
    if (sugar_slope < -1e-9 and 
        Plant["phenology_stage"] != "reproduction" and 
        Plant["growth_type"] != "biannual"):
        if Plant["growth_type"] == "annual":
            Plant["reproduction_ref"] = Plant["biomass_total"]
            Plant["phenology_stage"] = "reproduction"
        elif Plant["growth_type"] == "perennial":
            Plant["phenology_stage"] = "making_reserve"
        return
    
    # Photoperiod-based transitions
    if (sugar_slope < -1e-9 and 
        Plant["phenology_stage"] != "reproduction"):
        if (Plant["growth_type"] == "biannual" and 
            Plant["phenology_stage"] != "making_reserve" and
            day_index < 365):
            Plant["phenology_stage"] = "making_reserve"
        elif (Plant["growth_type"] == "biannual" and 
              day_index > 365 and 
              Plant["phenology_stage"] != "dessication"):
            Plant["phenology_stage"] = "dessication"
            Plant["ratio_allocation"]["repro"] = 0.0
            check_allocation(Plant)
        elif (sugar_slope < -1e-9 and Plant["growth_type"] == "perennial"
              and Plant["phenology_stage"] != "dessication"):
            Plant["phenology_stage"] = "dessication"
            Plant["ratio_allocation"]["repro"] = 0.0
            check_allocation(Plant)
        return

    # End-of-life dessication
    if Plant["biomass"]["photo"] < 0.001 and Plant["phenology_stage"] != "dormancy":
        Plant["phenology_stage"] = "dormancy"
        Plant["ratio_allocation"] = {"photo": 0.55, "support": 0.1, "absorp": 0.45, "repro": 0.0}
        check_allocation(Plant)


def manage_phenology(Plant, Env, day_index, daily_min_temps):
    # 1) On définit un dictionnaire 'dispatch' :
    phenology_dispatch = {
        "annual":    phenology_annual,
        "biannual":  phenology_biannual,
        "perennial": phenology_perennial
    }
    
    # 2) On récupère la clé (ex. "annual") depuis Plant
    phen_type = Plant.get("growth_type", "none")

    # 3) On cherche dans le dictionnaire la fonction associée
    #    et on fournit une fonction "par défaut" si la clé est introuvable
    handler = phenology_dispatch.get(phen_type, "none")
    
    # 4) On appelle cette fonction "spécialisée"
    handler(Plant, Env, day_index, daily_min_temps)



def intitialize_state_variables(Plant):
    """
    Resets daily or per-cycle plant state variables, cost structures, and fluxes.
    Called at the beginning of each hour or day in the simulation loop.

    Parameters
    ----------
    Plant : dict
    """
    Plant["diag"] = {}
    Plant["reserve_used"] = {
        "maintenance": False,
        "extension": False,
        "reproduction": False,
        "transpiration": False
    }
    Plant["adjusted_used"] = {
        "maintenance": False,
        "extension": False,
        "reproduction": False,
        "transpiration": False
    }
    Plant["success_cycle"] = {"extension": 1.0, "reproduction": 1.0}
    Plant["cost"] = {
        "extension": {"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
        "reproduction": {"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
        "maintenance": {"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
        "transpiration": {"sugar": 0.0, "water": 0.0, "nutrient": 0.0}
    }
    Plant["flux_in"] = {"sugar": 0.0, "water": 0.0, "nutrient": 0.0}
    Plant["new_biomass"] = 0.0
    Plant["total_water_needed"] = 0.0


def check_allocation(Plant):
    """
    Ensures the sum of ratio_allocation is 1.0. If not, normalizes them.

    Parameters
    ----------
    Plant : dict
    """
    ra = Plant["ratio_allocation"]
    sumalloc = ra["support"] + ra["photo"] + ra["absorp"] + ra["repro"]
    if sumalloc != 1.0 and sumalloc != 0.0:
        ra["support"] /= sumalloc
        ra["photo"] /= sumalloc
        ra["absorp"] /= sumalloc
        ra["repro"] /= sumalloc


def slope_last_hours(history_list, nb_hours=72):
    """
    Computes the slope of a linear regression over the last nb_hours data points.

    Parameters
    ----------
    history_list : list of float
        The data to analyze (e.g. reserve_sugar from Hi.history).
    nb_hours : int
        Number of hours to consider.

    Returns
    -------
    float
        The slope in units of 'value per hour'. 0.0 if insufficient data.
    """
    if len(history_list) < nb_hours:
        return 0.0

    data = history_list[-nb_hours:]
    x = np.arange(len(data), dtype=float)
    y = np.array(data, dtype=float)
    slope, _ = np.polyfit(x, y, 1)
    return slope