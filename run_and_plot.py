# run_and_plot.py
import matplotlib.pyplot as plt
import time_loop as Ti
import global_constants as Gl
import copy
import numpy as np
import Plant_def as Pl

def aggregate_day_night(history, points_per_day=24, day_hours=12):
    """
    Agrège l'historique en deux blocs par jour :
      - day_data : moyenne (ou somme) sur les 12 premières heures
      - night_data : moyenne (ou somme) sur les 12 heures suivantes

    :param history: Dictionnaire 'history' avec les listes de variables
    :param points_per_day: 24 si 1 cycle = 1h -> 24 points par jour
    :param day_hours: 12 => on considère les 12 premiers points comme "jour"
    :return: day_data, night_data (deux dictionnaires avec moyennes)
    """
    day_data = {}
    night_data = {}

    # On initialise les clés :
    for key in history.keys():
        day_data[key] = []
        night_data[key] = []

    total_points = len(history["time"])
    # Nombre de jours complets qu’on peut agréger
    num_days = total_points // points_per_day

    for day_idx in range(num_days):
        start = day_idx * points_per_day
        # Intervalle jour
        day_start = start
        day_end   = start + day_hours
        # Intervalle nuit
        night_start = day_end
        night_end   = start + points_per_day

        for key, values in history.items():
            # Récupère les segments correspondants
            chunk_day   = values[day_start:day_end]
            chunk_night = values[night_start:night_end]

            # Moyenne sur la tranche jour
            if len(chunk_day) > 0:
                day_avg = sum(chunk_day) / len(chunk_day)
            else:
                day_avg = 0.0

            # Moyenne sur la tranche nuit
            if len(chunk_night) > 0:
                night_avg = sum(chunk_night) / len(chunk_night)
            else:
                night_avg = 0.0

            day_data[key].append(day_avg)
            night_data[key].append(night_avg)

    # Pour la variable "time", on remplace par un simple [1..num_days]
    # afin de tracer sur l’échelle du nombre de jours.
    day_data["time"]   = list(range(1, num_days + 1))
    night_data["time"] = list(range(1, num_days + 1))

    return day_data, night_data


