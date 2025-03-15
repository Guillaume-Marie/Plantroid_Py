import numpy as np
from scipy.optimize import fsolve
import global_constants as Gl
import functions as Fu
import math



def saturation_vapor_pressure(T_C):
    """Pression de vapeur saturante (Pa) à T_C (°C), formule de Magnus."""
    return 610.78 * np.exp(17.27 * T_C / (T_C + 237.3))

def leaf_energy_balance_plantroid(T_leaf_K, Plant, Env):
    """
    Bilan d'énergie foliaire adapté au modèle Plantroid,
    incluant le facteur géométrique cos(leaf_angle) sur le rayonnement incident.
    """
    # --- 1) Extraire les variables depuis Env ---
    shortwave_solar = Env["atmos"]["light"]                     # W·m^-2
    LWR_in          = Env.get("atmos",{}).get("longwave_in", 400.0)
    T_air_C         = Env["atmos"]["temperature"]               # °C
    RH              = Env.get("atmos",{}).get("RH", 0.5)
    wind_speed      = Env.get("wind_speed", 1.0)

    # --- 2) Depuis Plant ---
    albedo_leaf     = Plant.get("albedo_leaf", 0.25)
    emissivity_leaf = Plant.get("emissivity_leaf", 0.95)
    r_stomatal      = Plant.get("r_stomatal", 100.0)   # s/m
    leaf_size       = Plant.get("leaf_size", 0.05)     # m
    leaf_angle      = Plant.get("leaf_angle", 0.0)     # radians, angle entre la normale et le rayon

    # Conversion pour l'air
    T_air_K = T_air_C + 273.15
    T_leaf_C = T_leaf_K - 273.15

    # --- a) Rayonnement solaire absorbé ---
    # On applique cos(leaf_angle), borné à 0 si < 0.
    cos_theta = np.cos(leaf_angle)
    if cos_theta < 0:
        cos_theta = 0.0
    absorbed_solar = shortwave_solar * cos_theta * (1.0 - albedo_leaf)

    # Rayonnement infrarouge émis par la feuille
    LWR_out = emissivity_leaf * Gl.SIGMA * (T_leaf_K**4)
    # Rayonnement net : R_n = (solaire absorbé) + (LWR_in - LWR_out)
    R_n = absorbed_solar + (LWR_in - LWR_out)

    # --- b) Flux de chaleur sensible H ---
    c_coeff = 100.0
    r_a = c_coeff * np.sqrt(leaf_size / max(wind_speed, 0.1))
    H = (Gl.RHO_AIR * Gl.CP_AIR / r_a) * (T_leaf_K - T_air_K)

    # --- c) Flux de chaleur latente (lambda E) ---
    e_s_leaf = saturation_vapor_pressure(T_leaf_C)
    e_s_air  = saturation_vapor_pressure(T_air_C)
    e_a = RH * e_s_air

    r_total = r_stomatal + r_a
    delta_e = max(0.0, e_s_leaf - e_a)  # Pa
    # Flux massique d’eau (kg m^-2 s^-1)
    E_mass = (delta_e / (Gl.R_GAS * T_leaf_K)) * Gl.M_WATER / r_total
    E_mass = 2.0 * E_mass  # double face
    lambdaE = Gl.LAMBDA_VAP * E_mass

    # convertir un flux de chaleur latente λE (en W·m⁻²) en gH2O consommés pendant un pas de temps Δt.
    total_leaf_surface = Plant["biomass"]["photo"] *Plant["sla_max"] * Plant["slai"]
    Plant["cost"]["transpiration"]["water"] += E_mass * 1000 * Gl.DT * total_leaf_surface
    # --- d) Bilan ---
    balance = R_n - H - lambdaE
    return balance

