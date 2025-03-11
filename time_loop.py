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
    Boucle principale de simulation, 
    avec condition de germination si min nocturne > 10°C sur 7 jours.
    """
    global time
    cycle_count = 0
    time = 0  # réinitialisation
    time_for_reproduction = False
    time_for_dessication = False
    time_for_making_reserve = False

    # Variables pour suivre la température minimale quotidienne
    daily_min_temps = []
    day_min_temp = float('inf')  # Pour stocker la T min courante de la journée
    previous_day_index = 0       # Pour savoir quand on change de jour
    Pl.Plant["biomass"]['photo'] = Pl.Plant["biomass_total"] * Pl.Plant["ratio_allocation"]['photo']
    Pl.Plant["biomass"]['support'] = Pl.Plant["biomass_total"] * Pl.Plant["ratio_allocation"]['support']
    Pl.Plant["biomass"]['absorp'] = Pl.Plant["biomass_total"] * Pl.Plant["ratio_allocation"]['absorp']
    Pl.Plant["biomass"]['repro'] = Pl.Plant["biomass_total"] * Pl.Plant["ratio_allocation"]['repro']
    
    while Pl.Plant["alive"] and cycle_count < max_cycles:
        time += 1
        cycle_count += 1

        # Calcul de l'heure locale (0..23)
        hour_in_day = time % 24
        day_index   = time // 24  # numéro du jour en cours

        # 1. Environnement 
        Ev.update_environment(time, Ev.Environment)
        # -- Mise à jour de la température minimale quotidienne --
        # 1) Si on vient de changer de jour => on remet day_min_temp à inf
        if day_index != previous_day_index:
            #print("day:", day_index)  
            #print("time_for_making_reserve:",time_for_making_reserve)
            #print("time_for_reproduction:",time_for_reproduction)
            #print("time_for_dessication:",time_for_dessication)
            #print("is_dormancy:",Pl.Plant["is_dormancy"])
            day_min_temp = float('inf')
            # reset stomatal conductance everyday
            Pl.Plant["stomatal_conductance"] = 1.0
            previous_day_index = day_index

        # 2) Mettre à jour la valeur min au fur et à mesure
        Ev.update_environment(time, Ev.Environment)
        T_current = Ev.Environment["atmos"]["temperature"]
        if T_current < day_min_temp:
            day_min_temp = T_current

        # 3) En fin de journée (e.g. hour_in_day == 23), on sauvegarde la T min du jour
        if hour_in_day == 23:
            daily_min_temps.append(day_min_temp)
            # On ne garde que les 30 derniers jours par ex. pour éviter de gonfler la liste
            if len(daily_min_temps) > 30:
                daily_min_temps.pop(0)

            # Vérifier si la plante est déjà germée
            if not Pl.Plant["germinated"] or Pl.Plant["is_dormancy"] :
                # Si on a au moins 7 jours, vérifier si toutes > 10°C
                if len(daily_min_temps) >= 3:
                    last_7 = daily_min_temps[-3:]  # on prend les 7 dernières
                    if all(t > 3.0 for t in last_7):
                        Pl.Plant["germinated"] = True
                        Pl.Plant["is_dormancy"] = False
                        # Optionnel: print("Germination déclenchée le jour", day_index)


        Pl.Plant["diag"] = {}
        Pl.Plant["reserve_used"]  = {"maintenance": False,
                                    "extension": False, 
                                    "reproduction": False, 
                                    "transpiration":False}
        Pl.Plant["adjusted_used"] = {"maintenance": False, 
                                     "extension": False, 
                                     "reproduction": False, 
                                     "transpiration":False}
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
        Pl.Plant["light_absorption_coeff"] = Pl.Plant["light_absorption_max"]

        if not Pl.Plant["germinated"]:
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

        #print("photoperiod : ",Ev.calc_daily_photoperiod(day_index))
        if Ev.calc_daily_photoperiod(day_index) < Ev.calc_daily_photoperiod(day_index-1):            
                if Pl.Plant["growth_type"] != "biannual":
                    if ( Ev.calc_daily_photoperiod(day_index) < Pl.Plant["photoperiod_for_repro"] 
                        and Pl.Plant["growth_type"] == "perennial"):
                        time_for_dessication = True  
                    elif Pl.Plant["growth_type"] != "perennial":
                        time_for_dessication = True 
                else:
                    time_for_making_reserve = True 

        if Ev.calc_daily_photoperiod(day_index) > Pl.Plant["photoperiod_for_repro"]:
            if day_index > 365 and Pl.Plant["growth_type"] == "biannual":
                time_for_reproduction = True               
                time_for_dessication = True
            elif Pl.Plant["growth_type"] != "biannual":
                time_for_reproduction = True

        if Ev.calc_daily_photoperiod(day_index) < Pl.Plant["photoperiod_for_repro"]:
            if Pl.Plant["growth_type"] != "biannual":
                time_for_reproduction = False
                Pl.Plant["ratio_allocation"]["repro"] = 0.0
                Fu.check_allocation(Pl.Plant)

        if Pl.Plant["biomass"]["photo"] < 0.001 and time_for_dessication:
                time_for_dessication = False
                Pl.Plant["is_dormancy"] = True   
                Pl.Plant["ratio_allocation"]["photo"] = 0.55
                Pl.Plant["ratio_allocation"]["absorb"] = 0.35
                Pl.Plant["ratio_allocation"]["support"] = 0.1                
                Fu.check_allocation(Pl.Plant)

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

        # 4. Assimilation
        Fu.nutrient_absorption(Pl.Plant, Ev.Environment)

        # 5. Maintenance
        Fu.handle_process(Pl.Plant, Ev.Environment, "maintenance")

        if Ev.Environment["atmos"]["light"] > 0.0:
            # 6. Reproduction
            if time_for_reproduction and not Pl.Plant["is_dormancy"]:
                Fu.handle_process(Pl.Plant, Ev.Environment, "reproduction")
                Fu.update_success_history(Pl.Plant, "reproduction")
                Fu.adapt_for_reproduction(Pl.Plant)

            if time_for_dessication and not Pl.Plant["is_dormancy"]: 
                    Fu.dessication(Pl.Plant, Ev.Environment)

            if not time_for_dessication and not time_for_making_reserve and not Pl.Plant["is_dormancy"]:
                #7. extension
                Fu.handle_process(Pl.Plant, Ev.Environment, "extension")
                Fu.update_success_history(Pl.Plant, "extension")  
                # 9. Water stress adaptation
                if Pl.Plant["adjusted_used"]["transpiration"]:
                    Fu.adapt_water_supply(Pl.Plant, Ev.Environment)

            # 8. Réserves
            Fu.refill_reserve(Pl.Plant, "sugar")
            Fu.refill_reserve(Pl.Plant, "water")
            Fu.refill_reserve(Pl.Plant, "nutrient")

        # 10. Mortalité
        if Pl.Plant["biomass_total"] <= 0.005: 
            Pl.Plant["alive"] = False

        # 11. Sauvegarde historique
        Hi.history_update(Pl.Plant, Hi.history, Ev.Environment, time)

    return Hi.history, Pl.Plant, Ev.Environment
