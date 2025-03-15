# run_and_plot.py
import matplotlib.pyplot as plt
import time_loop as Ti
import global_constants as Gl
import Plant_def as Pl

def aggregate_day_night(history, threshold_light=1.0):
    """
    Agrège l'historique en deux blocs (jour/nuit) pour chaque journée,
    en se basant sur la luminosité atmosphérique.
    
    :param history: Dictionnaire avec les listes de variables 
                    (incluant "time" et "atmos_light", etc.)
    :param threshold_light: Valeur de luminosité au-dessus de laquelle 
                            on considère qu'il fait jour (par exemple 1.0)
    :return: day_data, night_data 
         - day_data["time"] = [1, 2, 3, ...]
         - day_data["biomass_total"] = [moyenne du jour 1, ...]
         - etc.
    """

    # 1) Prépare deux structures identiques à l’historique 
    #    pour stocker les agrégats jour/nuit.
    day_data = {}
    night_data = {}

    # Si l’historique est vide, on renvoie directement deux dict vides
    total_points = len(history["time"])
    if total_points == 0:
        return day_data, night_data

    # 2) Détermine le nombre total de jours simulés
    #    Sachant que time[i] est en heures simulées
    max_time = max(history["time"])
    total_days = (max_time // 24) + 1  # ex. si max_time=47 => total_days=2

    # 3) Initialise pour chaque clé de l’history, 
    #    une liste de longueur = total_days, dans laquelle on accumule.
    #    On va d’abord accumuler des sommes, puis on divisera par le nb de points.
    for key in history:
        # On crée des listes vides ou à 0 pour chaque jour
        day_data[key] = [0.0] * total_days
        night_data[key] = [0.0] * total_days

    # Compteurs jour/nuit (combien d’heures dans le jour / nuit)
    day_counts = [0] * total_days
    night_counts = [0] * total_days

    # 4) Boucle sur tous les points
    for i in range(total_points):
        t = history["time"][i]
        # jour_index = (ex. t=0..23 => jour_index=0, t=24..47 => jour_index=1)
        day_index = t // 24

        # Vérifie si c’est “jour” ou “nuit”
        # On utilise la luminosité AtmosLight
        atm_light = history["atmos_light"][i]
        is_day = (atm_light > threshold_light)

        # Ajoute la valeur de chaque variable dans la liste correspondante
        for key, values in history.items():
            val = values[i]
            if is_day:
                day_data[key][day_index] += val
            else:
                night_data[key][day_index] += val

        # On incrémente le compteur
        if is_day:
            day_counts[day_index] += 1
        else:
            night_counts[day_index] += 1

    # 5) Moyennage final
    #    Pour chaque jour, on divise la somme par le nombre de points journaliers/nuit
    for key in history:
        for d in range(total_days):
            if day_counts[d] > 0:
                day_data[key][d] /= day_counts[d]
            if night_counts[d] > 0:
                night_data[key][d] /= night_counts[d]

    # 6) On remplace la liste time par une échelle de jours [1..total_days]
    day_data["time"] = list(range(1, total_days + 1))
    night_data["time"] = list(range(1, total_days + 1))

    return day_data, night_data


def simulate_and_plot(species_name):
    """
    Exécute la simulation, agrège les données à l'échelle journalière,
    et produit divers graphiques (y compris météo, reserve_used, etc.).
    """
    Pl.set_plant_species(Pl.Plant, species_name, Pl.species_db)

    data, final_Plant, final_env = Ti.run_simulation_collect_data(Gl.max_cycles)
    day_data, night_data = aggregate_day_night(data)

    day_fig, day_axes = plt.subplots(nrows=5, ncols=4, figsize=(65, 35))
    day_fig.suptitle("", fontsize=16)

    # ------------------------------------------------------------------
    # Rangée 0
    # ------------------------------------------------------------------
    day_axes[0,0].plot(day_data["time"], day_data["biomass_total"], label="Biomasse")
    day_axes[0,0].plot(day_data["time"], day_data["biomass_necromass"], label="Nécromasse")
    day_axes[0,0].set_xlabel("Jour")
    day_axes[0,0].set_ylabel("Biomasse (g)")
    day_axes[0,0].set_title("Évolution : vivante vs nécromasse")
    day_axes[0,0].legend()

    day_axes[0,1].plot(day_data["time"], day_data["biomass_support"], label="Support")
    day_axes[0,1].plot(day_data["time"], day_data["biomass_photo"],   label="Photo")
    day_axes[0,1].plot(day_data["time"], day_data["biomass_absorp"],  label="Absorp")
    day_axes[0,1].plot(day_data["time"], day_data["biomass_repro"],   label="Repro")
    day_axes[0,1].set_xlabel("Jour")
    day_axes[0,1].set_ylabel("Biomasse (g)")
    day_axes[0,1].set_title("Compartiments vivants")
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

    day_axes[1,1].plot(day_data["time"], day_data["reserve_sugar"], label="Sucre")
    day_axes[1,1].plot(day_data["time"], day_data["reserve_water"], label="Eau")
    day_axes[1,1].set_xlabel("Jour")
    day_axes[1,1].set_ylabel("Réserves (g)")
    day_axes[1,1].set_title("Réserves internes")
    day_axes[1,1].legend()

    day_axes[1,2].plot(day_data["time"], day_data["reserve_nutrient"], label="Nutriments")
    day_axes[1,2].set_xlabel("Jour")
    day_axes[1,2].set_ylabel("Réserves (g)")
    day_axes[1,2].set_title("Réserves internes")
    day_axes[1,2].legend()

    day_axes[1,3].plot(day_data["time"], day_data["atmos_temperature"], label="Tair")
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

    # reserve_used & adjusted_used
    day_axes[2,1].plot(day_data["time"], day_data["reserve_used_maintenance"], label="Maint.")
    day_axes[2,1].plot(day_data["time"], day_data["reserve_used_extension"], label="Ext.")
    day_axes[2,1].plot(day_data["time"], day_data["reserve_used_reproduction"], label="Repr.")
    day_axes[2,1].plot(day_data["time"], day_data["reserve_used_transpiration"], label="Transp.")  
    day_axes[2,1].set_xlabel("Jour")
    day_axes[2,1].set_ylabel("0 ou 1")
    day_axes[2,1].set_title("reserve_used (bool)")
    day_axes[2,1].legend()

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

    day_axes[3,1].plot(day_data["time"], day_data["adjusted_used_maintenance"], label="Maint.")
    day_axes[3,1].plot(day_data["time"], day_data["adjusted_used_extension"], label="Ext.")
    day_axes[3,1].plot(day_data["time"], day_data["adjusted_used_reproduction"], label="Repr.")
    day_axes[3,1].plot(day_data["time"], day_data["adjusted_used_transpiration"], label="Transp.")   
    day_axes[3,1].set_xlabel("Jour")
    day_axes[3,1].set_ylabel("0 ou 1")
    day_axes[3,1].set_title("adjusted_used (bool)")
    day_axes[3,1].legend()

    # Ratios + stress
    day_axes[3,2].plot(day_data["time"], day_data["ratio_support"], label="support")
    day_axes[3,2].plot(day_data["time"], day_data["ratio_photo"], label="photo")
    day_axes[3,2].plot(day_data["time"], day_data["ratio_absorp"], label="absorp")
    day_axes[3,2].plot(day_data["time"], day_data["ratio_repro"], label="repro")
    day_axes[3,2].set_xlabel("Jour")
    day_axes[3,2].set_ylabel("Ratios / Stress")
    day_axes[3,2].set_title("Ratios d’allocation & Stress")
    day_axes[3,2].legend()

    day_axes[3,3].plot(day_data["time"], day_data["success_extension"], label="Extension")
    day_axes[3,3].plot(day_data["time"], day_data["success_reproduction"], label="Reproduction")
    day_axes[3,3].set_xlabel("Jour")
    day_axes[3,3].set_ylabel("Succès (0..1)")
    day_axes[3,3].set_title("Succès des processus")
    day_axes[3,3].legend()


    ax = day_axes[4, 0]
    x = day_data["time"]      
    #ax.plot(x, day_data["cost_transpiration_water"], label="Eau")  
    ax.set_xlabel("Jour")
    ax.set_ylabel("Coût (g)")
    ax.set_title(f"Processus transpiration")
    ax.legend()

    ax = day_axes[4, 1]
    x = day_data["time"]      
    ax.plot(x, day_data["cost_maintenance_sugar"], label="Sucre")       
    ax.set_xlabel("Jour")
    ax.set_ylabel("Coût (g)")
    ax.set_title(f"Processus maintenance")
    ax.legend()

    ax = day_axes[4, 2]
    x = day_data["time"]      
    ax.plot(x, day_data["cost_extension_sugar"], label="Sucre")
    ax.plot(x, day_data["cost_extension_water"], label="Eau")
    ax.plot(x, day_data["cost_extension_nutrient"], label="Nutriments")       
    ax.set_xlabel("Jour")
    ax.set_ylabel("Coût (g)")
    ax.set_title(f"Processus extension")
    ax.legend()

    ax = day_axes[4, 3]
    x = day_data["time"]      
    ax.plot(x, day_data["cost_reproduction_sugar"], label="Sucre")
    ax.plot(x, day_data["cost_reproduction_water"], label="Eau")
    ax.plot(x, day_data["cost_reproduction_nutrient"], label="Nutriments")       
    ax.set_xlabel("Jour")
    ax.set_ylabel("Coût (g)")
    ax.set_title(f"Processus reproduction")
    ax.legend()


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


    # ------------------------------------------------------------------
    # Rangée 2
    # ------------------------------------------------------------------
    #night_axes[2,0].plot(night_data["time"], night_data["sugar_photo"], label="sugar_photo")
    night_axes[2,0].set_xlabel("Jour")
    night_axes[2,0].set_ylabel("Flux_in spéciaux (g)")
    night_axes[2,0].set_title("Flux_in après transpiration / photo")
    night_axes[2,0].legend()

    night_axes[2,1].plot(night_data["time"], night_data["reserve_sugar"], label="Sucre")
    night_axes[2,1].plot(night_data["time"], night_data["reserve_water"], label="Eau")
    night_axes[2,1].set_xlabel("Jour")
    night_axes[2,1].set_ylabel("Réserves (g)")
    night_axes[2,1].set_title("Réserves internes")
    night_axes[2,1].legend()

    night_axes[2,2].plot(night_data["time"], night_data["reserve_nutrient"], label="Nutriments")
    night_axes[2,2].set_xlabel("Jour")
    night_axes[2,2].set_ylabel("Réserves (g)")
    night_axes[2,2].set_title("Réserves internes")
    night_axes[2,2].legend()
    # ------------------------------------------------------------------
    # Rangée 3 : Températures
    # ------------------------------------------------------------------
    night_axes[3,0].plot(night_data["time"], night_data["atmos_temperature"], label="Tair")
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
    night_axes[4,0].plot(night_data["time"], night_data["max_transpiration_capacity"], label="Max capacity")
    night_axes[4,0].set_xlabel("Jour")
    night_axes[4,0].set_ylabel("H2O (g/jour)")
    night_axes[4,0].set_title("Détails Transpiration")
    night_axes[4,0].legend()

    night_axes[4,1].plot(night_data["time"], night_data["raw_sugar_flux"], label="Flux brut")
    night_axes[4,1].plot(night_data["time"], night_data["pot_sugar"], label="Net after g/s, T_lim")
    night_axes[4,1].set_xlabel("Jour")
    night_axes[4,1].set_ylabel("gC6H12O6/gleaf/s")
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
    #plt.show()

if __name__ == "__main__":
    simulate_and_plot("ble")