def newton_leaf_temperature(Plant, Env, T_guess, max_iter=2, delta=0.01):
    """
    Effectue 1 à 2 itérations de Newton pour résoudre R_n - H - λE = 0.
    T_guess est la T foliaire initiale (K).
    
    On renvoie T_newton (K).
    """
    def f(TK):
        return leaf_energy_balance_plantroid(TK, Plant, Env)
    
    T_current = T_guess
    for _ in range(max_iter):
        f_plus = f(T_current + delta)
        f_minus = f(T_current - delta)
        fprime = (f_plus - f_minus) / (2.0*delta)  # dérivée centrée

        val = f(T_current)
        if abs(fprime) < 1e-9:
            # Évite la division par zéro
            break

        # Mise à jour Newton
        T_next = T_current - val / fprime
        T_current = T_next

    return T_current

def approximate_leaf_temperature(Plant, Env):
    """
    Retourne une estimation de la température foliaire (°C)
    par un bilan linéarisé (1 itération) sans fsolve.
    """

    # --- Paramètres ---
    emissivity_leaf = Plant.get("emissivity_leaf", 0.95)
    albedo_leaf = Plant.get("albedo_leaf", 0.25)
    leaf_angle = Plant.get("leaf_angle", 0.0)

    T_air = Env["atmos"]["temperature"]  # °C
    wind_speed = Env.get("wind_speed", 1.0)
    RH = Env["atmos"].get("RH", 0.5)
    LWR_in = Env["atmos"].get("longwave_in", 400.0)  # W/m2

    # Convert °C -> K
    T_air_K = T_air + 273.15

    # Rayonnement solaire absorbé
    shortwave_solar = Env["atmos"]["light"]  # W/m2
    cos_theta = max(0.0, math.cos(leaf_angle))
    absorbed_solar = shortwave_solar * cos_theta * (1.0 - albedo_leaf)

    # Approximons la LWR_out en prenant T_air comme pivot
    LWR_out_guess = emissivity_leaf * Gl.SIGMA * (T_air_K ** 4)
    R_n0 = absorbed_solar + (LWR_in - LWR_out_guess)  # W/m2

    # --- Chaleur sensible : g_H ---
    rho_air = 1.225
    c_p = 1005.0
    leaf_size = Plant.get("leaf_size", 0.05)

    # Résistance aéro:
    c_coeff = 100.0
    r_a = c_coeff * math.sqrt(leaf_size / max(wind_speed, 0.1))  # s/m
    g_H = (rho_air * c_p) / r_a  # W/(m2.K)  (cf. eq. H = g_H * (T_leaf - T_air))

    # --- Latente : g_lambda ---
    # 1) Derivée e_s'(T) ~ e_s'(T_air)
    T_air_C = T_air  # en °C
    def saturation_vapor_pressure(TC):
        return 610.78 * math.exp(17.27 * TC / (TC+237.3))  # Pa

    es_air = saturation_vapor_pressure(T_air_C)  # Pa
    # dérivée environ:
    # d es/dT ~ (es(T+0.1) - es(T-0.1)) / 0.2
    es_air_plus  = saturation_vapor_pressure(T_air_C + 0.1)
    es_air_minus = saturation_vapor_pressure(T_air_C - 0.1)
    Delta = (es_air_plus - es_air_minus) / 0.2  # Pa/°C

    # e_a = RH * es(T_air_C)
    e_a = RH * es_air

    # Hypothèse : r_total = r_a + r_stomatal
    r_stomatal = Plant.get("r_stomatal", 100.0)
    r_total = r_a + r_stomatal

    # On peut approx.  g_lambda ~ (lambda_vap * Delta / (r_total ...)) 
    lambda_vap = 2.45e6  # J/kg
    # S’il faut plus de rigueur, Penman–Monteith introduit la “psychrometric constant” etc.
    # Simplifions:
    g_lambda = 0.0
    # Par exemple, un ratio empirique:
    # g_lambda = ??? -> Cf. doc. On fait un ratio de la forme:
    #   E = (Delta * (T_leaf - T_air)) / (r_total * R_gas * T)
    #   => lambda E = ...
    # => On va donner juste un ordre de grandeur paramétrable:
    g_lambda = 10.0 * (Delta / (r_total+1e-9))  # un coefficient empirique W/m2.K

    # --- T_leaf (1 itération) ---
    T_leaf_lin = T_air + R_n0 / (g_H + g_lambda)

    return T_leaf_lin  # °C

