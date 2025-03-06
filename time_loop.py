# -*- coding: utf-8 -*-
"""
Traduction en Python du pseudo-code "pseudo_OV_Pl.Plant_v6.txt"
pour modéliser le cycle de vie d'une Pl.Plante.

Version modifiée pour afficher des informations plus détaillées
sur la transpiration et la photosynthèse dans les graphiques.
"""
import Plant_def as Pl
import Environnement_def as Ev
import functions as Fu
import global_constants as Gl
import history_def as Hi

#############################
#         MAIN LOOP         #
#############################

def run_simulation_collect_data(max_cycles):
    """
    Lance la simulation en collectant à chaque cycle un ensemble
    de variables dans 'history'.
    """
    global time
    cycle_count = 0
    time = 0  # réinitialisation

    # Boucle principale
    while Pl.Plant["alive"] and cycle_count < max_cycles:
        time += 1
        cycle_count += 1

        # Réinit
        Pl.Plant["diag"] = {}
        Pl.Plant["reserve_used"]  = {"maintenance": False, "reproduction": False}
        Pl.Plant["adjusted_used"] = {"maintenance": False, "extension": False, "reproduction": False}
        Pl.Plant["success_cycle"] = {"extension": 1.0, "reproduction": 1.0}
        Pl.Plant["cost"] = {
            "extension":   {"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
            "reproduction":{"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
            "maintenance":{"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
            "transpiration":{"sugar": 0.0, "water": 0.0, "nutrient": 0.0}
        }
        Pl.Plant["flux_in"] =  {"sugar": 0.0, "water": 0.0, "nutrient": 0.0}
        Pl.Plant["new_biomass"] = 0
        Pl.Plant["total_water_needed"] = 0
        Pl.Plant["stomatal_conductance"] = 1.0
        Pl.Plant["light_absorption_fraction"] = 0.7

        # 1. Environnement 
        Ev.update_environment(time, Ev.Environment)
        Ev.co2_availability(time, Ev.Environment)
        #Ev.Environment_hazards(Pl.Plant, Ev.Environment)

        # 2. Calcul des coûts
        Fu.photosynthesis(Pl.Plant, Ev.Environment)
        Fu.calculate_cost(Pl.Plant, Ev.Environment, "transpiration") 
        Pl.Plant["new_biomass"] = Fu.calculate_potential_new_biomass(Pl.Plant)
        Fu.calculate_cost(Pl.Plant, Ev.Environment, "maintenance")
        if Ev.Environment["atmos"]["light"] > 0.0:
            Fu.calculate_cost(Pl.Plant, Ev.Environment, "extension")
            Fu.calculate_cost(Pl.Plant, Ev.Environment,"reproduction")

        # 3. Transpiration
        Fu.handle_process(Pl.Plant, Ev.Environment, "transpiration")
        Ev.Environment["soil"]["water"] -= Pl.Plant["trans_cooling"]
        Pl.Plant["diag"]["water_after_transp"] = Pl.Plant["flux_in"]["water"]
        Pl.Plant["diag"]["sugar_photo"]  = Pl.Plant["flux_in"]["sugar"]
        Pl.Plant["diag"]["stomatal_conductance"] = Pl.Plant["stomatal_conductance"]
        #Pl.Plant["diag"]["light_absorption_fraction"] =Pl.Plant["light_absorption_fraction"]

        # 4. Assimilation
        Fu.nutrient_absorption(Pl.Plant, Ev.Environment)

        # 5. Maintenance
        Fu.handle_process(Pl.Plant, Ev.Environment, "maintenance")

        # 6. Extension
        if Ev.Environment["atmos"]["light"] > 0.0:
            Fu.handle_process(Pl.Plant, Ev.Environment, "extension")
            Fu.update_success_history(Pl.Plant, "extension")

        # 7. Réserves
        Fu.refill_reserve(Pl.Plant, "sugar")
        Fu.refill_reserve(Pl.Plant, "water")
        Fu.refill_reserve(Pl.Plant, "nutrient")

        # 8. Reproduction
        if (Pl.Plant["biomass_total"] >= Pl.Plant["reproduction_biomass_thr"] and
            Pl.Plant["health_state"] >= Pl.Plant["reproduction_health_thr"] and
            Ev.Environment["atmos"]["light"] > 0.0):
            Fu.handle_process(Pl.Plant, Ev.Environment, "reproduction")
            Fu.update_success_history(Pl.Plant, "reproduction")
        else:
            Pl.Plant["success_cycle"]["reproduction"] = 0.0
            Fu.update_success_history(Pl.Plant, "reproduction")

        # 9. Adaptation
        if Pl.Plant["biomass_total"] >= Pl.Plant["reproduction_biomass_thr"]:
            if Gl.trend_is_negative(Pl.Plant["success_history"]["reproduction"]):
                Fu.adapt_and_optimize(Pl.Plant, Ev.Environment)
        else:
            if Gl.trend_is_negative(Pl.Plant["success_history"]["extension"]):
                Fu.adapt_and_optimize(Pl.Plant, Ev.Environment)

        # 10. Mortalité
        if Pl.Plant["biomass_total"] <= 0.0: # or Pl.Plant["dying_state_count"] > Gl.dying_state_thr:
            Pl.Plant["alive"] = False

        # 11. Sauvegarde historique
        Hi.history_update(Pl.Plant, Hi.history, Ev.Environment, time)

    return Hi.history, Pl.Plant, Ev.Environment
