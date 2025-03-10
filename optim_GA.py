import copy
import random

import time_loop as Ti
import Plant_def as Pl
import Environnement_def as Ev
import history_def as Hi
import global_constants as Gl
import run_and_plot as Rp

def ga_multi_criteria_optimization(
    population_size=20,
    generations=10,
    crossover_rate=0.7,
    mutation_rate=0.1,
    elite_size=2,
    # Contraintes sur la biomasse finale
    B_min=1.0,
    B_max=4.0,
    # Plage fraction sucre
    BT_min=0.4,
    BT_max=0.6,
    BL_min=0.0,
    BL_max=0.1,   
    # Pondérations
    alpha_biomass=1.0,
    alpha_leaving=1.0,
    alpha_sugar=1.0,
    alpha_stability=1.0
):
    """
    Algorithme génétique qui optimise 5 paramètres du modèle Plantroid
    en respectant certaines contraintes et en maximisant un score agrégé:
      score = alpha_biomass * B_final 
            + alpha_sugar   * sugar_final 
            + alpha_stability * stability_score
    avec:
      - Contrainte: B_min <= B_final <= B_max
      - Contrainte: fraction_sucre ∈ [reprod_frac_min..reprod_frac_max]
      - stability_score: lié à la pente finale (plus la pente est proche de 0, mieux c'est).
    
    Paramètres à optimiser:
      "r_max", "alpha", "dessication_rate",
      "root_absorption_coefficient", "transpiration_coefficient"

    Paramètres GA:
      population_size, generations, crossover_rate, mutation_rate, elite_size
    """

    # ----------------------------------------------------------------
    # 1) Bornes des 5 paramètres
    param_bounds = {
        "r_max": (0.001, 0.01),
        "alpha": (0.0001, 0.001),
        "light_absorption_max": (0.3, 1.0),
        "stomatal_density": (1e6, 1e7)
    }
    param_names = list(param_bounds.keys())

    # ----------------------------------------------------------------
    # 2) Création population initiale
    def random_individual():
        ind = {}
        for name in param_names:
            low, high = param_bounds[name]
            ind[name] = random.uniform(low, high)
        return ind

    population = [random_individual() for _ in range(population_size)]

    # ----------------------------------------------------------------
    # 3) Évaluer un individu (avec calcul des constraints + score)
    def evaluate(individual):
        """
        Lance la simulation, puis calcule un score agrégé.
        On applique une pénalité si les contraintes ne sont pas satisfaites,
        au lieu de mettre la fitness à 0.
        """
        # Copie la plante et l’environnement initiaux
        plant_copy = copy.deepcopy(Pl.Plant)
        env_copy = copy.deepcopy(Ev.Environment)

        # Applique les paramètres
        plant_copy["r_max"] = individual["r_max"]
        plant_copy["alpha"] = individual["alpha"]
        plant_copy["light_absorption_max"] = individual["light_absorption_max"]
        plant_copy["stomatal_density"] = individual["stomatal_density"]

        # Sauvegarde l’état global
        original_plant = Pl.Plant
        original_env   = Ev.Environment

        # Remplace globalement
        Pl.Plant       = plant_copy
        Ev.Environment = env_copy

        # Réinitialise l’historique
        for k in Hi.history:
            Hi.history[k].clear()

        # Lance la simulation
        data, final_plant, final_env = Ti.run_simulation_collect_data(Gl.max_cycles)

        # Restaure
        Pl.Plant       = original_plant
        Ev.Environment = original_env

        # Récupération des données d’intérêt
        B_final   = final_plant["biomass"]["repro"]
        BT_final  = final_plant["biomass"]["necromass"]
        BL_final  = final_plant["biomass_total"]

        # -------------------------
        # 1) Score de base
        # -------------------------
        # Exemple : on garde l’existant
        stability_score = compute_stability_score(Hi.history, last_n=10)
        scoreBase = (alpha_biomass * B_final
                    + alpha_sugar   * BT_final
                    + alpha_leaving   * BL_final
                    + alpha_stability * stability_score)

        # -------------------------
        # 2) Calcul de la pénalité
        # -------------------------
        penalty = 0.0

        # Pénalité sur la biomasse hors de [B_min..B_max]
        if B_final < B_min:
            penalty += (B_min - B_final) ** 2
        elif B_final > B_max:
            penalty += (B_final - B_max) ** 2

        # Pénalité sur la fraction de sucre hors de [reprod_frac_min..reprod_frac_max]
        if BT_final < BT_min:
            penalty += (BT_min - BT_final) ** 2
        elif BT_final > BT_max:
            penalty += (BT_final - BT_max) ** 2

        # Pénalité sur la fraction de sucre hors de [reprod_frac_min..reprod_frac_max]
        if BL_final < BL_min:
            penalty += (BL_min - BL_final) ** 2
        elif BL_final > BL_max:
            penalty += (BL_final - BL_max) ** 2
        # Vous pouvez ajouter d'autres pénalités sur d’autres variables 
        # (santé trop basse, mortalité, etc.)

        # -------------------------
        # 3) Fitness finale
        # -------------------------
        # Méthode 1 : on divise le score par (1 + penalty)
        if scoreBase < 0:
            scoreBase = 0.0
        fitness = scoreBase / (1.0 + penalty)

        return fitness

    # ----------------------------------------------------------------
    # 4) Calcul de la stabilité (pente finale)
    def compute_stability_score(history, last_n=10):
        """
        Exemple: On récupère les 10 derniers points de la biomasse totale
        ET de la réserve de sucre, on calcule la pente absolue moyenne 
        et on la transforme en un score [0..∞).
        Plus la pente est faible, plus le score est élevé.
        """
        # Récupère la liste des biomasses
        B_list = history["biomass_repro"][-last_n:]
        S_list = history["biomass_necromass"][-last_n:]

        # Si on n’a pas assez de points, on renvoie un score neutre
        if len(B_list) < 2 or len(S_list) < 2:
            return 1.0

        # calcule la pente en absolu (moyenne des pentes sur B et S)
        slope_B = linear_slope(B_list)
        slope_S = linear_slope(S_list)
        abs_slope = (abs(slope_B) + abs(slope_S)) / 2.0

        # Transforme en un score (plus c’est bas, mieux c’est)
        # ex:  score = 1 / (1 + abs_slope)
        # => si abs_slope = 0 => score = 1
        # => plus abs_slope est grand, plus le score se rapproche de 0
        stability = 1.0 / (1.0 + abs_slope)
        return stability

    def linear_slope(values):
        """
        Renvoie la pente (slope) d'une régression linéaire 
        sur la liste de valeurs.
        """
        n = len(values)
        if n < 2:
            return 0.0
        x_vals = range(n)
        sum_x  = sum(x_vals)
        sum_y  = sum(values)
        sum_xy = sum(x*y for x,y in zip(x_vals, values))
        sum_x2 = sum(x*x for x in x_vals)

        denom = n*sum_x2 - sum_x*sum_x
        if abs(denom) < 1e-12:
            return 0.0
        slope = (n*sum_xy - sum_x*sum_y) / denom
        return slope

    # ----------------------------------------------------------------
    # 5) Sélection (tournoi)
    def tournament_selection(pop, fits, k=3):
        chosen_indices = random.sample(range(len(pop)), k)
        best_ind = None
        best_fit = -1e9
        for idx in chosen_indices:
            if fits[idx] > best_fit:
                best_fit = fits[idx]
                best_ind = pop[idx]
        return best_ind

    # ----------------------------------------------------------------
    # 6) Croisement (crossover) uniforme
    def crossover(p1, p2):
        child = {}
        for name in param_names:
            if random.random() < 0.5:
                child[name] = p1[name]
            else:
                child[name] = p2[name]
        return child

    # ----------------------------------------------------------------
    # 7) Mutation
    def mutate(ind):
        for name in param_names:
            if random.random() < mutation_rate:
                low, high = param_bounds[name]
                # On peut aussi faire un petit offset au lieu d’un random complet
                ind[name] = random.uniform(low, high)

    # ----------------------------------------------------------------
    # 8) Boucle Génétique
    best_solution = None
    best_fitness = -1.0

    for gen in range(generations):
        # Évalue chaque individu
        fitnesses = [evaluate(ind) for ind in population]

        # Mise à jour du meilleur
        for i, fit in enumerate(fitnesses):
            if fit > best_fitness:
                best_fitness = fit
                best_solution = copy.deepcopy(population[i])

        print(f"Génération {gen+1}/{generations} | Best Fitness = {best_fitness:.3f}")

        # Tri pour élitisme
        sorted_idx = sorted(range(len(population)), key=lambda i: fitnesses[i], reverse=True)

        # Nouvelle population
        new_pop = []
        # Élitisme
        for i in range(elite_size):
            new_pop.append(copy.deepcopy(population[sorted_idx[i]]))

        # Croisement + mutation
        while len(new_pop) < population_size:
            parent1 = tournament_selection(population, fitnesses, k=3)
            parent2 = tournament_selection(population, fitnesses, k=3)

            if random.random() < crossover_rate:
                child = crossover(parent1, parent2)
            else:
                child = copy.deepcopy(parent1)

            mutate(child)
            new_pop.append(child)

        # Remplace la population
        population = new_pop

    # ----------------------------------------------------------------
    # Résultat final
    print("==============================================")
    print("Meilleure solution trouvée :")
    for p in best_solution:
        print(f"{p} = {best_solution[p]:.6f}")
    print(f"Score max = {best_fitness:.3f}")
    print("==============================================")

    return best_solution, best_fitness

if __name__ == "__main__":
    best_config, best_score = ga_multi_criteria_optimization(
        population_size=20,
        generations=20,
        crossover_rate=0.7,
        mutation_rate=0.1,
        elite_size=2,
        B_max=6.0,
        BT_min=5.0,
        BT_max=6.0,
        BL_min=0.0,
        BL_max=0.1,
        alpha_biomass=1.0,
        alpha_leaving=1.0,
        alpha_sugar=1.0,
        alpha_stability=0.0
    )
    Rp.simulate_and_plot()  