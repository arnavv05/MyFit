# 💪 Myfitness

A full-stack, personalized fitness tracking and recommendation application with machine learning-driven recommendations and population telemetry dashboards.

---

## 🏛️ System Architecture & Roles

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   /frontend     │       │    /backend     │       │      /ml        │
│  React 19+Vite  │◄─────►│ FastAPI+MongoDB │◄─────►│ ML Recommender  │
│    (Member C)   │       │   (Member A)    │       │   (Member B)    │
└─────────────────┘       └────────┬────────┘       └─────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │   /dashboard    │
                          │Streamlit+Plotly │
                          │   (Member C)    │
                          └─────────────────┘
```

- **Member A (`/backend`)**: FastAPI REST API, MongoDB storage, JWT Authentication, and schema contracts under `/api/v1`.
- **Member B (`/ml`)**: Collaborative filtering, K-Means user clustering, and calorie estimation models.
- **Member C (`/frontend` & `/dashboard`)**:
  - Web Application: React 19, Vite, responsive UI, mock/live API adapters, Vitest unit tests, Playwright E2E smoke tests.
  - Analytics Dashboard: Streamlit + Plotly, live API client with automatic offline aggregate fallbacks, Pytest suite.

---

## 🚀 Quickstart & Running Locally

### 1. Frontend (`/frontend`)
```bash
cd frontend
npm ci

# Run with mock data (default for offline development):
npm run dev

# Run against live backend:
# Set VITE_USE_MOCK=false and VITE_API_BASE_URL=http://localhost:8000/api/v1 in frontend/.env
npm run dev
```

### 2. Backend (`/backend`)
```bash
# Requires MongoDB running on localhost:27017
uvicorn backend.app.main:app --reload --port 8000
```

### 3. Analytics Dashboard (`/dashboard`)
```bash
# Install Python dependencies:
pip install -r dashboard/requirements.txt

# Launch Streamlit dashboard:
streamlit run dashboard/app.py
```
> The dashboard operates in two view modes:
> - **Population Analytics**: Live `/analytics/population` telemetry with automatic fallback to precomputed aggregates (`data/eda_aggregates/`).
> - **My Personal Analytics**: Per-user trajectory tracking from `/analytics/me` with token authentication.

---

## 🧪 Testing & Verification

| Component | Framework | Command |
| :--- | :--- | :--- |
| Frontend Unit Tests | Vitest | `cd frontend && npm test` |
| Frontend E2E Smoke | Playwright | `cd frontend && npm run test:e2e` |
| Frontend Linting | Oxlint | `cd frontend && npm run lint` |
| Dashboard Unit Tests | Pytest | `pytest dashboard -q` |
| Dashboard Typing | Mypy | `mypy dashboard` |

---

## 📋 CI/CD Pipeline

Automated checks run via GitHub Actions (`.github/workflows/frontend-ci.yml`):
- **Frontend CI (`test-and-build`)**: Installs Node 20 LTS, runs Oxlint, Vitest, and production Vite bundle build.
- **Dashboard CI (`dashboard-test`)**: Installs Python 3.11, dashboard requirements, and executes the Pytest test suite.
