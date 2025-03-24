# Environnement_def.py
"""
This module defines and updates the environment (soil, atmosphere, etc.) for the Plantroid model.
Comments are in English, while variable/function names in French are kept to ensure compatibility.
"""

import functions as Fu
import random
import math

# ---------------------------------------------------------------------------
# Default environment structure
# ---------------------------------------------------------------------------
Environment = {
    "soil": {
        "water": 0.0,
        "nutrient": 6000.0
    },
    "litter": {
        "necromass": 0.0,
        "repro": 0.0
    },
    "atmos": {
        "Co2": 1000.0,
        "light": 1000.0,
        "water": 100.0,           # not fully used yet
        "temperature": 25.0,
        "wind": 1.0,
        "RH": 0.5,                # relative humidity (0..1)
        "longwave": 400.0         # incoming longwave radiation (W/m²)
    },

    # Basic parameters for daily/seasonal cycles
    "day_temp_amplitude": 5.0,     # day/night temperature amplitude (°C)
    "seasonal_temp_offset": 10.0,  # seasonal temp offset (±10°C)
    "base_temp": 15.0,             # average annual temperature (°C)

    "base_light": 1000.0,          # peak light in summer (W/m²)
    "seasonal_light_var": 0.5,     # fraction of light variation winter vs summer

    "precipitation_base": 1.9,     # mm of rain per day on average
    "seasonal_rain_var": 0.3,     # fraction for seasonal variation in rain
    "random_factor": 0.3,          # intensity of random weather factor (30%)
    "soil_volume": 1.00            # volume of soil in m³
}


# ---------------------------------------------------------------------------
# Main function: update_environment
# ---------------------------------------------------------------------------
def update_environment(time, Env):
    """
    Updates the environment (Env) according to time in hours, including:
      - annual cycle (seasons)
      - daily cycle (day/night)
      - random weather factor

    Assumptions
    -----------
    - time is an integer representing hours since start of simulation
    - simple sinusoidal patterns for temperature, light, precipitation
    - single location with temperate climate
    """
    # Convert time in hours to day index and hour of day
    day_index = time // 24
    hour_in_day = time % 24
    day_of_year = day_index % 365

    # -----------------------------
    # Seasonal cycle (temperature, light, rainfall)
    # -----------------------------
    # We approximate the peak around day 173 (22 June Northern Hemisphere),
    # so we shift by ~81 days in the sine function.
    # T_season = base_temp + seasonal_temp_offset * sin(2π*(day_of_year - 81)/365)
    seasonal_angle = 2.0 * math.pi * (day_of_year - 81) / 365.0
    T_season = (
        Env["base_temp"]
        + Env["seasonal_temp_offset"] * math.sin(seasonal_angle)
    )

    # Light seasonal factor: from (1 - seasonal_light_var) in winter up to (1 + var) in summer
    light_season_factor = 1.0 + Env["seasonal_light_var"] * math.sin(seasonal_angle)
    if light_season_factor < 0.0:
        light_season_factor = 0.0

    # Seasonal factor for precipitation
    precipitation_season_factor = 1.0 + Env["seasonal_rain_var"] * math.sin(seasonal_angle)

    # -----------------------------
    # Daily cycle (temperature, light)
    # -----------------------------
    # Day/night temperature amplitude is day_temp_amplitude (±5°C default),
    # with a simple sinusoidal shape.
    daily_angle = math.pi * ((hour_in_day / 12.0) - 0.5)
    T_daily = T_season + Env["day_temp_amplitude"] * math.sin(daily_angle)

    # Light model: 6h to 20h is day, zero at night, with a sinus for sunrise/sunset
    # Then scaled by the seasonal light factor
    if 6 <= hour_in_day < 20:
        frac_daytime = (hour_in_day - 6.0) / 14.0
        raw_light = Env["base_light"] * light_season_factor * max(0.0, math.sin(math.pi * frac_daytime))
    else:
        raw_light = 0.0

    # -----------------------------
    # Rain model: random daily event at 6h
    # -----------------------------
    if hour_in_day == 6:
        daily_rain_mean = Env["precipitation_base"] * precipitation_season_factor
        # random_factor => ± 30% of the mean
        daily_rain = daily_rain_mean * (1.0 + Env["random_factor"] * (2.0 * random.random() - 1.0))

        # Convert from mm to grams of water, using soil_volume
        # 1 mm = 1 L/m² => for a certain area, we interpret it as:
        # daily_rain [mm] * 1000 * soil_volume [m³]
        # Simplified approach
        water_max = (Env["soil_volume"] * 1000.0 * 1000.0) * 0.8
        added_water = daily_rain * 1000.0 * Env["soil_volume"]

        if Env["soil"]["water"] < water_max:
            Env["soil"]["water"] += added_water
        Env["rain_event"] = added_water
    else:
        Env["rain_event"] = 0.0

    # -----------------------------
    # Random fluctuations on T and light
    # -----------------------------
    rand_temp = 1.0 + Env["random_factor"] * (2.0 * random.random() - 1.0)
    rand_light = 1.0 + 0.2 * Env["random_factor"] * (2.0 * random.random() - 1.0)

    T_final = T_daily * rand_temp
    light_final = raw_light * rand_light

    # Store results back into the environment dictionary
    Env["atmos"]["temperature"] = T_final
    Env["atmos"]["light"] = max(0.0, light_final)

    # Update CO2 availability
    co2_availability(time, Env)


def co2_availability(time, Env):
    """
    Manages CO2 fluctuations (approx. ~400 to 410 ppm).
    A small sine or random wave can be introduced.
    """
    base_co2 = 400.0
    fluctuation = 10.0 * math.sin(time / 10.0)  # a minor sinus variation
    Env["atmos"]["Co2"] = base_co2 + fluctuation


def calc_daily_photoperiod(day_of_year):
    """
    Returns the day length (hours of light) for a given day_of_year (0..364),
    using a simple sinus-based approach for temperate latitudes.

    Hypothesis
    ----------
    - Amplitude: about ±4h around 12h => day length from 8h (winter) to 16h (summer)
    - We shift by ~81 days to align max with late June.

    Returns
    -------
    float
        The approximate daylight duration in hours.
    """
    seasonal_angle = 2.0 * math.pi * (day_of_year - 81) / 365.0
    base_hours = 12.0
    amplitude = 4.0
    day_length = base_hours + amplitude * math.sin(seasonal_angle)
    # clamp to [0..24]
    return max(0.0, min(24.0, day_length))


def environment_hazards(Plant, Env):
    """
    Random hazards such as strong winds or insects/fungus.

    This function optionally damages some plant biomass.
    The probabilities and damage factors can be adjusted.
    """
    # Wind
    wind_prob = 0.01
    if random.random() < wind_prob:
        damage_photo = 0.001 * Plant["slai"]
        damage_support = 0.001 * ((100 - Plant["health_state"]) / 100.0)
        Fu.destroy_biomass(Plant, Env, "photo", damage_factor=damage_photo, process=None)
        Fu.destroy_biomass(Plant, Env, "support", damage_factor=damage_support, process=None)

    # Insects or fungus
    insect_prob = 0.01
    if random.random() < insect_prob:
        damage_photo = 0.001 * Plant["slai"] * ((100 - Plant["health_state"]) / 100.0)
        damage_absorp = 0.001 * ((100 - Plant["health_state"]) / 100.0)
        Fu.destroy_biomass(Plant, Env, "absorp", damage_factor=damage_absorp, process=None)
        Fu.destroy_biomass(Plant, Env, "photo", damage_factor=damage_photo, process=None)
