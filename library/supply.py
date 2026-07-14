import logging
from library.helpers import fetch_grist_data
from library.classes import PowerModelInput, PowerModelResult, PowerModelRow
import numpy as np
import pandas as pd


def assign_users(df, total_potential_users):
    df = df.copy()
    df["assigned_users"] = 0
    df["_row_order"] = np.arange(len(df))

    # Sort by cost, then original order
    df = df.sort_values(["cost_per_passing", "_row_order"])

    remaining = int(round(total_potential_users))

    for cost, grp in df.groupby("cost_per_passing", sort=False):
        idx = grp.index
        capacities = grp["users_supported"].to_numpy()
        tier_capacity = capacities.sum()

        if remaining <= 0:
            break

        # Case 1: fill entire tier
        if remaining >= tier_capacity:
            df.loc[idx, "assigned_users"] = capacities
            remaining -= tier_capacity
            continue

        # Case 2: partial fill of this tier
        n = len(grp)

        # Sub-case A: equal capacities
        if np.all(capacities == capacities[0]):
            base = remaining // n
            rem = int(remaining % n)
            alloc = np.full(n, int(base))
            alloc[:rem] += 1

        # Sub-case B: proportional allocation
        else:
            alloc = np.floor(
                remaining * capacities / tier_capacity
            ).astype(int)

            shortfall = int(remaining - alloc.sum())
            if shortfall > 0:
                alloc[:shortfall] += 1

        # Cap allocations
        alloc = np.minimum(alloc, capacities)

        df.loc[idx, "assigned_users"] = alloc
        remaining -= alloc.sum()
        break  # bin exhausted

    return (
        df
        .drop(columns="_row_order")
        .sort_index()
    )


def apply_cpe_costs(df):
    df = df.copy()
    if "access_capex" in df.columns:
        df["access_capex"] = df["access_capex"].astype(float)
    mask = (df["cpe_cost"] != 0) & (df["assigned_users"] != 0)
    if "users_per_ue" in df.columns:
        df.loc[mask, "access_capex"] += round(df.loc[mask, "cpe_cost"] * (df.loc[mask, "assigned_users"] / df.loc[mask, "users_per_ue"]), 2)
    else:
        df.loc[mask, "access_capex"] += round(df.loc[mask, "cpe_cost"] * df.loc[mask, "assigned_users"], 2)
    return df


