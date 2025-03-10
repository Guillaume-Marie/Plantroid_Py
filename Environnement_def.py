import functions as Fu
import random
import math

#Environnement initial
Environment = {
    "soil":    {"water": 2000000.0, "nutrient": 5000000.0},
    "litter":  {"absorp": 20000.0, "photo": 500.0, "support": 500.0},
    "atmos":   {"Co2": 1000.0, "light": 1000.0, "water": 100.0, "temperature": 25.0},
    # -------------------------
    # 1) Paramètres de base
    # -------------------------
    "day_temp_amplitude":   5.0,    # amplitude (°C) de la variation jour/nuit
    "seasonal_temp_offset": 10.0,   # amplitude (°C) de la variation saisonnière
    "base_temp":            10.0,  # température moyenne annuelle (°C)

    "base_light":           800.0, # luminosité max (p. ex. W/m²) en plein été
    "seasonal_light_var":   0.5,    # en hiver, la luminosité max ~ base_light * (1 - seasonal_light_var)

    "precipitation_base":   3.0,    # mm (ou g eau/m²) par jour, en moyenne
    "seasonal_rain_var":    0.5,    # +/- 50% selon la saison
    "random_factor":        0.3    # intensité du facteur aléatoire (30%)
}

#######################################
#    FONCTIONS SUR L'ENVIRONNEMENT    #
#######################################
def update_environment(time, Env):
    """
    Met à jour l'environnement en fonction de l'heure (time), en intégrant :
      - Un cycle annuel de 365 jours (saisons).
      - Un cycle journalier (jour/nuit).
      - Une variabilité aléatoire (météo).
    Hypothèses simplifiées pour un climat tempéré d'Europe centrale.
    
    Paramètres ajustables :
    -----------------------
    - day_temp_amplitude  : amplitude moyenne de température jour/nuit (ex. +/- 5°C)
    - seasonal_temp_offset: amplitude saisonnière de la température moyenne (ex. +/- 10°C)
    - base_temp           : température moyenne annuelle (ex. 10°C)
    - base_light          : luminosité maximale (W/m² ou un équivalent) en été, par beau temps
    - seasonal_light_var  : variation saisonnière de la luminosité (rapport entre hiver et été)
    - precipitation_base  : précipitation moyenne (ex. 3 mm par jour)
    - seasonal_rain_var   : variation saisonnière des précipitations (ex. +50% au printemps)
    - random_factor       : facteur d’aléa météo pour pluie ou luminosité
    """


    # -------------------------
    # 2) Conversion du temps
    # -------------------------
    # On suppose que 'time' est un compteur d’heures.
    # -> On calcule le jour absolu et l’heure dans la journée.
    day_index  = time // 24             # indice du jour
    hour_in_day = time % 24             # heure locale dans la journée
    day_of_year = day_index % 365       # position dans l’année (0..364)

    # -------------------------
    # 3) Cycle saisonnier
    # -------------------------
    # On fait varier la température moyenne T_season en fonction d’un sinus,
    # avec un pic ~ jour 173 (22 juin dans l’hémisphère nord).
    # Formule indicative :
    #  T_season = base_temp + seasonal_temp_offset * sin( 2π*(day_of_year - 81)/365 )
    # (Le décalage de ~81 jours rapproche le pic de la fin juin.)
    seasonal_angle = 2.0 * math.pi * (day_of_year - 81) / 365.0
    T_season = Environment["base_temp"] + Environment["seasonal_temp_offset"] * math.sin(seasonal_angle)

    # De même pour la luminosité maximale journalière 
    # (on suppose plus de lumière l’été et moins l’hiver).
    # Par exemple, en hiver : luminosité max = base_light * (1 - seasonal_light_var)
    # en été : ~ base_light * (1 + seasonal_light_var)
    light_season_factor = 1.0 + Environment["seasonal_light_var"] * math.sin(seasonal_angle)
    # coefficient multiplicateur de la lumière journalière
    # oscillant entre (1 - seasonal_light_var) et (1 + seasonal_light_var).
    # On clamp si besoin pour éviter d’être < 0.
    if light_season_factor < 0:
        light_season_factor = 0

    # Même logique pour la pluie : 
    # précipitations plus fortes au printemps/automne, plus faibles en été/hiver
    # (ça dépend des régions, on adapte ci-dessous un sinus simple).
    precipitation_season_factor = 1.0 + Environment["seasonal_rain_var"] * math.sin(seasonal_angle)

    # -------------------------
    # 4) Cycle journalier
    # -------------------------
    # On fait une variation sinusoïdale de la température dans la journée
    # autour de T_season : T_jour = T_season + day_temp_amplitude*sin(π * (heure/12 - 0.5))
    # De sorte que la température est minimale vers 5-6h du matin et max vers 14-15h.
    
    # (Pour rester simple, on prend un pic au milieu de la journée de 12h – c’est perfectible)
    daily_angle = math.pi * (hour_in_day / 12.0 - 0.5)
    T_daily = T_season +  Environment["day_temp_amplitude"] * math.sin(daily_angle)

    # Lumière : on considère 12-16h de jour l’été, 8-10h de jour l’hiver, etc.
    # Pour simplifier, on fait :
    #    - Jour : 6h -> 20h -> sin pour le lever/coucher
    #    - Nuit : 20h -> 6h (luminosité = 0)
    # Ex.: on modélise la luminosité instantanée par un sin(π*(h-6)/14) si 6 <= h < 20
    # On la multiplie par la factor saisonnier + un aléa.
    if 6 <= hour_in_day < 20:
        frac_daytime = (hour_in_day - 6) / 14.0  # de 0..1 entre 6h et 20h
        light_day =  Environment["base_light"] * light_season_factor * max(0.0, math.sin(math.pi * frac_daytime))
    else:
        light_day = 0.0

    # -------------------------
    # 5) Pluie
    # -------------------------
    # On distribue la pluie moyenne journalière (en g eau par m² ou en mm)
    # de manière aléatoire. Par exemple, on décide à chaque jour s’il pleut 
    # et combien. On peut le faire une seule fois par jour_index ou
    # l’étaler aléatoirement sur la journée. 
    # Exemple minimaliste : événement de pluie aléatoire à 6h du matin.
    
    if hour_in_day == 6:
        # pluie journalière moyenne
        daily_rain_mean =  Environment["precipitation_base"] * precipitation_season_factor
        # aléa multiplicatif
        daily_rain = daily_rain_mean * (1.0 +  Environment["random_factor"] * (2.0*random.random() - 1.0))
        # on ajoute la pluie dans le sol (grand réservoir) 
        # Conversion mm -> g eau... c’est arbitraire, on peut rester cohérent
        Env["soil"]["water"] += daily_rain * 1000.0  # x1000 si 1 mm = 1 L/m² ...
        Env["rain_event"] = daily_rain * 1000.0
    else:
        # Pas de pluie à cette heure
        Env["rain_event"] = 0.0

    # -------------------------
    # 6) Ajout d’un facteur aléatoire
    # -------------------------
    # On peut ajouter un bruit sur la température, la lumière...
    rand_temp = 1.0 + Environment["random_factor"] * (2.0*random.random() - 1.0)
    rand_light = 1.0 + 0.2 * Environment["random_factor"] * (2.0*random.random() - 1.0)  # plus faible
    T_final = T_daily * rand_temp
    light_final = light_day * rand_light

    # -------------------------
    # 7) Mise à jour de Env
    # -------------------------
    Env["atmos"]["temperature"] = T_final
    Env["atmos"]["light"]       = max(0.0, light_final)  # évite toute valeur négative
    # On garde la logique existante pour le CO2 :
    co2_availability(time, Env)


