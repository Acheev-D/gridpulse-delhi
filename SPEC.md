\# SPEC.md: Delhi GridPulse (AI Electricity Demand Prediction)



\## System Overview

A zero-latency, single-process Streamlit operations cockpit forecasting 15-minute Delhi operational electricity demand (P10, P50, P90). Features vectorized solar PV derating and CERC top-down feeder disaggregation using in-memory Polars and DuckDB.



\## Tech Stack

\- Python 3.11

\- Core Engines: Polars, LightGBM (Quantiles: 0.1, 0.5, 0.9), DuckDB (:memory:), httpx, numpy

\- UI \& Visualization: Streamlit, Plotly (WebGL enabled)



\## File Specifications



\### 1. engine/ingestion.py

\- `fetch\_weather\_telemetry(start\_date: str, end\_date: str) -> tuple\[pl.DataFrame, str]`:

&#x20; - Attempts live query to Open-Meteo API for Delhi NCR (Lat 28.6139, Lon 77.2090) with 5.0s timeout.

&#x20; - Failover: Gracefully falls back to reading `data/mock\_delhi\_heatwave.parquet`.

&#x20; - Upsamples hourly data to 15-minute intervals (96 time blocks/day).

&#x20; - Feature extraction:

&#x20;   - CDD spike: `apparent\_temp - 24.0` (clipped at 0.0).

&#x20;   - Thermal lags: `apparent\_temp` rolling means for 4h (16 blocks) and 24h (96 blocks).

&#x20;   - `time\_block\_idx`: `(hour \* 4 + minute // 15)`.

&#x20; - Returns tuple: `(processed\_df, provenance\_label)`.



\### 2. engine/forecaster.py

\- `train\_and\_predict(train\_path: str, inference\_df: pl.DataFrame)`:

&#x20; - Loads `data/synthetic\_delhi\_demand.parquet`.

&#x20; - Trains three LightGBM regressors with `objective='quantile'` for `alpha=0.1` (P10), `alpha=0.5` (P50), and `alpha=0.9` (P90).

&#x20; - Uses features: `apparent\_temperature`, `cdd\_spike`, `thermal\_lag\_4h`, `thermal\_lag\_24h`, `time\_block\_idx`.

&#x20; - Predicts and outputs columns: `gross\_p10`, `gross\_p50`, `gross\_p90`.

&#x20; - Cached via `@st.cache\_resource`.



\### 3. engine/physics.py

\- `apply\_net\_load\_and\_feeders(forecast\_df: pl.DataFrame, feeder\_weights\_path: str, installed\_solar\_mw: float = 1400.0, temp\_delta: float = 0.0)`:

&#x20; - Computes derated rooftop solar generation in Polars:

&#x20;   `installed\_solar\_mw \* (ghi / 1000.0) \* max(0.0, 1.0 - 0.004 \* (temp - 25.0))`.

&#x20; - Subtracts solar yield to produce `net\_p10`, `net\_p50`, and `net\_p90`.

&#x20; - Performs left join with `data/feeder\_weights.parquet` on `time\_block\_idx` to allocate demand to `BRPL`, `BYPL`, and `TPDDL`.



\### 4. engine/alerting.py

\- `evaluate\_grid\_alerts(df: pl.DataFrame, mva\_limit: float = 8500.0, power\_factor: float = 0.95) -> pl.DataFrame`:

&#x20; - Registers Arrow table in in-memory DuckDB (`:memory:`).

&#x20; - Evaluates transformer loading: `(net\_p90 / (mva\_limit \* power\_factor)) \* 100.0`.

&#x20; - Evaluates 15-minute ramp rate: `(net\_p50 - LAG(net\_p50, 1) OVER (ORDER BY timestamp)) / 15.0`.

&#x20; - Flags loading > 85% (Amber), > 95% (Critical Red), and ramp rates > 35 MW/min.



\### 5. app.py

\- Streamlit application entry point.

\- Top status header displaying data lineage badge (`LIVE` vs `SIMULATION`).

\- Interactive sidebar controls: Ambient temperature delta slider (`-3.0°C` to `+3.0°C`) and Installed Solar Capacity slider (`0` to `3000 MW`).

\- Primary Plotly WebGL fan chart showing P10, P50, P90 forecast curves against grid headroom.

\- Metrics cards for Peak Net Demand, Transformer Loading %, and Alert Status.

\- Feeder breakdown tab showing regional discom shares (BRPL, BYPL, TPDDL).

