# Myfitness Frontend (React + Vite)

Frontend application for the **Myfitness** personalized fitness web app (Member C).

---

## 1. Prerequisites

- **Node.js**: `v20.x LTS` (Node 20 LTS is the team standard)
- **npm**: `v10.x` or higher

---

## 2. Quick Start

### 2.1 Install Dependencies
```bash
npm ci
```
> `npm ci` installs exact versions from `package-lock.json` — use this instead of `npm install` on CI and when pairing with teammates.

### 2.2 Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default values in `.env.example`:
```env
# URL for Member A's FastAPI backend
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Enable local mock mode (true = offline, false = live backend)
VITE_USE_MOCK=true
```

### 2.3 Run Development Server
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 3. Running Against the Live Backend

Requires Member A's FastAPI service and a MongoDB instance.

**Step 1 — Start the backend** (from repo root):
```bash
# Install backend deps once
pip install -r backend/requirements.txt
# Optional: seed exercise/food catalog
python -m backend.app.db.seed
# Start FastAPI
uvicorn backend.app.main:app --reload --port 8000
```

**Step 2 — Set env vars** in `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_USE_MOCK=false
```

**Step 3 — Start the frontend:**
```bash
npm run dev
```

**Step 4 — Verify:** open [http://localhost:5173](http://localhost:5173), register a new account (with profile + goal), log in, and check the Progress page.

> **Live Backend Endpoints:**
> - Connected to live backend at `/api/v1` with full catalog support (`/api/v1/catalog`), JWT authentication, daily log persistence, recommendations, feedback, and telemetry analytics.


---

## 4. Project Architecture

The `/frontend` code is strictly decoupled and modular:

```
src/
├── api/             # Single source of truth for API communication & auth storage
│   ├── client.js    # Fetch client: JWT injection, error normalisation, 401 events, mock toggle
│   ├── authStorage.js # LocalStorage wrapper for token persistence
│   └── types.js     # JSDoc type definitions matching backend schemas
├── components/      # Reusable UI components (Alert, Badge, EmptyState, Navbar)
├── context/         # AuthContext & AuthProvider for global session state
├── hooks/           # Custom React hooks (e.g. useAuth)
├── mocks/           # Local fixtures + handlers matching backend contracts exactly
│   ├── fixtures.js
│   └── mockHandlers.js
├── pages/           # Application views
│   ├── LoginPage.jsx
│   ├── RegisterPage.jsx
│   ├── OnboardingPage.jsx
│   ├── DailyLogPage.jsx
│   ├── RecommendationsPage.jsx
│   └── ProgressPage.jsx
├── tests/           # Vitest + React Testing Library test suites
│   ├── apiClient.test.js
│   └── components.test.jsx
├── App.jsx          # Root component & hash router
└── index.css        # Global modern design system & CSS tokens
```

---

## 5. Scripts & Verification

| Command | Description |
|---|---|
| `npm ci` | Install exact locked dependencies |
| `npm run dev` | Starts Vite HMR dev server on port 5173 |
| `npm run build` | Produces optimized production bundle in `dist/` |
| `npm test` | Runs the full Vitest suite (12 tests) |
| `npm run lint` | Runs the high-speed Oxlint linter |
| `npm run preview` | Previews the production build locally |

---

## 6. Mock Mode vs Live Backend

| | Mock (`VITE_USE_MOCK=true`) | Live (`VITE_USE_MOCK=false`) |
|---|---|---|
| Requires backend? | ❌ No | ✅ Yes (port 8000) |
| Requires MongoDB? | ❌ No | ✅ Yes |
| Tests run in? | Mock always | — |
| Data persists? | In-memory only | MongoDB |

All pages work identically in both modes — the toggle is a single env var.
