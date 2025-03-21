# run_and_plot_v2.py

"""
This module runs a Plantroid simulation and produces daily-aggregated plots
for both day and night data, using calendar dates on the X-axis.
It also draws vertical lines to indicate phenology stage changes (if present).

All comments/docstrings are in English; function/variable names remain in French
for compatibility with the other parts of the Plantroid model.
"""

import matplotlib.pyplot as plt
import time_loop as Ti
import global_constants as Gl
import Plant_def as Pl

from datetime import datetime, timedelta
import matplotlib.dates as mdates


def aggregate_day_night(history, threshold_light=1.0):
    """
    Aggregates the simulation history into two sets of daily data: day vs night.
    If history["time"] stores hours (0..N), we compute total_days = (max_time//24)+1.
    Each day's daytime data is averaged over hours with atmos_light > threshold_light,
    while nighttime data is for hours below that threshold.

    Parameters
    ----------
    history : dict
        The simulation history, with keys like "time", "atmos_light", "biomass_total", etc.
        Optionally, it may contain non-numeric fields such as "phenology_stage".
    threshold_light : float
        The luminosity threshold above which we consider it daytime.

    Returns
    -------
    (day_data, night_data) : tuple of dict
        Each dict contains aggregated data for day vs night.
        day_data["time"] = [1..total_days].
        If a value is numeric, we average it; if it's a string, we overwrite
        with the last encountered value in that day segment.
    """
    day_data = {}
    night_data = {}

    total_points = len(history["time"])
    if total_points == 0:
        return day_data, night_data

    # If "time" is in hours, we figure out how many days we have
    max_time = max(history["time"])
    total_days = (max_time // 24) + 1

    # Prepare lists
    for key in history:
        # If the stored values are numeric, init with 0.0
        # If they are strings, we init with "" so we can store last state
        if isinstance(history[key][0], (int, float)):
            day_data[key] = [0.0] * total_days
            night_data[key] = [0.0] * total_days
        else:
            # e.g. phenology_stage
            day_data[key] = [""] * total_days
            night_data[key] = [""] * total_days

    day_counts = [0] * total_days
    night_counts = [0] * total_days

    for i in range(total_points):
        hour = history["time"][i]  # e.g. 0.., in hours
        day_index = hour // 24
        atm_light = history["atmos_light"][i]
        is_day = (atm_light > threshold_light)

        for key in history:
            val = history[key][i]
            if isinstance(val, (int, float)):
                # Accumulate numeric data
                if is_day:
                    day_data[key][day_index] += val
                else:
                    night_data[key][day_index] += val
            else:
                # Non-numeric, e.g. string
                if is_day:
                    day_data[key][day_index] = val
                else:
                    night_data[key][day_index] = val

        if is_day:
            day_counts[day_index] += 1
        else:
            night_counts[day_index] += 1

    # Average the numeric fields
    for key in history:
        for d in range(total_days):
            if isinstance(day_data[key][d], (int, float)) and day_counts[d] > 0:
                day_data[key][d] /= day_counts[d]
            if isinstance(night_data[key][d], (int, float)) and night_counts[d] > 0:
                night_data[key][d] /= night_counts[d]

    # The "time" array: 1.. total_days
    day_data["time"] = list(range(1, total_days + 1))
    night_data["time"] = list(range(1, total_days + 1))

    return day_data, night_data


def simulate_and_plot(species_name, start_date=datetime(2025, 1, 1)):
    """
    Runs the Plantroid simulation for a given species, aggregates data
    (day vs night), and creates two figures:
      - day_fig (5×4 subplots)
      - night_fig (7×3 subplots)
    with a date-based X-axis. Also shows vertical lines for phenology stage changes.

    Parameters
    ----------
    species_name : str
        The plant species name (key in Plant_def.species_db).
    start_date : datetime
        The real-world date corresponding to day=1 of the simulation.
    """
    # 1) Setup species and run the simulation
    Pl.set_plant_species(Pl.Plant, species_name, Pl.species_db)
    data, final_plant, final_env = Ti.run_simulation_collect_data(Gl.max_cycles)

    # 2) Aggregate data (day vs night)
    day_data, night_data = aggregate_day_night(data)

    # 3) Convert day indices => real calendar dates
    day_date_list = [start_date + timedelta(days=int(d - 1)) for d in day_data["time"]]
    night_date_list = [start_date + timedelta(days=int(d - 1)) for d in night_data["time"]]

    ########################################################################
    #                      PART A : DAY FIGURE (5×4)                        #
    ########################################################################
    day_fig, day_axes = plt.subplots(nrows=5, ncols=4, figsize=(65, 35),
                                     gridspec_kw=dict(hspace=0.3, wspace=0.2,
                                                      top=0.96, right=0.96,
                                                      left=0.03, bottom=0.05))
    day_fig.suptitle(f"Résultats (Jour) - {species_name}", fontsize=16)

    # ------------------------------------------------------------------
    # Row 0
    # ------------------------------------------------------------------
    # (0,0) Biomasse vivante vs nécromasse vs max
    ax = day_axes[0, 0]
    ax.plot(day_date_list, day_data["biomass_total"], label="Biomasse", color="green")
    ax.plot(day_date_list, day_data["biomass_necromass"], label="Nécromasse", color="brown")
    if "max_biomass" in day_data:
        ax.plot(day_date_list, day_data["max_biomass"], label="Théorique", color="black", linestyle="dotted")
    ax.set_xlabel("Date")
    ax.set_ylabel("Biomasse (g)")
    ax.set_title("Évolution : vivante vs nécromasse")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (0,1) Compartiments vivants
    ax = day_axes[0, 1]
    ax.plot(day_date_list, day_data["biomass_support"], label="Support", color="brown")
    ax.plot(day_date_list, day_data["biomass_photo"], label="Photo", color="green")
    ax.plot(day_date_list, day_data["biomass_absorp"], label="Absorp", color="blue")
    ax.plot(day_date_list, day_data["biomass_repro"], label="Repro", color="violet")
    ax.set_xlabel("Date")
    ax.set_ylabel("Biomasse (g)")
    ax.set_title("Compartiments vivants")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (0,2) eau du sol
    ax = day_axes[0, 2]
    ax.plot(day_date_list, day_data["soil_water"], color="blue")
    ax.set_xlabel("Date")
    ax.set_ylabel("Eau sol (g)")
    ax.set_title("Réserve d'eau sol")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (0,3) Santé
    ax = day_axes[0, 3]
    ax.plot(day_date_list, day_data["health_state"])
    ax.set_xlabel("Date")
    ax.set_ylabel("Santé (0..100)")
    ax.set_title("État de santé")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # ------------------------------------------------------------------
    # Row 1
    # ------------------------------------------------------------------
    # (1,0) actual_sugar
    ax = day_axes[1, 0]
    ax.plot(day_date_list, day_data["actual_sugar"], label="Sucre dispo", color="orange")
    ax.set_xlabel("Date")
    ax.set_ylabel("g sucre / heure")
    ax.set_title("Photosynthèse nette")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (1,1) Réserves : sugar, water
    ax = day_axes[1, 1]
    ax.plot(day_date_list, day_data["reserve_sugar"], label="Sucre", color="orange")
    ax.plot(day_date_list, day_data["reserve_water"], label="Eau", color="blue")
    ax.set_xlabel("Date")
    ax.set_ylabel("Réserves (g)")
    ax.set_title("Réserves internes")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (1,2) Réserves : nutriment
    ax = day_axes[1, 2]
    ax.plot(day_date_list, day_data["reserve_nutrient"], label="Nutriments", color="green")
    ax.set_xlabel("Date")
    ax.set_ylabel("Réserves (g)")
    ax.set_title("Réserves internes")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (1,3) Température atmos vs feuille
    ax = day_axes[1, 3]
    ax.plot(day_date_list, day_data["atmos_temperature"], label="Tair")
    ax.plot(day_date_list, day_data["leaf_temperature_after"], label="Tfeuille")
    ax.set_xlabel("Date")
    ax.set_ylabel("Température (°C)")
    ax.set_title("Température foliaire")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # ------------------------------------------------------------------
    # Row 2
    # ------------------------------------------------------------------
    # (2,0) Stomates / angle / nutrient_index
    ax = day_axes[2, 0]
    ax.plot(day_date_list, day_data["stomatal_conductance"], label="gs")
    ax.plot(day_date_list, day_data["leaf_angle"], label="angle")
    ax.plot(day_date_list, day_data["nutrient_index"], label="nutrient_index")
    ax.set_xlabel("Date")
    ax.set_ylabel("Index (0..1)")
    ax.set_title("Régulation stomates / angle / nutriment")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (2,1) reserve_used
    ax = day_axes[2, 1]
    ax.plot(day_date_list, day_data["reserve_used_maintenance"], label="Maint.", color="orange")
    ax.plot(day_date_list, day_data["reserve_used_extension"], label="Ext.", color="green")
    ax.plot(day_date_list, day_data["reserve_used_reproduction"], label="Repr.", color="violet")
    ax.set_xlabel("Date")
    ax.set_ylabel("0 ou 1")
    ax.set_title("reserve_used (bool)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (2,2) max_transpiration_capacity
    ax = day_axes[2, 2]
    ax.plot(day_date_list, day_data["max_transpiration_capacity"], label="Max capacity", color="blue")
    ax.set_xlabel("Date")
    ax.set_ylabel("H2O (g/heure)")
    ax.set_title("Détails Transpiration")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (2,3) raw_sugar_flux, pot_sugar
    ax = day_axes[2, 3]
    ax.plot(day_date_list, day_data["raw_sugar_flux"], label="Flux brut")
    ax.plot(day_date_list, day_data["pot_sugar"], label="Flux potentiel")
    ax.set_xlabel("Date")
    ax.set_ylabel("Flux photosynthèse")
    ax.set_title("Détails Photosynthèse")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # ------------------------------------------------------------------
    # Row 3
    # ------------------------------------------------------------------
    # (3,0) atmos_light
    ax = day_axes[3, 0]
    ax.plot(day_date_list, day_data["atmos_light"], label="Lumière", color="yellow")
    ax.set_xlabel("Date")
    ax.set_ylabel("Luminosité (W/m²)")
    ax.set_title("Luminosité atmosphérique")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (3,1) adjusted_used
    ax = day_axes[3, 1]
    ax.plot(day_date_list, day_data["adjusted_used_maintenance"], label="Maint.", color="orange")
    ax.plot(day_date_list, day_data["adjusted_used_extension"], label="Ext.", color="green")
    ax.plot(day_date_list, day_data["adjusted_used_reproduction"], label="Repr.", color="violet")
    ax.plot(day_date_list, day_data["adjusted_used_transpiration"], label="Transp.", color="blue")
    ax.set_xlabel("Date")
    ax.set_ylabel("0 ou 1")
    ax.set_title("adjusted_used (bool)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (3,2) ratios d'allocation
    ax = day_axes[3, 2]
    ax.plot(day_date_list, day_data["ratio_support"], label="support", color="brown")
    ax.plot(day_date_list, day_data["ratio_photo"], label="photo", color="green")
    ax.plot(day_date_list, day_data["ratio_absorp"], label="absorp", color="blue")
    ax.plot(day_date_list, day_data["ratio_repro"], label="repro", color="violet")
    ax.set_xlabel("Date")
    ax.set_ylabel("Ratios")
    ax.set_title("Ratios d’allocation")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (3,3) success_extension, success_reproduction
    ax = day_axes[3, 3]
    ax.plot(day_date_list, day_data["success_extension"], label="Extension", color="green")
    ax.plot(day_date_list, day_data["success_reproduction"], label="Reproduction", color="violet")
    ax.set_xlabel("Date")
    ax.set_ylabel("Succès (0..1)")
    ax.set_title("Succès des processus")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # ------------------------------------------------------------------
    # Row 4
    # ------------------------------------------------------------------
    # (4,0) cost_transpiration_water
    ax = day_axes[4, 0]
    ax.plot(day_date_list, day_data["cost_transpiration_water"], label="Eau (Transp.)", color="blue")
    ax.set_xlabel("Date")
    ax.set_ylabel("Coût (g)")
    ax.set_title("Processus transpiration")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (4,1) cost_maintenance_sugar
    ax = day_axes[4, 1]
    ax.plot(day_date_list, day_data["cost_maintenance_sugar"], label="Maintenance (Sucre)", color="orange")
    ax.set_xlabel("Date")
    ax.set_ylabel("Coût (g)")
    ax.set_title("Processus maintenance")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (4,2) cost_extension_sugar/water/nutrient
    ax = day_axes[4, 2]
    ax.plot(day_date_list, day_data["cost_extension_sugar"], label="Ext. (Sucre)", color="orange")
    ax.plot(day_date_list, day_data["cost_extension_water"], label="Ext. (Eau)", color="blue")
    ax.plot(day_date_list, day_data["cost_extension_nutrient"], label="Ext. (Nutr.)", color="green")
    ax.set_xlabel("Date")
    ax.set_ylabel("Coût (g)")
    ax.set_title("Processus extension")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (4,3) cost_reproduction_sugar/water/nutrient
    ax = day_axes[4, 3]
    ax.plot(day_date_list, day_data["cost_reproduction_sugar"], label="Repro (Sucre)", color="orange")
    ax.plot(day_date_list, day_data["cost_reproduction_water"], label="Repro (Eau)", color="blue")
    ax.plot(day_date_list, day_data["cost_reproduction_nutrient"], label="Repro (Nutr.)", color="green")
    ax.set_xlabel("Date")
    ax.set_ylabel("Coût (g)")
    ax.set_title("Processus reproduction")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # Lignes verticales : changements de stade phénologique (jour)
    if "phenology_stage" in day_data:
        phen_stages_day = day_data["phenology_stage"]
        changes_day = []
        for i in range(1, len(phen_stages_day)):
            if phen_stages_day[i] != phen_stages_day[i - 1]:
                changes_day.append(i)

        for idx_change in changes_day:
            x_val = day_date_list[idx_change]
            new_stage = phen_stages_day[idx_change]
            for row in range(5):
                for col in range(4):
                    axc = day_axes[row, col]
                    axc.axvline(x_val, color='grey', linestyle='--', alpha=0.7)
                    ymax = axc.get_ylim()[1]
                    if row > 0 or col > 0:
                        pass
                    else :
                        axc.text(x_val, ymax * 0.2, new_stage, rotation=90,
                             color='grey', ha='right', va='bottom')

    day_fig.autofmt_xdate(rotation=45)
    day_fig.tight_layout()

    ########################################################################
    #                      PART B : NIGHT FIGURE (7×3)                      #
    ########################################################################
    night_fig, night_axes = plt.subplots(nrows=7, ncols=3, figsize=(15, 35))
    night_fig.suptitle(f"Résultats (Nuit) - {species_name}", fontsize=16)

    # ------------------------------------------------------------------
    # Row 0
    # ------------------------------------------------------------------
    # (0,0) Biomasse totale
    ax = night_axes[0, 0]
    ax.plot(night_date_list, night_data["biomass_total"], color="green")
    ax.set_xlabel("Date")
    ax.set_ylabel("Biomasse totale (g)")
    ax.set_title("Biomasse totale (nuit)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (0,1) support, photo, absorp
    ax = night_axes[0, 1]
    ax.plot(night_date_list, night_data["biomass_support"], label="support", color="brown")
    ax.plot(night_date_list, night_data["biomass_photo"], label="photo", color="green")
    ax.plot(night_date_list, night_data["biomass_absorp"], label="absorp", color="blue")
    ax.set_xlabel("Date")
    ax.set_ylabel("Biomasse (g)")
    ax.set_title("Compartiments (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (0,2) SLAI
    ax = night_axes[0, 2]
    ax.plot(night_date_list, night_data["slai"])
    ax.set_xlabel("Date")
    ax.set_ylabel("SLAI")
    ax.set_title("Surface Foliaire (nuit)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # ------------------------------------------------------------------
    # Row 1
    # ------------------------------------------------------------------
    # (1,0) Santé
    ax = night_axes[1, 0]
    ax.plot(night_date_list, night_data["health_state"])
    ax.set_xlabel("Date")
    ax.set_ylabel("Santé (0..100)")
    ax.set_title("État de santé (nuit)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (1,1) Flux entrants
    ax = night_axes[1, 1]
    ax.plot(night_date_list, night_data["sugar_in"], label="sugar_in")
    ax.plot(night_date_list, night_data["water_in"], label="water_in")
    ax.plot(night_date_list, night_data["nutrient_in"], label="nutrient_in")
    ax.set_xlabel("Date")
    ax.set_ylabel("Flux entrants (g)")
    ax.set_title("Flux entrants (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (1,2) (pas clairement défini dans la version d'origine => vous pouvez laisser vide ou rajouter un plot)
    # On laisse un exemple "vide"
    night_axes[1, 2].axis("off")

    # ------------------------------------------------------------------
    # Row 2
    # ------------------------------------------------------------------
    # (2,0) pas clairement défini dans l'original => on laisse vide
    night_axes[2, 0].axis("off")

    # (2,1) Réserves sugar, water
    ax = night_axes[2, 1]
    ax.plot(night_date_list, night_data["reserve_sugar"], label="Sucre", color="orange")
    ax.plot(night_date_list, night_data["reserve_water"], label="Eau", color="blue")
    ax.set_xlabel("Date")
    ax.set_ylabel("Réserves (g)")
    ax.set_title("Réserves internes (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (2,2) Réserve nutriment
    ax = night_axes[2, 2]
    ax.plot(night_date_list, night_data["reserve_nutrient"], label="Nutriments", color="green")
    ax.set_xlabel("Date")
    ax.set_ylabel("Réserves (g)")
    ax.set_title("Réserves internes (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # ------------------------------------------------------------------
    # Row 3
    # ------------------------------------------------------------------
    # (3,0) Tair, Tfeuille
    ax = night_axes[3, 0]
    ax.plot(night_date_list, night_data["atmos_temperature"], label="Tair")
    ax.plot(night_date_list, night_data["leaf_temperature_after"], label="Tfeuille")
    ax.set_xlabel("Date")
    ax.set_ylabel("Température (°C)")
    ax.set_title("Température foliaire (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (3,1) stomatal_conductance
    ax = night_axes[3, 1]
    ax.plot(night_date_list, night_data["stomatal_conductance"])
    ax.set_xlabel("Date")
    ax.set_ylabel("Conductance (0..1)")
    ax.set_title("Stomates (nuit)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (3,2) success_extension, success_reproduction
    ax = night_axes[3, 2]
    ax.plot(night_date_list, night_data["success_extension"], label="Extension", color="green")
    ax.plot(night_date_list, night_data["success_reproduction"], label="Reproduction", color="violet")
    ax.set_xlabel("Date")
    ax.set_ylabel("Succès (0..1)")
    ax.set_title("Succès des processus (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # ------------------------------------------------------------------
    # Row 4
    # ------------------------------------------------------------------
    # (4,0) max_transpiration_capacity
    ax = night_axes[4, 0]
    ax.plot(night_date_list, night_data["max_transpiration_capacity"], label="Max capacity", color="blue")
    ax.set_xlabel("Date")
    ax.set_ylabel("H2O (g/nuit)")
    ax.set_title("Détails Transpiration (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (4,1) raw_sugar_flux, pot_sugar
    ax = night_axes[4, 1]
    ax.plot(night_date_list, night_data["raw_sugar_flux"], label="Flux brut", color="orange")
    ax.plot(night_date_list, night_data["pot_sugar"], label="Flux potentiel", color="red")
    ax.set_xlabel("Date")
    ax.set_ylabel("Flux photosynthèse")
    ax.set_title("Détails Photosynthèse (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (4,2) axis off
    night_axes[4, 2].axis("off")

    # ------------------------------------------------------------------
    # Row 5
    # ------------------------------------------------------------------
    # (5,0) atmos_light
    ax = night_axes[5, 0]
    ax.plot(night_date_list, night_data["atmos_light"], label="Lumière")
    ax.set_xlabel("Date")
    ax.set_ylabel("Luminosité (W/m²)")
    ax.set_title("Luminosité atmosphérique (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (5,1) rain_event
    ax = night_axes[5, 1]
    ax.plot(night_date_list, night_data["rain_event"], label="Pluie (somme/nuit)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Pluie (g eau/nuit)")
    ax.set_title("Événement de pluie (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (5,2) axis off
    night_axes[5, 2].axis("off")

    # ------------------------------------------------------------------
    # Row 6
    # ------------------------------------------------------------------
    # (6,0) reserve_used_maintenance, extension, reproduction
    ax = night_axes[6, 0]
    ax.plot(night_date_list, night_data["reserve_used_maintenance"], label="Maint.", color="brown")
    ax.plot(night_date_list, night_data["reserve_used_extension"], label="Ext.", color="orange")
    ax.plot(night_date_list, night_data["reserve_used_reproduction"], label="Repr.", color="violet")
    ax.set_xlabel("Date")
    ax.set_ylabel("0 ou 1")
    ax.set_title("reserve_used (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (6,1) adjusted_used_maintenance, extension, reproduction
    ax = night_axes[6, 1]
    ax.plot(night_date_list, night_data["adjusted_used_maintenance"], label="Maint.", color="brown")
    ax.plot(night_date_list, night_data["adjusted_used_extension"], label="Ext.", color="orange")
    ax.plot(night_date_list, night_data["adjusted_used_reproduction"], label="Repr.", color="violet")
    ax.set_xlabel("Date")
    ax.set_ylabel("0 ou 1")
    ax.set_title("adjusted_used (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # (6,2) ratio_support, ratio_photo, ratio_absorp, stress_sugar, stress_water
    ax = night_axes[6, 2]
    ax.plot(night_date_list, night_data["ratio_support"], label="support", color="brown")
    ax.plot(night_date_list, night_data["ratio_photo"], label="photo", color="green")
    ax.plot(night_date_list, night_data["ratio_absorp"], label="absorp", color="blue")
    ax.plot(night_date_list, night_data["stress_sugar"], label="stress_sugar", linestyle="--", color="orange")
    ax.plot(night_date_list, night_data["stress_water"], label="stress_water", linestyle="--", color="red")
    ax.set_xlabel("Date")
    ax.set_ylabel("Ratios / Stress")
    ax.set_title("Ratios & Stress (nuit)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))

    # Lignes verticales : changements de stade phénologique (nuit)
    if "phenology_stage" in night_data:
        phen_stages_n = night_data["phenology_stage"]
        changes_n = []
        for i in range(1, len(phen_stages_n)):
            if phen_stages_n[i] != phen_stages_n[i-1]:
                changes_n.append(i)

        for idx_change in changes_n:
            x_val = night_date_list[idx_change]
            new_stage = phen_stages_n[idx_change]
            for row in range(7):
                for col in range(3):
                    axc = night_axes[row, col]
                    axc.axvline(x_val, color='red', linestyle='--', alpha=0.7)
                    ymax = axc.get_ylim()[1]
                    axc.text(x_val, ymax * 0.9, new_stage, rotation=90,
                             color='red', ha='right', va='bottom')

    night_fig.autofmt_xdate(rotation=45)
    night_fig.tight_layout()

    # Display both figures
    plt.show()


if __name__ == "__main__":
    # Example usage: 
    # You can specify the real start date for day 1,
    # e.g. 1 Jan 2025
    simulate_and_plot("ble", start_date=datetime(2025, 1, 1))
