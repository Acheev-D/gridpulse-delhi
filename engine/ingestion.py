from pathlib import Path
from typing import Optional, Tuple
import httpx
import polars as pl

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FALLBACK_PARQUET = DATA_DIR / "mock_delhi_heatwave.parquet"
DELHI_LAT = 28.6139
DELHI_LON = 77.2090
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _extract_weather_features(df: pl.DataFrame, provenance_label: str) -> pl.DataFrame:
    """Extract required features: CDD spike, thermal lags, and time block index."""
    df = df.sort("timestamp")

    # Time block index: (hour * 4 + minute // 15)
    time_block_expr = (
        df["timestamp"].dt.hour() * 4 + df["timestamp"].dt.minute() // 15
    ).cast(pl.Int8)

    processed = df.with_columns(
        time_block_expr.alias("time_block_idx"),
        (pl.col("apparent_temperature") - 24.0)
        .clip(lower_bound=0.0)
        .alias("cdd_spike"),
        pl.col("apparent_temperature")
        .rolling_mean(window_size=16, min_samples=1)
        .alias("thermal_lag_4h"),
        pl.col("apparent_temperature")
        .rolling_mean(window_size=96, min_samples=1)
        .alias("thermal_lag_24h"),
        pl.lit(provenance_label).alias("data_provenance"),
    )
    return processed


def fetch_weather_telemetry(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    mock_file: Optional[Path] = None,
) -> Tuple[pl.DataFrame, str]:
    """
    Fetch weather telemetry for Delhi NCR.

    Attempts live query to Open-Meteo rolling 7-day forecast.
    Falls back to mock_delhi_heatwave.parquet on failure or HTTP != 200.
    Upsamples hourly data to 15-minute intervals.
    Returns (processed_df, provenance_label).
    """
    provenance_label = "LIVE: Open-Meteo API"
    live_df: Optional[pl.DataFrame] = None
    target_mock = mock_file or FALLBACK_PARQUET

    try:
        params = {
            "latitude": DELHI_LAT,
            "longitude": DELHI_LON,
            "forecast_days": 7,
            "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,global_horizontal_irradiance,shortwave_radiation",
            "timezone": "Asia/Kolkata",
        }
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(OPEN_METEO_FORECAST_URL, params=params)

        if resp.status_code == 200:
            payload = resp.json()
            hourly = payload.get("hourly", {})
            times = hourly.get("time", [])

            if times:
                ghi_vals = hourly.get("global_horizontal_irradiance")
                if ghi_vals is None or all(v is None for v in ghi_vals):
                    ghi_vals = hourly.get("shortwave_radiation", [0.0] * len(times))

                raw_df = pl.DataFrame({
                    "timestamp": pl.Series(times).str.to_datetime(),
                    "temperature_2m": hourly.get("temperature_2m", []),
                    "relative_humidity_2m": hourly.get("relative_humidity_2m", []),
                    "apparent_temperature": hourly.get("apparent_temperature", []),
                    "ghi": ghi_vals,
                }).sort("timestamp")

                # Upsample hourly data to 15-minute intervals (96 time blocks/day)
                upsampled = raw_df.upsample(time_column="timestamp", every="15m").interpolate()
                live_df = upsampled
        else:
            live_df = None
    except Exception:
        live_df = None

    if live_df is not None and live_df.height > 0:
        processed_df = _extract_weather_features(live_df, provenance_label)
        return processed_df, provenance_label

    # Fallback to cached heatwave baseline parquet
    provenance_label = "SIMULATION: Cached Heatwave Baseline"
    fallback_df = pl.read_parquet(target_mock)

    # If start_date and end_date provided, check if matching slice exists in mock data
    if start_date is not None and end_date is not None:
        try:
            start_ts = pl.lit(start_date).str.to_datetime().dt.cast(fallback_df["timestamp"].dtype)
            end_ts = pl.lit(end_date).str.to_datetime().dt.cast(fallback_df["timestamp"].dtype)
            filtered = fallback_df.filter(
                (pl.col("timestamp") >= start_ts) & (pl.col("timestamp") <= end_ts)
            )
            if filtered.height > 0:
                fallback_df = filtered
        except Exception:
            pass

    # Ensure 15m intervals and feature extraction
    processed_df = _extract_weather_features(fallback_df, provenance_label)
    return processed_df, provenance_label
