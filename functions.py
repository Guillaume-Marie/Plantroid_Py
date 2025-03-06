import global_constants as Gl
import Environnement_def as Ev

#######################################
#         FONCTIONS DE SANTÉ          #
#######################################

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

def destroy_biomass(Plant, Env, which_biomass, damage_factor=None):
    """
    Détruit une fraction (Gl.delta_adapt ou damage_factor) de la biomasse spécifiée,
    et ajoute cette biomasse détruite aux 'litter'.
    """
    if damage_factor is None:
        damage_factor = Gl.delta_adapt

    lost = Plant["biomass"][which_biomass] * damage_factor
    Plant["biomass"][which_biomass] -= lost
    Env["litter"][which_biomass] += lost
    Plant["biomass_total"] = sum(Plant["biomass"].values())


def refill_reserve(Plant, rsc):
    """
    Transfère toute la flux_in[rsc] dans les réserves reserve[rsc].
    """
    if Plant["flux_in"][rsc] > 0 :
        usable_in = Plant["flux_in"][rsc]
        Plant["flux_in"][rsc] -= usable_in
        Plant["reserve"][rsc] += usable_in


#################################################
#      FONCTIONS PHYSIOLOGIQUES FLUX BASED      #
#################################################

def calculate_potential_new_biomass(Plant):
    """
    Forme monomoléculaire : new_biomass = biomasse_totale * (r_max / (1 + alpha * biomasse_totale))
    """
    bm_total = Plant["biomass_total"]
    r_max = Plant["r_max"]
    alpha = Plant["alpha"]
    return bm_total * (r_max / (1.0 + alpha * bm_total))

def photosynthesis(Plant, Env):
    """
    Photosynthèse : production de sucre (flux_in["sugar"]).
    On enregistre aussi des variables pour l'affichage détaillé.
    """
    # 1) fraction de la puissance lumineuse interceptée J/s/gleaf
    power_absorbed = Env["atmos"]["light"] * 0.02 * Plant["slai"] \
                     * Plant["light_absorption_fraction"]
    
    # Facteur limitant selon la température
    temp_diff = abs(Plant["temperature"]["photo"] - Plant["T_optim"])
    temp_lim = max(0.0, 1.0 - 0.01 * temp_diff)

    # flux initial gC6H12O6/s/gleaf
    C6H12O6_flux_pot = power_absorbed * Gl.conversion_factor * temp_lim 

    # facteur CO2 dimensionless (0...1)
    cf = Env["atmos"]["Co2"] / 400.0

    # on prend en compte la conductance et le CO2
    C6H12O6_flux = C6H12O6_flux_pot * cf * Plant["stomatal_conductance"] 

    # Production finale de sucre en gC6H12O6/DT
    Plant["flux_in"]["sugar"] = C6H12O6_flux * Plant["biomass"]["photo"] * Gl.DT

    # On peut donc estimer la quantité de H2O utilisé pour formé les sucres
    Plant["cost"]["transpiration"]["water"] = Plant["flux_in"]["sugar"] * 0.6

    # Sauvegarde des variables de diagnostic
    Plant["diag"]["raw_sugar_flux"] = C6H12O6_flux_pot   # (gSugar/s par gFeuille, avant surface complète)
    Plant["diag"]["pot_sugar"]      = C6H12O6_flux      # (gSugar/s, avant limitation température)

def nutrient_absorption(Plant, Env):
    """
    Absorption d'eau et de nutriments (flux_in) selon la conduction et la transpiration disponible.
    """
    # Eau absorbée (déjà calculée dans flux_in["water"])
    # Nutriments absorbés proportionnellement
    Plant["flux_in"]["nutrient"] = Plant["flux_in"]["water"] * Plant["water_nutrient"]

def estimate_WUE(Plant, Env):
    """
    Efficacité d'usage de l'eau (WUE) : ratio sucre produit / gramme d'eau
    """ 
    temp_diff = abs(Plant["temperature"]["photo"] - Plant["T_optim"]) / Plant["T_optim"]
    penalty = (1.0 - temp_diff) * Plant["stomatal_conductance"]
    if penalty < 0.33:
        penalty = 0.33
    if Plant["biomass"]["photo"] <= 0:
        penalty = 0.33
    return Gl.base_WUE * penalty

