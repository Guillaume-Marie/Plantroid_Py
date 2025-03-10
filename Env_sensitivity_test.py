# -*- coding: utf-8 -*-

import copy
import random
import matplotlib.pyplot as plt

# On importe les modules du modèle
import global_constants as Gl
import Plant_def as Pl
import Environnement_def as Ev
import time_loop as Ti
import history_def as Hi

def run_simulation_with_modified_env(
    water_initial=None, 
    base_temp=None, 
    base_light=None
):
    """
    Lance une simulation en modifiant l'environnement initial
    puis renvoie (final_plant, final_env).
    
    Paramètres optionnels :
    -----------------------
    - water_initial : quantité d'eau initiale dans le sol (en g)
    - base_temp     : température moyenne annuelle (°C)
    - base_light    : luminosité max en été (W/m² ou autre)
    """
    # Sauvegarde l’environnement et la plante initiaux
    original_env   = copy.deepcopy(Ev.Environment)
    original_plant = copy.deepcopy(Pl.Plant)
    original_history = copy.deepcopy(Hi.history)

    # Réinitialise l’historique
    for k in Hi.history:
        Hi.history[k].clear()

    # Copie locale
    local_env   = copy.deepcopy(Ev.Environment)
    local_plant = copy.deepcopy(Pl.Plant)

    # Applique les changements d'environnement si demandés
    if water_initial is not None:
        local_env["soil"]["water"] = water_initial
    if base_temp is not None:
        # Ex. on place la valeur dans local_env pour la lire dans update_environment
        local_env["base_temp"] = base_temp
    if base_light is not None:
        local_env["base_light"] = base_light

    # Écrase l’environnement global par notre version locale
    Ev.Environment = local_env
    Pl.Plant       = local_plant

    # Lance la simulation
    result_history, final_plant, final_env = Ti.run_simulation_collect_data(Gl.max_cycles)

    # Restaure l’état initial global pour ne pas perturber les tests suivants
    Ev.Environment = original_env
    Pl.Plant       = original_plant
    Hi.history     = original_history

    return final_plant, final_env


def run_replicates_for_gradient(
    param_values,
    nb_rep=5,
    mode="water"
):
    """
    Pour un certain gradient (liste de valeurs de paramètre),
    exécute nb_rep répétitions à chaque valeur,
    et renvoie pour chacun:
    - la nécromasse min/mean/max
    - la biomasse de repro min/mean/max

    :param param_values: liste de valeurs du gradient (eau, T, lumière)
    :param nb_rep: nombre de répétitions par valeur
    :param mode: "water", "temp", ou "light" pour savoir quel paramètre on modifie

    Retourne:
    ---------
    {
      "x_values": [...] (les valeurs du gradient),
      "necromass_min": [...],
      "necromass_mean": [...],
      "necromass_max": [...],
      "repro_min": [...],
      "repro_mean": [...],
      "repro_max": [...]
    }
    """
    necro_min_list = []
    necro_mean_list = []
    necro_max_list = []
    repro_min_list = []
    repro_mean_list = []
    repro_max_list = []

    for val in param_values:
        necro_vals = []
        repro_vals = []

        for _ in range(nb_rep):
            if mode=="water":
                final_plant, _ = run_simulation_with_modified_env(water_initial=val)
            elif mode=="temp":
                final_plant, _ = run_simulation_with_modified_env(base_temp=val)
            elif mode=="light":
                final_plant, _ = run_simulation_with_modified_env(base_light=val)
            else:
                raise ValueError("Mode inconnu !")

            necro_vals.append(final_plant["biomass"]["necromass"])
            repro_vals.append(final_plant["biomass"]["repro"])

        # Calcul min/mean/max
        necro_min = min(necro_vals)
        necro_max = max(necro_vals)
        necro_mean = sum(necro_vals)/len(necro_vals)

        repro_min = min(repro_vals)
        repro_max = max(repro_vals)
        repro_mean = sum(repro_vals)/len(repro_vals)

        necro_min_list.append(necro_min)
        necro_mean_list.append(necro_mean)
        necro_max_list.append(necro_max)

        repro_min_list.append(repro_min)
        repro_mean_list.append(repro_mean)
        repro_max_list.append(repro_max)

    return {
        "x_values": param_values,
        "necromass_min": necro_min_list,
        "necromass_mean": necro_mean_list,
        "necromass_max": necro_max_list,
        "repro_min": repro_min_list,
        "repro_mean": repro_mean_list,
        "repro_max": repro_max_list
    }


