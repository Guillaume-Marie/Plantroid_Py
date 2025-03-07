
import time_loop as Ti
import global_constants as Gl
import copy
import numpy as np
import Plant_def as Pl

def optimize_parameters():
    """
    Effectue une recherche par grille (grid search) pour trouver la 
    combinaison de 5 paramètres qui maximise la biomasse totale finale.
    
    Paramètres à optimiser:
      1) r_max
      2) alpha
      3) light_absorption_fraction
      4) root_absorption_coefficient
      5) transpiration_coefficient

    Retourne un dictionnaire contenant la meilleure configuration 
    et la biomasse finale associée.
    """

    # -- Définition des plages de valeurs à tester pour chaque paramètre --
    # Vous pouvez ajuster les min, max et pas selon vos besoins.
    r_max_values   = np.linspace(0.001, 0.01, 3)     # exemple: 3 valeurs
    alpha_values   = np.linspace(0.0001, 0.001, 3)
    light_abs_values = np.linspace(0.5, 0.9, 3)
    root_abs_values  = np.linspace(0.001, 0.01, 3)
    trans_coef_values = np.linspace(0.001, 0.01, 3)

    # Variable pour suivre le maximum
    best_config = None
    best_biomass = -1.0

    # -- Parcours de toutes les combinaisons possibles --
    for r_max in r_max_values:
        for alpha in alpha_values:
            for light_abs in light_abs_values:
                for root_abs in root_abs_values:
                    for trans_coef in trans_coef_values:
                        
                        # Copie profonde de la plante initiale
                        Plant_copy = copy.deepcopy(Pl.Plant)
                        
                        # Réinitialiser l'environnement également si besoin
                        # (cela dépend si on veut que l'environnement reparte
                        #  de zéro ou continue tel quel).
                        # Par exemple:
                        # Environment_copy = copy.deepcopy(Ev.Environment)

                        # -- Modifier les paramètres --
                        Plant_copy["r_max"] = r_max
                        Plant_copy["alpha"] = alpha
                        Plant_copy["light_absorption_fraction"] = light_abs
                        Plant_copy["root_absorption_coefficient"] = root_abs
                        Plant_copy["transpiration_coefficient"]  = trans_coef

                        # -- Lancer la simulation --
                        # On utilise la structure 'run_simulation_collect_data',
                        # mais on doit passer la copie de Plant et un nouveau history.
                        # Pour rendre cela possible, il faut éventuellement adapter
                        # la fonction dans time_loop.py 
                        # ou bien affecter à Pl.Plant = Plant_copy avant l’appel.
                        # Ici, on fait une "astuce" : on écrase la Pl.Plant globale
                        # TEMPORAIREMENT, puis on la restaure ensuite.
                        
                        original_plant = Pl.Plant  # on garde l'original
                        Pl.Plant = Plant_copy      # on met la copie
                        
                        # Remettre l'historique à zéro si la fonction time_loop l'utilise directement
                        # (Dans le code existant, 'history' est global aussi, donc à voir
                        #  s'il faut également le réinitialiser. Cela dépend de l'implémentation.)
                        # Par exemple:
                        import history_def as Hi
                        for key in Hi.history:
                            Hi.history[key].clear()

                        # Paramètre max_cycles éventuellement plus petit pour accélérer l'optim
                        # (sinon vous faites l'optim sur la durée complète).
                        data, final_Plant, final_Env = Ti.run_simulation_collect_data(Gl.max_cycles)

                        # Restaure la Plant globale
                        Pl.Plant = original_plant

                        # -- Évalue la biomasse finale --
                        final_biomass = final_Plant["biomass_total"]

                        # -- Compare et stocke la meilleure config --
                        if final_biomass > best_biomass:
                            best_biomass = final_biomass
                            best_config = {
                                "r_max": r_max,
                                "alpha": alpha,
                                "light_absorption_fraction": light_abs,
                                "root_absorption_coefficient": root_abs,
                                "transpiration_coefficient": trans_coef
                            }

    # -- Affichage du résultat --
    print("================================================")
    print("Meilleure combinaison trouvée (grid search) :")
    print(best_config)
    print(f"Biomasse finale maximale : {best_biomass:.3f}")
    print("================================================")

    return best_config, best_biomass

if __name__ == "__main__":
    # Exemple d’appel
    best_config, best_biomass = optimize_parameters()