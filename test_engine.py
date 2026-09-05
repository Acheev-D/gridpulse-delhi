"""
Temporary verification test script for Delhi GridPulse engine.
Tests ingestion (offline fallback), LightGBM quantile forecasting,
solar physics derating, feeder disaggregation, and DuckDB grid alerting.
"""
from pathlib import Path
import polars as pl
import numpy as np

from engine.ingestion import fetch_weather_telemetry
from engine.forecaster import train_and_predict
from engine.physics import apply_net_load_and_feeders
from engine.alerting import evaluate_grid_alerts

DATA_DIR = Path("data")
TRAIN_PARQUET = str(DATA_DIR / "synthetic_delhi_demand.parquet")
FEEDER_PARQUET = str(DATA_DIR / "feeder_weights.parquet")
MOCK_HEATWAVE = DATA_DIR / "mock_delhi_heatwave.parquet"


def run_tests():
    print("==================================================")
    print(" Delhi GridPulse Engine: End-to-End Verification")
    print("==================================================")

    # 1. Ingestion Testing (Offline Fallback for 96 blocks)
    print("\n[1/4] Testing Ingestion & Feature Extraction...")
    weather_df, provenance = fetch_weather_telemetry(
        start_date="2023-05-01 00:00:00",
        end_date="2023-05-01 23:45:00",
    )
    # Ensure 96 blocks for single-day evaluation
    if weather_df.height > 96:
        weather_df = weather_df.head(96)

    print(f" -> Provenance Badge: {provenance}")
    print(f" -> Telemetry Rows: {weather_df.height} (Expected: 96 blocks)")
    assert weather_df.height == 96, f"Expected 96 blocks, got {weather_df.height}"
    assert "SIMULATION: Cached Heatwave Baseline" in provenance, f"Unexpected provenance: {provenance}"

    required_weather_cols = [
        "timestamp",
        "temperature_2m",
        "apparent_temperature",
        "ghi",
        "cdd_spike",
        "thermal_lag_4h",
        "thermal_lag_24h",
        "time_block_idx",
    ]
    for col in required_weather_cols:
        assert col in weather_df.columns, f"Missing column in weather_df: {col}"

    # Verify CDD math: non-negative
    assert weather_df["cdd_spike"].min() >= 0.0, "CDD spike contains negative values!"
    print(" [PASSED] Ingestion and feature extraction verified.")

    # 2. Forecaster Testing
    print("\n[2/4] Testing LightGBM Multi-Quantile Regressor...")
    forecast_df = train_and_predict(TRAIN_PARQUET, weather_df)

    for col in ["gross_p10", "gross_p50", "gross_p90"]:
        assert col in forecast_df.columns, f"Missing forecast column: {col}"

    p10 = forecast_df["gross_p10"].to_numpy()
    p50 = forecast_df["gross_p50"].to_numpy()
    p90 = forecast_df["gross_p90"].to_numpy()

    # Monotonic quantile ordering
    assert np.all(p10 <= p50 + 1e-5), "Violated quantile ordering: P10 > P50"
    assert np.all(p50 <= p90 + 1e-5), "Violated quantile ordering: P50 > P90"
    print(f" -> Mean Gross Demand: P10={p10.mean():.1f} MW, P50={p50.mean():.1f} MW, P90={p90.mean():.1f} MW")
    print(" [PASSED] Multi-quantile forecasting verified.")

    # 3. Physics & Feeder Disaggregation Testing
    print("\n[3/4] Testing Solar Physics Derating & Feeder Disaggregation...")
    physics_df = apply_net_load_and_feeders(
        forecast_df=forecast_df,
        feeder_weights_path=FEEDER_PARQUET,
        installed_solar_mw=1400.0,
        temp_delta=1.5,
    )

    for col in ["solar_generation_mw", "net_p10", "net_p50", "net_p90", "BRPL", "BYPL", "TPDDL"]:
        assert col in physics_df.columns, f"Missing physics column: {col}"

    solar = physics_df["solar_generation_mw"].to_numpy()
    net_p50 = physics_df["net_p50"].to_numpy()
    brpl = physics_df["BRPL"].to_numpy()
    bypl = physics_df["BYPL"].to_numpy()
    tpddl = physics_df["TPDDL"].to_numpy()

    # Solar generation must be non-negative
    assert np.all(solar >= 0.0), "Solar generation contains negative values!"
    # Conservation of feeder shares (BRPL + BYPL + TPDDL approx equals net_p50)
    discom_sum = brpl + bypl + tpddl
    max_feeder_discrepancy = np.max(np.abs(discom_sum - net_p50))
    print(f" -> Peak Solar Generation: {solar.max():.2f} MW")
    print(f" -> Max Discom Sum vs Net P50 Discrepancy: {max_feeder_discrepancy:.2f} MW (Rounding tolerance)")
    assert max_feeder_discrepancy < 1.0, f"Feeder disaggregation mismatch: {max_feeder_discrepancy} MW"
    print(" [PASSED] Solar derating and feeder disaggregation verified.")

    # 4. DuckDB Grid Alerting Testing
    print("\n[4/4] Testing In-Memory DuckDB Grid Alerting...")
    alert_df = evaluate_grid_alerts(
        physics_df,
        mva_limit=8500.0,
        power_factor=0.95,
    )

    alert_cols = ["transformer_loading_pct", "ramp_rate_mw_min", "loading_alert", "ramp_alert", "alert_status"]
    for col in alert_cols:
        assert col in alert_df.columns, f"Missing alert column: {col}"

    print(f" -> Evaluated Blocks: {alert_df.height}")
    print(f" -> Peak Transformer Loading: {alert_df['transformer_loading_pct'].max():.2f}%")
    print(f" -> Max Ramp Rate: {alert_df['ramp_rate_mw_min'].abs().max():.2f} MW/min")
    print(f" -> Alert Status Counts: {dict(alert_df['alert_status'].value_counts().iter_rows())}")

    assert alert_df.height == 96, f"Expected 96 alert rows, got {alert_df.height}"
    print(" [PASSED] DuckDB grid alert evaluation verified.")

    print("\n==================================================")
    print(" ALL ENGINE MODULES VERIFIED SUCCESSFULLY (96 BLOCKS)")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
