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
npm install
```

### 2.2 Configure Environment
Copy `.env.example` to `.env` (or use the pre-configured `.env`):
```env
# URL for Member A's FastAPI backend
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Enable local mock mode for development without running the backend
VITE_USE_MOCK=true
```

### 2.3 Run Development Server
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 3. Project Architecture

The `/frontend` code is strictly decoupled and modular:

```
src/
├── api/             # Single source of truth for API communication & auth storage
│   ├── apiClient.js # Fetch client with JWT handling, error normalisation, 401 events
│   ├── authStorage.js # LocalStorage wrapper for token persistence
│   └── index.js
├── components/      # Reusable UI components (Alert, Badge, EmptyState, Navbar)
├── context/         # AuthContext & AuthProvider for global session state
├── hooks/           # Custom React hooks (e.g. useAuth)
├── mocks/           # Local fixtures matching Member A & B's API contracts exactly
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
├── App.jsx          # Root component & page router
└── index.css        # Global modern design system & CSS tokens
```

---

## 4. Scripts & Verification

| Command | Description |
|---|---|
| `npm run dev` | Starts Vite HMR dev server on port 5173 |
| `npm run build` | Produces optimized production bundle in `dist/` |
| `npm test` | Runs the full Vitest suite (12 tests) |
| `npm run lint` | Runs the high-speed Oxlint linter |
| `npm run preview` | Previews the production build locally |

---

## 5. Mock Mode vs Live Backend

When `VITE_USE_MOCK=true`, the API client routes all requests through `src/mocks/fixtures.js`. This allows:
- Full offline testing and UI development.
- Instant feedback during development without requiring Docker or MongoDB.
- Seamless transition to live endpoints by setting `VITE_USE_MOCK=false` with zero component code changes.
