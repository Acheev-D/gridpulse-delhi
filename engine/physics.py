from pathlib import Path
from typing import Union
import numpy as np
import polars as pl


def apply_net_load_and_feeders(
    forecast_df: pl.DataFrame,
    feeder_weights_path: Union[str, Path],
    installed_solar_mw: float = 1800.0,
    temp_delta: float = 0.0,
) -> pl.DataFrame:
    """
    Computes derated rooftop solar generation and thermal cooling demand elasticity,
    subtracting solar from gross demand quantiles to compute net load (net_p10, net_p50, net_p90).
    Performs left join on time_block_idx to allocate regional feeder demand
    (BRPL, BYPL, TPDDL).
    """
    effective_temp = pl.col("temperature_2m") + temp_delta
    temp_derate = pl.max_horizontal(
        pl.lit(0.0),
        1.0 - 0.004 * (effective_temp - 25.0)
    )

    solar_expr = (
        pl.lit(installed_solar_mw) * (pl.col("ghi") / 1000.0) * temp_derate
    ).clip(lower_bound=0.0)

    # Ambient temperature cooling load elasticity (~180 MW per °C thermal cooling spike across NCT)
    cooling_shock_mw = pl.lit(temp_delta * 180.0)

    # Calculate solar generation and net demand quantiles
    with_solar = forecast_df.with_columns(
        solar_expr.round(2).alias("solar_generation_mw"),
        (pl.col("gross_p10") + cooling_shock_mw - solar_expr).clip(lower_bound=0.0).round(2).alias("net_p10"),
        (pl.col("gross_p50") + cooling_shock_mw - solar_expr).clip(lower_bound=0.0).round(2).alias("net_p50"),
        (pl.col("gross_p90") + cooling_shock_mw - solar_expr).clip(lower_bound=0.0).round(2).alias("net_p90"),
    )

    # Load feeder weights and left-join on time_block_idx
    feeder_df = pl.read_parquet(feeder_weights_path)
    if feeder_df["time_block_idx"].dtype != with_solar["time_block_idx"].dtype:
        feeder_df = feeder_df.with_columns(
            pl.col("time_block_idx").cast(with_solar["time_block_idx"].dtype)
        )

    joined = with_solar.join(feeder_df, on="time_block_idx", how="left")

    # Normalize weights so sum equals 1.0 across DISCOMs for exact conservation
    total_w = pl.col("weight_brpl") + pl.col("weight_bypl") + pl.col("weight_tpddl")

    # Allocate demand to regional discoms based on net_p50
    result = joined.with_columns(
        (pl.col("net_p50") * (pl.col("weight_brpl") / total_w)).round(2).alias("BRPL"),
        (pl.col("net_p50") * (pl.col("weight_bypl") / total_w)).round(2).alias("BYPL"),
        (pl.col("net_p50") * (pl.col("weight_tpddl") / total_w)).round(2).alias("TPDDL"),
        (pl.col("net_p50") * (pl.col("weight_brpl") / total_w)).round(2).alias("discom_brpl_mw"),
        (pl.col("net_p50") * (pl.col("weight_bypl") / total_w)).round(2).alias("discom_bypl_mw"),
        (pl.col("net_p50") * (pl.col("weight_tpddl") / total_w)).round(2).alias("discom_tpddl_mw"),
    )

    return result


def simulate_bess_dispatch(
    df: pl.DataFrame,
    battery_capacity_mwh: float = 1200.0,
    max_power_mw: float = 400.0,
    shave_threshold_mw: float = 8000.0,
) -> pl.DataFrame:
    """
    Simulates a utility-scale BESS for peak clipping and solar buffering.
    Discharges whenever net_p50 > shave_threshold_mw up to max_power_mw.
    Charges during solar surplus trough (10:00 to 14:00).
    Tracks dynamic state-of-charge (SoC %).

    Returns original DataFrame appended with:
    - 'bess_dispatch_mw': Positive for discharge (clipping), negative for charging.
    - 'post_bess_demand_mw': Clamped operational demand profile.
    - 'bess_soc_pct': Rolling battery charge percentage across 96 blocks.
    """
    n_blocks = df.height
    if n_blocks == 0:
        return df.with_columns([
            pl.lit(0.0).alias("bess_dispatch_mw"),
            pl.lit(0.0).alias("post_bess_demand_mw"),
            pl.lit(50.0).alias("bess_soc_pct"),
        ])

    dt = 0.25  # 15 minutes = 0.25 hours
    min_energy = 0.10 * battery_capacity_mwh  # 10% reserve margin
    max_energy = 1.00 * battery_capacity_mwh
    current_energy = 0.50 * battery_capacity_mwh  # Start day at 50% SoC
    eta_charge = 0.95
    eta_discharge = 0.95

    net_demands = df["net_p50"].to_numpy()
    hours = df["timestamp"].dt.hour().to_numpy()

    dispatch_mw = np.zeros(n_blocks, dtype=np.float64)
    soc_pct = np.zeros(n_blocks, dtype=np.float64)

    for i in range(n_blocks):
        net_d = net_demands[i]
        hr = hours[i]
        p_disp = 0.0

        # Peak Shaving Dispatch
        if net_d > shave_threshold_mw:
            needed = net_d - shave_threshold_mw
            max_discharge_avail = max(0.0, (current_energy - min_energy) * eta_discharge / dt)
            p_discharge = min(needed, max_power_mw, max_discharge_avail)
            p_disp = p_discharge
            energy_drawn = (p_discharge / eta_discharge) * dt
            current_energy = max(min_energy, current_energy - energy_drawn)

        # Midday Solar Absorption Charging (10:00 - 14:00 IST)
        elif 10 <= hr < 14 and current_energy < max_energy:
            max_charge_avail = (max_energy - current_energy) / (dt * eta_charge)
            p_charge = min(max_power_mw * 0.75, max_charge_avail)
            p_disp = -p_charge
            energy_stored = p_charge * dt * eta_charge
            current_energy = min(max_energy, current_energy + energy_stored)

        dispatch_mw[i] = p_disp
        soc_pct[i] = (current_energy / battery_capacity_mwh) * 100.0

    post_bess = np.round(net_demands - dispatch_mw, 2)
    dispatch_mw = np.round(dispatch_mw, 2)
    soc_pct = np.round(soc_pct, 1)

    return df.with_columns([
        pl.Series("bess_dispatch_mw", dispatch_mw),
        pl.Series("post_bess_demand_mw", post_bess),
        pl.Series("bess_soc_pct", soc_pct),
    ])
