#############################
#  GLOBAL INITIALIZATION    #
#############################

# Variables et constantes globales :
time = 0  # temps (unité discrète)
max_cycles = 24*365
DT = 3600 # pas de temps en secondes
delta_adapt = 0.01/72
N = 10
dying_state_thr = 1000

# Conversion lumière -> sucres.
# Voir explication dans le commentaire ci-dessus.
conversion_factor = 0.000001  # J/s ---> gC6H12O6/s
base_WUE = 0.006 # gsugar/gH2O

# Constantes utiles
LATENT_HEAT_VAPORIZATION = 2450   # J par g d'eau (approx. ~ 2450 J/g)
SPECIFIC_HEAT_LEAF       = 2.2    # J / (g·°C), chaleur massique feuilles
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

