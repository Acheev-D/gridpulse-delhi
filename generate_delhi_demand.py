from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import polars as pl

OUTPUT_DIR = Path('data')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_LOAD_MW = 4100.0
CDD_THRESHOLD_C = 24.0
LINEAR_COOLING_COEFF = 180.0
NONLINEAR_COOLING_EXP = 1.35
INSTALLED_SOLAR_MW = 1400.0

def build_offline_weather_and_demand():
    start = datetime(2023, 5, 1, 0, 0)
    total_blocks = 61 * 96
    timestamps = [start + timedelta(minutes=15 * i) for i in range(total_blocks)]
    ts_series = pl.Series('timestamp', timestamps)

    hours = ts_series.dt.hour().to_numpy() + (ts_series.dt.minute().to_numpy() / 60.0)
    weekdays = ts_series.dt.weekday().to_numpy()
    time_block_indices = (ts_series.dt.hour() * 4 + ts_series.dt.minute() // 15).to_numpy()

    np.random.seed(42)

    diurnal_temp = 32.0 + 11.5 * np.sin((hours - 8.0) * np.pi / 12.0)
    ambient_temp = np.clip(diurnal_temp + np.random.normal(0, 1.2, total_blocks), 26.0, 47.5)
    humidity = np.clip(55.0 - (ambient_temp - 30.0) * 2.2 + np.random.normal(0, 3.0, total_blocks), 15.0, 80.0)
    apparent_temp = ambient_temp + 0.15 * (humidity / 100.0) * (ambient_temp - 20.0)

    solar_elevation = np.maximum(0.0, np.sin((hours - 6.0) * np.pi / 13.0))
    ghi = np.where((hours >= 6.0) & (hours <= 19.0), solar_elevation * 950.0 + np.random.normal(0, 15, total_blocks), 0.0)
    ghi = np.clip(ghi, 0.0, 1050.0)

    afternoon_peak = 750.0 * np.exp(-0.5 * ((hours - 15.5) / 2.8) ** 2)
    night_peak = 900.0 * np.exp(-0.5 * ((np.minimum(np.abs(hours - 23.5), 24 - hours)) / 2.2) ** 2)
    morning_trough = -600.0 * np.exp(-0.5 * ((hours - 4.5) / 2.0) ** 2)
    diurnal_curve = afternoon_peak + night_peak + morning_trough

    weekend_penalty = np.where(weekdays == 7, -350.0, np.where(weekdays == 6, -180.0, 0.0))

    cdd_delta = np.maximum(0.0, apparent_temp - CDD_THRESHOLD_C)
    cooling_load = (LINEAR_COOLING_COEFF * cdd_delta) + (18.0 * (cdd_delta ** NONLINEAR_COOLING_EXP))

    noise = np.random.normal(0.0, 30.0, total_blocks)
    gross_demand = BASE_LOAD_MW + diurnal_curve + weekend_penalty + cooling_load + noise

    solar_generation = np.clip(
        INSTALLED_SOLAR_MW * (ghi / 1000.0) * np.maximum(0.0, 1.0 - 0.004 * (ambient_temp - 25.0)),
        0.0,
        None
    )
    net_demand = gross_demand - solar_generation

    brpl_load = net_demand * 0.42 + np.random.normal(0, 8, total_blocks)
    tpddl_load = net_demand * 0.31 + np.random.normal(0, 6, total_blocks)
    bypl_load = net_demand * 0.27 + np.random.normal(0, 5, total_blocks)

    demand_df = pl.DataFrame({
        'timestamp': ts_series,
        'temperature_2m': np.round(ambient_temp, 2),
        'relative_humidity_2m': np.round(humidity, 2),
        'apparent_temperature': np.round(apparent_temp, 2),
        'ghi': np.round(ghi, 2),
        'time_block_idx': time_block_indices,
        'gross_demand_mw': np.round(gross_demand, 2),
        'solar_generation_mw': np.round(solar_generation, 2),
        'net_demand_mw': np.round(net_demand, 2),
        'discom_brpl_mw': np.round(brpl_load, 2),
        'discom_tpddl_mw': np.round(tpddl_load, 2),
        'discom_bypl_mw': np.round(bypl_load, 2),
    }).with_columns(
        pl.lit('CALIBRATED_PHYSICS_SYNTHESIS_OFFLINE').alias('data_provenance')
    )

    feeder_weights = (
        demand_df.group_by('time_block_idx')
        .agg([
            (pl.col('discom_brpl_mw').mean() / pl.col('net_demand_mw').mean()).alias('weight_brpl'),
            (pl.col('discom_tpddl_mw').mean() / pl.col('net_demand_mw').mean()).alias('weight_tpddl'),
            (pl.col('discom_bypl_mw').mean() / pl.col('net_demand_mw').mean()).alias('weight_bypl'),
        ])
        .sort('time_block_idx')
    )

    return demand_df, feeder_weights

if __name__ == '__main__':
    df, weights = build_offline_weather_and_demand()
    df.write_parquet(OUTPUT_DIR / 'synthetic_delhi_demand.parquet')
    weights.write_parquet(OUTPUT_DIR / 'feeder_weights.parquet')
    print('[✓] Baseline data generated.')