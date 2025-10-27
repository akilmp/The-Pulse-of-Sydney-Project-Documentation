# The Pulse of Sydney: Project Documentation

A personal data analytics project exploring how **transport, weather, housing, and local demographics** shape day‑to‑day life across Sydney, Australia — anchored by a small **self‑logged dataset** (commute + mood) to make the story uniquely mine.

---

## 1) Project Overview

### 1.1 Problem Statement

Sydney residents often make trade‑offs between where they live, how they commute, and how they feel. This project investigates: **How do transport reliability, weather, and housing context correlate with commute experience and wellbeing across Sydney suburbs?**

### 1.2 Objectives

* Build an end‑to‑end data workflow (ingest → clean → model → visualise → narrate) using open Sydney data plus a small personal dataset.
* Create an opinionated **Sydney Commute Happiness Index (SCHI)** combining objective and subjective inputs.
* Deliver an interactive dashboard and a reproducible analysis that an employer can run locally.

### 1.3 Success Criteria

* A working, reproducible pipeline with cached raw data and deterministic transforms.
* A dashboard enabling suburb‑level comparisons and time‑series exploration.
* A clear written narrative that surfaces at least **3 non‑obvious insights** with evidence.

---

## 2) Personal Angle (Why This Is Mine)

* I commute from Olympic to Randwick primarily by Train/Bus.
* For **30 days**, I self‑logged **departure time, arrival time, connection count, perceived delay, and mood (1–5)**.
* I include optional diary notes (e.g., trackwork, rain, crowding) to enrich qualitative context.

> This small, private dataset ties the broader Sydney data back to my lived experience.

---

## 3) Deliverables

