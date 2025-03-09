#############################
#  GLOBAL INITIALIZATION    #
#############################

# Variables et constantes globales :
time = 0  # temps (unité discrète)
max_cycles = 24*210
DT = 3600 # pas de temps en secondes
delta_adapt = 0.0000015 * DT # vitesse d'evolution des paramètre par DT 0.000001389
N = 24
total_soil_volume = 1e7 # cm³ (hypothèse : 10 m³ de sol total dans l'environnement)

# Conversion lumière -> sucres.
# Voir explication dans le commentaire ci-dessus.
k_root = 100 # cm³ de sol exploré par gramme de racine (à ajuster selon le type de sol)
# Constantes utiles
LATENT_HEAT_VAPORIZATION = 2450   # J par g d'eau (approx. ~ 2450 J/g)
SPECIFIC_HEAT_LEAF       = 2.2    # J / (g·°C), chaleur massique feuilles
RATIO_H2O_C6H12O6        = 0.6    # ratio de H2O utilisé pour formé un sucres
K = 0.1  # W/°C par gFeuille (exemple)

# Catégories de biomasse
biomass_function = ["support", "photo", "absorp"]

# Ressources (toutes en grammes)
resource = ["sugar", "water", "nutrient"]

# Processus physiologiques
physiologic_process = ["transpiration", "maintenance", "extension", "reproduction"]


#######################################
#            FONCTIONS UTILITAIRES    #
#######################################

def add_to_list(vector, value):
    """
    Ajoute 'value' en fin de liste 'vector'
    """
    vector.append(value)


def keep_last_N(vector, keep):
    """
    Conserve seulement les N derniers éléments de la liste 'vector'
    """
    while len(vector) > keep:
        vector.pop(0)
    return vector


def trend_is_negative(value_list):
    """
    Vérifie si la pente de régression linéaire est négative.
    value_list contient des valeurs (0..1).
    """
    n = len(value_list)
    if n < 2:
        return False

    sum_x = sum(range(n))
    sum_y = sum(value_list)
    sum_xy = 0.0
    sum_x2 = 0.0

    for i, y in enumerate(value_list):
        x = i
        sum_xy += x * y
        sum_x2 += x * x

    numerator = (n * sum_xy) - (sum_x * sum_y)
    denominator = (n * sum_x2) - (sum_x * sum_x)

    if denominator == 0:
        return False

    slope = numerator / denominator
    return (slope < 0)

