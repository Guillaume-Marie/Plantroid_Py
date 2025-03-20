import global_constants as Gl
import history_def as Hi
import Environnement_def as Ev
import global_constants as Gl
import math

#######################################
#         FONCTIONS DE SANTÉ          #
#######################################
def check_for_negatives(Plant, Env, time):
    """
    Vérifie si un pool de biomasse ou un flux est devenu négatif.
    Si oui, on affiche un message d'erreur détaillé et on met Plant["alive"] à False.
    """
    # 1) Vérifier la biomasse
    for compartment, val in Plant["biomass"].items():
        if val < -1e-12:  # on tolère éventuellement un léger écart numérique
            print("====================================================")
            print(f"ERREUR: Biomasse négative détectée à t={time} h !")
            print(f"Compartiment '{compartment}' = {val:.5f}")
            print("Voici d'autres informations utiles pour le diagnostic :")
            print(f"  - Biomasse totale       = {Plant['biomass_total']:.5f}")
            print(f"  - Biomasse totale       = { Plant['biomass']['photo']:.5f}")
            print(f"  - Biomasse totale       = { Plant['biomass']['absorp']:.5f}")
            print(f"  - Biomasse totale       = { Plant['biomass']['support']:.5f}")    
            print(f"  - Biomasse totale       = { Plant['biomass']['repro']:.5f}") 
            print(f"  - Flux in sugar         = { Plant['flux_in']['sugar'] :.5f}")
            print(f"  - Flux in water         = { Plant['flux_in']['water'] :.5f}")  
            print(f"  - Flux in nutrient      = { Plant['flux_in']['nutrient'] :.5f}")                   
            print(f"  - Reserve sugar         = {Plant['reserve']['sugar']:.5f}")
            print(f"  - Reserve water         = {Plant['reserve']['water']:.5f}")
            print(f"  - Reserve nutrient      = {Plant['reserve']['nutrient']:.5f}")
            print(f"  - Phenology stage       = {Plant['phenology_stage']}")
            print(f"  - Health state          = {Plant['health_state']}")
            print("====================================================")
            Plant["alive"] = False
            return True  # indique qu'on a trouvé une erreur

    # 2) Vérifier les flux
    for flux_name, val in Plant["flux_in"].items():
        if val < -1e-12:
            print("====================================================")
            print(f"ERREUR: Flux négatif détecté à t={time} h !")
            print(f"Flux '{flux_name}' = {val:.5f}")
            print("Informations de diagnostic :")
            print(f"  - Biomasse total        = {Plant['biomass_total']:.5f}")
            print(f"  - Biomasse photo        = { Plant['biomass']['photo']:.5f}")
            print(f"  - Biomasse absorp       = { Plant['biomass']['absorp']:.5f}")
            print(f"  - Biomasse support      = { Plant['biomass']['support']:.5f}")    
            print(f"  - Biomasse repro        = { Plant['biomass']['repro']:.5f}")  
            print(f"  - Flux in sugar         = { Plant['flux_in']['sugar'] :.5f}")
            print(f"  - Flux in water         = { Plant['flux_in']['water'] :.5f}")  
            print(f"  - Flux in nutrient      = { Plant['flux_in']['nutrient'] :.5f}")                     
            print(f"  - Reserve sugar         = {Plant['reserve']['sugar']:.5f}")
            print(f"  - Reserve water         = {Plant['reserve']['water']:.5f}")
            print(f"  - Reserve nutrient      = {Plant['reserve']['nutrient']:.5f}")
            print(f"  - Phenology stage       = {Plant['phenology_stage']}")
            print(f"  - Health state          = {Plant['health_state']}")
            print("====================================================")
            Plant["alive"] = False
            return True

    # 3) Aucune erreur trouvée
    return False


import numpy as np

def slope_last_hours(history, nb_hours=72):
    """
    Calcule la pente d'une régression linéaire
    sur les nb_hours derniers pas de temps de history[var_name].
    
    history : dictionnaire contenant notamment history[var_name] (liste ou array)
    var_name : nom de la variable, ex. "reserve_sugar"
    nb_hours : nombre d'heures sur lesquelles faire la régression (72 = 3 jours)
    
    Renvoie le slope (pente) en unités de var_name par pas de temps.
    """
    if len(history) < nb_hours:
        # si on n'a pas assez de points, on renvoie zéro ou None
        return 0.0

    # Extraction des nb_hours derniers points
    data = history[-nb_hours:]
    x = np.arange(len(data), dtype=float)  # 0..(nb_hours-1)
    y = np.array(data, dtype=float)

    # Ajustement linéaire : slope, intercept
    slope, intercept = np.polyfit(x, y, 1)
    return slope


