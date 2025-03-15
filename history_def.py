
# Dictionnaire pour l'historique
history = {
    "time": [],
    # Biomasses
    "biomass_total": [],
    "biomass_support": [],
    "biomass_photo":   [],
    "biomass_absorp":  [],
    "biomass_repro": [],
    "biomass_necromass": [],
    # SLAI et santé
    "slai": [],
    "health_state": [],
    # Flux in/out
    "sugar_in": [],
    "water_in": [],
    "nutrient_in": [],
    # Réserves
    "reserve_sugar": [],
    "reserve_water": [],
    "reserve_nutrient": [],
    # Eau dans le sol
    "soil_water": [],
    # Stomates / T
    "stomatal_conductance": [],
    "leaf_angle": [],
    "nutrient_index": [],
    "atmos_temperature": [],
    "leaf_temperature_after": [],   
    # Success cycles
    "success_extension": [],
    "success_reproduction": [],
    "max_transpiration_capacity": [],
    "raw_sugar_flux": [],
    "pot_sugar": [],
    "actual_sugar": [],
    "atmos_light": [],  # luminosité ambiante
    "rain_event": [],   # pluie (g d’eau vers le sol)
    # Reserve used (bool -> 0 ou 1) pour 3 process
    "reserve_used_maintenance": [],
    "reserve_used_extension": [],
    "reserve_used_reproduction": [],   
    "reserve_used_transpiration": [],
    "cost_transpiration_water": [], 
    "cost_maintenance_sugar": [], 
    "cost_extension_sugar": [], 
    "cost_extension_water": [], 
    "cost_extension_nutrient": [],
    "cost_reproduction_sugar": [], 
    "cost_reproduction_water": [], 
    "cost_reproduction_nutrient": [],
    # Adjusted used (bool -> 0 ou 1)
    "adjusted_used_maintenance": [],
    "adjusted_used_extension": [],
    "adjusted_used_reproduction": [],
    "adjusted_used_transpiration": [],
    # Ratios d’allocation
    "ratio_support": [],
    "ratio_photo": [],
    "ratio_absorp": [],
    "ratio_repro": [],
    # Stress
    "stress_sugar": [],
    "stress_water": []
}

def history_update(Plant, history, Environment, time):
        history["time"].append(time)
        # biomasses
        history["biomass_total"].append(Plant["biomass_total"])
        history["biomass_support"].append(Plant["biomass"]["support"])
        history["biomass_photo"].append(Plant["biomass"]["photo"])
        history["biomass_absorp"].append(Plant["biomass"]["absorp"])
        history["biomass_repro"].append(Plant["biomass"]["repro"])
        history["biomass_necromass"].append(Plant["biomass"]["necromass"])
        # slai, santé
        history["slai"].append(Plant["slai"])
        history["health_state"].append(Plant["health_state"])
        # flux in/out
        history["sugar_in"].append(Plant["flux_in"]["sugar"])
        history["water_in"].append(Plant["flux_in"]["water"])
        history["nutrient_in"].append(Plant["flux_in"]["nutrient"])
        # Réserves
        history["reserve_sugar"].append(Plant["reserve"]["sugar"])
        history["reserve_water"].append(Plant["reserve"]["water"])
        history["reserve_nutrient"].append(Plant["reserve"]["nutrient"])
        # eau sol
        history["soil_water"].append(Environment["soil"]["water"])
        # stomates / T
        history["stomatal_conductance"].append(Plant["stomatal_conductance"])
        history["leaf_angle"].append(Plant["leaf_angle"])  
        history["nutrient_index"].append(Plant["nutrient_index"])  
        history["atmos_temperature"].append(Environment["atmos"]["temperature"])
        history["leaf_temperature_after"].append(Plant["temperature"]["photo"] )
        # succès
        history["success_extension"].append(Plant["success_cycle"]["extension"])
        history["success_reproduction"].append(Plant["success_cycle"]["reproduction"])
        # flux_in spéciaux
        # nouveaux diagnostics
        history["max_transpiration_capacity"].append(Plant["max_transpiration_capacity"])
        history["raw_sugar_flux"].append(Plant["diag"].get("raw_sugar_flux", 0.0))
        history["pot_sugar"].append(Plant["diag"].get("pot_sugar", 0.0))
        history["actual_sugar"].append(Plant["diag"].get("actual_sugar", 0.0))
        history["atmos_light"].append(Environment["atmos"]["light"])
        history["rain_event"].append(Environment["rain_event"])

        # reserve_used / adjusted_used en 0 ou 1
        history["reserve_used_maintenance"].append(1 if Plant["reserve_used"]["maintenance"] else 0)
        # On n’a pas "extension" dans reserve_used, donc on met 0:
        history["reserve_used_extension"].append(1 if Plant["reserve_used"]["extension"] else 0)
        history["reserve_used_reproduction"].append(1 if Plant["reserve_used"]["reproduction"] else 0)
        history["reserve_used_transpiration"].append(1 if Plant["reserve_used"]["transpiration"] else 0)   

        history["adjusted_used_maintenance"].append(1 if Plant["adjusted_used"]["maintenance"] else 0)
        history["adjusted_used_extension"].append(1 if Plant["adjusted_used"]["extension"] else 0)
        history["adjusted_used_reproduction"].append(1 if Plant["adjusted_used"]["reproduction"] else 0)
        history["adjusted_used_transpiration"].append(1 if Plant["adjusted_used"]["transpiration"] else 0)

        history["cost_transpiration_water"].append(Plant["cost"]["transpiration"]["water"])
        history["cost_maintenance_sugar"].append(Plant["cost"]["maintenance"]["sugar"])
        history["cost_extension_sugar"].append(Plant["cost"]["extension"]["sugar"])
        history["cost_extension_water"].append(Plant["cost"]["extension"]["water"])
        history["cost_extension_nutrient"].append(Plant["cost"]["extension"]["nutrient"])
        history["cost_reproduction_sugar"].append(Plant["cost"]["reproduction"]["sugar"])
        history["cost_reproduction_water"].append(Plant["cost"]["reproduction"]["water"])
        history["cost_reproduction_nutrient"].append(Plant["cost"]["reproduction"]["nutrient"])

        # Ratios d’allocation
        history["ratio_support"].append(Plant["ratio_allocation"]["support"])
        history["ratio_photo"].append(Plant["ratio_allocation"]["photo"])
        history["ratio_absorp"].append(Plant["ratio_allocation"]["absorp"])
        history["ratio_repro"].append(Plant["ratio_allocation"]["repro"])
        # Stress : on prend la dernière valeur des listes de stress
        # (sugar et water) si elles existent, sinon 0
        if Plant["stress_history"]["sugar"]:
            history["stress_sugar"].append(Plant["stress_history"]["sugar"][-1])
        else:
            history["stress_sugar"].append(0.0)

        if Plant["stress_history"]["water"]:
            history["stress_water"].append(Plant["stress_history"]["water"][-1])
        else:
            history["stress_water"].append(0.0)