def co2_availability(time, Env):
    """
    Fluctuation de CO2 autour de ~400 ppm
    """
    base_co2 = 400.0
    fluctuation = 10.0 * math.sin(time / 10.0)
    Env["atmos"]["Co2"] = base_co2 + fluctuation

def calc_daily_photoperiod(day_of_year):
    """
    Calcule la durée du jour (photopériode) en heures pour un 'day_of_year' (0..364)
    à l'aide d'une variation sinusoïdale simple.
    
    Hypothèses :
    ------------
    - Amplitude d'environ +/- 4 heures autour de 12h.
      => la longueur du jour varie approximativement de 8h (en plein hiver) à 16h (en été).
    - Pic de la sinusoïde autour du jour 173 (22 juin Hémisphère Nord).
      => On décale le sinus de ~81 jours pour aligner le maximum sur fin juin.
    - On borne la valeur obtenue dans l’intervalle [0..24], pour éviter les anomalies.

    Paramètres :
    ------------
    day_of_year : int
        Numéro du jour dans l'année, entre 0 et 364 (ex. 0 = 1er janvier).

    Retour :
    --------
    float
        Nombre d'heures de lumière pour ce jour (photopériode).
    """
    # Position saisonnière (en radians).
    seasonal_angle = 2.0 * math.pi * (day_of_year - 81) / 365.0

    # Base : 12h de lumière de moyenne annuelle
    base_hours = 12.0

    # Amplitude : +/- 4h autour de 12, ici on ajuste selon le climat/latitude visée
    amplitude = 4.0  

    # Photopériode théorique
    day_length = base_hours + amplitude * math.sin(seasonal_angle)

    # Pour éviter d’avoir moins de 0 ou plus de 24
    day_length = max(0.0, min(24.0, day_length))
    return day_length

def environment_hazards(Plant, Env):
    """
    Événements aléatoires : vents, insectes, champignons.
    """
    # Dommages causés par le vent
    wind_prob = 0.01
    if random.random() < wind_prob:
        damage_factor_photo = 0.001 * Plant["slai"]
        damage_factor_support = 0.001 * ((100 - Plant["health_state"]) / 100.0)
        Fu.destroy_biomass(Plant, Env, "photo", damage_factor=damage_factor_photo)
        Fu.destroy_biomass(Plant, Env, "support", damage_factor=damage_factor_support)

    # Dommages causés par insectes / champignons
    insect_prob = 0.01
    if random.random() < insect_prob:
        damage_factor_photo = 0.001 * Plant["slai"] * ((100 - Plant["health_state"]) / 100.0)
        damage_factor_absorp = 0.001 * ((100 - Plant["health_state"]) / 100.0)
        Fu.destroy_biomass(Plant, Env, "absorp", damage_factor=damage_factor_absorp)
        Fu.destroy_biomass(Plant, Env, "photo", damage_factor=damage_factor_photo)