def degrade_health_state(Plant):
    """
    Diminue la santé de la plante de 1.
    Incrémente dying_state_count si health_state < 0.
    """
    Plant["health_state"] -= 1
    if Plant["health_state"] < 0:
        Plant["dying_state_count"] += 1
    else:
        Plant["dying_state_count"] = 0

def restore_health(Plant):
    """
    Restaure la santé de 1 unité si < 100.
    """
    if Plant["health_state"] < 100:
        Plant["health_state"] += 1

def destroy_biomass(Plant, Env, which_biomass, process, damage_factor=None):
    """
    Détruit une fraction de la biomasse spécifiée et l'ajoute à la nécromasse.
    Récupère eau et nutriments, renvoyés par exemple au sol (simplifié).
    """

    if damage_factor is None:
        damage_factor = Gl.delta_adapt

    lost = Plant["biomass"][which_biomass] * damage_factor

    # On enlève lost du compartiment vivant
    Plant["biomass"][which_biomass] -= lost

    # On ajoute la même quantité à la nécromasse
    if which_biomass == "necromass" or which_biomass == "repro":
        Env["litter"]["necromass"] += lost
    else: 
        Plant["biomass"]["necromass"] += lost

    # retranslocation des nutriment vers le reserve
    if which_biomass == "nutrient" and process == "extension":
        Plant["reserve"][which_biomass] += (lost / 
            Plant["cost_params"][process][which_biomass]["nutrient"])*0.5

    # Mettre à jour la biomasse vivante totale :
    update_biomass_total(Plant)

def ensure_maintenance_sugar(Plant, Env):
    """
    Vérifie si la plante a suffisamment de sucre pour la maintenance.
    Sinon, détruit assez de biomasse (cannibalisation) pour libérer 
    le sucre manquant et éviter un flux négatif.
    
    Hypothèse : 1 g de biomasse vivante détruite fournit 'cannibal_ratio' g de sucre.
                On détruit d'abord la biomasse 'photo', puis si besoin 'support', etc.
    """
    # 1) Récupérer le coût en sucre pour la maintenance
    needed_sugar = Plant["cost"]["maintenance"]["sugar"]
    
    # 2) Calculer la quantité actuellement disponible
    available_sugar = Plant["flux_in"]["sugar"] + Plant["reserve"]["sugar"]
    
    # 3) Court-circuit si tout va bien
    shortfall = needed_sugar - available_sugar
    if shortfall <= 0:
        return  # Rien à faire, on a déjà assez de sucre

    # ------------------------------------------------------------
    # 4) Sinon, on détruit de la biomasse vivante pour libérer du sucre
    #    Hypothèse simplifiée : 1 g de biomasse => cannibal_ratio g de sucre
    # ------------------------------------------------------------

    # On procède dans un ordre défini (ex: 'photo' puis 'support' puis 'absorp')
    compartments_order = ["photo","absorp","support"]
    
    # Combien de grammes de biomasse nous faut-il détruire ?
    # shortfall = mass_to_destroy * cannibal_ratio
    # => mass_to_destroy = shortfall / cannibal_ratio
    mass_to_destroy = shortfall / Plant["cannibal_ratio"]
    
    for comp in compartments_order:
        if mass_to_destroy <= 0:
            break  # on a déjà couvert le besoin
        if Plant["biomass"][comp] > 0:
            # quantité qu'on peut détruire sur ce compartiment
            can_destroy = Plant["biomass"][comp]*0.05
            destroy_here = min(can_destroy, mass_to_destroy)
            
            # 1) On détruit effectivement la biomasse
            Plant["biomass"][comp] -= destroy_here
                # On ajoute la même quantité à la nécromasse
            if comp == "necromass" or comp == "repro":
                Env["litter"]["necromass"] += destroy_here
            else: 
                Plant["biomass"]["necromass"] += destroy_here
            # 2) On récupère le sucre correspondant
            sugar_recovered = destroy_here * Plant["cannibal_ratio"]
            
            # 3) On ajoute ce sucre à flux_in ou reserve, pour payer la maintenance
            #    ici, on choisit par ex. d'ajouter dans flux_in["sugar"]
            Plant["flux_in"]["sugar"] += sugar_recovered
            
            # 4) On met à jour la quantité qu’il reste à détruire
            mass_to_destroy -= destroy_here
    
    # MàJ : on recalcule la biomasse vivante totale
    update_biomass_total(Plant)
    
    # Facultatif : si malgré tout la plante n'a toujours pas assez de sucre,
    # on peut la forcer à mourir ou dégrader sa santé
    remaining_shortfall = Plant["cost"]["maintenance"]["sugar"] - (Plant["flux_in"]["sugar"] + Plant["reserve"]["sugar"])
    if remaining_shortfall > 0:
        pass
        #print("WARNING: Even after cannibalizing biomass, not enough sugar for maintenance!")
        # Option 1 : on tue la plante
        # Plant["alive"] = False
        # Option 2 : on dégrade simplement la santé
        # degrade_health_state(Plant)