def solve_leaf_temperature_Newton(Plant, Env):
    #T_guess_K = T_air + 273.15
    #T_solution_K = fsolve(func_balance, x0=T_guess_K)[0]
    #return T_solution_K - 273.15
    T_air_C = Env["atmos"]["temperature"]
    T_guess_K = T_air_C + 273.15

    T_leaf_K = newton_leaf_temperature(Plant, Env, T_guess_K, max_iter=2, delta=0.01)
    return T_leaf_K - 273.15  # repasse en °C

def solve_leaf_temperature_fsolve(Plant, Env):
    """
    Trouve la T_f (°C) qui annule leaf_energy_balance_plantroid(...).
    """
    T_air_C = Env["atmos"]["temperature"]
    T_guess_K = T_air_C + 273.15

    def func_balance(T_leaf_K):
        return leaf_energy_balance_plantroid(T_leaf_K, Plant, Env)

    T_solution_K = fsolve(func_balance, x0=T_guess_K, xtol=1e-2)[0]
    return T_solution_K - 273.15

def compute_leaf_temperature(Plant, Env, method):
    """
    Fonction d'interface pour mettre à jour Plant["temperature"]["photo"].
    """
    if method == "Newton":
        T_leaf_eq_C = solve_leaf_temperature_Newton(Plant, Env)
    elif method == "fsolve":
        T_leaf_eq_C = solve_leaf_temperature_fsolve(Plant, Env)
    elif method == "linear":
        T_leaf_eq_C = approximate_leaf_temperature(Plant, Env)
    Plant["temperature"]["photo"] = T_leaf_eq_C
    # Optionnel : stocker dans diag
    if "diag" not in Plant:
        Plant["diag"] = {}
    Plant["diag"]["leaf_temp_equilibrium"] = T_leaf_eq_C

