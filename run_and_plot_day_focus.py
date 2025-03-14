# run_and_plot_day_focus.py

import matplotlib.pyplot as plt
import time_loop as Ti
import global_constants as Gl
import Plant_def as Pl
import history_def as Hi

def simulate_entire_period(species_name="ble", total_days=365):
    """
    Simule une période de 'total_days' jours (1 jour = 24 cycles = 24 heures).
    Renvoie l'historique complet, ainsi que l'état final de la plante et de l'environnement.
    """
    # 1) Réinitialise l'historique global pour partir d'une base propre
    for k in Hi.history:
        Hi.history[k].clear()

    # 2) Initialise l'espèce
    Pl.set_plant_species(Pl.Plant, species_name, Pl.species_db)

    # 3) Lance la simulation pour total_days * 24 cycles
    max_cycles = total_days * 24
    data, final_plant, final_env = Ti.run_simulation_collect_data(max_cycles)

    return data, final_plant, final_env

def extract_day_data(data, day_of_interest):
    """
    Extrait les données correspondant uniquement au 'day_of_interest' (entier)
    dans l'historique complet.

    day_of_interest : numéro de jour (0..total_days-1)
    Par exemple, day_of_interest=120 => 120e jour depuis le début.
    """
    start_hour = day_of_interest * 24
    end_hour   = start_hour + 24

    # Indices pour lesquels time est dans [start_hour, end_hour)
    indices = [i for i, t in enumerate(data["time"]) if start_hour <= t < end_hour]

    # Construire un dictionnaire "day_data" similaire à l'historique original,
    # mais limité aux 24 heures de la journée sélectionnée.
    day_data = {}
    for key, values in data.items():
        day_data[key] = [values[i] for i in indices]

    return day_data

def plot_day_data(day_data):
    """
    Trace les courbes heure par heure pour la journée donnée.
    Variables affichées :
      - Flux de photosynthèse (sugar_photo)
      - Conductance stomatique (stomatal_conductance)
      - Transpiration (water_after_transp)
      - Température foliaire vs Température de l'air
      - Flux brut et flux après limitation T (raw_sugar_flux, pot_sugar)
      - Transpiration de refroidissement (transpiration_cooling)
      - Coût en eau de la transpiration (cost_transpiration_water)
      - Coefficient d'absorption lumineux (light_absorption_coeff)
    """
    # Sur l'axe des x : on considère l'heure locale de [0..23]
    if len(day_data["time"]) == 0:
        print("Aucune donnée pour ce jour (vérifier day_of_interest).")
        return

    # On crée un vecteur x = heure relative (0..23)
    start_t = day_data["time"][0]
    x = [t - start_t for t in day_data["time"]]

    # Récupération des variables d'intérêt
    stomatal_cond     = day_data["stomatal_conductance"]       # eau absorbée après transpiration
    leaf_temp         = day_data["leaf_temperature_after"]
    air_temp          = day_data["atmos_temperature"]
    raw_sugar_flux    = day_data["raw_sugar_flux"]            # flux brut (avant limitation T)
    pot_sugar         = day_data["pot_sugar"]                 # flux après limitation T
    cost_trans_water  = day_data["cost_transpiration_water"]   # Coût en eau du process transpiration

    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(12, 16))
    fig.suptitle("Focus sur le jour choisi (Heure par heure)", fontsize=16)

    # Subplot (1) : Flux de photosynthèse
    #axes[0, 0].plot(x, sugar_flux, label="Flux de photosynthèse (sugar_photo)")
    axes[0, 0].set_xlabel("Heure")
    axes[0, 0].set_ylabel("g sucre / heure")
    axes[0, 0].set_title("Photosynthèse")
    axes[0, 0].legend()

    # Subplot (2) : Conductance stomatique
    axes[0, 1].plot(x, stomatal_cond, label="Conductance stomatique")
    axes[0, 1].set_xlabel("Heure")
    axes[0, 1].set_ylabel("Conductance (0..1)")
    axes[0, 1].set_title("Conductance Stomatique")
    axes[0, 1].legend()


    # Subplot (4) : Température foliaire vs air
    axes[1, 1].plot(x, leaf_temp, label="T_foliaire")
    axes[1, 1].plot(x, air_temp,  label="T_air")
    axes[1, 1].set_xlabel("Heure")
    axes[1, 1].set_ylabel("Température (°C)")
    axes[1, 1].set_title("Température Feuille vs Air")
    axes[1, 1].legend()

    # Subplot (5) : Flux brut vs flux après limitation T
    axes[2, 0].plot(x, raw_sugar_flux, label="raw_sugar_flux (avant T_lim)")
    axes[2, 0].plot(x, pot_sugar,      label="pot_sugar (après T_lim)")
    axes[2, 0].set_xlabel("Heure")
    axes[2, 0].set_ylabel("gC6H12O6 / s*gFeuille")
    axes[2, 0].set_title("Détails Photosynthèse")
    axes[2, 0].legend()


    axes[2,1].plot(x, day_data["biomass_support"], label="Support")
    axes[2,1].plot(x, day_data["biomass_photo"],   label="Photo")
    axes[2,1].plot(x, day_data["biomass_absorp"],  label="Absorp")
    axes[2,1].plot(x, day_data["biomass_repro"],   label="Repro")
    axes[2,1].set_xlabel("Jour")
    axes[2,1].set_ylabel("Biomasse (g)")
    axes[2,1].set_title("Compartiments vivants")
    axes[2,1].legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # 1) On simule par exemple 1 an (365 jours) pour l'espèce 'ble'
    data_year, final_plant, final_env = simulate_entire_period(species_name="ble", total_days=365)

    # 2) On choisit un jour, par exemple le 120e jour
    day_of_interest = 175  # (0 => premier jour; 120 => 121e jour depuis le début)

    # 3) On extrait l'historique de ce jour uniquement
    day_data = extract_day_data(data_year, day_of_interest)

    # 4) On trace les variables heure par heure pour ce jour
    plot_day_data(day_data)