def compute_root_explored_volume(Plant):
    """
    Calcule le volume de sol exploré par les racines en fonction de la biomasse racinaire.
    """
    explored_volume = Plant["biomass"]["absorp"] * Gl.k_root  # cm³
    return min(explored_volume, Gl.total_soil_volume)


def compute_available_water(Plant, Env):
    """
    Calcule l'eau disponible pour la plante en fonction du volume de sol exploré.
    """
    explored_volume = compute_root_explored_volume(Plant)   
    # Calcul de la teneur en eau du sol (g d’eau / cm³ de sol)
    soil_moisture = Env["soil"]["water"] / Gl.total_soil_volume  # g d'eau / cm³ de sol
    available_water = explored_volume * soil_moisture  # g d'eau total disponible
    
    return min(available_water, Env["soil"]["water"])  # On ne peut pas extraire plus que ce qui est dispo

def compute_max_transpiration_capacity(Plant, Env):
    """
    Capacité maximale de transpiration (en g d'eau / cycle) 
    selon :
    - capacité d'absorption des racines
    - capacité de transpiration foliaire
    - eau disponible dans le sol
    """
    absorp_capacity = Plant["biomass"]["absorp"] * Plant["root_absorption_coefficient"] * Gl.DT
    photo_capacity = Plant["biomass"]["photo"] * Plant["slai"] * Plant["stomatal_conductance"] \
                     * Plant["transpiration_coefficient"] * Gl.DT
    soil_capacity = compute_available_water(Plant, Env)

    Plant["max_transpiration_capacity"] = min(soil_capacity, absorp_capacity,  photo_capacity)

def find_transpiration_for_cooling(Plant, Env):
    """
    Besoin d’eau (trans_cooling) pour évacuer la puissance reçue en excès
    sous forme de chaleur latente.
    """
    T_leaf = Plant["temperature"]["photo"]
    T_air  = Env["atmos"]["temperature"]

    # Si la feuille est plus froide ou égale, on ne transpire pas pour le froid.
    if T_leaf < T_air and Env["atmos"]["light"] <= 0.0:
        return 0.0

    # calcul d'une puissance absorbée
    power_absorbed = Env["atmos"]["light"] * 0.02 \
                        * Plant["slai"] * Plant["light_absorption_fraction"] \
                        * 0.5
    power_sensible = Gl.K * (T_leaf - T_air) # J/s
    power_evap = power_absorbed #+ power_sensible  # J/s
    flux_water = power_evap / Gl.LATENT_HEAT_VAPORIZATION  # gH2O/s
    if flux_water < 0:
        flux_water = 0
    return flux_water * Plant["biomass"]["photo"] * Gl.DT

def transpiration_cost(Plant, Env):
    """
    Calcul du besoin total en eau (refroidissement + photosynthèse),
    sous la limite de la capacité max de transpiration.
    On enregistre également des diagnostics pour le suivi.
    """
    compute_max_transpiration_capacity(Plant, Env)
    Plant["trans_cooling"] = find_transpiration_for_cooling(Plant, Env)
    # On définit flux_in["water"] comme la capacité max (on suppose l'absorption tentée)
    Plant["cost"]["transpiration"]["water"] += Plant["trans_cooling"]
    #print("Trans cost:",Plant["cost"]["transpiration"]["water"])
    #print("Trans avail:",Plant["max_transpiration_capacity"])
    if Plant["cost"]["transpiration"]["water"] > Plant["max_transpiration_capacity"]:
        Plant["flux_in"]["water"] = Plant["max_transpiration_capacity"]
    else:
        Plant["flux_in"]["water"] = Plant["cost"]["transpiration"]["water"] 
    Plant["diag"]["max_transpiration_capacity"] = Plant["max_transpiration_capacity"] 
    Plant["max_transpiration_capacity"] -= Plant["flux_in"]["water"] 
    #print("Trans flux in:",Plant["flux_in"]["water"])
    # Sauvegarde dans diag
    Plant["diag"]["trans_cooling"] = Plant["trans_cooling"]


