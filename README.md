# ⚡ GridPulse Delhi: Next-Gen Grid Dispatch & Predictive Load Cockpit

[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Polars](https://img.shields.io/badge/Polars-0.20+-CD792C?style=flat&logo=polars&logoColor=white)](https://pola.rs/)
[![DuckDB](https://img.shields.io/badge/DuckDB-0.9+-FFF000?style=flat&logo=duckdb&logoColor=black)](https://duckdb.org/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.0+-0284C7?style=flat)](https://lightgbm.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-10B981.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade, glassmorphic power dispatch and load-forecasting cockpit built for the **Delhi State Load Despatch Centre (SLDC)** ecosystem. **GridPulse Delhi** transitions power telemetry from passive monitoring into an active operational decision-support system—combining multi-quantile time-series forecasting, physics-based thermal shock modeling, rooftop solar derating, and automated battery peak-shaving dispatch.

---

## 🌟 Core Highlights

* **Multi-Quantile Load Horizons (P10/P50/P90):** LightGBM quantile regression engine calibrated on Delhi's historical demand profiles and weather drivers, providing uncertainty bands across 96 operational blocks (15-minute dispatch).
* **Thermal Inertia & Weather Synthesis:** Real-time cooling demand modeling capturing apparent temperature, Cooling Degree Days (CDD), and heatwave thermal lag spikes ($T > 42^\circ\text{C}$).
* **Dynamic Rooftop Solar Offset:** Vectorized temperature-derated solar generation ($1,400\text{–}1,800\text{ MW}$ baseline) computed from Global Horizontal Irradiance (GHI) to calculate true Net Operational Demand.
* **Automated BESS Peak Shaving:** Simulated 400 MW / 1,200 MWh utility-scale Battery Energy Storage System (BESS) dispatcher that automatically clamps peaks when net load nears the critical 8,000 MW grid capacity ceiling.
* **Discom-Level Load Balancing:** Top-down diurnal disaggregation across Delhi's primary discoms (BRPL, BYPL, and TPDDL) based on CERC allocation ratios.
* **Frosted Glassmorphic Interface:** Clean, light-mode command-center UI built with tactile glass elevation, dynamic CSS status beacons, and an embedded plain-English AI assistant (`GridPulse Buddy`).

---

## 🏗️ Architecture & Pipeline

```text
                 ┌───────────────────────────────┐
                 │    Open-Meteo Weather API     │
                 │  (or Cached Baseline Telemetry)│
                 └───────────────┬───────────────┘
                                 │
                                 ▼
┌────────────────────────┐   ┌───────────────────────────────┐
│ Historical Load Series │──▶│      engine/forecaster.py     │
│  (Delhi Discom Scada)  │   │  (Multi-Quantile LightGBM)    │
└────────────────────────┘   └───────────────┬───────────────┘
                                             │ [Gross Demand P10/P50/P90]
                                             ▼
                             ┌───────────────────────────────┐
                             │       engine/physics.py       │
                             │  - Thermal Shock (CDD Lag)    │
                             │  - Rooftop PV Derating (GHI)  │
                             │  - Automated BESS Dispatch    │
                             └───────────────┬───────────────┘
                                             │ [Net Demand Profiles]
                                             ▼
                             ┌───────────────────────────────┐
                             │       engine/alerting.py      │
                             │    (In-Memory DuckDB Engine)  │
                             │   Headroom & Ramp-Rate Checks │
                             └───────────────┬───────────────┘
                                             │
                                             ▼
                             ┌───────────────────────────────┐
                             │             app.py            │
                             │  Frosted Glassmorphic Cockpit │
                             └───────────────────────────────┘
```

---

## 📊 Key Operational Metrics

| Metric | Nominal State | Peak Stress Simulation | Unit |
| :--- | :--- | :--- | :--- |
| **Grid Capacity Limit** | 9,025 / 9,500 | 8,000 (Constrained) | MVA / MW |
| **Projected Peak Demand** | 7,640 – 8,120 | > 8,470 | MW |
| **Solar PV Inflow** | 1,200 – 1,800 | 0 (Night/Cloud Transient) | MW |
| **BESS Shave Capacity** | 400 MW / 1,200 MWh | Automated Trigger at 8,000 MW | MW / MWh |
| **Forecast Accuracy (MAPE)** | 1.84% | Conf. Interval: 98.16% | % |

---

## 🚀 Quick Start

### Prerequisites
* Python 3.10 or higher
* Git

### 1. Clone the Repository
```bash
git clone https://github.com/Acheev-D/gridpulse-delhi.git
cd gridpulse-delhi
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch Dashboard
```bash
streamlit run app.py
```
The application will open automatically at `http://localhost:8501`.

---

## 🗂️ Project Structure

```text
gridpulse-delhi/
├── app.py                      # Main Streamlit dashboard & injected CSS design system
├── generate_delhi_demand.py    # Synthetic telemetry calibration script
├── requirements.txt            # Python dependencies
├── SPEC.md                     # Technical system design specification
├── assets/                     # UI visual assets, icons, and backgrounds
├── data/                       # Parquet datasets & discom feeder weights
│   ├── feeder_weights.parquet
│   └── mock_delhi_heatwave.parquet
└── engine/                     # Core computational and physics engines
    ├── alerting.py             # In-memory DuckDB real-time SQL rule evaluator
    ├── forecaster.py           # Multi-quantile LightGBM load forecasting model
    ├── ingestion.py            # Weather API telemetry ingestion & fallback pipeline
    └── physics.py              # Thermal shock, PV deration, and BESS dispatch math
```

---

## 🛡️ License
Distributed under the MIT License. See LICENSE for details.