def adjust_leaf_params_angle(
    Plant,
    Env,
    alpha=1.0,
    beta=1.0,
    gamma=1.0,
    steps=3,
    angle_max=np.pi/2,
    method="Newton"
):
    """
    Ajuste la conductance stomatique (Plant["stomatal_conductance"]) ET
    l'angle foliaire (Plant["leaf_angle"]) pour optimiser 3 critères :
      1) T_leaf proche de T_optim
      2) Coût en eau proche de la capacité max
      3) Photosynthèse élevée

    :param alpha, beta, gamma: poids respectifs des trois critères
    :param steps: nombre de points pour chaque axe (conductance, angle)
    :param angle_max: angle maximal (radians) entre la normale de la feuille et les rayons
                     ex. pi/2 => la feuille peut se mettre à la verticale

    Méthode:
    --------
    - On fait une double boucle: 
        stomatal_conductance ∈ [stomatal_conductance_min..1.0]
        leaf_angle ∈ [0..angle_max]
    - Pour chaque (SC, angle), on:
        1) applique
        2) calcule T_leaf, photosynth, cost eau
        3) évalue un score = alpha*fT + beta*fW + gamma*fPhoto
    - On retient (SC, angle) qui maximise le score

    -> On modifie Plant in place.
    """

    # 1) Sauvegarde de l'état initial
    gsmax= Fu.compute_stomatal_conductance_max(Plant)
    original_sc    = Plant["stomatal_conductance"]
    original_angle = Plant.get("leaf_angle", 0.0)


    # Bornes pour la conductance
    c_min = Plant["stomatal_conductance_min"]
    c_max = 1.0  # on suppose 1.0 comme max possible

    best_score = -1e9
    best_sc    = original_sc
    best_angle = original_angle

    # Pas
    dc = (c_max - c_min) / float(steps)
    da = angle_max / float(steps)

    for i in range(steps+1):
        for j in range(steps+1):
            # Valeurs candidates
            sc_candidate    = c_min + i*dc
            angle_candidate = j*da

            # On applique *temporairement* ces valeurs
            Plant["stomatal_conductance"] = sc_candidate
            Plant["leaf_angle"]           = angle_candidate

            # 2) On fait le calcul complet:
            #   a) On convertit conduction -> r_stomatal si c'est ainsi dans le bilan :
            Plant["r_stomatal"] = 1.0 / max(sc_candidate * gsmax, 1e-6)
            #   d) Calculer la T_feuille => solve_leaf_temperature_plantroid(Plant, Env)

            compute_leaf_temperature(Plant, Env, method)
            
            #   b) Calculer la photosynthèse (ex. your function photosynthesis(Plant, Env))
            Fu.photosynthesis(Plant, Env)  
            # => doit mettre à jour Plant["flux_in"]["sugar"], 
            #    Plant["cost"]["transpiration"]["water"] = cost_eau_photo

            #   c) Calculer la transpiration maxi
            Fu.compute_max_transpiration_capacity(Plant, Env)
   
            #   e) Récupérer:
            #  - photosynth = Plant["flux_in"]["sugar"]
            #  - cost_water = Plant["cost"]["transpiration"]["water"] + (cooling if you have it)
            #  - capacity   = Plant["max_transpiration_capacity"]
            #  - T_leaf     = T_leaf_C
            #  - T_opt      = Plant["T_optim"]

            photosynth = Plant["flux_in"]["sugar"]
            cost_water = Plant["cost"]["transpiration"]["water"] 
            capacity   = Plant.get("max_transpiration_capacity", 1e-3)
            T_leaf     = Plant["temperature"]["photo"] 
            T_opt      = Plant.get("T_optim", 25.0)
            '''
            print("with a Gs=", Plant["stomatal_conductance"]," and a leaf angle of :",Plant["leaf_angle"] )
            print("photosynthesis estimate:", Plant["flux_in"]["sugar"])
            print("transpiration estimate:", Plant["cost"]["transpiration"]["water"] )
            print("Max transpiration", capacity )
            print("leaf tempertature",  Plant["temperature"]["photo"]  )
            print("air temp", Env["atmos"]["temperature"])
            '''
            # 3) Calcul des 3 sous-critières
            # (a) fT: T_leaf proche T_opt
            diffT = abs(T_leaf - T_opt)
            fT = 1.0 - min(1.0, diffT / max(1.0, T_opt))  
            # => si T_leaf = T_opt => fT=1, 
            #    si T_leaf s'éloigne fortement => fT tend vers 0

            # (b) fW: cost_water proche capacity
            if capacity <= 0:
                fW = 0.0
            else:
                diffW = abs(cost_water - capacity)
                ratioW = diffW / capacity
                fW = 1.0 - min(1.0, ratioW)
            # => si cost_water ~ capacity => fW ~1
            #    si on dépasse bcp => fW plus faible

            # (c) fPhoto: normaliser la photosynth
            # ex: fPhoto = photosynth / (1 + photosynth)
            fPhoto = photosynth / (1.0 + photosynth) if photosynth>0 else 0.0

            # Score final
            score = alpha*fT + beta*fW + gamma*fPhoto
            #print("gives a score of:", score)
            # MàJ best si amélioration
            if score > best_score:
                best_score = score
                best_sc    = sc_candidate
                best_angle = angle_candidate

    # 4) Après exploration, on applique le meilleur
    Plant["stomatal_conductance"] = best_sc
    Plant["leaf_angle"]           = best_angle
    Plant["r_stomatal"]           = 1.0 / max(best_sc, 1e-6)

    # 5) Recalcule les variables finales sur le "vrai" Plant
    compute_leaf_temperature(Plant, Env, method)
    Fu.photosynthesis(Plant, Env)
    Fu.compute_max_transpiration_capacity(Plant, Env)
    Plant["flux_in"]["water"] = Plant["max_transpiration_capacity"] - Plant["cost"]["transpiration"]["water"]    # Fin
    return  # le Plant est mis à jour in-place