def power_model(input_data: PowerModelInput) -> PowerModelResult:
    logging.info("Entered the power model")

    # Get variables from the input data
    location = input_data.location
    latitude = input_data.latitude
    longitude = input_data.longitude
    logging.info(f"lat & long: {latitude}, {longitude}")
    power_reliable_hours = input_data.power_reliable_hours
    power_required = input_data.power_required
    system_life = input_data.system_life
    battery_cost_watt_hour = input_data.battery_cost_watt_hour
    charger_inverter_base = input_data.charger_inverter_base
    charger_inverter_variable = input_data.charger_inverter_variable
    mains_power_cost_kwh = input_data.mains_power_cost_kwh
    mains_power_installation_cost = input_data.mains_power_installation_cost
    solar_cost_watt = input_data.solar_cost_watt
    power_intermittent_hours = input_data.power_intermittent_hours
    power_hybrid_hours = input_data.power_hybrid_hours
    system_type = input_data.system_type
    collection_w_day_m2 = None
    panels_needed_m2 = None
    solar_cost = 0.0
    power_capex = 0
    power_opex = 0

    query_name = "solarstats_query"
    sql_query = """
        SELECT
        location, iso_2, latitude, longitude, min_sun, max_no_sun_days, annual_no_sun_days, avg_temp, min_temp, max_temp
        FROM solarstats
        where latitude = {}
        and longitude = {}
        """.format(latitude, longitude)

    # Fetch Data
    logging.info(f'running the db query')
    try:
        data = fetch_grist_data(sql_query)
    except Exception as e:
        logging.info(f"Failed to load {query_name} data: {str(e)}")
        raise
    if not data:
        raise ValueError(f"No solar statistics found for latitude={latitude}, longitude={longitude}")

    min_sun = float(data[0]["min_sun"])
    max_no_sun_days = float(data[0]["max_no_sun_days"])
    annual_no_sun_days = float(data[0]["annual_no_sun_days"])
    min_temp = float(data[0]["min_temp"])
    solar_efficiency = input_data.solar_efficiency / 100
    solar_derating = input_data.solar_derating / 100
    battery_age_derating = input_data.battery_age_derating / 100
    battery_dod = input_data.battery_dod / 100
    logging.info(f'extracted results from the db query')

    # Cold derating calculation
    def calculate_cold_derating(_min_temp):
        if _min_temp <= -20:
            return 65
        elif -20 < _min_temp <= -10:
            return 1.5 * _min_temp + 95
        elif -10 < _min_temp <= 0:
            return _min_temp + 90
        elif 0 < _min_temp <= 10:
            return 0.7 * _min_temp + 90
        elif 10 < _min_temp <= 20:
            return 0.3 * _min_temp + 94
        else:
            return 100

    if system_type == "power_mains_rel":
        adjusted_hours = power_reliable_hours
        base_battery = power_required * adjusted_hours * battery_dod
        aged_battery = base_battery / ((1 - battery_age_derating) ** system_life)
        cold_derating = calculate_cold_derating(min_temp)
        battery_required = aged_battery / (cold_derating / 100)
        battery_cost = battery_required * battery_cost_watt_hour
        charger_cost = charger_inverter_base + (power_required * charger_inverter_variable)
        power_opex = (mains_power_cost_kwh / 1000) * power_required * 24 * 365 * system_life
        power_capex = battery_cost + charger_cost + mains_power_installation_cost

    elif system_type == "power_mains_int":
        adjusted_hours = power_intermittent_hours
        base_battery = power_required * adjusted_hours * battery_dod
        aged_battery = base_battery / ((1 - battery_age_derating) ** system_life)
        cold_derating = calculate_cold_derating(min_temp)
        battery_required = aged_battery / (cold_derating / 100)
        battery_cost = battery_required * battery_cost_watt_hour
        charger_cost = charger_inverter_base + (power_required * charger_inverter_variable)
        power_opex = (mains_power_cost_kwh / 1000) * power_required * 24 * 365 * system_life
        power_capex = battery_cost + charger_cost + mains_power_installation_cost

    elif system_type == "power_hybrid":
        adjusted_hours = power_hybrid_hours
        base_battery = power_required * adjusted_hours * battery_dod
        aged_battery = base_battery / ((1 - battery_age_derating) ** system_life)
        cold_derating = calculate_cold_derating(min_temp)
        battery_required = aged_battery / (cold_derating / 100)
        solar_watts_needed = power_required * adjusted_hours
        irradiance_w_day_m2 = min_sun * 1000
        collection_w_day_m2 = irradiance_w_day_m2 * (solar_efficiency * ((1 - solar_derating) ** system_life))
        panels_needed_m2 = solar_watts_needed / collection_w_day_m2
        panel_watts_per_m2 = solar_efficiency * 1350
        panel_watts_needed = panels_needed_m2 * panel_watts_per_m2
        panel_cost = panel_watts_per_m2 * solar_cost_watt
        solar_cost = panels_needed_m2 * panel_cost
        battery_cost = battery_required * battery_cost_watt_hour
        charger_cost = charger_inverter_base + (panel_watts_needed * charger_inverter_variable)
        power_opex = (mains_power_cost_kwh / 1000) * power_required * 24 * annual_no_sun_days * system_life
        power_capex = battery_cost + charger_cost + mains_power_installation_cost

    elif system_type == "power_solar":
        power_opex = 0
        mains_power_installation_cost = 0
        adjusted_hours = max_no_sun_days * 24
        base_battery = power_required * adjusted_hours * battery_dod
        aged_battery = base_battery / ((1 - battery_age_derating) ** system_life)
        cold_derating = calculate_cold_derating(min_temp)
        battery_required = aged_battery / (cold_derating / 100)
        solar_watts_needed = power_required * adjusted_hours
        irradiance_w_day_m2 = min_sun * 1000
        collection_w_day_m2 = irradiance_w_day_m2 * (solar_efficiency * ((1 - solar_derating) ** system_life))
        panels_needed_m2 = solar_watts_needed / collection_w_day_m2
        panel_watts_per_m2 = solar_efficiency * 1350
        panel_watts_needed = panels_needed_m2 * panel_watts_per_m2
        panel_cost = panel_watts_per_m2 * solar_cost_watt
        solar_cost = panels_needed_m2 * panel_cost
        battery_cost = battery_required * battery_cost_watt_hour
        charger_cost = charger_inverter_base + (panel_watts_needed * charger_inverter_variable)
        power_capex = battery_cost + charger_cost + solar_cost
    else:
        raise ValueError(f"Unsupported power system type: {system_type}")

    power_row = PowerModelRow(
        location_name=location.location_name,
        system_type=system_type,
        latitude=latitude,
        longitude=longitude,
        power_required=round(float(power_required), 2),
        system_life=system_life,
        solar_cost_watt=solar_cost_watt,
        solar_derating=input_data.solar_derating,
        solar_efficiency=input_data.solar_efficiency,
        battery_age_derating=input_data.battery_age_derating,
        battery_cost_watt_hour=battery_cost_watt_hour,
        battery_dod=input_data.battery_dod,
        charger_inverter_base=charger_inverter_base,
        charger_inverter_variable=charger_inverter_variable,
        mains_power_cost_kwh=mains_power_cost_kwh,
        mains_power_installation_cost=mains_power_installation_cost,
        power_hybrid_hours=power_hybrid_hours,
        power_intermittent_hours=power_intermittent_hours,
        power_reliable_hours=power_reliable_hours,
        min_daily_sun_wm2=round(min_sun, 2),
        max_no_sun_days=round(max_no_sun_days, 2),
        annual_no_sun_days=round(annual_no_sun_days, 2),
        min_temp_c=round(min_temp, 2),
        adjusted_hours=round(float(adjusted_hours), 2),
        battery_required=round(float(battery_required), 2),
        battery_cost=round(float(battery_cost), 2),
        charger_cost=round(float(charger_cost), 2),
        power_opex=round(float(power_opex), 2),
        watts_day_m2=round(float(collection_w_day_m2), 2) if collection_w_day_m2 is not None else None,
        panels_need_m2=round(float(panels_needed_m2), 2) if panels_needed_m2 is not None else None,
        solar_cost=round(float(solar_cost), 2),
        power_capex=round(float(power_capex), 2),
    )

    logging.info("Power model result row: %s", power_row.model_dump())

    return PowerModelResult(
        power_capex=round(float(power_capex), 2),
        power_opex=round(float(power_opex), 2),
        power_row=power_row,
    )
