# run_and_plot.py
import matplotlib.pyplot as plt
import time_loop as Ti
import global_constants as Gl
import Plant_def as Pl

def aggregate_day_night(history, threshold_light=1.0):
    """
    Agrège l'historique en deux blocs (jour/nuit) pour chaque journée,
    en se basant sur la luminosité atmosphérique.
    """
    day_data = {}
    night_data = {}

    total_points = len(history["time"])
    if total_points == 0:
        return day_data, night_data

    max_time = max(history["time"])
    total_days = (max_time // 24) + 1

    for key in history:
        day_data[key] = [0.0] * total_days
        night_data[key] = [0.0] * total_days

    day_counts = [0] * total_days
    night_counts = [0] * total_days

    for i in range(total_points):
        t = history["time"][i]
        day_index = t // 24
        atm_light = history["atmos_light"][i]
        is_day = (atm_light > threshold_light)

        for key, values in history.items():
            val = values[i]
            if is_day:
                day_data[key][day_index] += val
            else:
                night_data[key][day_index] += val

        if is_day:
            day_counts[day_index] += 1
        else:
            night_counts[day_index] += 1

    for key in history:
        for d in range(total_days):
            if day_counts[d] > 0:
                day_data[key][d] /= day_counts[d]
            if night_counts[d] > 0:
                night_data[key][d] /= night_counts[d]

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

    day_fig, day_axes = plt.subplots(nrows=5, ncols=4, figsize=(65, 35), 
                        sharex='col', gridspec_kw=dict(hspace=0.3,
                                                       wspace=0.2,
                                                       top=0.96,
                                                       right=0.96,
                                                       left=0.03,
                                                       bottom=0.05))
    day_fig.suptitle("", fontsize=16)

    # ------------------------------------------------------------------
    # Ligne 0
    # ------------------------------------------------------------------
    # Biomasse => vert, Nécromasse => marron
    day_axes[0,0].plot(day_data["time"], day_data["biomass_total"], label="Biomasse", color="green")
    day_axes[0,0].plot(day_data["time"], day_data["biomass_necromass"], label="Nécromasse", color="brown")
    day_axes[0,0].plot(day_data["time"], day_data["max_biomass"], label="Theoric", color="black", linestyle="dotted")
    day_axes[0,0].set_xlabel("Jour")
    day_axes[0,0].set_ylabel("Biomasse (g)")
    day_axes[0,0].set_title("Évolution : vivante vs nécromasse")
    day_axes[0,0].legend()

    # Compartiments vivants : support/photo/absorp en vert, repro en violet
    day_axes[0,1].plot(day_data["time"], day_data["biomass_support"], label="Support", color="brown")
    day_axes[0,1].plot(day_data["time"], day_data["biomass_photo"],   label="Photo", color="green")
    day_axes[0,1].plot(day_data["time"], day_data["biomass_absorp"],  label="Absorp", color="blue")
    day_axes[0,1].plot(day_data["time"], day_data["biomass_repro"],   label="Repro", color="violet")
    day_axes[0,1].set_xlabel("Jour")
    day_axes[0,1].set_ylabel("Biomasse (g)")
    day_axes[0,1].set_title("Compartiments vivants")
    day_axes[0,1].legend()

    day_axes[0,2].plot(day_data["time"], day_data["soil_water"], color="blue")  # Pas de code couleur imposé
    day_axes[0,2].set_xlabel("Jour")
    day_axes[0,2].set_ylabel("soil water in g")
    day_axes[0,2].set_title("")

    day_axes[0,3].plot(day_data["time"], day_data["health_state"])  # Idem
    day_axes[0,3].set_xlabel("Jour")
    day_axes[0,3].set_ylabel("Santé (0..100)")
    day_axes[0,3].set_title("État de santé")

    # ------------------------------------------------------------------
    # Ligne 1
    # ------------------------------------------------------------------
    # Sucre => orange
    day_axes[1,0].plot(day_data["time"], day_data["actual_sugar"], label="Sucre disponible", color="orange")
    day_axes[1,0].set_xlabel("Jour")
    day_axes[1,0].set_ylabel("Valeurs calculées")
    day_axes[1,0].set_title("Photosynthèse nette")
    day_axes[1,0].legend()

    # Réserves : sucre (orange), eau (bleu), nutriments (vert)
    day_axes[1,1].plot(day_data["time"], day_data["reserve_sugar"], label="Sucre", color="orange")
    day_axes[1,1].plot(day_data["time"], day_data["reserve_water"], label="Eau", color="blue")
    day_axes[1,1].set_xlabel("Jour")
    day_axes[1,1].set_ylabel("Réserves (g)")
    day_axes[1,1].set_title("Réserves internes")
    day_axes[1,1].legend()

    day_axes[1,2].plot(day_data["time"], day_data["reserve_nutrient"], label="Nutriments", color="green")
    day_axes[1,2].set_xlabel("Jour")
    day_axes[1,2].set_ylabel("Réserves (g)")
    day_axes[1,2].set_title("Réserves internes")
    day_axes[1,2].legend()

    # Températures : pas de code couleur imposé
    day_axes[1,3].plot(day_data["time"], day_data["atmos_temperature"], label="Tair")
    day_axes[1,3].plot(day_data["time"], day_data["leaf_temperature_after"], label="Tfeuille")
    day_axes[1,3].set_xlabel("Jour")
    day_axes[1,3].set_ylabel("Température (°C)")
    day_axes[1,3].set_title("Température foliaire")
    day_axes[1,3].legend()

    # ------------------------------------------------------------------
    # Ligne 2
    # ------------------------------------------------------------------
    # Paramètres physiologiques => pas de couleurs imposées
    day_axes[2,0].plot(day_data["time"], day_data["stomatal_conductance"], label="gs")
    day_axes[2,0].plot(day_data["time"], day_data["leaf_angle"], label="angle")
    day_axes[2,0].plot(day_data["time"], day_data["nutrient_index"], label="nutrient_index")
    day_axes[2,0].set_xlabel("Jour")
    day_axes[2,0].set_ylabel("Index (0..1)")
    day_axes[2,0].set_title("Régulation stomates/angle/nutriment")
    day_axes[2,0].legend()

    # reserve_used : maintenance => marron, extension => orange, reproduction => violet, transpiration => bleu
    day_axes[2,1].plot(day_data["time"], day_data["reserve_used_maintenance"], label="Maint.", color="orange")
    day_axes[2,1].plot(day_data["time"], day_data["reserve_used_extension"], label="Ext.", color="green")
    day_axes[2,1].plot(day_data["time"], day_data["reserve_used_reproduction"], label="Repr.", color="violet")
    day_axes[2,1].set_xlabel("Jour")
    day_axes[2,1].set_ylabel("0 ou 1")
    day_axes[2,1].set_title("reserve_used (bool)")
    day_axes[2,1].legend()

    # Capacité max de transpiration => bleu (transpiration)
    day_axes[2,2].plot(day_data["time"], day_data["max_transpiration_capacity"], label="Max capacity", color="blue")
    day_axes[2,2].set_xlabel("Jour")
    day_axes[2,2].set_ylabel("H2O (g/jour)")
    day_axes[2,2].set_title("Détails Transpiration")
    day_axes[2,2].legend()

    # Flux brut/potentiels de sucre => orange (sucre)
    day_axes[2,3].plot(day_data["time"], day_data["raw_sugar_flux"], label="Flux brut")
    day_axes[2,3].plot(day_data["time"], day_data["pot_sugar"], label="Flux potentiel")
    day_axes[2,3].set_xlabel("Jour")
    day_axes[2,3].set_ylabel("Valeurs calculées")
    day_axes[2,3].set_title("Détails Photosynthèse")
    day_axes[2,3].legend()

    # ------------------------------------------------------------------
    # Ligne 3
    # ------------------------------------------------------------------
    # Lumière atmosphérique : pas de code couleur imposé
    day_axes[3,0].plot(day_data["time"], day_data["atmos_light"], label="Lumière", color="yellow")
    day_axes[3,0].set_xlabel("Jour")
    day_axes[3,0].set_ylabel("Luminosité (W/m²)")
    day_axes[3,0].set_title("Luminosité atmosphérique")
    day_axes[3,0].legend()

    # adjusted_used : maintenance => marron, extension => orange, reproduction => violet, transpiration => bleu
    day_axes[3,1].plot(day_data["time"], day_data["adjusted_used_maintenance"], label="Maint.", color="orange")
    day_axes[3,1].plot(day_data["time"], day_data["adjusted_used_extension"], label="Ext.", color="green")
    day_axes[3,1].plot(day_data["time"], day_data["adjusted_used_reproduction"], label="Repr.", color="violet")
    day_axes[3,1].set_xlabel("Jour")
    day_axes[3,1].set_ylabel("0 ou 1")
    day_axes[3,1].set_title("adjusted_used (bool)")
    day_axes[3,1].legend()

    # Ratios d’allocation => pas de couleurs imposées
    day_axes[3,2].plot(day_data["time"], day_data["ratio_support"], label="support", color="brown")
    day_axes[3,2].plot(day_data["time"], day_data["ratio_photo"], label="photo", color="green")
    day_axes[3,2].plot(day_data["time"], day_data["ratio_absorp"], label="absorp", color="blue")
    day_axes[3,2].plot(day_data["time"], day_data["ratio_repro"], label="repro", color="violet")
    day_axes[3,2].set_xlabel("Jour")
    day_axes[3,2].set_ylabel("Ratios / Stress")
    day_axes[3,2].set_title("Ratios d’allocation")
    day_axes[3,2].legend()

    # Succès extension => orange, reproduction => violet
    day_axes[3,3].plot(day_data["time"], day_data["success_extension"], label="Extension", color="green")
    day_axes[3,3].plot(day_data["time"], day_data["success_reproduction"], label="Reproduction", color="violet")
    day_axes[3,3].set_xlabel("Jour")
    day_axes[3,3].set_ylabel("Succès (0..1)")
    day_axes[3,3].set_title("Succès des processus")
    day_axes[3,3].legend()

    # ------------------------------------------------------------------
    # Ligne 4 : Coûts par processus
    # ------------------------------------------------------------------
    # Transpiration => bleu
    ax = day_axes[4, 0]
    x = day_data["time"]
    ax.plot(x, day_data["cost_transpiration_water"], label="Eau (Transp.)", color="blue")
    ax.set_xlabel("Jour")
    ax.set_ylabel("Coût (g)")
    ax.set_title("Processus transpiration")
    ax.legend()

    # Maintenance => marron
    ax = day_axes[4, 1]
    ax.plot(x, day_data["cost_maintenance_sugar"], label="Maintenance (Sucre)", color="orange")
    ax.set_xlabel("Jour")
    ax.set_ylabel("Coût (g)")
    ax.set_title("Processus maintenance")
    ax.legend()

    # Extension => orange
    ax = day_axes[4, 2]
    ax.plot(x, day_data["cost_extension_sugar"],     label="Ext. (Sucre)",     color="orange")
    ax.plot(x, day_data["cost_extension_water"],     label="Ext. (Eau)",       color="blue")
    ax.plot(x, day_data["cost_extension_nutrient"],  label="Ext. (Nutriments)",color="green")
    ax.set_xlabel("Jour")
    ax.set_ylabel("Coût (g)")
    ax.set_title("Processus extension")
    ax.legend()

    # Reproduction => violet
    ax = day_axes[4, 3]
    ax.plot(x, day_data["cost_reproduction_sugar"],     label="Repro (Sucre)",     color="orange")
    ax.plot(x, day_data["cost_reproduction_water"],     label="Repro (Eau)",       color="blue")
    ax.plot(x, day_data["cost_reproduction_nutrient"],  label="Repro (Nutriments)",color="green")
    ax.set_xlabel("Jour")
    ax.set_ylabel("Coût (g)")
    ax.set_title("Processus reproduction")
    ax.legend()

    day_fig.tight_layout()
    plt.show()

    # ------------------------------------------------------------------
    # PARTIE NUIT : mêmes principes de couleurs
    # ------------------------------------------------------------------
    night_fig, night_axes = plt.subplots(nrows=7, ncols=3, figsize=(15, 35))
    night_fig.suptitle("Résultats de la simulation (agrégation journalière) - Modèle Plantroid", fontsize=16)

    # Biomasse totale => vert
    night_axes[0,0].plot(night_data["time"], night_data["biomass_total"], color="green")
    night_axes[0,0].set_xlabel("Jour")
    night_axes[0,0].set_ylabel("Biomasse totale (g)")
    night_axes[0,0].set_title("Biomasse totale")

    # Compartiments : support/photo/absorp => vert, repro => violet
    night_axes[0,1].plot(night_data["time"], night_data["biomass_support"], label="support", color="green")
    night_axes[0,1].plot(night_data["time"], night_data["biomass_photo"],   label="photo",   color="green")
    night_axes[0,1].plot(night_data["time"], night_data["biomass_absorp"],  label="absorp",  color="green")
    night_axes[0,1].set_xlabel("Jour")
    night_axes[0,1].set_ylabel("Biomasse (g)")
    night_axes[0,1].set_title("Biomasse par compartiment")
    night_axes[0,1].legend()

    night_axes[0,2].plot(night_data["time"], night_data["slai"])
    night_axes[0,2].set_xlabel("Jour")
    night_axes[0,2].set_ylabel("SLAI")
    night_axes[0,2].set_title("Surface foliaire (SLAI)")

    # Santé => pas de couleur imposée
    night_axes[1,0].plot(night_data["time"], night_data["health_state"])
    night_axes[1,0].set_xlabel("Jour")
    night_axes[1,0].set_ylabel("Santé (0..100)")
    night_axes[1,0].set_title("État de santé")

    # Flux entrants => pas de code couleur imposé ici, on peut les laisser par défaut
    night_axes[1,1].plot(night_data["time"], night_data["sugar_in"], label="sugar_in")
    night_axes[1,1].plot(night_data["time"], night_data["water_in"], label="water_in")
    night_axes[1,1].plot(night_data["time"], night_data["nutrient_in"], label="nutrient_in")
    night_axes[1,1].set_xlabel("Jour")
    night_axes[1,1].set_ylabel("Flux entrants (g)")
    night_axes[1,1].set_title("Flux entrants")
    night_axes[1,1].legend()

    # Réserves : on peut reprendre la même coloration : sucre (orange), eau (bleu), nutriments (vert)
    night_axes[2,1].plot(night_data["time"], night_data["reserve_sugar"], label="Sucre", color="orange")
    night_axes[2,1].plot(night_data["time"], night_data["reserve_water"], label="Eau", color="blue")
    night_axes[2,1].set_xlabel("Jour")
    night_axes[2,1].set_ylabel("Réserves (g)")
    night_axes[2,1].set_title("Réserves internes")
    night_axes[2,1].legend()

    night_axes[2,2].plot(night_data["time"], night_data["reserve_nutrient"], label="Nutriments", color="green")
    night_axes[2,2].set_xlabel("Jour")
    night_axes[2,2].set_ylabel("Réserves (g)")
    night_axes[2,2].set_title("Réserves internes")
    night_axes[2,2].legend()

    # Températures
    night_axes[3,0].plot(night_data["time"], night_data["atmos_temperature"], label="Tair")
    night_axes[3,0].plot(night_data["time"], night_data["leaf_temperature_after"], label="Tfeuille")
    night_axes[3,0].set_xlabel("Jour")
    night_axes[3,0].set_ylabel("Température (°C)")
    night_axes[3,0].set_title("Température foliaire")
    night_axes[3,0].legend()

    # Conductance stomatique => pas de code imposé
    night_axes[3,1].plot(night_data["time"], night_data["stomatal_conductance"])
    night_axes[3,1].set_xlabel("Jour")
    night_axes[3,1].set_ylabel("Conductance (0..1)")
    night_axes[3,1].set_title("Conductance stomatique")

    # Succès extension => orange, reproduction => violet
    night_axes[3,2].plot(night_data["time"], night_data["success_extension"], label="Extension", color="orange")
    night_axes[3,2].plot(night_data["time"], night_data["success_reproduction"], label="Reproduction", color="violet")
    night_axes[3,2].set_xlabel("Jour")
    night_axes[3,2].set_ylabel("Succès (0..1)")
    night_axes[3,2].set_title("Succès des processus")
    night_axes[3,2].legend()

    # Transpiration => bleu
    night_axes[4,0].plot(night_data["time"], night_data["max_transpiration_capacity"], label="Max capacity", color="blue")
    night_axes[4,0].set_xlabel("Jour")
    night_axes[4,0].set_ylabel("H2O (g/jour)")
    night_axes[4,0].set_title("Détails Transpiration")
    night_axes[4,0].legend()

    # Flux de photosynthèse => orange
    night_axes[4,1].plot(night_data["time"], night_data["raw_sugar_flux"], label="Flux brut", color="orange")
    night_axes[4,1].plot(night_data["time"], night_data["pot_sugar"], label="Flux potentiel", color="orange")
    night_axes[4,1].set_xlabel("Jour")
    night_axes[4,1].set_ylabel("gC6H12O6/gleaf/s")
    night_axes[4,1].set_title("Détails Photosynthèse")
    night_axes[4,1].legend()
    night_axes[4,2].axis("off")

    # Lumière/pluie => pas de code imposé
    night_axes[5,0].plot(night_data["time"], night_data["atmos_light"], label="Lumière")
    night_axes[5,0].set_xlabel("Jour")
    night_axes[5,0].set_ylabel("Luminosité (W/m²)")
    night_axes[5,0].set_title("Luminosité atmosphérique")
    night_axes[5,0].legend()

    night_axes[5,1].plot(night_data["time"], night_data["rain_event"], label="Pluie (somme/jour)")
    night_axes[5,1].set_xlabel("Jour")
    night_axes[5,1].set_ylabel("Pluie (g eau/jour)")
    night_axes[5,1].set_title("Événement de pluie")
    night_axes[5,1].legend()

    night_axes[5,2].axis("off")

    # Variables booléennes + ratio + stress
    # reserve_used => maintenance (marron), extension (orange), reproduction (violet)
    night_axes[6,0].plot(night_data["time"], night_data["reserve_used_maintenance"], label="Maint.", color="brown")
    night_axes[6,0].plot(night_data["time"], night_data["reserve_used_extension"], label="Ext.", color="orange")
    night_axes[6,0].plot(night_data["time"], night_data["reserve_used_reproduction"], label="Repr.", color="violet")
    night_axes[6,0].set_xlabel("Jour")
    night_axes[6,0].set_ylabel("0 ou 1")
    night_axes[6,0].set_title("reserve_used (bool)")
    night_axes[6,0].legend()

    # adjusted_used => idem
    night_axes[6,1].plot(night_data["time"], night_data["adjusted_used_maintenance"], label="Maint.", color="brown")
    night_axes[6,1].plot(night_data["time"], night_data["adjusted_used_extension"], label="Ext.", color="orange")
    night_axes[6,1].plot(night_data["time"], night_data["adjusted_used_reproduction"], label="Repr.", color="violet")
    night_axes[6,1].set_xlabel("Jour")
    night_axes[6,1].set_ylabel("0 ou 1")
    night_axes[6,1].set_title("adjusted_used (bool)")
    night_axes[6,1].legend()

    # Ratios d’allocation & Stress => pas de code imposé
    night_axes[6,2].plot(night_data["time"], night_data["ratio_support"], label="support", color="brown")
    night_axes[6,2].plot(night_data["time"], night_data["ratio_photo"], label="photo", color="green")
    night_axes[6,2].plot(night_data["time"], night_data["ratio_absorp"], label="absorp", color="blue")
    night_axes[6,2].plot(night_data["time"], night_data["stress_sugar"], label="stress_sugar", linestyle="--")
    night_axes[6,2].plot(night_data["time"], night_data["stress_water"], label="stress_water", linestyle="--")
    night_axes[6,2].set_xlabel("Jour")
    night_axes[6,2].set_ylabel("Ratios / Stress")
    night_axes[6,2].set_title("Ratios & Stress")
    night_axes[6,2].legend()

    night_fig.tight_layout()
    # On peut afficher si souhaité :
    # plt.show()

if __name__ == "__main__":
    simulate_and_plot("ble")