def refill_reserve(Plant, rsc):
    """
    Transfère toute la flux_in[rsc] dans les réserves reserve[rsc].
    """
    if rsc =="water" and Plant["reserve"][rsc] >= Plant["biomass_total"]:
        return

    if Plant["flux_in"][rsc] >= 0.0 :
        usable_in = Plant["flux_in"][rsc] * Gl.delta_adapt
        Plant["flux_in"][rsc] -= usable_in
        Plant["reserve"][rsc] += usable_in
    else:
        print("error in refill flux_in in :", rsc,
               "is negative : ", Plant["flux_in"][rsc])


#################################################
#      FONCTIONS PHYSIOLOGIQUES FLUX BASED      #
#################################################

def calculate_potential_new_biomass(Plant, bm_total):
    """
    Forme monomoléculaire : new_biomass = biomasse_totale * (r_max / (1 + alpha * biomasse_totale))
    """
    r_max = Plant["r_max"]
    alpha = Plant["alpha"]
    return bm_total * (r_max / (1.0 + alpha * bm_total))

def photosynthesis(Plant, Env):
    """
    Photosynthèse : production de sucre (flux_in["sugar"]).
    On enregistre aussi des variables pour l'affichage détaillé.
    """
    cos_theta = max(0.0, math.cos(Plant["leaf_angle"]))
    absorbed_solar = Env["atmos"]["light"] * cos_theta * (1.0 - Plant["leaf_albedo"])
    # 1) fraction de la puissance lumineuse interceptée J/s/gleaf
    power_absorbed = absorbed_solar * Plant["sla_max"] * Plant["slai"] 
    
    # Facteur limitant selon la température
    temp_diff = abs(Plant["temperature"]["photo"] - Plant["T_optim"])
    temp_lim = max(0.0, 1.0 - Plant["temp_photo_sensitivity"] * temp_diff)

    # flux initial gC6H12O6/s/gleaf
    C6H12O6_flux_pot = (power_absorbed * 
                        Plant["watt_to_sugar_coeff"] * 
                        temp_lim * 
                        Plant["nutrient_index"])

    # facteur CO2 dimensionless (0...1)
    cf = Env["atmos"]["Co2"] / 400.0

    # on prend en compte la conductance et le CO2
    C6H12O6_flux = (C6H12O6_flux_pot * cf * 
                    Plant["stomatal_conductance"] * 
                    Plant["nutrient_index"])

    # Production finale de sucre en gC6H12O6/DT
    Plant["flux_in"]["sugar"] = C6H12O6_flux * Plant["biomass"]["photo"] * Gl.DT

    # On peut donc estimer la quantité de H2O utilisé pour formé les sucres
    Plant["cost"]["transpiration"]["water"] += Plant["flux_in"]["sugar"] * Gl.RATIO_H2O_C6H12O6 

    # Sauvegarde des variables de diagnostic
    # (gSugar/s par gFeuille, avant surface complète)
    Plant["diag"]["raw_sugar_flux"] = power_absorbed * Plant["watt_to_sugar_coeff"]  
    # (gSugar/s, aprés limitation température)
    Plant["diag"]["pot_sugar"]      = C6H12O6_flux  
    Plant["diag"]["actual_sugar"]   = Plant["flux_in"]["sugar"]

