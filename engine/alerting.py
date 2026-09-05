import duckdb
import polars as pl


def evaluate_grid_alerts(
    df: pl.DataFrame,
    mva_limit: float = 9500.0,
    power_factor: float = 0.95,
) -> pl.DataFrame:
    """
    Evaluates transformer loading headroom and 15-minute ramp rates using
    in-memory DuckDB over an Arrow table.
    Flags transformer loading > 85% (Amber), > 95% (Critical Red),
    and ramp rate > 35 MW/min.
    """
    con = duckdb.connect(":memory:")
    arrow_table = df.to_arrow()
    con.register("grid_telemetry", arrow_table)

    effective_capacity_mw = mva_limit * power_factor

    query = f"""
    WITH evaluated AS (
        SELECT
            *,
            ROUND((net_p90 / {effective_capacity_mw}) * 100.0, 2) AS transformer_loading_pct,
            ROUND(COALESCE((net_p50 - LAG(net_p50, 1) OVER (ORDER BY timestamp)) / 15.0, 0.0), 2) AS ramp_rate_mw_min,
            ROUND({effective_capacity_mw}, 2) AS grid_capacity_mw
        FROM grid_telemetry
    )
    SELECT
        *,
        CASE
            WHEN transformer_loading_pct > 95.0 THEN 'CRITICAL_RED'
            WHEN transformer_loading_pct > 85.0 THEN 'AMBER'
            ELSE 'NORMAL'
        END AS loading_alert,
        CASE
            WHEN ABS(ramp_rate_mw_min) > 35.0 THEN 'RAMP_ALERT'
            ELSE 'NORMAL'
        END AS ramp_alert,
        CASE
            WHEN transformer_loading_pct > 95.0 THEN 'CRITICAL_RED'
            WHEN transformer_loading_pct > 85.0 THEN 'AMBER'
            WHEN ABS(ramp_rate_mw_min) > 35.0 THEN 'RAMP_ALERT'
            ELSE 'NORMAL'
        END AS alert_status
    FROM evaluated
    ORDER BY timestamp
    """

    result = con.execute(query).pl()
    con.close()
    return result
