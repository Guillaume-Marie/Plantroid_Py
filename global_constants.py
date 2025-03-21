# global_constants.py
"""
Global constants and utility functions for the Plantroid model.

All comments and explanations are in English, while variable/function
names remain in French for compatibility with other parts of the project.
"""

#############################
#  GLOBAL INITIALIZATION    #
#############################

# Basic global time parameters
time = 0                # discrete simulation time (in hours)
max_cycles = 24 * 220   # default maximum cycles if needed
DT = 3600               # time step in seconds (1 hour)

# Rate of adaptation for certain parameters in the model
delta_adapt = 0.0000015 * DT
N = 24                  # typical window size for certain rolling calculations

# Water diffusion coefficient (simplified)
D_H2O = 2.5e-5          # m²/s

# Vapor Pressure Deficit approximation
VPD = 11.2

# Characteristic distance for stomatal pore depth (m)
pore_depth = 1e-5

# Physical constants
SIGMA = 5.670374419e-8  # Stefan-Boltzmann constant (W/m².K⁴)
RHO_AIR = 1.225         # air density (kg/m³)
CP_AIR = 1005.0         # specific heat capacity of air (J/kg.K)
LAMBDA_VAP = 2.45e6     # latent heat of vaporization of water (J/kg)
R_GAS = 8.314462618     # universal gas constant (J/mol.K)
M_WATER = 0.01801528    # molar mass of water (kg/mol)

# Parameter for soil exploration by roots
# e.g. 1 g of root can explore ~100 cm³ of soil
k_root = 100
c_coeff = 100

# Additional constants
SPECIFIC_HEAT_LEAF = 2.2        # leaf specific heat, J/(g·°C)
RATIO_H2O_C6H12O6 = 0.6         # ratio of water used per sugar formed
K = 0.1                         # example conduction factor (W/°C per g of leaf)

# Categories of biomass within the plant
biomass_function = ["support", "photo", "absorp"]

# Resources used by the plant (in grams)
resource = ["sugar", "water", "nutrient"]

# Physiological processes handled in the model
physiologic_process = ["transpiration", "maintenance", "extension", "reproduction"]


#######################################
#            UTILITY FUNCTIONS        #
#######################################

def add_to_list(vector, value):
    """
    Append 'value' to the list 'vector'.
    """
    vector.append(value)


def keep_last_N(vector, keep):
    """
    Keep only the last 'keep' elements in the list 'vector'.
    """
    while len(vector) > keep:
        vector.pop(0)
    return vector


def trend_is_negative(value_list):
    """
    Check if the linear regression slope of 'value_list' is negative.
    'value_list' is expected to contain values (0..1).
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
    return slope < 0
