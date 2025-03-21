# Plant_def.py
"""
This module defines the data structure and parameters for the plant (Plant),
including a function to set species-specific parameters from a database.
All comments are in English; code and variable names remain in French.
"""

import global_constants as Gl
import functions as Fu


def set_plant_species(Plant, species_name, species_db):
    """
    Assigns species-specific parameters (from species_db) into the Plant dictionary.

    Parameters
    ----------
    Plant : dict
        The main dictionary representing the plant's state and parameters.
    species_name : str
        The key that identifies which species in the species_db to use.
    species_db : dict
        A dictionary that maps species_name to another dict of plant parameters.

    Raises
    ------
    ValueError
        If the given species_name is not found in species_db.
    """
    if species_name not in species_db:
        raise ValueError(f"Espèce inconnue : {species_name}")

    params = species_db[species_name]

    # Copy relevant parameters into the Plant dict
    Plant["growth_type"] = params["growth_type"]
    Plant["T_optim"] = params["T_optim"]
    Plant["r_max"] = params["r_max"]
    Plant["alpha"] = params["alpha"]
    Plant["temp_photo_sensitivity"] = params["temp_photo_sensitivity"]
    Plant["sla_max"] = params["sla_max"]
    Plant["stomatal_conductance_min"] = params["stomatal_conductance_min"]
    Plant["leaf_size"] = params["leaf_size"]
    Plant["leaf_albedo"] = params["leaf_albedo"]
    Plant["leaf_emissivity"] = params["leaf_emissivity"]
    Plant["watt_to_sugar_coeff"] = params["watt_to_sugar_coeff"]
    Plant["support_transport_coeff"] = params["support_transport_coeff"]
    Plant["soil_supply_coeff"] = params["soil_supply_coeff"]
    Plant["water_nutrient_coeff"] = params["water_nutrient_coeff"]
    Plant["stomatal_density"] = params["stomatal_density"]
    Plant["dessication_rate"] = params["dessication_rate"]
    Plant["alloc_repro_max"] = params["alloc_repro_max"]
    Plant["alloc_change_rate"] = params["alloc_change_rate"]
    Plant["support_turnover"] = params["support_turnover"]
    Plant["storage_fraction"] = params["storage_fraction"]
    Plant["ratio_allocation"] = params["ratio_allocation"]
    Plant["cannibal_ratio"] = params["cannibal_ratio"]
    Plant["cost_params"] = params["cost_params"]
    Plant["reserve"] = params["reserve"]
    Plant["size"] = params["size"]
    Plant["biomass_total"] = params["biomass_total"]

    # Once parameters are set, allocate the total biomass to subcompartments
    Fu.allocate_biomass(Plant, Plant["biomass_total"])


