import matplotlib.pyplot as plt
import time_loop as Ti
import global_constants as Gl

def simulate_and_plot():
    """
    Exécute la simulation (par ex. 365*24 cycles) et
    trace tous les graphiques, incluant maintenant
    des informations détaillées sur la transpiration
    et la photosynthèse.
    """
    data, final_Plant, final_env = Ti.run_simulation_collect_data(Gl.max_cycles)

    # On crée plus de subplots pour inclure les nouvelles variables
    fig, axes = plt.subplots(nrows=5, ncols=3, figsize=(15, 20))
    fig.suptitle("Résultats de la simulation - Modèle cycle de vie Pl.Plante", fontsize=16)

    # ------------------------------------------------------------------
    # Rangée 0
    # ------------------------------------------------------------------
    # 0,0 : biomasse totale
    axes[0,0].plot(data["time"], data["biomass_total"])
    axes[0,0].set_xlabel("Temps (cycles)")
    axes[0,0].set_ylabel("Biomasse totale (g)")
    axes[0,0].set_title("Biomasse totale")

    # 0,1 : biomasse par compartiment
    axes[0,1].plot(data["time"], data["biomass_support"], label="support")
    axes[0,1].plot(data["time"], data["biomass_photo"],   label="photo")
    axes[0,1].plot(data["time"], data["biomass_absorp"],  label="absorp")
    axes[0,1].set_xlabel("Temps (cycles)")
    axes[0,1].set_ylabel("Biomasse (g)")
    axes[0,1].set_title("Biomasse par compartiment")
    axes[0,1].legend()

    # 0,2 : SLAI
    axes[0,2].plot(data["time"], data["slai"])
    axes[0,2].set_xlabel("Temps (cycles)")
    axes[0,2].set_ylabel("SLAI")
    axes[0,2].set_title("Surface foliaire (SLAI)")

    # ------------------------------------------------------------------
    # Rangée 1
    # ------------------------------------------------------------------
    # 1,0 : santé
    axes[1,0].plot(data["time"], data["health_state"])
    axes[1,0].set_xlabel("Temps (cycles)")
    axes[1,0].set_ylabel("Santé (0..100)")
    axes[1,0].set_title("État de santé")

    # 1,1 : flux_in
    axes[1,1].plot(data["time"], data["sugar_in"], label="sugar_in")
    axes[1,1].plot(data["time"], data["water_in"], label="water_in")
    axes[1,1].plot(data["time"], data["nutrient_in"], label="nutrient_in")
    axes[1,1].set_xlabel("Temps (cycles)")
    axes[1,1].set_ylabel("Flux entrants (g)")
    axes[1,1].set_title("Flux entrants (g)")
    axes[1,1].legend()

    # 1,2 : flux_out
    axes[1,2].plot(data["time"], data["water_after_transp"], label="water_after_transp")
    axes[1,2].set_xlabel("Temps (cycles)")
    axes[1,2].set_ylabel("Flux sortants (g)")
    axes[1,2].set_title("Flux sortants (g)")
    axes[1,2].legend()

    # ------------------------------------------------------------------
    # Rangée 2
    # ------------------------------------------------------------------
    # 2,0 : flux_in spéciaux (après transp / photo)
    axes[2,0].plot(data["time"], data["sugar_photo"],  label="sugar_photo")
    axes[2,0].set_xlabel("Temps (cycles)")
    axes[2,0].set_ylabel("Flux_in spéciaux (g)")
    axes[2,0].set_title("Flux_in après transpiration / photo")
    axes[2,0].legend()

    # 2,1 : réserves internes
    axes[2,1].plot(data["time"], data["reserve_sugar"],   label="Sucre")
    axes[2,1].plot(data["time"], data["reserve_water"],   label="Eau")
    axes[2,1].plot(data["time"], data["reserve_nutrient"], label="Nutriments")
    axes[2,1].set_xlabel("Temps (cycles)")
    axes[2,1].set_ylabel("Réserves (g)")
    axes[2,1].set_title("Réserves internes")
    axes[2,1].legend()

    # 2,2 : eau dans le sol
    axes[2,2].plot(data["time"], data["soil_water"], label="Soil water")
    axes[2,2].set_xlabel("Temps (cycles)")
    axes[2,2].set_ylabel("Eau (g)")
    axes[2,2].set_title("Eau dans le sol")
    axes[2,2].legend()

    # ------------------------------------------------------------------
    # Rangée 3
    # ------------------------------------------------------------------
    # 3,0 : Température foliaire
    axes[3,0].plot(data["time"], data["atmos_temperature"], label="Tair")
    axes[3,0].plot(data["time"], data["leaf_temperature_before"], label="Tbf")
    axes[3,0].plot(data["time"], data["leaf_temperature_after"], label="Taf") 
    axes[3,0].set_xlabel("Temps (cycles)")
    axes[3,0].set_ylabel("Température (°C)")
    axes[3,0].set_title("Température foliaire")
    axes[3,0].legend()

    # 3,1 : Conductance stomatique
    axes[3,1].plot(data["time"], data["stomatal_conductance"])
    axes[3,1].set_xlabel("Temps (cycles)")
    axes[3,1].set_ylabel("Conductance (0..1)")
    axes[3,1].set_title("Conductance stomatique")

    # 3,2 : Success cycles
    axes[3,2].plot(data["time"], data["success_extension"], label="Extension")
    axes[3,2].plot(data["time"], data["success_reproduction"], label="Reproduction")
    axes[3,2].set_xlabel("Temps (cycles)")
    axes[3,2].set_ylabel("Succès (0..1)")
    axes[3,2].set_title("Succès des processus")
    axes[3,2].legend()

    # ------------------------------------------------------------------
    # Rangée 4 : NOUVEAUX INDICATEURS (transpiration, photosynthèse)
    # ------------------------------------------------------------------

    # 4,0 : détails transpiration
    axes[4,0].plot(data["time"], data["transpiration_cooling"], label="Cooling")
    axes[4,0].plot(data["time"], data["max_transpiration_capacity"], label="Max capacity")
    axes[4,0].set_xlabel("Temps (cycles)")
    axes[4,0].set_ylabel("H2O (g/cycle)")
    axes[4,0].set_title("Détails Transpiration")
    axes[4,0].legend()

    # 4,1 : détails photosynthèse
    axes[4,1].plot(data["time"], data["raw_sugar_flux"], label="Flux brut (g/s*gFeuille)")
    axes[4,1].plot(data["time"], data["pot_sugar"], label="Pot. (g/s, avant T_lim)")
    axes[4,1].set_xlabel("Temps (cycles)")
    axes[4,1].set_ylabel("Valeurs calculées")
    axes[4,1].set_title("Détails Photosynthèse")
    axes[4,1].legend()

    # 4,2 : on laisse vide ou on pourrait y mettre d’autres indicateurs
    axes[4,2].axis("off")

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    simulate_and_plot()