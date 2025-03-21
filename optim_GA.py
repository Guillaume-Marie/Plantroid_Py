# optim_GA.py
"""
Genetic Algorithm (GA) for multi-criteria optimization of Plantroid model parameters.
Comments and docstrings are in English; variable/function names remain in French for consistency.
"""

import copy
import random

import time_loop as Ti
import Plant_def as Pl
import Environnement_def as Ev
import history_def as Hi
import global_constants as Gl
import run_and_plot_v2 as Rp


def ga_multi_criteria_optimization(
    species_name="Ble",
    population_size=20,
    generations=10,
    crossover_rate=0.7,
    mutation_rate=0.1,
    elite_size=2,
    # Constraints on final biomass
    B_min=1.0,
    B_max=4.0,
    # Sugar fraction range
    BT_min=0.4,
    BT_max=0.6,
    BL_min=0.0,
    BL_max=0.1,
    # Weights in the objective function
    alpha_biomass=1.0,
    alpha_leaving=1.0,
    alpha_sugar=1.0,
    alpha_stability=1.0
):
    """
    Performs a genetic algorithm (GA) to optimize several parameters
    of the Plantroid model under multiple constraints.

    The GA tries to maximize a score that combines final biomass, sugar fraction,
    and stability, subject to constraints on biomass range and sugar fractions.

    Parameters
    ----------
    species_name : str
        Key of the plant species used in Plant_def.species_db.
    population_size : int
        Number of individuals in the GA population.
    generations : int
        Number of GA iterations.
    crossover_rate : float
        Probability of performing crossover on two selected parents.
    mutation_rate : float
        Probability of mutating an individual's parameter.
    elite_size : int
        Number of top individuals carried over to the next generation without change.
    B_min : float
        Minimum allowed final biomass constraint.
    B_max : float
        Maximum allowed final biomass constraint.
    BT_min : float
        Minimum allowed fraction for one sugar-related biomass constraint (nécromass).
    BT_max : float
        Maximum allowed fraction for the same sugar fraction.
    BL_min : float
        Another fraction constraint min (could be leaf or total necromass).
    BL_max : float
        The same fraction constraint max.
    alpha_biomass : float
        Weight for final biomass in the objective.
    alpha_leaving : float
        Weight for final living biomass (or leaving?).
    alpha_sugar : float
        Weight for final sugar fraction.
    alpha_stability : float
        Weight for the stability component in the objective.

    Returns
    -------
    tuple
        (best_solution, best_fitness), where best_solution is a dictionary
        of parameter values, and best_fitness is the highest score achieved.
    """
    # Load species default parameters into the global Plant object
    Pl.set_plant_species(Pl.Plant, species_name, Pl.species_db)

    # 1) Parameter bounds: dictionary that sets a lower and upper limit for each GA parameter
    param_bounds = {
        # example: "watt_to_sugar_coeff" : (min_val, max_val)
        "watt_to_sugar_coeff": (1e-4, 1e-6),
        "alloc_repro_max": (0.5, 1.0),
        "stomatal_density": (5.0e6, 5.0e8)
    }
    param_names = list(param_bounds.keys())

    # ----------------------------------------------------------------
    # Population initialization
    # ----------------------------------------------------------------
    def random_individual():
        """
        Creates a random individual by sampling each parameter
        uniformly between its bounds.
        """
        ind = {}
        for name in param_names:
            low, high = param_bounds[name]
            # Note: the upper is smaller than the lower for "watt_to_sugar_coeff" in original code
            # we might fix this logic or keep as is. Here we do random.uniform(low, high) as intended.
            # If (low > high), might need to swap or fix.
            if low > high:
                low, high = high, low
            ind[name] = random.uniform(low, high)
        return ind

    population = [random_individual() for _ in range(population_size)]

    # ----------------------------------------------------------------
    # Evaluation function
    # ----------------------------------------------------------------
    def evaluate(individual):
        """
        Runs a Plantroid simulation with the individual's parameters, then computes a score.

        Steps:
          - Copy the global Plant and Environment states
          - Apply individual's parameters
          - Run the simulation
          - Compute final constraints and a final score
          - Return the fitness

        Fitness function is influenced by alpha_biomass, alpha_sugar, alpha_stability, etc.
        Constraints penalize the fitness if outside specified ranges.
        """
        # Backup global states
        original_plant = copy.deepcopy(Pl.Plant)
        original_env = copy.deepcopy(Ev.Environment)

        # Copy for local changes
        plant_copy = copy.deepcopy(Pl.Plant)
        env_copy = copy.deepcopy(Ev.Environment)

        # Apply individual's parameters
        plant_copy["watt_to_sugar_coeff"] = individual["watt_to_sugar_coeff"]
        plant_copy["alloc_repro_max"] = individual["alloc_repro_max"]
        plant_copy["stomatal_density"] = individual["stomatal_density"]

        # Replace global references with copies
        Pl.Plant = plant_copy
        Ev.Environment = env_copy

        # Clear the history
        for k in Hi.history:
            Hi.history[k].clear()

        # Run simulation
        data, final_plant, final_env = Ti.run_simulation_collect_data(Gl.max_cycles)

        # Restore global states
        Pl.Plant = original_plant
        Ev.Environment = original_env

        # Retrieve final values
        B_final = final_plant["biomass"]["repro"]  # example usage
        BT_final = final_plant["biomass"]["necromass"]
        BL_final = final_plant["biomass_total"]

        # 1) Base score
        stability_score = compute_stability_score(Hi.history, last_n=10)
        score_base = (alpha_biomass * B_final
                      + alpha_sugar * BT_final
                      + alpha_leaving * BL_final
                      + alpha_stability * stability_score)

        # 2) Penalty for constraints
        penalty = 0.0

        # B_final in [B_min .. B_max]
        if B_final < B_min:
            penalty += (B_min - B_final) ** 2
        elif B_final > B_max:
            penalty += (B_final - B_max) ** 2

        # fraction_sucre in [BT_min..BT_max]
        if BT_final < BT_min:
            penalty += (BT_min - BT_final) ** 2
        elif BT_final > BT_max:
            penalty += (BT_final - BT_max) ** 2

        # fraction in [BL_min..BL_max]
        if BL_final < BL_min:
            penalty += (BL_min - BL_final) ** 2
        elif BL_final > BL_max:
            penalty += (BL_final - BL_max) ** 2

        # 3) Final fitness
        if score_base < 0:
            score_base = 0.0
        fitness = score_base / (1.0 + penalty)

        return fitness

    # ----------------------------------------------------------------
    # Stability measure (pente finale)
    # ----------------------------------------------------------------
    def compute_stability_score(history, last_n=10):
        """
        Example: compute the slope of the last 'last_n' points of
        "biomass_repro" and "biomass_necromass", average their absolute slopes,
        and transform it into [0..1] (the less slope, the higher the stability).
        """
        B_list = history["biomass_repro"][-last_n:]
        S_list = history["biomass_necromass"][-last_n:]

        if len(B_list) < 2 or len(S_list) < 2:
            return 1.0

        slope_B = linear_slope(B_list)
        slope_S = linear_slope(S_list)
        abs_slope = (abs(slope_B) + abs(slope_S)) / 2.0

        stability = 1.0 / (1.0 + abs_slope)
        return stability

    def linear_slope(values):
        """
        Returns the slope of a simple linear regression on 'values'.
        """
        n = len(values)
        if n < 2:
            return 0.0
        x_vals = range(n)
        sum_x = sum(x_vals)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_vals, values))
        sum_x2 = sum(x * x for x in x_vals)

        denom = n * sum_x2 - sum_x * sum_x
        if abs(denom) < 1e-12:
            return 0.0
        slope_val = (n * sum_xy - sum_x * sum_y) / denom
        return slope_val

    # ----------------------------------------------------------------
    # Selection (tournament)
    # ----------------------------------------------------------------
    def tournament_selection(pop, fits, k=3):
        """
        Randomly picks k individuals from 'pop', returns the best one based on 'fits'.
        """
        chosen_indices = random.sample(range(len(pop)), k)
        best_ind = None
        best_fit = -1e9
        for idx in chosen_indices:
            if fits[idx] > best_fit:
                best_fit = fits[idx]
                best_ind = pop[idx]
        return best_ind

    # ----------------------------------------------------------------
    # Crossover
    # ----------------------------------------------------------------
    def crossover(p1, p2):
        """
        Uniform crossover: each parameter is taken from p1 or p2 with 50% chance.
        """
        child = {}
        for name in param_names:
            if random.random() < 0.5:
                child[name] = p1[name]
            else:
                child[name] = p2[name]
        return child

    # ----------------------------------------------------------------
    # Mutation
    # ----------------------------------------------------------------
    def mutate(ind):
        """
        Mutates each parameter with 'mutation_rate', picking a random value in bounds.
        """
        for name in param_names:
            if random.random() < mutation_rate:
                low, high = param_bounds[name]
                # If low > high in param_bounds, swap to ensure random.uniform is valid
                if low > high:
                    low, high = high, low
                ind[name] = random.uniform(low, high)

    # ----------------------------------------------------------------
    # GA main loop
    # ----------------------------------------------------------------
    best_solution = None
    best_fitness = -1.0

    for gen in range(generations):
        fitnesses = [evaluate(ind) for ind in population]

        # Track the best
        for i, fit in enumerate(fitnesses):
            if fit > best_fitness:
                best_fitness = fit
                best_solution = copy.deepcopy(population[i])

        print(f"Generation {gen + 1}/{generations} | Best Fitness = {best_fitness:.3f}")

        # Sort population by fitness (descending)
        sorted_idx = sorted(range(len(population)), key=lambda i: fitnesses[i], reverse=True)

        # Elitism
        new_pop = []
        for i in range(elite_size):
            new_pop.append(copy.deepcopy(population[sorted_idx[i]]))

        # Fill the rest of the population by tournament selection and crossover
        while len(new_pop) < population_size:
            parent1 = tournament_selection(population, fitnesses, k=3)
            parent2 = tournament_selection(population, fitnesses, k=3)

            if random.random() < crossover_rate:
                child = crossover(parent1, parent2)
            else:
                child = copy.deepcopy(parent1)

            mutate(child)
            new_pop.append(child)

        population = new_pop

    # Final report
    print("==============================================")
    print("Best solution found:")
    for p in best_solution:
        print(f"{p} = {best_solution[p]:.6f}")
    print(f"Max score = {best_fitness:.3f}")
    print("==============================================")

    return best_solution, best_fitness


if __name__ == "__main__":
    # Example usage: runs the GA and then plots a simulation with the best config
    best_config, best_score = ga_multi_criteria_optimization(
        species_name="ble",
        population_size=20,
        generations=20,
        crossover_rate=0.7,
        mutation_rate=0.1,
        elite_size=2,
        B_max=4.0,
        B_min=2.0,
        BT_min=2.0,
        BT_max=4.0,
        BL_min=0.0,
        BL_max=0.1,
        alpha_biomass=1.0,
        alpha_leaving=1.0,
        alpha_sugar=1.0,
        alpha_stability=0.0
    )
    Rp.simulate_and_plot("ble")
