import functions as Fu
import random
import math

#Environnement initial
Environment = {
    "soil":    {"water": 100000.0, "nutrient": 5000000.0},
    "litter":  {"absorp": 20000.0, "photo": 500.0, "support": 500.0},
    "atmos":   {"Co2": 1000.0, "light": 1000.0, "water": 100.0, "temperature": 25.0}
}


#######################################
#    FONCTIONS SUR L'ENVIRONNEMENT    #
#######################################

def update_environment(time, Env):
    """
    Met à jour l'environnement en fonction de l'heure (en secondes).
    Exemple:
      - On fait varier la lumière de façon sinusoïdale entre 0 et un max.
      - On fait varier la température entre 15°C la nuit et 25°C le jour.
    """

    # cycle jour/nuit sur 24h
    day_length = 12   # 12h en secondes
    t_in_day   = time % 24

    # Lumière : sinusoïde simplifiée entre 0 et 1, qu’on multiplie par un max (ex. 800 W/g)
    # On suppose qu'il y a 12h de jour, 12h de nuit
    mod=random.random()
    if t_in_day < day_length:
        # fraction du jour
        frac_day = t_in_day / float(day_length)
        # sinus qui démarre à 0, culmine au milieu du jour
        Env["atmos"]["light"] = max(600.0,mod*1500.0) * max(0.0, math.sin(math.pi * frac_day))
        # Température : passe de 15°C le matin à 25°C en milieu de journée
        Env["atmos"]["temperature"] = 15.0 + (mod*15.0) * frac_day
    else:
        Env["atmos"]["light"] = 0.0
        # la nuit, on redescend de 25°C à 15°C
        frac_night = (t_in_day - day_length) / float(day_length)
        Env["atmos"]["temperature"] = 15.0 - mod*8.0 * frac_night

    """
    Met à jour l'environnement en fonction de l'heure (en cycles).
    """
    # ... (pas de changement pour la lumière/ température)...

    # Gérer la pluie comme un événement explicite
    Env["rain_event"] = 0.0
    if time % 100 == 0:
        Env["soil"]["water"] += 8000.0
        Env["rain_event"] = 8000.0

def co2_availability(time, Env):
    """
    Fluctuation de CO2 autour de ~400 ppm
    """
    base_co2 = 400.0
    fluctuation = 10.0 * math.sin(time / 10.0)
    Env["atmos"]["Co2"] = base_co2 + fluctuation


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