def adjust_stomatal_conductance(Plant, Env):
    """
    Ajuste la conductance stomatique pour rester dans la capacité de transpiration.
    """
    delta = Plant["cost"]["transpiration"]["water"] - Plant["flux_in"]["water"]
    #print("Ajust Gs cost:",Plant["flux_in"]["water"])
    #print("Ajust Gs cost:",Plant["cost"]["transpiration"]["water"])
    #print("delta:",delta)
    while delta > 0.0 and Plant["stomatal_conductance"] != 0.01:  
        Plant["stomatal_conductance"] -= 0.001
        if Plant["stomatal_conductance"] < 0.01:
            Plant["stomatal_conductance"] = 0.01
        Plant["light_absorption_fraction"] -= 0.0005
        if Plant["light_absorption_fraction"] <= 0.01:
            Plant["light_absorption_fraction"] = 0.01
        photosynthesis(Plant, Env)
        transpiration_cost(Plant, Env)
        #print("Ajust Gs cost:",Plant["cost"]["transpiration"]["water"])
        #print("Ajust Gs cost:",Plant["flux_in"]["water"])
        delta = Plant["cost"]["transpiration"]["water"] - Plant["flux_in"]["water"]


def adjust_leaf_temperature(Plant, Env):
    """
    Met à jour la température foliaire en fonction du bilan
    entre la puissance absorbée, l'évaporation et la convection.
    """
    #print("Ajust T cost:", Plant["trans_cooling"])
    power_absorbed = Env["atmos"]["light"] * 0.02 *  \
                        Plant["slai"] * Plant["light_absorption_fraction"] * 0.5
    power_evap = (Plant["trans_cooling"] / max(Plant["biomass"]["photo"],1e-9) / \
                 Gl.DT) * Gl.LATENT_HEAT_VAPORIZATION
    T_leaf = Plant["temperature"]["photo"]
    T_air  = Env["atmos"]["temperature"]
    Plant["diag"]["atmos_temperature"] = T_air
    Plant["diag"]["leaf_temperature_before"] = T_leaf
    power_sensible = Gl.K * (T_leaf - T_air)

    dE = power_absorbed - power_evap #+ power_sensible  # J/s
    if abs(dE) < 1e-9:
        dE = 0.0

    heat_capacity = Gl.SPECIFIC_HEAT_LEAF * Plant["biomass"]["photo"]  # J/°C
    if heat_capacity < 1e-9:
        heat_capacity = 1e-9
    #print("dE:", dE)
    #print("power_absorbed:",power_absorbed)
    #print("power_evap :",power_evap)
    #print("power_sensible:",power_sensible)
    dT = (dE * Gl.DT) / heat_capacity
    #print("dT:", dT)

    Plant["temperature"]["photo"] += dT

    if Plant["temperature"]["photo"] < T_air or power_absorbed <= 0.0 :
        Plant["temperature"]["photo"] = T_air

    Plant["diag"]["leaf_temperature_after"] = T_leaf
    if Plant["temperature"]["photo"] > 45:
        destroy_biomass(Plant, Env, "photo", 0.1)


##############################################
#   GESTION DES SUCCÈS/ÉCHECS DE PROCESSUS   #
##############################################

def post_process_success(Plant, Env, process):
    if process == "transpiration":
        #print("cost:",Plant["cost"]["transpiration"]["water"])
        #print("avail:",Plant["flux_in"]["water"])
        pass
    elif process == "maintenance":
        pass
    elif process == "extension":
        allocate_new_biomass(Plant)
        restore_health(Plant)
    elif process == "reproduction":
        restore_health(Plant)

def post_process_resist(Plant, Env, process):
    if process == "transpiration": 
        destroy_biomass(Plant, Env, "photo", 0.005)
    elif process == "maintenance":
        destroy_biomass(Plant, Env, "support",0.005)
    elif process == "extension":
        adjust_success_cycle(Plant, "extension")
        allocate_new_biomass(Plant)
        restore_health(Plant)
    elif process == "reproduction":
        adjust_success_cycle(Plant, "reproduction")
        restore_health(Plant)

