# Myfitness Streamlit Analytics Dashboard

Interactive telemetry and population intelligence dashboard built with [Streamlit](https://streamlit.io/) and [Plotly](https://plotly.com/).

---

## Features

1. **Population Analytics (ML Benchmarks)**
   - **K-Means Archetype Clusters**: Cluster distribution bar chart and 2D Scatter plot (Height vs Weight colored by cluster).
   - **Demographic Breakdown**: Gender ratio, BMI categories, and activity level donut charts.
   - **Daily Health Benchmarks**: Quartile benchmarks for sleep hours and daily water intake.
   - **Correlation Heatmap**: Pearson correlation matrix analyzing relationships between calorie deficit, sleep, hydration, and weight change.
   - **Catalog Item Popularity**: Top logged exercises and nutritional replenishments.

2. **Personal Fitness Analytics (Authenticated User Telemetry)**
   - **Weight Trajectory vs Goal**: Historical weight curve with target goal weight reference line.
   - **Calorie Balance**: Direct comparison between intake (`kcal_in`) and expenditure (`kcal_out`) with net deficit/surplus.
   - **Sleep & Hydration Tracking**: Recovery metrics with active daily logging streak.
   - **Goal Forecast & Anomaly Detection**: Live forecast milestones and biometric anomaly warnings.

### User Authentication & Data Resolution
In the sidebar under **API Connection**, you can input either:
- **JWT Access Token**: Paste the token returned from `POST /api/v1/auth/login`. The dashboard queries `GET /api/v1/analytics/me` with `Authorization: Bearer <token>`.
- **User ID**: Paste a user ID (e.g. `usr_0001` or a MongoDB UUID). The dashboard queries `GET /api/v1/analytics/user/<user_id>` directly.
- **Live Refresh**: Click the **🔄 Refresh Live Data** button to invalidate and re-fetch real-time telemetry directly from the database with no stale caching.

3. **High-Availability Hybrid Architecture**
   - Automatically queries live FastAPI backend endpoints (`/api/v1/analytics/population` and `/api/v1/analytics/me`).
   - Gracefully falls back to pre-computed EDA aggregates (`data/eda_aggregates/`) when offline or disconnected.

---

## Dedicated Virtual Environment Setup

To prevent dependency and version conflicts (such as Starlette version mismatches between FastAPI and Streamlit), the dashboard is designed to run in its own dedicated virtual environment (`dashboard/.venv`).

### 1. Create Dashboard Virtual Environment

From the repository root:

```bash
# Windows (PowerShell)
python -m venv dashboard/.venv

# macOS / Linux
python3 -m venv dashboard/.venv
```

### 2. Activate & Install Dependencies

```bash
# Windows (PowerShell)
dashboard\.venv\Scripts\pip install -r dashboard/requirements.txt

# macOS / Linux
source dashboard/.venv/bin/activate
pip install -r dashboard/requirements.txt
```

---

## Running the Dashboard

### Start the Streamlit App

```bash
# Windows
.\dashboard\.venv\Scripts\streamlit run dashboard/app.py --server.port 8501

# macOS / Linux
dashboard/.venv/bin/streamlit run dashboard/app.py --server.port 8501
```

Access the dashboard in your browser at:
**`http://localhost:8501`**

---

## Running Dashboard Unit Tests

Dashboard unit tests verify all Plotly charts, loaders, and API fallback mechanisms:

```bash
# Run headless pytest suite
pytest dashboard/tests
```