* **/report/Sydney_Pulse_DataStory.pdf** — Analyst write‑up with methods, findings, and limitations.
* **/app/streamlit_app.py** — Interactive dashboard.
* **/notebooks/** — Jupyter notebooks: cleaning, exploration, modelling, viz.
* **/data/** — Raw (immutable), interim (cleaned), and processed (features) datasets.
* **/src/** — Modular Python package with ETL, features, metrics, and plotting.
* **README.md** — Quickstart + demo instructions.

---

## 3.1) Running the Streamlit Dashboard

### Data prerequisites

The dashboard expects the feature engineering pipeline to populate the processed cache:

* `data/processed/commute_features.csv`
* `data/processed/weather_features.csv`
* `data/processed/sa2_geometries.csv`
* `data/processed/schi.csv`

Generate them with the provided make targets (or run the underlying modules directly):

```bash
pip install -e .
make features        # runs cleaning + feature builders and writes to data/processed/
```

### Launching Streamlit

```bash
pip install -r requirements.txt  # or `pip install -e .[dev]`
streamlit run app/streamlit_app.py
```

By default Streamlit opens a browser tab. In remote/headless environments you can keep the
server running and forward the port:

```bash
streamlit run app/streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

### Smoke test command

CI or local smoke tests can verify that the app loads without needing a browser by using the
headless Streamlit runner:

```bash
python -m streamlit.web.cli run app/streamlit_app.py --headless --server.port 8765 --server.address 127.0.0.1
```

The command exits once the script initialises, which is sufficient to detect missing data files
or syntax errors in the layout code.

---

## 4) Repository Structure

```
Sydney-Pulse-Project/
├── README.md
├── pyproject.toml              # or requirements.txt
├── .env.example               # API keys or config (no secrets committed)
├── data/
│   ├── raw/                   # Downloaded (never edited)
│   ├── interim/               # Cleaned tables
│   └── processed/             # Feature matrices & aggregates
├── notebooks/
│   ├── 01_data_discovery.ipynb
│   ├── 02_cleaning_merging.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_modeling_index.ipynb
│   └── 05_visual_story.ipynb
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── utils_io.py
│   ├── etl/
│   │   ├── fetch_transport.py
│   │   ├── fetch_weather.py
│   │   ├── fetch_housing.py
│   │   └── fetch_abs.py
│   ├── cleaning/
│   │   ├── clean_transport.py
│   │   ├── clean_weather.py
│   │   ├── clean_housing.py
│   │   └── clean_abs.py
│   ├── features/
│   │   ├── make_geometries.py
│   │   ├── engineer_commute_features.py
│   │   ├── engineer_weather_features.py
│   │   └── composite_index.py
│   ├── viz/
│   │   ├── maps.py
│   │   ├── timeseries.py
│   │   └── scatterplots.py
│   └── metrics/
│       └── evaluation.py
├── app/
│   └── streamlit_app.py
├── tests/
│   ├── test_cleaning.py
│   ├── test_features.py
│   └── test_index.py
└── report/
    └── Sydney_Pulse_DataStory.pdf
```

---

## 5) Data Sources (Conceptual)

> Note: Use Sydney‑relevant open data. This documentation avoids hardcoding URLs; use the README to link the specific endpoints you chose.

**Transport** (Sydney/NSW): routes, GTFS schedules, service alerts, delays, Opal usage summaries.

**Weather** (Sydney/BOM): daily rainfall, max/min temp, severe weather alerts.

**Housing** (NSW/City of Sydney/NSW Valuer General): median price by LGA/suburb, rental vacancies.

**Demographics** (ABS): population density, SEIFA (advantage/disadvantage), labour force participation.

**Personal Logs**: `data/raw/personal_commute_log.csv` collected by me.

---

## 6) Data Contracts & Dictionaries

### 6.1 Common Keys

* `date` (YYYY‑MM‑DD, local time AEST/AEDT)
* `sa2_code` (ABS SA2 code) and `sa2_name`
* `suburb` (string, standardised to NSW GNB names where possible)
* `lga_code` and `lga_name`
* `mode` (one of {train, bus, ferry, light_rail, car})

### 6.2 Personal Commute Log Schema (`personal_commute_log.csv`)

| column               | type | description               | example         |
| -------------------- | ---- | ------------------------- | --------------- |
| `date`               | date | calendar date             | 2025‑03‑12      |
| `origin_suburb`      | str  | My home suburb            | Ashfield        |
| `destination_area`   | str  | Work/study area           | Sydney CBD      |
| `dept_time`          | time | departure hh:mm           | 08:05           |
| `arr_time`           | time | arrival hh:mm             | 08:52           |
| `connections`        | int  | number of interchanges    | 1               |
| `observed_delay_min` | int  | delay minutes vs schedule | 7               |
| `mood`               | int  | 1 (low) – 5 (high)        | 3               |
| `crowding`           | int  | 1 (empty) – 5 (packed)    | 4               |
| `weather_note`       | str  | short note (e.g., rain)   | rainy           |
| `notes`              | str  | free text                 | trackwork on T2 |

### 6.3 Derived Features (examples)

* `travel_time_min = (arr_time – dept_time)`
* `on_time = observed_delay_min <= 3`
* `is_rain = rain_mm >= 1`
* `peak = dept_time in [7:00–9:00 or 16:30–18:30]`

---

## 7) Methodology

### 7.1 Ingestion & Storage

* Download raw CSV/JSON/GTFS into `data/raw/` (immutable; never edit by hand).
* Keep a `DATASET_REGISTRY.yaml` listing source, retrieval date (Sydney time), and checksum (SHA256).

### 7.2 Cleaning

* Standardise suburb names and geocodes (ABS ASGS 2021 SA2 or LGAs).
* Deduplicate by `date + suburb + mode` where appropriate.
* Localise timestamps to `Australia/Sydney` and convert to naive date where needed.
* Handle missing values using explicit rules per dataset (document in code comments).

### 7.3 Integration

* Spatially join data to SA2 or LGA boundaries (via GeoJSON/TopoJSON) using **GeoPandas**.
* Temporal alignment at **daily** grain for time‑series comparisons.

### 7.4 Feature Engineering

* Transport reliability: `pct_on_time`, `avg_delay_min`, `service_variability` (std of delay).
* Weather burden: `rain_mm`, `rainy_peak_days`, `temp_anomaly` vs monthly norm.
* Housing context: `median_rent_weekly`, `rent_to_income_ratio`.
* Demographics: `seifa_decile`, `population_density`.
* Personal: `my_mood_mean`, `my_delay_mean` by weekday and weather bucket.

### 7.5 Sydney Commute Happiness Index (SCHI)

A composite index per SA2 (or suburb) and day/week.

**Components (0–100 each, higher = better):**

1. **Reliability Score (RS)** = scaled inverse of `avg_delay_min` and `service_variability`.
2. **Access Score (AS)** = scaled function of frequency/headways during peak.
3. **Weather Comfort (WC)** = scaled inverse of `rain_mm` and `temp_anomaly`.
4. **Crowding/Experience (CX)** = proxy from Opal peaks or my self‑logged crowding + public stats.

**Composite:**

```
SCHI = 0.35*RS + 0.25*AS + 0.20*WC + 0.20*CX
```

* Scaling via min‑max within Sydney for interpretability.
* Provide sensitivity toggles in the dashboard to adjust weights.

### 7.6 Validation & Sanity Checks

* Correlate SCHI with my `mood` on overlapping dates to see if directionally consistent.
* Back‑test against known events (e.g., heavy rain weeks, trackwork weekends) for expected dips.
* Compare SA2 rankings with known anecdotal patterns (qualitative validation).

---

## 8) Implementation Details

### 8.1 Environment & Setup

* Python 3.11+
* Key libs: `pandas`, `numpy`, `pyyaml`, `geopandas`, `shapely`, `pyproj`, `matplotlib`, `plotly`, `streamlit`, `pytest`, `python-dotenv`.

**Install:**

```bash
# Using uv or pip
pip install -r requirements.txt
# or
uv pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with any required API tokens and config
```

### 8.2 Configuration (`.env` and `src/config.py`)

```ini
# .env.example
TZ=Australia/Sydney
PRIMARY_GEO_LEVEL=SA2
CACHE_TTL_DAYS=7
SCHI_WEIGHTS=0.35,0.25,0.20,0.20
```

```python
# src/config.py
import os
from dataclasses import dataclass

@dataclass
class Settings:
    TZ: str = os.getenv("TZ", "Australia/Sydney")
    PRIMARY_GEO_LEVEL: str = os.getenv("PRIMARY_GEO_LEVEL", "SA2")
    CACHE_TTL_DAYS: int = int(os.getenv("CACHE_TTL_DAYS", 7))
    SCHI_WEIGHTS: tuple = tuple(float(x) for x in os.getenv("SCHI_WEIGHTS", "0.35,0.25,0.20,0.20").split(','))
```

### 8.3 Reproducible Make Commands (optional)

```makefile
# Makefile
.PHONY: data clean features app test report

data: ## Fetch all raw data
	python -m src.etl.fetch_transport
	python -m src.etl.fetch_weather
	python -m src.etl.fetch_housing
	python -m src.etl.fetch_abs

clean: ## Run cleaning scripts
	python -m src.cleaning.clean_transport
	python -m src.cleaning.clean_weather
	python -m src.cleaning.clean_housing
	python -m src.cleaning.clean_abs

features: ## Build features and index
	python -m src.features.make_geometries
	python -m src.features.engineer_commute_features
	python -m src.features.engineer_weather_features
	python -m src.features.composite_index

app: ## Launch dashboard
	streamlit run app/streamlit_app.py

test: ## Run tests
	pytest -q

report: ## Build PDF from notebook
	jupyter nbconvert --to pdf notebooks/05_visual_story.ipynb --output report/Sydney_Pulse_DataStory.pdf
```

### 8.4 Example ETL Pattern

```python
# src/etl/fetch_weather.py
from pathlib import Path
import pandas as pd
from src.utils_io import write_csv, today_sydney

RAW = Path("data/raw")

def fetch_daily_weather():
    # Placeholder for actual request; this function should:
    # 1) Download daily weather for Sydney stations
    # 2) Normalize columns and station metadata
    # 3) Save to data/raw/weather_YYYYMMDD.csv
    df = pd.DataFrame([
        {"date":"2025-03-12","station":"Observatory Hill","rain_mm":12.4,"tmax":22.5,"tmin":18.1},
    ])
    out = RAW/ f"weather_{today_sydney()}.csv"
    write_csv(df, out)
    return out

if __name__ == "__main__":
    path = fetch_daily_weather()
    print(f"Saved {path}")
```

### 8.5 Feature Engineering Snippet

```python
# src/features/composite_index.py
import pandas as pd
from src.config import Settings

W_RS, W_AS, W_WC, W_CX = Settings().SCHI_WEIGHTS

# Assume df has columns: sa2_code, date, avg_delay_min, delay_std, headway_min,
# rain_mm, temp_anom, crowd_proxy

def minmax(series):
    return (series - series.min()) / (series.max() - series.min())

def compute_schi(df: pd.DataFrame) -> pd.DataFrame:
    rs = 1 - minmax(df["avg_delay_min"].fillna(df["avg_delay_min"].median()))
    rs *= (1 - minmax(df["delay_std"].fillna(0)))

    as_ = 1 - minmax(df["headway_min"].fillna(df["headway_min"].median()))

    wc = 1 - (0.6*minmax(df["rain_mm"].fillna(0)) + 0.4*minmax(df["temp_anom"].abs().fillna(0)))

    cx = 1 - minmax(df["crowd_proxy"].fillna(df["crowd_proxy"].median()))

    df["SCHI"] = 100 * (W_RS*rs + W_AS*as_ + W_WC*wc + W_CX*cx)
    return df
```

---

## 9) Dashboard Specification (Streamlit)

### 9.1 Pages

1. **Overview**: city‑wide time series of SCHI with weather overlays.
2. **Map**: choropleth of SA2 SCHI; hover for metrics; filter by mode & peak.
3. **Compare**: select two suburbs/SA2s to compare KPI cards.
4. **My Commute**: private page plotting my 30‑day log vs SCHI; diary notes.

### 9.2 UX Details

* Weight sliders for SCHI components with immediate recompute.
* Tooltips explaining each metric & data caveats.
* Download buttons for CSV of filtered results.

### 9.3 Example KPI Definitions

* `On‑time %` = share of services with `observed_delay_min <= 3`.
* `Typical headway` = median minutes between peak services.
* `Weather burden` = 0–100 subscore based on daily rain/temp anomaly.

---

## 10) Analysis Plan & Hypotheses

**H1:** Rainy days increase average delay and reduce SCHI, most in ferry/light rail corridors.

**H2:** Higher median rents correlate with better SCHI (access + reliability), but effect weakens beyond inner‑ring.

**H3:** My self‑reported mood correlates with SCHI at lag 0–1 day; deviations highlight personal biases (e.g., exam stress).

**Approach:**

* Correlation matrices; partial correlations controlling for income/rent.
* Weekday/peak faceting; rolling windows (7‑day) for trend robustness.
* Permutation tests for significance where appropriate.

---

## 11) Testing & Quality

### 11.1 Unit Tests (pytest)

* Cleaning: known messy suburb names → canonical forms.
* Features: min‑max scaling bounds ∈ [0,1].
* Index: determinism given fixed inputs; monotonic response to increased delays (SCHI should drop).

### 11.2 Data Checks

* Row counts before/after joins; left‑join warnings.
* Null audits per table; explicit imputation logs.
* Schema validation with `pandera` (optional).

### 11.3 Performance

* Cache raw downloads; store intermediate parquet.
* Pre‑aggregate by SA2/day to keep the dashboard snappy.

---

## 12) Ethics, Privacy & Bias

* Personal dataset is small and optional to share; obscure exact addresses and exact timestamps before publishing.
* Do not publish any API keys or private endpoints.
* Be explicit about index subjectivity (chosen weights, proxies for crowding).
* Weather and transport data have measurement biases; document limitations.

---

## 13) Reproducibility

* Version pin dependencies in `pyproject.toml` or `requirements.txt`.
* Record data retrieval date/time (AEST/AEDT) and checksums in `DATASET_REGISTRY.yaml`.
* Provide `seed` for any stochastic steps.
* Makefile targets for one‑command rebuilds.

---

## 14) Operational Runbook

**Initial Setup**

1. Clone repo, create virtual env, install deps.
2. Create `.env` from example; set timezone and optional keys.
3. Run `make data` → `make clean` → `make features`.
4. Launch `make app` to view dashboard.

**Updating Data Weekly**

* Run `make data features` (idempotent) and re‑generate report notebook.

**Troubleshooting**

* If geopandas errors: ensure `gdal` installed (see README platform notes).
* If maps blank: verify SA2 codes match boundaries; run `make features` again.

---

## 15) Interview Talking Points

* Why SA2 vs suburb? (Consistent ABS boundaries + joins.)
* Justification of SCHI weights; show sensitivity slider live.
* Lessons from mismatches between my mood and SCHI (limits of proxies).
* Data governance: audit trail, immutability of raw data, and checksum registry.

---

## 16) Risks & Mitigations

* **Data sparsity** on specific modes → aggregate to weekly or LGA level.
* **Schema drift** in external sources → schema validation + unit tests.
* **Geocoding errors** → maintain mapping table for canonical names.
* **Overfitting** narrative to personal experience → triangulate with external signals.

---

## 17) Timeline (Example 3–4 Weeks, Part‑time)

* **Week 1:** Data discovery, registry, personal log template, baseline ETL.
* **Week 2:** Cleaning, joins, initial features, first maps/TS.
* **Week 3:** SCHI v1, validation, dashboard skeleton.
* **Week 4:** Story polish, sensitivity analysis, PDF report, tests.

---

## 18) README Outline (to include in repo)

**Title & one‑line pitch.**

**Motivation (personal paragraph).**

**Quickstart**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
make data clean features
streamlit run app/streamlit_app.py
```

**Data Lineage Diagram** (ASCII or image): raw → interim → processed → app.

**How the SCHI works**: formula, weights, scaling, limits.

**Privacy**: what I publish vs keep private.

**Screenshots**: 2–3 key views with captions.

**License**: MIT (code) + separate terms for data (see below).

---

## 19) Licensing & Attribution

* **Code:** MIT License.
* **Data:** Include a `DATA_LICENSE.md` stating that third‑party data retains original licenses; do not redistribute where prohibited; provide scripts to fetch.
* **Attribution:** Acknowledge data providers in the report and README.

---

## 20) FAQ (For Reviewers/Employers)

**Q:** Is the index objective?
**A:** No index is purely objective. I expose weights and document proxies. Sensitivity analysis demonstrates robustness.

**Q:** How transferable is this?
**A:** The pipeline is city‑agnostic with new geographies and feeds; Sydney specifics are modularised.

**Q:** Can I reproduce locally?
**A:** Yes — one‑command Make targets; raw data fetched via scripts; no private data required.

---

## 21) Appendix

### 21.1 Personal Log Template (CSV)

```csv
date,origin_suburb,destination_area,dept_time,arr_time,connections,observed_delay_min,mood,crowding,weather_note,notes
2025-03-12,Ashfield,Sydney CBD,08:05,08:52,1,7,3,4,rainy,trackwork on T2
```

### 21.2 Example SQL for Aggregations (if loading to SQLite)

```sql
-- Average delay by SA2 per day
CREATE VIEW sa2_delay_daily AS
SELECT sa2_code,
       date,
       AVG(observed_delay_min) AS avg_delay_min,
       STDDEV(observed_delay_min) AS delay_std
FROM transport_clean
GROUP BY sa2_code, date;
```

### 21.3 Narrative Outline for Report

1. Personal motivation and questions.
2. Data inventory; ethics and privacy.
3. Methods and SCHI construction.
4. Findings: 3–5 figures with captions.
5. Sensitivity & limitations.
6. Implications for Sydney residents and planners.
7. Appendix with technical details.

---

## 22) Development Workflow & Quality Checks

### 22.1 Pytest Layout

All automated tests live under `tests/` and cover the end-to-end story with three layers:

* **ETL fixtures** — `tests/test_etl.py` guards the cached CSV schema committed in `data/fixtures/`.
* **Feature engineering** — `tests/test_features.py` validates aggregate calculations used downstream.
* **SCHI computation** — `tests/test_schi.py` keeps the index formula bounded and delay-sensitive.

The suite is configured via `pytest.ini`/`pyproject.toml` to automatically discover modules from `src/`.

```bash
# install tooling
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# stage cached fixtures then run the suite
make data
pytest  # or: make test
```

### 22.2 Optional Static Analysis

Ruff is configured in `pyproject.toml`. Run it locally with:

```bash
make lint
```

The CI workflow executes the same command with `continue-on-error: true` so style warnings do not block contributions.

### 22.3 Reproducible Make Targets

The automation workflow hinges on self-contained Make targets that avoid hitting live APIs:

* `make data` — copies synthetic fixtures into `data/raw/`.
* `make features` — produces a deterministic manifest under `data/processed/`.
* `make clean` — removes generated artefacts while keeping versioned fixtures intact.

These commands are exercised in GitHub Actions on every pull request alongside `pytest` to guarantee reproducibility without external services.

### 22.4 Contribution Guidelines

See `CONTRIBUTING.md` for a summary of style expectations, mandatory tests, and data privacy responsibilities before opening a pull request.

---

**End of Documentation**