def nutrient_absorption(Plant, Env):
    """
    Calcule l'absorption d'eau et de nutriments par la plante, en fonction :
      - de la quantité d'eau nécessaire pour compenser la transpiration
        (Plant["cost"]["transpiration"]["water"]).
      - de la concentration en nutriments dans le sol
      - d'un coefficient d'efficacité d'absorption (Plant["water_nutrient_coeff"]).

    Cette fonction met à jour :
      - Plant["flux_in"]["water"]
      - Plant["flux_in"]["nutrient"]
      - Env["soil"]["water"]
      - Env["soil"]["nutrient"]

    Hypothèses simplifiées :
    ------------------------
    1) L'eau prélevée par la plante est <= Env["soil"]["water"].
    2) Les nutriments absorbés sont proportionnels à la quantité d'eau absorbée
       et à la concentration en nutriments du sol.
    3) Un coefficient water_nutrient_coeff ∈ [0..1] environ, 
       qui reflète l'efficacité de l'absorption racinaire.

    Remarques :
    -----------
    - Si Env["soil"]["nutrient"] est la quantité *totale* de nutriments,
      on doit convertir en concentration via un volume de sol. 
      Exemple : Env.get("soil_volume", 1.0) = 10 m3 = 1e7 cm3, etc.
    - Si vous souhaitez un modèle plus complet, vous pouvez introduire
      des saturations, des cinétiques de Michaelis-Menten, etc.
    """

    # 1) Eau nécessaire pour la transpiration
    water_needed = Plant["cost"]["transpiration"]["water"]
    if water_needed <= 0.0:
        # Pas de besoin en eau => pas d'absorption de nutriments
        return

    # 2) Vérifier la disponibilité en eau dans le sol
    water_in_soil = Env["soil"]["water"]
    if water_in_soil <= 0.0:
        # Sol complètement sec => pas d'absorption possible
        return

    # 3) Eau effectivement absorbée = min(eau nécessaire, eau disponible)
    water_absorbed = min(water_needed, water_in_soil)

    # 4) Calcul de la concentration en nutriments dans le sol
    #    Soit on l'a déjà via Env["soil"].get("nutrient_concentration", 0.0)
    #    Soit on la calcule : nutriments_tot / volume_sol
    soil_nutrient_total = Env["soil"]["nutrient"]  # total (en g)
    soil_water = Env["soil"]["water"]      # exemple : 1 m3 = 1000 L

    Env["soil"]["nutrient_concentration"] = soil_nutrient_total / soil_water

    # 5) Nutriments potentiellement absorbables = eau_absorbée * concentration
    #    On applique aussi le coefficient water_nutrient_coeff
    nutrients_pot_absorbed = water_absorbed * Env["soil"]["nutrient_concentration"] * Plant["water_nutrient_coeff"]

    # On ne peut pas absorber plus de nutriments que ce qui est présent dans Env["soil"]["nutrient"]
    nutrients_absorbed = min(nutrients_pot_absorbed, Env["soil"]["nutrient"])

    #    - Les nutriments absorbés
    Plant["flux_in"]["nutrient"] += nutrients_absorbed

    # 7) Mise à jour du sol
    Env["soil"]["water"] -= water_absorbed
    Env["soil"]["nutrient"] -= nutrients_absorbed

    # 8) (Optionnel) : Stocker des infos de diagnostic si nécessaire
    if "diag" not in Plant:
        Plant["diag"] = {}
    Plant["diag"]["nutrient_absorption"] = {
        "water_absorbed": water_absorbed,
        "nutrients_absorbed": nutrients_absorbed,
        "nutrient_concentration": Env["soil"]["nutrient_concentration"] 
    }


def compute_stomatal_area(Plant):
    # Stomatal_number * pore_area => aire totale (m²) de tous les stomates / m² de feuille
    # => m² de pores par m² foliaire
    stomatal_factor = (Plant["stomatal_density"] *
                        Plant["biomass"]["photo"] *
                        Plant["sla_max"] * 
                        Plant["slai"])
    return stomatal_factor

def compute_stomatal_conductance_max(Plant):
    """
    Calcule la conductance stomatique maximale (en m/s, très simplifiée),
    à partir de la fraction de surface porale et d'hypothèses
    sur la diffusion et la profondeur des stomates.

    Retourne un float (m s^-1).
    """
    # 1) On récupère la fraction d'aire de pores (dimensionless) 
    #    depuis compute_stomatal_area(Plant).
    #    Par exemple, si compute_stomatal_area = 0.01, 
    #    ça veut dire 1% de la surface foliaire est 'ouverte'.
    area_fraction = compute_stomatal_area(Plant)
    # 4) Formule simplifiée
    g_stomatal_max = area_fraction * (Gl.D_H2O / Gl.pore_depth)

    return g_stomatal_max

def compute_root_explored_volume(Plant, Env):
    """
    Calcule le volume de sol exploré par les racines en fonction de la biomasse racinaire.
    """
    explored_volume = Plant["biomass"]["absorp"] * Gl.k_root  # cm³
    return min(explored_volume, Env["soil_volume"]*1e6 )


def compute_available_water(Plant, Env):
    """
    Calcule l'eau disponible pour la plante en fonction du volume de sol exploré.
    """
    explored_volume = compute_root_explored_volume(Plant, Env)   
    # Calcul de la teneur en eau du sol (g d’eau / cm³ de sol)
    soil_moisture = Env["soil"]["water"] / (Env["soil_volume"]*1e6)  # g d'eau / cm³ de sol
    available_water = explored_volume * soil_moisture  # g d'eau total disponible
    
    return min(available_water, Env["soil"]["water"])  # On ne peut pas extraire plus que ce qui est dispo

