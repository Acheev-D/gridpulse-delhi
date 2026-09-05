from pathlib import Path
from typing import Dict, List
import lightgbm as lgb
import numpy as np
import polars as pl
import streamlit as st

FEATURE_COLS: List[str] = [
    "apparent_temperature",
    "cdd_spike",
    "thermal_lag_4h",
    "thermal_lag_24h",
    "time_block_idx",
]
TARGET_COL: str = "gross_demand_mw"


def _prepare_training_data(train_path: str) -> tuple[np.ndarray, np.ndarray]:
    """Load training parquet and prepare feature matrix and target vector."""
    df = pl.read_parquet(train_path).sort("timestamp")

    if "cdd_spike" not in df.columns:
        df = df.with_columns(
            (pl.col("apparent_temperature") - 24.0)
            .clip(lower_bound=0.0)
            .alias("cdd_spike")
        )
    if "thermal_lag_4h" not in df.columns:
        df = df.with_columns(
            pl.col("apparent_temperature")
            .rolling_mean(window_size=16, min_samples=1)
            .alias("thermal_lag_4h")
        )
    if "thermal_lag_24h" not in df.columns:
        df = df.with_columns(
            pl.col("apparent_temperature")
            .rolling_mean(window_size=96, min_samples=1)
            .alias("thermal_lag_24h")
        )
    if "time_block_idx" not in df.columns:
        df = df.with_columns(
            (df["timestamp"].dt.hour() * 4 + df["timestamp"].dt.minute() // 15)
            .cast(pl.Int8)
            .alias("time_block_idx")
        )

    X = df.select(FEATURE_COLS).to_numpy()
    y = df[TARGET_COL].to_numpy()
    return X, y


@st.cache_resource(show_spinner=False)
def get_trained_models(train_path: str) -> Dict[float, lgb.Booster]:
    """Train and cache native LightGBM quantile regressors for P10, P50, and P90."""
    X_train, y_train = _prepare_training_data(train_path)

    models: Dict[float, lgb.Booster] = {}
    quantiles = [0.1, 0.5, 0.9]

    for alpha in quantiles:
        params = {
            "objective": "quantile",
            "alpha": alpha,
            "learning_rate": 0.08,
            "num_leaves": 31,
            "min_data_in_leaf": 20,
            "verbosity": -1,
            "random_state": 42,
        }
        train_data = lgb.Dataset(X_train, label=y_train, feature_name=FEATURE_COLS, free_raw_data=False)
        booster = lgb.train(params, train_data, num_boost_round=100)
        models[alpha] = booster

    return models


def train_and_predict(train_path: str, inference_df: pl.DataFrame) -> pl.DataFrame:
    """
    Train (or use cached) multi-quantile LightGBM models on synthetic demand
    and predict gross demand quantiles (gross_p10, gross_p50, gross_p90).
    """
    models = get_trained_models(train_path)

    # Ensure required feature columns exist in inference_df
    inf = inference_df
    if "cdd_spike" not in inf.columns:
        inf = inf.with_columns(
            (pl.col("apparent_temperature") - 24.0)
            .clip(lower_bound=0.0)
            .alias("cdd_spike")
        )
    if "thermal_lag_4h" not in inf.columns:
        inf = inf.with_columns(
            pl.col("apparent_temperature")
            .rolling_mean(window_size=16, min_samples=1)
            .alias("thermal_lag_4h")
        )
    if "thermal_lag_24h" not in inf.columns:
        inf = inf.with_columns(
            pl.col("apparent_temperature")
            .rolling_mean(window_size=96, min_samples=1)
            .alias("thermal_lag_24h")
        )
    if "time_block_idx" not in inf.columns:
        inf = inf.with_columns(
            (inf["timestamp"].dt.hour() * 4 + inf["timestamp"].dt.minute() // 15)
            .cast(pl.Int8)
            .alias("time_block_idx")
        )

    X_inf = inf.select(FEATURE_COLS).to_numpy()

    p10 = models[0.1].predict(X_inf)
    p50 = models[0.5].predict(X_inf)
    p90 = models[0.9].predict(X_inf)

    # Monotonicity adjustment: P10 <= P50 <= P90
    p50 = np.maximum(p10, p50)
    p90 = np.maximum(p50, p90)

    result_df = inf.with_columns(
        pl.Series("gross_p10", np.round(p10, 2)),
        pl.Series("gross_p50", np.round(p50, 2)),
        pl.Series("gross_p90", np.round(p90, 2)),
    )
    return result_df