def post_process_fail(Plant, Env, process):
    if process == "transpiration": 
        pay_cost(Plant, Env, process)
        #destroy_biomass(Plant, Env, "support")
        destroy_biomass(Plant, Env, "photo", 0.01)
        degrade_health_state(Plant)
        #print("degrade health due to",process)
    elif process == "maintenance":
        pay_cost(Plant, Env, process)
        degrade_health_state(Plant)
        destroy_biomass(Plant, Env, "support", 0.01)
        destroy_biomass(Plant, Env, "absorp", 0.01)
        #print("degrade health due to",process)
    elif process == "extension":
        adjust_success_cycle(Plant, "extension")
        if Plant["success_cycle"]["extension"] > 0:
            pay_cost(Plant, Env, process)
            allocate_new_biomass(Plant)
    elif process == "reproduction":
        pay_cost(Plant, Env, process)
        adjust_success_cycle(Plant, "reproduction")


################################################
#    HANDLER GÉNÉRAL POUR LES PROCESSUS        #
################################################

def handle_process(Plant, Env, process):
    """
    Vérifie si ressources suffisantes et effectue le paiement (cost).
    """
    if resources_available(Plant, process):
        update_stress_history(Plant, process)
        pay_cost(Plant, Env, process)
        post_process_success(Plant, Env, process)
        return

    draw_from_reserves(Plant, process)
    #print("draw_from_reserves for",process)
    if resources_available(Plant, process):
        update_stress_history(Plant, process)
        pay_cost(Plant, Env, process)
        post_process_resist(Plant, Env, process)
        return

    update_stress_history(Plant, process)
    #print("adjust_costs for",process)
    adjust_cost(Plant, Env, process)
    post_process_fail(Plant, Env, process)

def resources_available(Plant, process):
    """
    Vérifie la disponibilité des ressources pour chaque process.
    """
    if process != "transpiration":
        if (Plant["flux_in"]["sugar"]    >= Plant["cost"][process]["sugar"] and
            Plant["max_transpiration_capacity"] >= Plant["cost"][process]["water"] and
            Plant["flux_in"]["nutrient"] >= Plant["cost"][process]["nutrient"]):
            return True
        else:
            return False
    else:
        if(Plant["flux_in"]["water"] >= Plant["cost"][process]["water"]):
            return True
        else:
            return False


def pay_cost(Plant, Env, process):
    """
    Soustrait le coût en ressources ou en flux.
    """
    if process != "transpiration":
        Plant["max_transpiration_capacity"] -= Plant["cost"][process]["water"]
        Plant["reserve"]["water"] += Plant["cost"][process]["water"]
        Plant["flux_in"]["sugar"] -= Plant["cost"][process]["sugar"]
        Plant["flux_in"]["nutrient"] -= Plant["cost"][process]["nutrient"]      
    else:
        residual = Plant["flux_in"]["water"] - Plant["cost"][process]["water"]
        if residual >= 0:
            adjust_leaf_temperature(Plant, Ev.Environment)
            Plant["flux_in"]["water"] -= Plant["cost"][process]["water"] 
            Env["soil"]["water"] -= Plant["flux_in"]["water"]
        else:
            adjust_leaf_temperature(Plant, Ev.Environment)
            Env["soil"]["water"] -= Plant["flux_in"]["water"]
            Plant["flux_in"]["water"] = 0