def compute_max_transpiration_capacity(Plant, Env):
    """
    Calcule la capacité maximale de transpiration (en g d'eau / cycle) 
    selon :
    - capacité de transpiration foliaire
    - capacité de transport (biomasse support)
    - eau disponible dans le sol
    """
    # 1) Calcul des capacités individuelles
    gs = compute_stomatal_conductance_max(Plant) * Plant["stomatal_conductance"] 
    photo_capacity = gs * Gl.D_H2O * Gl.VPD * Gl.DT
    support_capacity = (Plant["biomass"]["support"]
                        * Plant["support_transport_coeff"]* Gl.DT)
    soil_capacity = compute_available_water(Plant, Env)

    # 2) Rassembler les capacités dans un dictionnaire
    capacities = {
        "photo": photo_capacity,
        "support": support_capacity,
        "soil": soil_capacity
    }
    #print("limiting_pool:",min(capacities, key=capacities.get))
    # 3) Extraire la valeur minimale et la clé correspondante
    min_capacity = min(capacities.values())
    limiting_pool = min(capacities, key=capacities.get)
    #print(limiting_pool)
    # 4) Stocker la valeur et l'information du compartiment limitant
    Plant["max_transpiration_capacity"] = min_capacity
    Plant["transp_limit_pool"] = limiting_pool

##############################################
#   GESTION DES SUCCÈS/ÉCHECS DE PROCESSUS   #
##############################################

def post_process_success(Plant, Env, process):
    if process == "maintenance":        
        pay_cost(Plant, Env, process)
    elif process == "extension":
        allocate_biomass(Plant, Plant["new_biomass"])
        pay_cost(Plant, Env, process)
        restore_health(Plant)
    elif process == "reproduction":        
        allocate_biomass(Plant, Plant["new_biomass"])
        pay_cost(Plant, Env, process)
        restore_health(Plant)

def post_process_resist(Plant, Env, process):
    if process == "maintenance":
        pay_cost(Plant, Env, process)
    elif process == "extension":
        allocate_biomass(Plant, Plant["new_biomass"])
        pay_cost(Plant, Env, process)
        adjust_success_cycle(Plant, "extension")
        restore_health(Plant)
    elif process == "reproduction":        
        allocate_biomass(Plant, Plant["new_biomass"])        
        pay_cost(Plant, Env, process)
        adjust_success_cycle(Plant, "reproduction")
        restore_health(Plant)

def post_process_fail(Plant, Env, process):
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
        if Plant["success_cycle"]["reproduction"] > 0:       
            pay_cost(Plant, Env, process)
            allocate_biomass(Plant, Plant["new_biomass"])



################################################
#    HANDLER GÉNÉRAL POUR LES PROCESSUS        #
################################################

def handle_process(Plant, Env, process):
    """
    Vérifie si ressources suffisantes et effectue le paiement (cost).
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
    Vérifie la disponibilité des ressources pour chaque process.
    """

    if (Plant["flux_in"]["sugar"] >= Plant["cost"][process]["sugar"] and
        Plant["flux_in"]["nutrient"] >= Plant["cost"][process]["nutrient"] and
        Plant["flux_in"]["water"] >= Plant["cost"][process]["water"]) :
        return True
    else:
        return False


def pay_cost(Plant, Env, process):
    """
    Soustrait le coût en ressources ou en flux.
    """
    if process == "extension" or  process == "reproduction":
        Plant["flux_in"]["sugar"] -= Plant["cost"][process]["sugar"]
        Plant["flux_in"]["nutrient"] -= Plant["cost"][process]["nutrient"]
        Plant["flux_in"]["water"] -= Plant["cost"][process]["water"] 
    elif process == "maintenance":
        Plant["flux_in"]["sugar"] -= Plant["cost"][process]["sugar"] 



def calculate_cost(Plant, Env, process):
    """
    Calcule le coût en ressources (en g).
    """
    if process == "reproduction":
        for r in Gl.resource:
            cost_factor = Plant["cost_params"][process]["unique"][r]
            Plant["cost"][process][r] = cost_factor * Plant["reproduction_ref"]* (0.1/24)
    elif process == "maintenance":
        cost_factor = Plant["cost_params"][process]["unique"]["sugar"]
        # Coût proportionnel à la biomasse totale et au temps
        Plant["cost"][process]["sugar"] = cost_factor * Gl.DT * Plant["biomass_total"]
    else: # extension
        for bf in Gl.biomass_function:
            for r in Gl.resource:
                cost_factor = Plant["cost_params"]["extension"][bf][r]
                Plant["cost"][process][r] += cost_factor * Plant["new_biomass"]


