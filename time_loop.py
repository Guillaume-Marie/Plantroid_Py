# -*- coding: utf-8 -*-
"""
time_loop.py

Main simulation loop for the Plantroid model.

This module defines the core simulation loop, iterating hour by hour,
updating environment conditions and plant processes, and recording data.
"""

import Plant_def as Pl
import Environnement_def as Ev
import functions as Fu
import global_constants as Gl
import history_def as Hi
import functions_BE as Be
import numpy as np
from datetime import datetime, timedelta



def run_simulation_collect_data(max_cycles):
    """
    Main simulation loop that runs up to 'max_cycles' hours.

    The loop increments the 'sim_time' (hours), updates environmental
    conditions, manages plant phenology, calculates costs, processes
    photosynthesis, reproduction, extension, and stores historical data.

    Parameters
    ----------
    max_cycles : int
        Maximum number of simulation steps (hours) to be performed.

    Returns
    -------
    tuple
        A tuple (history, Plant, Environment):
          - history : the dictionary tracking simulation variables over time
          - Plant   : the final plant state at the end of simulation
          - Environment : the final state of environment
    """
    # Choisissez une date de début pour la simulation
    start_date = datetime(2025, 1, 1)  # Exemple: 1er janvier 2025

    # Local time counter (in hours)
    sim_time = 0

    # Loop counter if needed (could be the same as sim_time)
    cycle_count = 0

    # Initialize soil water content to 50% of the soil volume
    Ev.Environment["soil"]["water"] = (
        Ev.Environment["soil_volume"] * 1000.0 * 1000.0 * 0.5
    )

    # Track minimum daily temperatures
    daily_min_temps = []
    day_min_temp = float('inf')
    previous_day_index = 0

    # Run the simulation loop until max_cycles or the plant dies
    while Pl.Plant["alive"] and cycle_count < max_cycles:
        sim_time += 1
        cycle_count += 1

        # Hour in day (0..23) and current day index
        hour_in_day = sim_time % 24
        day_index = sim_time // 24

        # Update environment (temperature, light, rain, etc.)
        Ev.update_environment(sim_time, Ev.Environment)

        # If we moved to a new day, reset the daily minimum temperature
        if day_index != previous_day_index:
            day_min_temp = float('inf')
            #print(day_index)

        current_temp = Ev.Environment["atmos"]["temperature"]
        if current_temp < day_min_temp:
            day_min_temp = current_temp

        # At the end of each day (hour 23), store the day's minimum temperature
        if hour_in_day == 23:
            daily_min_temps.append(day_min_temp)
            # Keep only the last 30 days of records
            if len(daily_min_temps) > 30:
                daily_min_temps.pop(0)

        # Re-initialize daily plant state variables
        Fu.intitialize_state_variables(Pl.Plant)
        Pl.Plant["temperature"]["photo"] = current_temp

        # If a new day has started, handle daily checks
        if day_index != previous_day_index:
            # If stomatal conductance was low in the previous day, adapt water strategy
            last_24_stomatal = Hi.history["stomatal_conductance"][-24:]
            if len(last_24_stomatal) == 24:
                if np.mean(last_24_stomatal) < 0.9:
                    Fu.adapt_water_supply(Pl.Plant, Ev.Environment)
            nutrient_slope = Fu.slope_last_hours(Hi.history["reserve_nutrient"], nb_hours=24 * 3)
            #print(nutrient_slope)
            if nutrient_slope < -1e-9:
                Fu.adapt_nutrient_supply(Pl.Plant)

            # Reset stomatal conductance and leaf angle each day
            Pl.Plant["stomatal_conductance"] = 1.0
            Pl.Plant["leaf_angle"] = 0.0

            # Manage plant phenology (e.g. germination, dormancy, reproduction)
            Fu.manage_phenology(Pl.Plant, Ev.Environment, day_index, daily_min_temps)
            previous_day_index = day_index

        # If still in seed stage, skip photosynthesis and store zeros for diagnostics
        if Pl.Plant["phenology_stage"] == "seed":
            Pl.Plant["diag"]["raw_sugar_flux"] = 0.0
            Pl.Plant["diag"]["pot_sugar"] = 0.0
            Pl.Plant["diag"]["leaf_temperature_after"] = 0.0
            Pl.Plant["diag"]["atmos_temperature"] = current_temp
            Pl.Plant["diag"]["leaf_temperature_before"] = 0.0
            Pl.Plant["diag"]["max_transpiration_capacity"] = 0.0
            Pl.Plant["diag"]["sugar_photo"] = 0.0
            Pl.Plant["diag"]["water_after_transp"] = 0.0
            Pl.Plant["diag"]["stomatal_conductance"] = 0.0

            # Save this state in history, then continue to next cycle
            Hi.history_update(Pl.Plant, Hi.history, Ev.Environment, sim_time)
            continue

        # Optional: environment hazards like wind or insects, if desired
        # Ev.environment_hazards(Pl.Plant, Ev.Environment)

        # 2) Calculate maintenance costs
        Fu.calculate_cost(Pl.Plant, "maintenance")

        # 3) If not dormant and there is light, adjust leaf transpiration parameters
        if (Pl.Plant["phenology_stage"] != "dormancy"
            and Ev.Environment["atmos"]["light"] > 10.0):
            Be.adjust_leaf_params_angle(
                Pl.Plant,
                Ev.Environment,
                alpha=1.0,
                beta=1.0,
                gamma=0.0
            )

        # 4) Soil nutrient absorption
        Fu.nutrient_absorption(Pl.Plant, Ev.Environment)
        #print("photosynthesis estimate before maint.:", Pl.Plant["flux_in"]["sugar"])

        # 5) Pay maintenance (handle_process checks resources and uses them)
        Fu.handle_process(Pl.Plant, Ev.Environment, "maintenance")
        #print("photosynthesis estimate after maint.:", Pl.Plant["flux_in"]["sugar"])

        # Continue with extension / reproduction only if there's enough light
        if Ev.Environment["atmos"]["light"] > 10.0:
            Fu.calculate_potential_new_biomass(Pl.Plant)
            #print("new biomass : ",Pl.Plant["new_biomass"])
            # Calculate extension and reproduction costs
            Fu.calculate_cost(Pl.Plant, "extension")

            # If in reproduction stage
            if Pl.Plant["phenology_stage"] == "reproduction":
                Fu.adapt_for_reproduction(Pl.Plant)

            # If in dessication stage
            if Pl.Plant["phenology_stage"] == "dessication":
                Fu.dessication(Pl.Plant, Ev.Environment, day_index)

            # If in vegetative stage
            if (Pl.Plant["phenology_stage"] == "vegetative" or 
                Pl.Plant["phenology_stage"] == "reproduction"):
                Fu.handle_process(Pl.Plant, Ev.Environment, "extension")
                Fu.update_success_history(Pl.Plant, "extension")

            # Finally, transfer any remaining flux_in to internal reserves
            Fu.refill_reserve(Pl.Plant, "sugar")
            Fu.refill_reserve(Pl.Plant, "nutrient")

        # Check for negative pools or fluxes, stop if it occurs
        stop_now = Fu.check_for_negatives(Pl.Plant, Ev.Environment, sim_time)
        if stop_now:
            break

        # Save current state to history
        Hi.history_update(Pl.Plant, Hi.history, Ev.Environment, sim_time)

        # Check if the plant dies (biomass below threshold)
        if Pl.Plant["biomass_total"] <= 0.005:
            Pl.Plant["alive"] = False

    # Return final results
    return Hi.history, Pl.Plant, Ev.Environment