def test_3_gradients_nb_rep(nb_rep=5):
    """
    Fait varier 3 gradients :
     1) Eau initiale
     2) Température moyenne annuelle
     3) Lumière max
    et fait nb_rep répétitions par valeur du gradient,
    puis affiche le tout dans UNE seule figure (3 subplots).
    """
    # 1. Définition des gradients
    water_values = [5e5, 1e6, 2e6, 3e6, 4e6, 5e6]
    temp_values  = [5, 10, 15, 20, 25, 30, 35]
    light_values = [400, 600, 800, 1000, 1200, 1500]

    # 2. Récupère les stats min/mean/max
    water_stats = run_replicates_for_gradient(water_values, nb_rep=nb_rep, mode="water")
    temp_stats  = run_replicates_for_gradient(temp_values,  nb_rep=nb_rep, mode="temp")
    light_stats = run_replicates_for_gradient(light_values, nb_rep=nb_rep, mode="light")

    # 3. Création de la figure et des 3 sous‐graphes
    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(18, 5))
    fig.suptitle(f"Tests de gradients (nb_rep={nb_rep} répétitions) - Nécromasse et Reproduction")

    # ---- Subplot (1) : Eau ----
    ax1 = axes[0]
    x_w = water_stats["x_values"]

    # Nécromasse
    ax1.fill_between(x_w, water_stats["necromass_min"], water_stats["necromass_max"], alpha=0.2, label="Nécromasse min-max")
    ax1.plot(x_w, water_stats["necromass_mean"], label="Nécromasse moyenne")

    # Repro
    ax1.fill_between(x_w, water_stats["repro_min"], water_stats["repro_max"], alpha=0.2, label="Repro min-max")
    ax1.plot(x_w, water_stats["repro_mean"], label="Repro moyenne")

    ax1.set_xlabel("Eau initiale dans le sol (g)")
    ax1.set_ylabel("Biomasse (g)")
    ax1.set_title("Gradient d'eau")
    ax1.legend()

    # ---- Subplot (2) : Température ----
    ax2 = axes[1]
    x_t = temp_stats["x_values"]

    # Nécromasse
    ax2.fill_between(x_t, temp_stats["necromass_min"], temp_stats["necromass_max"], alpha=0.2, label="Nécromasse min-max")
    ax2.plot(x_t, temp_stats["necromass_mean"], label="Nécromasse moyenne")

    # Repro
    ax2.fill_between(x_t, temp_stats["repro_min"], temp_stats["repro_max"], alpha=0.2, label="Repro min-max")
    ax2.plot(x_t, temp_stats["repro_mean"], label="Repro moyenne")

    ax2.set_xlabel("Température moyenne annuelle (°C)")
    ax2.set_ylabel("Biomasse (g)")
    ax2.set_title("Gradient de température")
    ax2.legend()

    # ---- Subplot (3) : Lumière ----
    ax3 = axes[2]
    x_l = light_stats["x_values"]

    # Nécromasse
    ax3.fill_between(x_l, light_stats["necromass_min"], light_stats["necromass_max"], alpha=0.2, label="Nécromasse min-max")
    ax3.plot(x_l, light_stats["necromass_mean"], label="Nécromasse moyenne")

    # Repro
    ax3.fill_between(x_l, light_stats["repro_min"], light_stats["repro_max"], alpha=0.2, label="Repro min-max")
    ax3.plot(x_l, light_stats["repro_mean"], label="Repro moyenne")

    ax3.set_xlabel("Lumière estivale max (base_light)")
    ax3.set_ylabel("Biomasse (g)")
    ax3.set_title("Gradient de lumière")
    ax3.legend()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # On peut ajuster le nb_rep pour plus ou moins de répétitions
    test_3_gradients_nb_rep(nb_rep=20)