def adjust_cost(Plant, Env, process):
    """
    Ajuste le coût si les ressources ou la capacité sont insuffisantes.  
    """    
    Plant["adjusted_used"][process] = True
    if process == "extension":
        # EXTENSION
        limiting_bio = Plant["new_biomass"]
        for bf in Gl.biomass_function:
            for r in Gl.resource:
                denom = Plant["cost_params"]["extension"][bf].get(r, 1e-12)
                if denom > 0:
                    max_bio = Plant["flux_in"][r] / denom
                    if max_bio < limiting_bio:
                        limiting_bio = max_bio
        if limiting_bio < Plant["new_biomass"]:
            Plant["new_biomass"] = limiting_bio
        # Recalcule le coût
        for bf in Gl.biomass_function:
            for r in Gl.resource:
                cost_factor = Plant["cost_params"]["extension"][bf].get(r, 0.0)
                Plant["cost"][process][r] = cost_factor * Plant["new_biomass"]
    elif process =="reproduction":
        limiting_bio = float('inf')
        for r in Gl.resource:
            denom = Plant["cost_params"][process]["unique"].get(r, 1e-12)
            if denom > 0:
                max_bio = Plant["flux_in"][r] / denom
                if max_bio < limiting_bio:
                    limiting_bio = max_bio
        if limiting_bio < Plant["new_biomass"]:
            Plant["new_biomass"] = limiting_bio
        for r in Gl.resource:
            cost_factor = Plant["cost_params"][process]["unique"].get(r, 0.0)
            Plant["cost"][process][r] = cost_factor * limiting_bio
    elif process =="maintenance":
            pass

