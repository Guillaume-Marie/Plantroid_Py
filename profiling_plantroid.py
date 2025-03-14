import matplotlib.pyplot as plt
import time_loop as Ti
import Plant_def as Pl
import history_def as Hi
import cProfile, pstats, io


def run_simulation_and_collect_data(species_name, total_days=365):
    """
    Lance une simulation complète et collecte les données.
    """
    # Initialisation de l'espèce végétale
    Pl.set_plant_species(Pl.Plant, species_name, Pl.species_db)

    # Réinitialisation de l'historique
    for k in Hi.history:
        Hi.history[k].clear()

    # Exécution de la simulation
    max_cycles = total_days * 24
    data, final_plant, final_env = Ti.run_simulation_collect_data(max_cycles)

    return data, final_plant, final_env


def profile_simulation(species_name='ble', total_days=200):
    """
    Fonction pour profiler la simulation à l'aide de cProfile.
    Retourne le résultat (data, final_plant, final_env) et affiche
    un rapport de profiling dans la console.
    """
    pr = cProfile.Profile()
    pr.enable()
    data, final_plant, final_env = run_simulation_and_collect_data(species_name, total_days)
    pr.disable()
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())
    return data, final_plant, final_env


def plot_simulation_results(data):
    """
    Génère des graphiques détaillés à partir des données de simulation.
    """
    fig, axes = plt.subplots(nrows=5, ncols=3, figsize=(18, 25))
    fig.suptitle("Résultats de la simulation - Modèle Plantroid", fontsize=16)

    time_days = [t/24 for t in data["time"]]

    # Biomasse
    axes[0, 0].plot(time_days, data["biomass_total"], label="Biomasse Totale")
    axes[0, 0].plot(time_days, data["biomass_necromass"], label="Nécromasse")
    axes[0, 0].set_xlabel("Jour")
    axes[0, 0].set_ylabel("Biomasse (g)")
    axes[0, 0].set_title("Évolution de la Biomasse")
    axes[0, 0].legend()

    # Flux de photosynthèse
    axes[0, 1].plot(time_days, data["raw_sugar_flux"], label="Flux Brut")
    axes[0, 1].plot(time_days, data["pot_sugar"], label="Flux Potentiel")
    axes[0, 1].set_xlabel("Jour")
    axes[0, 1].set_ylabel("Flux (g sucre)")
    axes[0, 1].set_title("Photosynthèse")
    axes[0, 1].legend()

    # Transpiration
    axes[0, 2].plot(time_days, data["cost_transpiration_water"], label="Coût en Eau")
    axes[0, 2].set_xlabel("Jour")
    axes[0, 2].set_ylabel("Eau (g)")
    axes[0, 2].set_title("Transpiration")
    axes[0, 2].legend()

    # Réserves
    axes[1, 0].plot(time_days, data["reserve_sugar"], label="Sucre")
    axes[1, 0].plot(time_days, data["reserve_water"], label="Eau")
    axes[1, 0].plot(time_days, data["reserve_nutrient"], label="Nutriments")
    axes[1, 0].set_xlabel("Jour")
    axes[1, 0].set_ylabel("Quantité (g)")
    axes[1, 0].set_title("Réserves Internes")
    axes[1, 0].legend()

    # Températures
    axes[1, 1].plot(time_days, data["atmos_temperature"], label="Température de l'Air")
    axes[1, 1].plot(time_days, data["leaf_temperature_after"], label="Température Foliaire")
    axes[1, 1].set_xlabel("Jour")
    axes[1, 1].set_ylabel("Température (°C)")
    axes[1, 1].set_title("Températures Atmosphérique et Foliaire")
    axes[1, 1].legend()

    # Conductance stomatique
    axes[1, 2].plot(time_days, data["stomatal_conductance"], label="Conductance Stomatique")
    axes[1, 2].set_xlabel("Jour")
    axes[1, 2].set_ylabel("Conductance (0..1)")
    axes[1, 2].set_title("Ouverture des Stomates")
    axes[1, 2].legend()

    # Pluie et lumière
    axes[2, 0].plot(time_days, data["rain_event"], label="Pluie")
    axes[2, 0].plot(time_days, data["atmos_light"], label="Lumière")
    axes[2, 0].set_xlabel("Jour")
    axes[2, 0].set_ylabel("Valeurs Environnementales")
    axes[2, 0].set_title("Pluie et Luminosité")
    axes[2, 0].legend()

    # Succès des processus
    axes[2, 1].plot(time_days, data["success_extension"], label="Extension")
    axes[2, 1].plot(time_days, data["success_reproduction"], label="Reproduction")
    axes[2, 1].set_xlabel("Jour")
    axes[2, 1].set_ylabel("Succès (0..1)")
    axes[2, 1].set_title("Succès des Processus")
    axes[2, 1].legend()

    # Stress hydrique et énergétique
    axes[2, 2].plot(time_days, data["stress_sugar"], label="Stress Sucre")
    axes[2, 2].plot(time_days, data["stress_water"], label="Stress Eau")
    axes[2, 2].set_xlabel("Jour")
    axes[2, 2].set_ylabel("Stress (0..1)")
    axes[2, 2].set_title("Stress Hydrique et Énergétique")
    axes[2, 2].legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    species = "ble"  # Espèce par défaut
    # Exemple d'exécution simple
    # data, final_plant, final_env = run_simulation_and_collect_data(species, total_days=365)
    # plot_simulation_results(data)

    # Exemple d'utilisation du profiler
    data, final_plant, final_env = profile_simulation(species_name=species, total_days=365)
    plot_simulation_results(data)