def calculate_cost(Plant, Env, process):
    """
    Calcule le coût en ressources (en g).
    """
    if process == "transpiration":
        transpiration_cost(Plant, Env)
    elif process == "reproduction":
            for r in Gl.resource:
                cost_factor = Plant["cost_params"][process]["unique"][r]
                Plant["cost"][process][r] = cost_factor * Plant["biomass"]["photo"]        
    elif process == "maintenance":
            cost_factor = Plant["cost_params"][process]["unique"]["sugar"]
            # Coût proportionnel à la biomasse totale et au temps
            Plant["cost"][process]["sugar"] = cost_factor *  \
                                        Plant["biomass_total"] * Gl.DT
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
    if process == "transpiration":
        adjust_stomatal_conductance(Plant, Env)
    elif process == "extension":
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
    else:
        if process in ["maintenance", "reproduction"]:
            limiting_bio = float('inf')
            for r in Gl.resource:
                denom = Plant["cost_params"][process]["unique"].get(r, 1e-12)
                if denom > 0:
                    max_bio = Plant["flux_in"][r] / denom
                    if max_bio < limiting_bio:
                        limiting_bio = max_bio

            for r in Gl.resource:
                cost_factor = Plant["cost_params"][process]["unique"].get(r, 0.0)
                Plant["cost"][process][r] = cost_factor * limiting_bio


def draw_from_reserves(Plant, process):
    """
    Tente d'utiliser les réserves internes si flux_in n'est pas suffisant.
    """
    for r in Gl.resource:
        shortfall = Plant["cost"][process][r] - Plant["flux_in"][r]
        #print("shortfal:",shortfall, "for :", r," in process :", process)
        #print("cost:",Plant["cost"][process][r])
        #print("avail:",Plant["flux_in"][r])
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
        sugar_available = Plant["flux_in"]["water"] + Plant["reserve"]["water"]
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
        Plant["slai"] = min(1.0, Plant["slai"] + Gl.delta_adapt)
    elif Env["atmos"]["light"] > 800:
        Plant["slai"] = max(0.01, Plant["slai"] - Gl.delta_adapt)

def adapt_and_optimize(Plant, Env):
    """
    Réallocation de la biomasse en cas de stress eau/sucre chroniques.
    """
    mean_stress_water = sum(Plant["stress_history"]["water"])/len(Plant["stress_history"]["water"]) \
                        if Plant["stress_history"]["water"] else 0.0
    mean_stress_sugar = sum(Plant["stress_history"]["sugar"])/len(Plant["stress_history"]["sugar"]) \
                        if Plant["stress_history"]["sugar"] else 0.0

    if mean_stress_water > mean_stress_sugar:
        # Stress eau
        #Plant["storage_fraction"]["water"]    += Gl.delta_adapt
        #Plant["storage_fraction"]["nutrient"] += Gl.delta_adapt
        if Plant["ratio_allocation"]["absorp"] <= 0.8:
            Plant["ratio_allocation"]["support"]  -= Gl.delta_adapt/2
            Plant["ratio_allocation"]["absorp"]   += Gl.delta_adapt
            Plant["ratio_allocation"]["photo"]    -= Gl.delta_adapt/2
        #destroy_biomass(Plant, Env, "absorp")
    else:
        # Stress sucre
        #Plant["storage_fraction"]["sugar"] += Gl.delta_adapt
        if Plant["ratio_allocation"]["photo"] <= 0.8:
            Plant["ratio_allocation"]["support"] -= Gl.delta_adapt/2
            Plant["ratio_allocation"]["photo"]   += Gl.delta_adapt
            Plant["ratio_allocation"]["absorp"]  -= Gl.delta_adapt/2
        #destroy_biomass(Plant, Env, "photo")
        adapt_leaf_structure(Plant, Env)


def allocate_new_biomass(Plant):
    """
    Répartit la new_biomass dans les trois catégories fonctionnelles.
    """
    nb = Plant["new_biomass"]
    ra = Plant["ratio_allocation"]
    add_support = nb * ra["support"]
    add_photo   = nb * ra["photo"]
    add_absorp  = nb * ra["absorp"]

    Plant["biomass"]["support"] += add_support
    Plant["biomass"]["photo"]   += add_photo
    Plant["biomass"]["absorp"]  += add_absorp

    Plant["biomass_total"] = sum(Plant["biomass"].values())


def adjust_success_cycle(Plant, process):
    """
    success_cycle = new_biomass / (biomass_total * croissance attendue).
    """
    expected = calculate_potential_new_biomass(Plant)
    if expected > 0:
        Plant["success_cycle"][process] = Plant["new_biomass"] / expected
    else:
        Plant["success_cycle"][process] = 0.0
