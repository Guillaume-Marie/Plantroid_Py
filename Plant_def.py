import global_constants as Gl

# Plante initiale
Plant = {
    "T_optim":                     25.0, 
    "r_max":                       0.009783, # 0.00533
    "alpha":                       0.000813,
    "temp_photo_sensitivity":      0.02,
    "sla_max":                     0.02,
    "stomatal_conductance_min":    0.01,
    "light_absorption_max":        0.3131,
    "watt_to_sugar_coeff":         0.000001,  # J/s ---> gC6H12O6/s
    "transpiration_coeff":         0.00115,
    "support_transport_coeff":     200.0,
    "soil_supply_coeff":           0.1,
    "water_nutrient_coeff":        0.003,
    "dessication_rate":            Gl.delta_adapt, 
    "cost_params": {
        "extension": {
            "photo":    {"sugar": 0.5,  "water": 0.75, "nutrient": 0.0},
            "absorp":   {"sugar": 0.5,  "water": 0.75, "nutrient": 0.0},
            "support":  {"sugar": 0.5,  "water": 0.75, "nutrient": 0.0}
        },
        "reproduction": {
            "unique":   {"sugar": 0.5,  "water": 0.25, "nutrient": 0.0}
        },
        "maintenance": {
            "unique":   {"sugar": 0.0000005, "water": 0.0, "nutrient": 0.0}
        }
    },
    "storage_fraction": {"sugar": 0.05, "water": 0.05, "nutrient": 0.05},
    "ratio_allocation": {"support": 0.05, "absorp": 0.15, "photo": 0.8, "repro": 0.0},
    "stomatal_conductance": 1.0,
    "light_absorption_coeff": 0.0,
    "trans_cooling" : 0.0,
    "temperature": {"photo": 10.0},
    "slai": 1.0,
    "flux_in":  {"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
    "reserve":  {"sugar": 0.039, "water": 0.01, "nutrient": 0.001},
    "cost": {
        "extension":   {"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
        "reproduction":{"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
        "maintenance":{"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
        "transpiration":{"sugar": 0.0, "water": 0.0, "nutrient": 0.0}
    },
    "total_water_needed": 0.0,
    "transp_limit_pool" : "none",
    "health_state": 100.0,
    "alive": True,
    "germinated": False,
    "reserve_used":  {"maintenance": False, "reproduction": False},
    "adjusted_used": {"maintenance": False, "extension": False, "reproduction": False},
    "stress_history": {"sugar": [], "water": [], "nutrient": []},
    "success_history": {"extension": [], "reproduction": []},
    "success_cycle":   {"extension": 1.0, "reproduction": 1.0},
    "size": 1.0,
    "biomass_total": 0.01,
    "new_biomass": 0.0,
    "biomass": {"support": 0, 
                "photo":   0, 
                "absorp":  0,        
                "repro":   0,  
                "necromass": 0},
    "dying_state_count": 0,
    "diag": {}  # pour stocker nos valeurs de diagnostic
}