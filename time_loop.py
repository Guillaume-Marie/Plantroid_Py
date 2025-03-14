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
import functions_BE as Be
import numpy as np

#############################
#         MAIN LOOP         #
#############################
 
def run_simulation_collect_data(max_cycles):
    """
    Boucle principale de simulation, 
    avec condition de germination si min nocturne > 10°C sur 7 jours.
    """
    global time
    cycle_count = 0
    time = 0  # réinitialisation

    # Variables pour suivre la température minimale quotidienne
    daily_min_temps = []
    day_min_temp = float('inf')  # Pour stocker la T min courante de la journée
    previous_day_index = 0       # Pour savoir quand on change de jour

    while Pl.Plant["alive"] and cycle_count < max_cycles:
        time += 1
        cycle_count += 1

        # Calcul de l'heure locale (0..23)
        hour_in_day = time % 24
        day_index   = time // 24  # numéro du jour en cours

        # 2) Mettre à jour la valeur min au fur et à mesure
        Ev.update_environment(time, Ev.Environment)

        if day_index != previous_day_index:
            #print("day:", day_index)  
            day_min_temp = float('inf')

        T_current = Ev.Environment["atmos"]["temperature"]
        if T_current < day_min_temp:
            day_min_temp = T_current

        # 3) En fin de journée (e.g. hour_in_day == 23), on sauvegarde la T min du jour
        if hour_in_day == 23:
            daily_min_temps.append(day_min_temp)
            # On ne garde que les 30 derniers jours par ex. pour éviter de gonfler la liste
            if len(daily_min_temps) > 30:
                daily_min_temps.pop(0)

        Fu.intitialize_state_variables(Pl.Plant)
        Pl.Plant["temperature"]["photo"] = Ev.Environment["atmos"]["temperature"]

        if day_index != previous_day_index:
            # reset stomatal conductance everyday
            Pl.Plant["stomatal_conductance"] = 1.0
            Pl.Plant["leaf_angle"] = 1.0
            # 1. Phenology
            Fu.manage_phenology(Pl.Plant, Ev.Environment, day_index, daily_min_temps)
            previous_day_index = day_index
            #print("phenology :",Pl.Plant["phenology_stage"],"day:",day_index)

        if  Pl.Plant["phenology_stage"] == "seed":
            # On met quand même à jour l’historique pour la température, etc.
            # Mais la plante reste "en dormance" (skip photosynthèse, etc.)
            Pl.Plant["diag"]["raw_sugar_flux"] = 0.0
            Pl.Plant["diag"]["pot_sugar"] = 0.0  
            Pl.Plant["diag"]["leaf_temperature_after"] = 0.0 
            Pl.Plant["diag"]["atmos_temperature"] = T_current
            Pl.Plant["diag"]["leaf_temperature_before"] = 0.0
            Pl.Plant["diag"]["max_transpiration_capacity"] = 0.0
            Pl.Plant["diag"]["sugar_photo"]  = 0.0
            Pl.Plant["diag"]["water_after_transp"] = 0.0
            Pl.Plant["diag"]["stomatal_conductance"] = 0.0
            Hi.history_update(Pl.Plant, Hi.history, Ev.Environment, time)
            continue
        
        #Ev.Environment_hazards(Pl.Plant, Ev.Environment)

        # 2. Calcul des coûts
        Pl.Plant["new_biomass"] = Fu.calculate_potential_new_biomass(Pl.Plant)
        Fu.calculate_cost(Pl.Plant, Ev.Environment, "maintenance")
        if Ev.Environment["atmos"]["light"] > 0.0:
            Fu.calculate_cost(Pl.Plant, Ev.Environment, "extension")
            Fu.calculate_cost(Pl.Plant, Ev.Environment,"reproduction")
        
        if  (Pl.Plant["phenology_stage"] != "dormancy") and  Ev.Environment["atmos"]["light"] > 0.0:
            # 3. Transpiration
            Be.adjust_leaf_params_angle(
                        Pl.Plant,
                        Ev.Environment,
                        alpha=0.0,
                        beta=0.0,
                        gamma=1.0) 

        # 4. Assimilation
        Fu.nutrient_absorption(Pl.Plant, Ev.Environment)

        # 5. Maintenance
        Fu.handle_process(Pl.Plant, Ev.Environment, "maintenance")

        if Ev.Environment["atmos"]["light"] > 0.0:
            # 6. Reproduction
            if  (Pl.Plant["phenology_stage"] == "reproduction"):
                Fu.handle_process(Pl.Plant, Ev.Environment, "reproduction")
                Fu.update_success_history(Pl.Plant, "reproduction")
                Fu.adapt_for_reproduction(Pl.Plant)

            if (Pl.Plant["phenology_stage"] == "dessication"): 
                    Fu.dessication(Pl.Plant, Ev.Environment)

            if (Pl.Plant["phenology_stage"] == "vegetative"):
                #7. extension
                Fu.handle_process(Pl.Plant, Ev.Environment, "extension")
                Fu.update_success_history(Pl.Plant, "extension")  
                # 9. Water stress adaptation
                if Pl.Plant["adjusted_used"]["extension"]:
                    Fu.adapt_water_supply(Pl.Plant, Ev.Environment) 


            # 8. Réserves
            Fu.refill_reserve(Pl.Plant, "sugar")
            Fu.refill_reserve(Pl.Plant, "water")
            Fu.refill_reserve(Pl.Plant, "nutrient")

        #Fu.destroy_biomass(Pl.Plant, Ev.Environment, "necromass", Gl.delta_adapt)

        # 10. Mortalité
        if Pl.Plant["biomass_total"] <= 0.005: 
            Pl.Plant["alive"] = False

        # 11. Sauvegarde historique
        Hi.history_update(Pl.Plant, Hi.history, Ev.Environment, time)

    return Hi.history, Pl.Plant, Ev.Environment