# ---------------------------------------------------------------------------
# Main Plant dictionary: describes the plant's dynamic states and sub-states.
# This is a global dictionary that will be updated continuously by the model.
# ---------------------------------------------------------------------------
Plant = {
    # Dynamic regulation / morphological attributes
    "stomatal_conductance": 1.0,
    "nutrient_index": 1.0,
    "trans_cooling": 0.0,
    "leaf_angle": 0.0,
    "temperature": {"photo": 0.0},
    "slai": 1.0,

    # Flux inputs (in g or g/hour, depending on context)
    "flux_in": {"sugar": 0.0, "water": 0.0, "nutrient": 0.0},

    # Internal reserves (in grams)
    "reserve": {"sugar": 0.039, "water": 0.01, "nutrient": 0.001},

    # Cost structures: each process can have sugar/water/nutrient cost
    "cost": {
        "extension": {"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
        "reproduction": {"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
        "maintenance": {"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
        "transpiration": {"sugar": 0.0, "water": 0.0, "nutrient": 0.0}
    },

    # Additional tracking of water needs and transpiration constraints
    "total_water_needed": 0.0,
    "transp_limit_pool": "none",

    # Health / alive status
    "health_state": 100.0,
    "alive": True,
    "phenology_stage": "seed",

    # Flags for resource usage (needed in processes)
    "reserve_used": {
        "maintenance": False,
        "extension": False,
        "reproduction": False
    },
    "adjusted_used": {
        "maintenance": False,
        "extension": False,
        "reproduction": False,
        "transpiration": False
    },

    # Stress and success histories
    "stress_history": {"sugar": [], "water": [], "nutrient": []},
    "success_history": {"extension": [], "reproduction": []},
    "success_cycle": {"extension": 1.0, "reproduction": 1.0},

    # Biomass increments / references
    "new_biomass": 0.0,
    "max_biomass": 0.0,
    "reproduction_ref": 0.0,
    "max_transpiration_capacity": 0.0,

    # Actual biomass in compartments
    "biomass": {
        "support": 0.0,
        "photo": 0.0,
        "absorp": 0.0,
        "repro": 0.0,
        "necromass": 0.0
    },
    "dying_state_count": 0,

    # Diagnostic dictionary used to store intermediate results for debugging
    "diag": {}
}


# ---------------------------------------------------------------------------
# Dictionary of species-specific parameters. Each entry is a key (species name)
# mapped to a dict of parameter values used for initialization and calculations.
# ---------------------------------------------------------------------------
species_db = {
    "ble": {
        "growth_type": "annual",
        "T_optim": 22.0,
        "r_max": 5.0e-3,
        "alpha": 8.00e-4,
        "temp_photo_sensitivity": 0.03,
        "sla_max": 0.02,
        "stomatal_conductance_min": 0.01,
        "leaf_size": 0.05,
        "leaf_albedo": 0.25,
        "leaf_emissivity": 0.95,
        "watt_to_sugar_coeff": 0.00004,
        "support_transport_coeff": 2e-2,
        "soil_supply_coeff": 0.1,
        "water_nutrient_coeff": 3.5e-4,
        "stomatal_density": 38658154,
        "alloc_change_rate": Gl.delta_adapt / 5,
        "alloc_repro_max": 0.84,
        "dessication_rate": Gl.delta_adapt * 3,
        "support_turnover": Gl.delta_adapt / 20,
        "cannibal_ratio": 0.3,
        "cost_params": {
            "extension": {
                "photo": {"sugar": 0.5, "water": 0.75, "nutrient": 0.02},
                "absorp": {"sugar": 0.5, "water": 0.75, "nutrient": 0.02},
                "support": {"sugar": 0.5, "water": 0.75, "nutrient": 0.01}
            },
            "reproduction": {
                "unique": {"sugar": 0.5, "water": 0.75, "nutrient": 0.03}
            },
            "maintenance": {
                "unique": {"sugar": 5e-7, "water": 0.0, "nutrient": 0.0}
            }
        },
        "storage_fraction": {"sugar": 0.05, "water": 0.05, "nutrient": 0.05},
        "ratio_allocation": {"support": 0.2, "absorp": 0.3, "photo": 0.5, "repro": 0.0},
        "reserve": {"sugar": 0.039, "water": 0.01, "nutrient": 0.003},
        "size": 1.0,
        "biomass_total": 0.01
    },

    "mais": {
        "growth_type": "annual",
        "photoperiod_for_repro": 15.5,
        "T_optim": 32.0,
        "r_max": 1.13e-2,
        "alpha": 4.5e-3,
        "temp_photo_sensitivity": 0.03,
        "sla_max": 0.02,
        "stomatal_conductance_min": 0.03,
        "leaf_size": 0.05,
        "leaf_albedo": 0.25,
        "leaf_emissivity": 0.95,
        "watt_to_sugar_coeff": 4.0e-6,
        "support_transport_coeff": 5e-3,
        "soil_supply_coeff": 0.1,
        "water_nutrient_coeff": 7e-3,
        "stomatal_density": 6.0e7,
        "alloc_change_rate": Gl.delta_adapt / 4,
        "alloc_repro_max": 0.95,
        "dessication_rate": Gl.delta_adapt * 3,
        "support_turnover": Gl.delta_adapt / 20,
        "cost_params": {
            "extension": {
                "photo": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "absorp": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "support": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0}
            },
            "reproduction": {
                "unique": {"sugar": 0.5, "water": 0.25, "nutrient": 0.0}
            },
            "maintenance": {
                "unique": {"sugar": 0.0000005, "water": 0.0, "nutrient": 0.0}
            }
        },
        "storage_fraction": {"sugar": 0.05, "water": 0.05, "nutrient": 0.05},
        "ratio_allocation": {"support": 0.2, "absorp": 0.3, "photo": 0.5, "repro": 0.0},
        "reserve": {"sugar": 0.039, "water": 0.01, "nutrient": 0.001},
        "size": 1.0,
        "biomass_total": 0.01
    },

    "biannual herbaceous": {
        "growth_type": "biannual",
        "photoperiod_for_repro": 12.0,
        "T_optim": 25.0,
        "r_max": 4.78e-3,
        "alpha": 8.13e-4,
        "temp_photo_sensitivity": 0.03,
        "sla_max": 0.02,
        "stomatal_conductance_min": 0.01,
        "leaf_size": 0.05,
        "leaf_albedo": 0.25,
        "leaf_emissivity": 0.95,
        "watt_to_sugar_coeff": 1.7e-6,
        "support_transport_coeff": 5e-3,
        "soil_supply_coeff": 0.1,
        "water_nutrient_coeff": 3e-3,
        "stomatal_density": 5.0e7,
        "alloc_change_rate": Gl.delta_adapt / 4,
        "alloc_repro_max": 0.75,
        "dessication_rate": Gl.delta_adapt,
        "support_turnover": Gl.delta_adapt / 20,
        "cost_params": {
            "extension": {
                "photo": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "absorp": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "support": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0}
            },
            "reproduction": {
                "unique": {"sugar": 0.5, "water": 0.25, "nutrient": 0.0}
            },
            "maintenance": {
                "unique": {"sugar": 0.0000005, "water": 0.0, "nutrient": 0.0}
            }
        },
        "storage_fraction": {"sugar": 0.05, "water": 0.05, "nutrient": 0.05},
        "ratio_allocation": {"support": 0.2, "absorp": 0.3, "photo": 0.5, "repro": 0.0},
        "reserve": {"sugar": 0.039, "water": 0.01, "nutrient": 0.001},
        "size": 1.0,
        "biomass_total": 0.01
    },

    "perennial herbaceous": {
        "growth_type": "perennial",
        "photoperiod_for_repro": 15.5,
        "T_optim": 25.0,
        "r_max": 2.78e-3,
        "alpha": 8.13e-4,
        "temp_photo_sensitivity": 0.05,
        "sla_max": 0.02,
        "stomatal_conductance_min": 0.01,
        "leaf_size": 0.05,
        "leaf_albedo": 0.25,
        "leaf_emissivity": 0.95,
        "watt_to_sugar_coeff": 1.7e-6,
        "support_transport_coeff": 5e-3,
        "soil_supply_coeff": 0.1,
        "water_nutrient_coeff": 3e-3,
        "stomatal_density": 5.0e7,
        "alloc_change_rate": Gl.delta_adapt / 4,
        "alloc_repro_max": 0.1,
        "dessication_rate": Gl.delta_adapt * 3,
        "support_turnover": Gl.delta_adapt / 20,
        "cost_params": {
            "extension": {
                "photo": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "absorp": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "support": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0}
            },
            "reproduction": {
                "unique": {"sugar": 0.5, "water": 0.25, "nutrient": 0.0}
            },
            "maintenance": {
                "unique": {"sugar": 0.0000005, "water": 0.0, "nutrient": 0.0}
            }
        },
        "storage_fraction": {"sugar": 0.05, "water": 0.05, "nutrient": 0.05},
        "ratio_allocation": {"support": 0.2, "absorp": 0.3, "photo": 0.5, "repro": 0.0},
        "reserve": {"sugar": 0.039, "water": 0.01, "nutrient": 0.001},
        "size": 1.0,
        "biomass_total": 0.01
    },

    "quercus_coccifera": {
        "growth_type": "perennial",
        "photoperiod_for_repro": 15.5,
        "T_optim": 25.0,
        "r_max": 2.48e-3,
        "alpha": 8.13e-5,
        "temp_photo_sensitivity": 0.05,
        "sla_max": 0.02,
        "stomatal_conductance_min": 0.01,
        "leaf_size": 0.05,
        "leaf_albedo": 0.25,
        "leaf_emissivity": 0.95,
        "watt_to_sugar_coeff": 1.7e-6,
        "support_transport_coeff": 5e-3,
        "soil_supply_coeff": 0.1,
        "water_nutrient_coeff": 3e-3,
        "stomatal_density": 5.0e7,
        "alloc_change_rate": Gl.delta_adapt / 4,
        "alloc_repro_max": 0.1,
        "dessication_rate": Gl.delta_adapt * 3,
        "support_turnover": Gl.delta_adapt / 100,
        "cost_params": {
            "extension": {
                "photo": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "absorp": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "support": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0}
            },
            "reproduction": {
                "unique": {"sugar": 0.5, "water": 0.25, "nutrient": 0.0}
            },
            "maintenance": {
                "unique": {"sugar": 0.0000005, "water": 0.0, "nutrient": 0.0}
            }
        },
        "storage_fraction": {"sugar": 0.05, "water": 0.05, "nutrient": 0.05},
        "ratio_allocation": {"support": 0.2, "absorp": 0.3, "photo": 0.5, "repro": 0.0},
        "reserve": {"sugar": 0.039, "water": 0.01, "nutrient": 0.001},
        "size": 1.0,
        "biomass_total": 0.01
    },

    "quercus_ilex": {
        "growth_type": "perennial",
        "photoperiod_for_repro": 15.5,
        "T_optim": 25.0,
        "r_max": 2.28e-3,
        "alpha": 8.13e-5,
        "temp_photo_sensitivity": 0.05,
        "sla_max": 0.02,
        "stomatal_conductance_min": 0.01,
        "leaf_size": 0.05,
        "leaf_albedo": 0.25,
        "leaf_emissivity": 0.95,
        "watt_to_sugar_coeff": 1.7e-6,
        "support_transport_coeff": 5e-3,
        "soil_supply_coeff": 0.1,
        "water_nutrient_coeff": 3e-3,
        "stomatal_density": 5.0e7,
        "alloc_change_rate": Gl.delta_adapt / 4,
        "alloc_repro_max": 0.1,
        "dessication_rate": Gl.delta_adapt * 3,
        "support_turnover": Gl.delta_adapt / 200,
        "cost_params": {
            "extension": {
                "photo": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "absorp": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "support": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0}
            },
            "reproduction": {
                "unique": {"sugar": 0.5, "water": 0.25, "nutrient": 0.0}
            },
            "maintenance": {
                "unique": {"sugar": 0.0000005, "water": 0.0, "nutrient": 0.0}
            }
        },
        "storage_fraction": {"sugar": 0.05, "water": 0.05, "nutrient": 0.05},
        "ratio_allocation": {"support": 0.2, "absorp": 0.3, "photo": 0.5, "repro": 0.0},
        "reserve": {"sugar": 0.039, "water": 0.01, "nutrient": 0.001},
        "size": 1.0,
        "biomass_total": 0.01
    },

    "fagus_sylvatica": {
        "growth_type": "perennial",
        "photoperiod_for_repro": 15.5,
        "T_optim": 25.0,
        "r_max": 2.28e-3,
        "alpha": 8.13e-5,
        "temp_photo_sensitivity": 0.05,
        "sla_max": 0.02,
        "stomatal_conductance_min": 0.01,
        "leaf_size": 0.05,
        "leaf_albedo": 0.25,
        "leaf_emissivity": 0.95,
        "watt_to_sugar_coeff": 1.7e-6,
        "support_transport_coeff": 5e-3,
        "soil_supply_coeff": 0.1,
        "water_nutrient_coeff": 3e-3,
        "stomatal_density": 5.0e7,
        "alloc_change_rate": Gl.delta_adapt / 4,
        "alloc_repro_max": 0.1,
        "dessication_rate": Gl.delta_adapt * 3,
        "support_turnover": Gl.delta_adapt / 200,
        "cost_params": {
            "extension": {
                "photo": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "absorp": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "support": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0}
            },
            "reproduction": {
                "unique": {"sugar": 0.5, "water": 0.25, "nutrient": 0.0}
            },
            "maintenance": {
                "unique": {"sugar": 0.0000005, "water": 0.0, "nutrient": 0.0}
            }
        },
        "storage_fraction": {"sugar": 0.05, "water": 0.05, "nutrient": 0.05},
        "ratio_allocation": {"support": 0.2, "absorp": 0.3, "photo": 0.5, "repro": 0.0},
        "reserve": {"sugar": 0.039, "water": 0.01, "nutrient": 0.001},
        "size": 1.0,
        "biomass_total": 0.01
    },

    "picea_abies": {
        "growth_type": "perennial",
        "photoperiod_for_repro": 15.5,
        "T_optim": 25.0,
        "r_max": 9.78e-3,
        "alpha": 8.13e-4,
        "temp_photo_sensitivity": 0.03,
        "sla_max": 0.02,
        "stomatal_conductance_min": 0.01,
        "leaf_size": 0.05,
        "leaf_albedo": 0.25,
        "leaf_emissivity": 0.95,
        "watt_to_sugar_coeff": 1.7e-6,
        "support_transport_coeff": 5e-3,
        "soil_supply_coeff": 0.1,
        "water_nutrient_coeff": 3e-3,
        "stomatal_density": 5.0e7,
        "alloc_change_rate": Gl.delta_adapt / 4,
        "alloc_repro_max": 0.15,
        "dessication_rate": Gl.delta_adapt * 3,
        "support_turnover": Gl.delta_adapt / 60,
        "cost_params": {
            "extension": {
                "photo": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "absorp": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0},
                "support": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0}
            },
            "reproduction": {
                "unique": {"sugar": 0.5, "water": 0.75, "nutrient": 0.0}
            },
            "maintenance": {
                "unique": {"sugar": 0.0000005, "water": 0.0, "nutrient": 0.0}
            }
        },
        "storage_fraction": {"sugar": 0.05, "water": 0.05, "nutrient": 0.05},
        "ratio_allocation": {"support": 0.2, "absorp": 0.3, "photo": 0.5, "repro": 0.0},
        "reserve": {"sugar": 0.039, "water": 0.01, "nutrient": 0.001},
        "size": 1.0,
        "biomass_total": 0.01
    }
}
