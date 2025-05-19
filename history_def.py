# history_def.py
"""
Manages the simulation's historical records (Plant and Environment states).
All comments in English, while variable and dictionary keys remain in French.
"""

# A global dictionary named 'history' that will store lists of values
# over time (one entry per simulation step).
history = {
    "time": [],
    # Biomasses
    "biomass_total": [],
    "biomass_transport": [],
    "biomass_stock": [],    
    "biomass_photo": [],
    "biomass_absorp": [],
    "biomass_repro": [],
    "biomass_necromass": [],
    # SLAI and health
    "slai": [],
    "health_state": [],
    # Flux in/out
    "sugar_in": [],
    "water_in": [],
    "nutrient_in": [],
    # Internal reserves
    "reserve_sugar": [],
    "reserve_water": [],
    "reserve_nutrient": [],
    # Soil water
    "soil_water": [],
    # Stomatal data, temperature
    "stomatal_conductance": [],
    "leaf_angle": [],
    "nutrient_index": [],
    "atmos_temperature": [],
    "leaf_temperature_after": [],
    # Success cycles
    "success_extension": [],
    "success_reproduction": [],
    "max_transpiration_capacity": [],
    # Photosynthesis details
    "raw_sugar_flux": [],
    "pot_sugar": [],
    "actual_sugar": [],
    # Atmospheric data
    "atmos_light": [],
    "rain_event": [],
    # Resource usage flags (0 or 1)
    "reserve_used_maintenance": [],
    "reserve_used_extension": [],
    "reserve_used_transpiration": [],
    # Process costs
    "cost_transpiration_water": [],
    "cost_maintenance_sugar": [],
    "dormancy_index": [],   
    "cost_extension_sugar": [],
    "cost_extension_water": [],
    "cost_extension_nutrient": [],
    # alloc ratios
    "ratio_transport": [],
    "ratio_stock": [],
    "ratio_photo": [],
    "ratio_absorp": [],
    "ratio_repro": [],
    # Stress
    "stress_sugar": [],
    "stress_water": [],   
    "phenology_stage":  [],
}


def history_update(Plant, history, Environment, time):
    """
    Appends the current state of 'Plant' and 'Environment' to the history dictionary.

    Parameters
    ----------
    Plant : dict
        The plant state dictionary, containing biomass, reserves, stress, etc.
    history : dict
        The global history structure (lists of values).
    Environment : dict
        The environment dictionary, containing soil, atmospheric data, etc.
    time : int or float
        The current simulation time (in hours).
    """
    # Time
    history["time"].append(time)

    # Biomasses
    history["biomass_total"].append(Plant["biomass_total"])
    history["phenology_stage"].append(Plant["phenology_stage"])
    history["biomass_transport"].append(Plant["biomass"]["transport"])
    history["biomass_stock"].append(Plant["biomass"]["stock"])   
    history["biomass_photo"].append(Plant["biomass"]["photo"])
    history["biomass_absorp"].append(Plant["biomass"]["absorp"])
    history["biomass_repro"].append(Plant["biomass"]["repro"])
    history["biomass_necromass"].append(Plant["biomass"]["necromass"])

    # SLAI, health
    history["slai"].append(Plant["slai"])
    history["health_state"].append(Plant["health_state"])

    # In/out fluxes
    history["sugar_in"].append(Plant["flux_in"]["sugar"])
    history["water_in"].append(Plant["flux_in"]["water"])
    history["nutrient_in"].append(Plant["flux_in"]["nutrient"])

    # Reserves
    history["reserve_sugar"].append(Plant["reserve"]["sugar"])
    history["reserve_water"].append(Plant["reserve"]["water"])
    history["reserve_nutrient"].append(Plant["reserve"]["nutrient"])

    # Soil water
    history["soil_water"].append(Environment["soil"]["water"])

    # Stomatal and thermal data
    history["stomatal_conductance"].append(Plant["stomatal_conductance"])
    history["leaf_angle"].append(Plant["leaf_angle"])
    history["nutrient_index"].append(Plant["nutrient_index"])
    history["atmos_temperature"].append(Environment["atmos"]["temperature"])
    history["leaf_temperature_after"].append(Plant["temperature"]["photo"])

    # Success cycles
    history["success_extension"].append(Plant["success_cycle"]["extension"])
    history["success_reproduction"].append(Plant["success_cycle"]["reproduction"])

    # Photosynthesis details
    history["max_transpiration_capacity"].append(Plant["max_transpiration_capacity"])
    history["raw_sugar_flux"].append(Plant["diag"].get("raw_sugar_flux", 0.0))
    history["pot_sugar"].append(Plant["diag"].get("pot_sugar", 0.0))
    history["actual_sugar"].append(Plant["diag"].get("actual_sugar", 0.0))

    # Environmental data
    history["atmos_light"].append(Environment["atmos"]["light"])
    history["rain_event"].append(Environment["rain_event"])

    # Resource usage flags
    history["reserve_used_maintenance"].append(int(Plant["reserve_used"]["maintenance"]))
    history["reserve_used_extension"].append(int(Plant["reserve_used"]["extension"]))
    history["reserve_used_transpiration"].append(int(Plant["reserve_used"]["transpiration"]))
    # Process costs
    history["cost_transpiration_water"].append(Plant["cost"]["transpiration"]["water"])
    history["cost_maintenance_sugar"].append(Plant["cost"]["maintenance"]["sugar"])
    history["dormancy_index"].append(Plant["dormancy_index"])    
    history["cost_extension_sugar"].append(Plant["cost"]["extension"]["sugar"])
    history["cost_extension_water"].append(Plant["cost"]["extension"]["water"])
    history["cost_extension_nutrient"].append(Plant["cost"]["extension"]["nutrient"])

    # alloc ratios
    history["ratio_transport"].append(Plant["ratio_alloc"]["transport"])
    history["ratio_stock"].append(Plant["ratio_alloc"]["stock"])    
    history["ratio_photo"].append(Plant["ratio_alloc"]["photo"])
    history["ratio_absorp"].append(Plant["ratio_alloc"]["absorp"])
    history["ratio_repro"].append(Plant["ratio_alloc"]["repro"])

    # Stress
    if Plant["stress_history"]["sugar"]:
        history["stress_sugar"].append(Plant["stress_history"]["sugar"][-1])
    else:
        history["stress_sugar"].append(0.0)

    if Plant["stress_history"]["water"]:
        history["stress_water"].append(Plant["stress_history"]["water"][-1])
    else:
        history["stress_water"].append(0.0)