def draw_from_reserves(Plant, process):
    """
    Tente d'utiliser les réserves internes si flux_in n'est pas suffisant.
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
    Calcule une mesure de stress (0..1).
    Pour maintenance : compare sucre nécessaire vs dispo.
    Pour transpiration : compare eau dispo vs eau demandée.
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
        sugar_available = Plant["reserve"]["water"]
        needed = Plant["cost"]["maintenance"]["water"]
        if needed <= 0:
            return (0.0, "water")
        ratio_available = sugar_available / needed
        stress = 1.0 - min(1.0, ratio_available / Gl.N)
        return (stress, "water")



def update_success_history(Plant, process):
    """
    Ajoute la valeur success_cycle[process] dans l'historique.
    """
    sc = Plant["success_cycle"].get(process, 0.0)
    Plant["success_history"][process].append(sc)
    Plant["success_history"][process] = Gl.keep_last_N(Plant["success_history"][process], Gl.N)


def update_stress_history(Plant, process):
    """
    Met à jour le stress_history pour maintenance ou transpiration.
    """
    if process in ["maintenance" "transpiration"]:
        cycle_stress, rsc = compute_stress(Plant, process)
        Plant["stress_history"][rsc].append(cycle_stress)
        Plant["stress_history"][rsc] = Gl.keep_last_N(Plant["stress_history"][rsc], Gl.N)


##############################################
#  ADAPTATION LIÉE À LA LUMIÈRE / STRESS     #
##############################################

def adapt_leaf_structure(Plant, Env):
    """
    Ajustement du SLAI en fonction de la lumière ambiante.
    """
    if Env["atmos"]["light"] < 300:
        Plant["slai"] = max(0.01, Plant["slai"] - Gl.delta_adapt)
    elif Env["atmos"]["light"] > 800:
        Plant["slai"] = min(1.0, Plant["slai"] + Gl.delta_adapt)
    

def adapt_leaf_nutrient(Plant):

    Plant["nutrient_index"] = max(0.1, 
                Plant["nutrient_index"] - Gl.delta_adapt) 
    Plant["cost_params"]["extension"]["photo"]["nutrient"]= max(0.001, 
                Plant["cost_params"]["extension"]["photo"]["nutrient"] - Gl.delta_adapt) 
    Plant["cost_params"]["extension"]["absorp"]["nutrient"]= max(0.001, 
                Plant["cost_params"]["extension"]["absorp"]["nutrient"] - Gl.delta_adapt) 
    Plant["cost_params"]["extension"]["support"]["nutrient"]= max(0.001, 
                Plant["cost_params"]["extension"]["support"]["nutrient"] - Gl.delta_adapt) 

def adapt_water_supply(Plant, Env):
    """
    Réallocation de la biomasse en cas de stress eau/sucre chroniques.
    """
    #print(Plant["transp_limit_pool"])
    if Plant["transp_limit_pool"]== "soil":
        #Plant["storage_fraction"]["water"]    += Gl.delta_adapt
        #Plant["storage_fraction"]["nutrient"] += Gl.delta_adapt
        if Plant["ratio_allocation"]["absorp"] <= 0.8:
            Plant["ratio_allocation"]["support"]  = max(Plant["ratio_allocation"]["support"]-Gl.delta_adapt/2, 0.0)
            Plant["ratio_allocation"]["absorp"]   += Gl.delta_adapt
            Plant["ratio_allocation"]["photo"]    = max(Plant["ratio_allocation"]["photo"]-Gl.delta_adapt/2, 0.0)
    elif Plant["transp_limit_pool"]== "support":
        if Plant["ratio_allocation"]["support"] <= 0.8:
            Plant["ratio_allocation"]["support"]  += Gl.delta_adapt
            Plant["ratio_allocation"]["absorp"]   = max(Plant["ratio_allocation"]["absorp"]-Gl.delta_adapt/2, 0.0)
            Plant["ratio_allocation"]["photo"]    = max(Plant["ratio_allocation"]["photo"]-Gl.delta_adapt/2 , 0.0)   
    elif Plant["transp_limit_pool"]== "photo":
        #Plant["storage_fraction"]["sugar"] += Gl.delta_adapt
        if Plant["ratio_allocation"]["photo"] <= 0.8:
            Plant["ratio_allocation"]["support"] = max(Plant["ratio_allocation"]["support"]-Gl.delta_adapt/2, 0.0)
            Plant["ratio_allocation"]["photo"]   += Gl.delta_adapt
            Plant["ratio_allocation"]["absorp"]  = max(Plant["ratio_allocation"]["absorp"]-Gl.delta_adapt/2, 0.0)
        adapt_leaf_structure(Plant, Env)
    check_allocation(Plant)

def adapt_for_reproduction(Plant):
    """
    Réallocation de la biomasse en cas de stress eau/sucre chroniques.
    """ 
    if Plant["ratio_allocation"]["repro"] <= Plant["alloc_repro_max"]:
        Plant["ratio_allocation"]["support"] = max(Plant["ratio_allocation"]["support"]-Plant["alloc_change_rate"]/3, 0.0)
        Plant["ratio_allocation"]["photo"]   = max(Plant["ratio_allocation"]["photo"] -Plant["alloc_change_rate"]/3, 0.0)
        Plant["ratio_allocation"]["absorp"]  = max( Plant["ratio_allocation"]["absorp"]-Plant["alloc_change_rate"]/3, 0.0)
        Plant["ratio_allocation"]["repro"]   +=Plant["alloc_change_rate"] 
    check_allocation(Plant)

def adapt_nutrient_supply(Plant):
    """
    Réallocation de la biomasse en cas de stress eau/sucre chroniques.
    """
    #print(Plant["transp_limit_pool"])
    if Plant["ratio_allocation"]["absorp"] <= 0.8:
        Plant["ratio_allocation"]["support"]  = max(Plant["ratio_allocation"]["support"]-Gl.delta_adapt/2, 0.0)
        Plant["ratio_allocation"]["absorp"]   += Gl.delta_adapt
        Plant["ratio_allocation"]["photo"]    = max(Plant["ratio_allocation"]["photo"]-Gl.delta_adapt/2, 0.0)
        adapt_leaf_nutrient(Plant)
    check_allocation(Plant)

def check_allocation(Plant):
    sumalloc = (Plant["ratio_allocation"]["support"]+
    Plant["ratio_allocation"]["photo"] +
    Plant["ratio_allocation"]["absorp"] +
    Plant["ratio_allocation"]["repro"])
    if sumalloc != 1.0:
        Plant["ratio_allocation"]["support"]/sumalloc
        Plant["ratio_allocation"]["photo"] /sumalloc
        Plant["ratio_allocation"]["absorp"]/sumalloc
        Plant["ratio_allocation"]["repro"]/sumalloc

def dessication(Plant, Env):
    """
    Réallocation de la biomasse en cas de stress eau/sucre chroniques.
    """
    if Plant["growth_type"] == "annual" or Plant["growth_type"] == "biannual":
        destroy_biomass(Plant, Env, "support","extension",Plant["dessication_rate"])
    elif Plant["growth_type"] == "perennial":
        destroy_biomass(Plant, Env, "support","extension",Plant["support_turnover"])

    destroy_biomass(Plant, Env, "absorp","extension", Plant["dessication_rate"])
    destroy_biomass(Plant, Env, "photo","extension", Plant["dessication_rate"])
    #destroy_biomass(Plant, Env, "repro","reproduction", Plant["dessication_rate"])


def update_biomass_total(Plant):
    """Recalcule la biomasse totale vivante."""
    Plant["biomass_total"] = (
        Plant["biomass"]["support"] 
        + Plant["biomass"]["photo"] 
        + Plant["biomass"]["absorp"] 
    )

def allocate_biomass(Plant, nb):
    ra = Plant["ratio_allocation"]
    add_support = nb * ra["support"]
    add_photo   = nb * ra["photo"]
    add_absorp  = nb * ra["absorp"]
    add_repro   = nb * ra["repro"]

    Plant["biomass"]["support"] += add_support
    Plant["biomass"]["photo"]   += add_photo
    Plant["biomass"]["absorp"]  += add_absorp
    Plant["biomass"]["repro"]   += add_repro


    # Recalcule la biomasse vivante (nécromasse non incluse)
    update_biomass_total(Plant)


def adjust_success_cycle(Plant, process):
    """
    success_cycle = new_biomass / (biomass_total * croissance attendue).
    """
    expected = Plant["max_biomass"]
    if expected > 0:
        Plant["success_cycle"][process] = Plant["new_biomass"] / expected
    else:
        Plant["success_cycle"][process] = 0.0



def manage_phenology(Plant, Env, day_index, daily_min_temps):
    """
    Gère les événements phénologiques tels que la germination, la reproduction,
    la mise en réserve et la dessiccation en fonction des variations saisonnières 
    de photopériode et de température.

    :param Plant: Dictionnaire représentant la plante.
    :param Env: Dictionnaire représentant l'environnement.
    :param day_index: Numéro du jour courant dans la simulation.
    :param daily_min_temps: Liste des températures minimales journalières récentes.
    """

    photoperiod_today = Ev.calc_daily_photoperiod(day_index)
    photoperiod_yesterday = Ev.calc_daily_photoperiod(day_index - 1)

    # Germination (sortie de dormance)
    if  Plant["phenology_stage"] == "seed" or Plant["phenology_stage"] == "dormancy":
        if len(daily_min_temps) >= 7 and all(t > 3.0 for t in daily_min_temps[-7:]):
            #print("germination ! Day : ",day_index )
            Plant["phenology_stage"] = "vegetative"
            return
        return
    
    sugar_slope = slope_last_hours(Hi.history["reserve_sugar"], nb_hours=24*3)
    #print("sugar_slope:", sugar_slope)
    # Déclenchement de la reproduction
    #photoperiod_today >= Plant["photoperiod_for_repro"] or 
    if (sugar_slope < 0.0 and
        Plant["phenology_stage"] != "reproduction"):
        #print("reproduction time !")
        if Plant["growth_type"] == "biannual" and day_index > 365:
            Plant["phenology_stage"] = "reproduction"
        elif Plant["growth_type"] == "annual":
            Plant["reproduction_ref"] = Plant["biomass_total"]
            Plant["phenology_stage"] = "reproduction"
        elif Plant["growth_type"] == "perennial":
            Plant["phenology_stage"] = "making_reserve"           
        return

    # Détection de la réduction photopériodique
    if photoperiod_today < photoperiod_yesterday:
        if (Plant["growth_type"] == "biannual" and 
             Plant["phenology_stage"] != "making_reserve"):
            Plant["phenology_stage"] = "making_reserve"
        elif (Plant["growth_type"] == "biannual" and 
             Plant["phenology_stage"] != "making_reserve" and
             day_index > 365):
            Plant["phenology_stage"] = "dessication"
            #Plant["ratio_allocation"]["repro"] = 0.0
            check_allocation(Plant)
        elif (photoperiod_today < Plant["photoperiod_for_repro"] and 
             Plant["phenology_stage"] != "dessication"):
            #Plant["phenology_stage"] = "dessication"
            #Plant["ratio_allocation"]["repro"] = 0.0
            check_allocation(Plant)
        return

    # Gestion de la dessiccation en fin de vie ou stress sévère
    if Plant["biomass"]["photo"] < 0.001 and Plant.get("phenology_stage") == "dessication":
        Plant["phenology_stage"] = "dormancy"
        Plant["ratio_allocation"] = {"photo": 0.55, "support": 0.1, "absorp": 0.45, "repro": 0.0}
        check_allocation(Plant)
        return

    # Retourne la plante avec le stade phénologique mis à jour
    return Plant

def intitialize_state_variables(Plant):
    Plant["diag"] = {}
    Plant["reserve_used"]  = {"maintenance": False,
                                "extension": False, 
                                "reproduction": False, 
                                "transpiration":False}
    Plant["adjusted_used"] = {"maintenance": False, 
                                 "extension": False, 
                                 "reproduction": False, 
                                 "transpiration":False}
    Plant["success_cycle"] = {"extension": 1.0, "reproduction": 1.0}
    Plant["cost"] = {
        "extension":   {"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
        "reproduction":{"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
        "maintenance":{"sugar": 0.0, "water": 0.0, "nutrient": 0.0},
        "transpiration":{"sugar": 0.0, "water": 0.0, "nutrient": 0.0}
    }
    Plant["flux_in"] =  {"sugar": 0.0, "water": 0.0, "nutrient": 0.0}
    Plant["new_biomass"] = 0
    Plant["total_water_needed"] = 0