def simulate_and_plot():
    """
    Exécute la simulation, agrège les données à l'échelle journalière,
    et produit divers graphiques (y compris météo, reserve_used, etc.).
    """
    data, final_Plant, final_env = Ti.run_simulation_collect_data(Gl.max_cycles)
    day_data, night_data = aggregate_day_night(data, points_per_day=24, day_hours=12)

    day_fig, day_axes = plt.subplots(nrows=4, ncols=4, figsize=(65, 35))
    day_fig.suptitle("", fontsize=16)

    # ------------------------------------------------------------------
    # Rangée 0
    # ------------------------------------------------------------------
    day_axes[0,0].plot(day_data["time"], day_data["biomass_total"])
    day_axes[0,0].set_xlabel("Jour")
    day_axes[0,0].set_ylabel("Biomasse totale (g)")
    day_axes[0,0].set_title("Biomasse totale")

    day_axes[0,1].plot(day_data["time"], day_data["biomass_support"], label="support")
    day_axes[0,1].plot(day_data["time"], day_data["biomass_photo"],   label="photo")
    day_axes[0,1].plot(day_data["time"], day_data["biomass_absorp"],  label="absorp")
    day_axes[0,1].set_xlabel("Jour")
    day_axes[0,1].set_ylabel("Biomasse (g)")
    day_axes[0,1].set_title("Biomasse par compartiment")
    day_axes[0,1].legend()

    day_axes[0,2].plot(day_data["time"], day_data["slai"])
    day_axes[0,2].set_xlabel("Jour")
    day_axes[0,2].set_ylabel("SLAI")
    day_axes[0,2].set_title("Surface foliaire (SLAI)")

    day_axes[0,3].plot(day_data["time"], day_data["health_state"])
    day_axes[0,3].set_xlabel("Jour")
    day_axes[0,3].set_ylabel("Santé (0..100)")
    day_axes[0,3].set_title("État de santé")

    # ------------------------------------------------------------------
    # Rangée 1
    # ------------------------------------------------------------------
    day_axes[1,0].plot(day_data["time"], day_data["sugar_photo"], label="sugar_photo")
    day_axes[1,0].set_xlabel("Jour")
    day_axes[1,0].set_ylabel("Flux_in spéciaux (g)")
    day_axes[1,0].set_title("Flux_in après transpiration / photo")
    day_axes[1,0].legend()

    day_axes[1,1].plot(day_data["time"], day_data["reserve_sugar"], label="Sucre")
    day_axes[1,1].plot(day_data["time"], day_data["reserve_water"], label="Eau")
    day_axes[1,1].plot(day_data["time"], day_data["reserve_nutrient"], label="Nutriments")
    day_axes[1,1].set_xlabel("Jour")
    day_axes[1,1].set_ylabel("Réserves (g)")
    day_axes[1,1].set_title("Réserves internes")
    day_axes[1,1].legend()

    day_axes[1,2].plot(day_data["time"], day_data["soil_water"], label="Soil water")
    day_axes[1,2].set_xlabel("Jour")
    day_axes[1,2].set_ylabel("Eau (g)")
    day_axes[1,2].set_title("Eau dans le sol")
    day_axes[1,2].legend()

    day_axes[1,3].plot(day_data["time"], day_data["atmos_temperature"], label="Tair")
    day_axes[1,3].plot(day_data["time"], day_data["leaf_temperature_before"], label="Tbf")
    day_axes[1,3].plot(day_data["time"], day_data["leaf_temperature_after"], label="Taf") 
    day_axes[1,3].set_xlabel("Jour")
    day_axes[1,3].set_ylabel("Température (°C)")
    day_axes[1,3].set_title("Température foliaire")
    day_axes[1,3].legend()

    # ------------------------------------------------------------------
    # Rangée 2 : Températures
    # ------------------------------------------------------------------
    day_axes[2,0].plot(day_data["time"], day_data["stomatal_conductance"])
    day_axes[2,0].set_xlabel("Jour")
    day_axes[2,0].set_ylabel("Conductance (0..1)")
    day_axes[2,0].set_title("Conductance stomatique")

    day_axes[2,1].plot(day_data["time"], day_data["success_extension"], label="Extension")
    day_axes[2,1].plot(day_data["time"], day_data["success_reproduction"], label="Reproduction")
    day_axes[2,1].set_xlabel("Jour")
    day_axes[2,1].set_ylabel("Succès (0..1)")
    day_axes[2,1].set_title("Succès des processus")
    day_axes[2,1].legend()

    day_axes[2,2].plot(day_data["time"], day_data["transpiration_cooling"], label="Cooling")
    day_axes[2,2].plot(day_data["time"], day_data["max_transpiration_capacity"], label="Max capacity")
    day_axes[2,2].set_xlabel("Jour")
    day_axes[2,2].set_ylabel("H2O (g/jour)")
    day_axes[2,2].set_title("Détails Transpiration")
    day_axes[2,2].legend()

    day_axes[2,3].plot(day_data["time"], day_data["raw_sugar_flux"], label="Flux brut (g/s*gFeuille)")
    day_axes[2,3].plot(day_data["time"], day_data["pot_sugar"], label="Pot. (g/s, avant T_lim)")
    day_axes[2,3].set_xlabel("Jour")
    day_axes[2,3].set_ylabel("Valeurs calculées")
    day_axes[2,3].set_title("Détails Photosynthèse")
    day_axes[2,3].legend()

    # ------------------------------------------------------------------
    # Rangée 3 : Météo (lumière, pluie)
    # ------------------------------------------------------------------
    day_axes[3,0].plot(day_data["time"], day_data["atmos_light"], label="Lumière")
    day_axes[3,0].set_xlabel("Jour")
    day_axes[3,0].set_ylabel("Luminosité (W/g?)")
    day_axes[3,0].set_title("Luminosité atmosphérique")
    day_axes[3,0].legend()

    day_axes[3,1].plot(day_data["time"], day_data["adjusted_used_maintenance"], label="Adjusted Maint.")
    day_axes[3,1].plot(day_data["time"], day_data["adjusted_used_extension"], label="Adjusted Ext.")
    day_axes[3,1].plot(day_data["time"], day_data["adjusted_used_reproduction"], label="Adjusted Repr.")
    day_axes[3,1].set_xlabel("Jour")
    day_axes[3,1].set_ylabel("0 ou 1")
    day_axes[3,1].set_title("adjusted_used (bool)")
    day_axes[3,1].legend()

    # Ratios + stress
    day_axes[3,2].plot(day_data["time"], day_data["ratio_support"], label="support")
    day_axes[3,2].plot(day_data["time"], day_data["ratio_photo"], label="photo")
    day_axes[3,2].plot(day_data["time"], day_data["ratio_absorp"], label="absorp")
    day_axes[3,2].plot(day_data["time"], day_data["stress_sugar"], label="stress_sugar", linestyle="--")
    day_axes[3,2].plot(day_data["time"], day_data["stress_water"], label="stress_water", linestyle="--")
    day_axes[3,2].set_xlabel("Jour")
    day_axes[3,2].set_ylabel("Ratios / Stress")
    day_axes[3,2].set_title("Ratios d’allocation & Stress")
    day_axes[3,2].legend()

    # reserve_used & adjusted_used
    day_axes[3,3].plot(day_data["time"], day_data["reserve_used_maintenance"], label="Reserve used Maint.")
    day_axes[3,3].plot(day_data["time"], day_data["reserve_used_extension"], label="Reserve used Ext.")
    day_axes[3,3].plot(day_data["time"], day_data["reserve_used_reproduction"], label="Reserve used Repr.")
    day_axes[3,3].set_xlabel("Jour")
    day_axes[3,3].set_ylabel("0 ou 1")
    day_axes[3,3].set_title("reserve_used (bool)")
    day_axes[3,3].legend()

    day_fig.tight_layout()
    plt.show()

    night_fig, night_axes = plt.subplots(nrows=7, ncols=3, figsize=(15, 35))
    night_fig.suptitle("Résultats de la simulation (agrégation journalière) - Modèle Plantroid", fontsize=16)

    # ------------------------------------------------------------------
    # Rangée 0
    # ------------------------------------------------------------------
    night_axes[0,0].plot(night_data["time"], night_data["biomass_total"])
    night_axes[0,0].set_xlabel("Jour")
    night_axes[0,0].set_ylabel("Biomasse totale (g)")
    night_axes[0,0].set_title("Biomasse totale")

    night_axes[0,1].plot(night_data["time"], night_data["biomass_support"], label="support")
    night_axes[0,1].plot(night_data["time"], night_data["biomass_photo"],   label="photo")
    night_axes[0,1].plot(night_data["time"], night_data["biomass_absorp"],  label="absorp")
    night_axes[0,1].set_xlabel("Jour")
    night_axes[0,1].set_ylabel("Biomasse (g)")
    night_axes[0,1].set_title("Biomasse par compartiment")
    night_axes[0,1].legend()

    night_axes[0,2].plot(night_data["time"], night_data["slai"])
    night_axes[0,2].set_xlabel("Jour")
    night_axes[0,2].set_ylabel("SLAI")
    night_axes[0,2].set_title("Surface foliaire (SLAI)")

    # ------------------------------------------------------------------
    # Rangée 1
    # ------------------------------------------------------------------
    night_axes[1,0].plot(night_data["time"], night_data["health_state"])
    night_axes[1,0].set_xlabel("Jour")
    night_axes[1,0].set_ylabel("Santé (0..100)")
    night_axes[1,0].set_title("État de santé")

    night_axes[1,1].plot(night_data["time"], night_data["sugar_in"], label="sugar_in")
    night_axes[1,1].plot(night_data["time"], night_data["water_in"], label="water_in")
    night_axes[1,1].plot(night_data["time"], night_data["nutrient_in"], label="nutrient_in")
    night_axes[1,1].set_xlabel("Jour")
    night_axes[1,1].set_ylabel("Flux entrants (g)")
    night_axes[1,1].set_title("Flux entrants (g)")
    night_axes[1,1].legend()

    night_axes[1,2].plot(night_data["time"], night_data["water_after_transp"], label="water_after_transp")
    night_axes[1,2].set_xlabel("Jour")
    night_axes[1,2].set_ylabel("Flux sortants (g)")
    night_axes[1,2].set_title("Flux sortants (g)")
    night_axes[1,2].legend()

    # ------------------------------------------------------------------
    # Rangée 2
    # ------------------------------------------------------------------
    night_axes[2,0].plot(night_data["time"], night_data["sugar_photo"], label="sugar_photo")
    night_axes[2,0].set_xlabel("Jour")
    night_axes[2,0].set_ylabel("Flux_in spéciaux (g)")
    night_axes[2,0].set_title("Flux_in après transpiration / photo")
    night_axes[2,0].legend()

    night_axes[2,1].plot(night_data["time"], night_data["reserve_sugar"], label="Sucre")
    night_axes[2,1].plot(night_data["time"], night_data["reserve_water"], label="Eau")
    night_axes[2,1].plot(night_data["time"], night_data["reserve_nutrient"], label="Nutriments")
    night_axes[2,1].set_xlabel("Jour")
    night_axes[2,1].set_ylabel("Réserves (g)")
    night_axes[2,1].set_title("Réserves internes")
    night_axes[2,1].legend()

    night_axes[2,2].plot(night_data["time"], night_data["soil_water"], label="Soil water")
    night_axes[2,2].set_xlabel("Jour")
    night_axes[2,2].set_ylabel("Eau (g)")
    night_axes[2,2].set_title("Eau dans le sol")
    night_axes[2,2].legend()

    # ------------------------------------------------------------------
    # Rangée 3 : Températures
    # ------------------------------------------------------------------
    night_axes[3,0].plot(night_data["time"], night_data["atmos_temperature"], label="Tair")
    night_axes[3,0].plot(night_data["time"], night_data["leaf_temperature_before"], label="Tbf")
    night_axes[3,0].plot(night_data["time"], night_data["leaf_temperature_after"], label="Taf") 
    night_axes[3,0].set_xlabel("Jour")
    night_axes[3,0].set_ylabel("Température (°C)")
    night_axes[3,0].set_title("Température foliaire")
    night_axes[3,0].legend()

    night_axes[3,1].plot(night_data["time"], night_data["stomatal_conductance"])
    night_axes[3,1].set_xlabel("Jour")
    night_axes[3,1].set_ylabel("Conductance (0..1)")
    night_axes[3,1].set_title("Conductance stomatique")

    night_axes[3,2].plot(night_data["time"], night_data["success_extension"], label="Extension")
    night_axes[3,2].plot(night_data["time"], night_data["success_reproduction"], label="Reproduction")
    night_axes[3,2].set_xlabel("Jour")
    night_axes[3,2].set_ylabel("Succès (0..1)")
    night_axes[3,2].set_title("Succès des processus")
    night_axes[3,2].legend()

    # ------------------------------------------------------------------
    # Rangée 4 : Transpiration / photosynthèse
    # ------------------------------------------------------------------
    night_axes[4,0].plot(night_data["time"], night_data["transpiration_cooling"], label="Cooling")
    night_axes[4,0].plot(night_data["time"], night_data["max_transpiration_capacity"], label="Max capacity")
    night_axes[4,0].set_xlabel("Jour")
    night_axes[4,0].set_ylabel("H2O (g/jour)")
    night_axes[4,0].set_title("Détails Transpiration")
    night_axes[4,0].legend()

    night_axes[4,1].plot(night_data["time"], night_data["raw_sugar_flux"], label="Flux brut (g/s*gFeuille)")
    night_axes[4,1].plot(night_data["time"], night_data["pot_sugar"], label="Pot. (g/s, avant T_lim)")
    night_axes[4,1].set_xlabel("Jour")
    night_axes[4,1].set_ylabel("Valeurs calculées")
    night_axes[4,1].set_title("Détails Photosynthèse")
    night_axes[4,1].legend()
    night_axes[4,2].axis("off")

    # ------------------------------------------------------------------
    # Rangée 5 : Météo (lumière, pluie)
    # ------------------------------------------------------------------
    night_axes[5,0].plot(night_data["time"], night_data["atmos_light"], label="Lumière")
    night_axes[5,0].set_xlabel("Jour")
    night_axes[5,0].set_ylabel("Luminosité (W/g?)")
    night_axes[5,0].set_title("Luminosité atmosphérique")
    night_axes[5,0].legend()

    night_axes[5,1].plot(night_data["time"], night_data["rain_event"], label="Pluie (somme/jour)")
    night_axes[5,1].set_xlabel("Jour")
    night_axes[5,1].set_ylabel("Pluie (g eau/jour)")
    night_axes[5,1].set_title("Événement de pluie")
    night_axes[5,1].legend()

    # On laisse 5,2 vide pour l’instant
    night_axes[5,2].axis("off")

    # ------------------------------------------------------------------
    # Rangée 6 : Variables booléennes + ratio + stress
    # ------------------------------------------------------------------
    # reserve_used & adjusted_used
    night_axes[6,0].plot(night_data["time"], night_data["reserve_used_maintenance"], label="Reserve used Maint.")
    night_axes[6,0].plot(night_data["time"], night_data["reserve_used_extension"], label="Reserve used Ext.")
    night_axes[6,0].plot(night_data["time"], night_data["reserve_used_reproduction"], label="Reserve used Repr.")
    night_axes[6,0].set_xlabel("Jour")
    night_axes[6,0].set_ylabel("0 ou 1")
    night_axes[6,0].set_title("reserve_used (bool)")
    night_axes[6,0].legend()

    night_axes[6,1].plot(night_data["time"], night_data["adjusted_used_maintenance"], label="Adjusted Maint.")
    night_axes[6,1].plot(night_data["time"], night_data["adjusted_used_extension"], label="Adjusted Ext.")
    night_axes[6,1].plot(night_data["time"], night_data["adjusted_used_reproduction"], label="Adjusted Repr.")
    night_axes[6,1].set_xlabel("Jour")
    night_axes[6,1].set_ylabel("0 ou 1")
    night_axes[6,1].set_title("adjusted_used (bool)")
    night_axes[6,1].legend()

    # Ratios + stress
    night_axes[6,2].plot(night_data["time"], night_data["ratio_support"], label="support")
    night_axes[6,2].plot(night_data["time"], night_data["ratio_photo"], label="photo")
    night_axes[6,2].plot(night_data["time"], night_data["ratio_absorp"], label="absorp")
    night_axes[6,2].plot(night_data["time"], night_data["stress_sugar"], label="stress_sugar", linestyle="--")
    night_axes[6,2].plot(night_data["time"], night_data["stress_water"], label="stress_water", linestyle="--")
    night_axes[6,2].set_xlabel("Jour")
    night_axes[6,2].set_ylabel("Ratios / Stress")
    night_axes[6,2].set_title("Ratios d’allocation & Stress")
    night_axes[6,2].legend()

    night_fig.tight_layout()
    plt.show()

if __name__ == "__main__":
    simulate_and_plot()
