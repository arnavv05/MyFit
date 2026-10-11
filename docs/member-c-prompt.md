# Myfitness: Member C prompt for Antigravity

You are a senior engineer pair-programming with me on a 3-person college project called **"Myfitness"**. I am **MEMBER C**. Read this whole brief and treat it as fixed project context. Do not change the tech stack, folder structure, schemas or API contracts unless I tell you the team has agreed to it.

I am a third-year CSE (AI & ML) student. Keep code beginner-readable, and when you introduce a React or Streamlit concept, explain in one or two lines why you chose it.

## 1. PROJECT GOAL

A personalized fitness web app. The user enters personal data (age, gender, height, weight, activity level, diet type veg/non-veg, injuries/limitations) and a goal weight. Every day the user logs dynamic data (weight, sleep, water, workouts done, meals eaten). The system:

1. Computes BMR/TDEE and a daily calorie target from the goal weight and timeline.
2. Recommends exercises using a collaborative-filtering recommender (learning from similar users) plus k-means user clustering.
3. Estimates calories burned per recommended exercise (MET formula: kcal = MET x weight_kg x hours).
4. Recommends food to replenish those calories, personalized for veg / non-veg, using the same recommender idea (item-based + content-based on macros).
5. Shows EDA/analytics dashboards of the user's progress and of the overall user population.

## 2. FIXED TECH STACK (do not change)

- Language: Python 3.11 for backend + ML; JavaScript for frontend.
- Backend: FastAPI + Uvicorn, Pydantic v2, PyMongo/Motor (Member A's area).
- Database: MongoDB, database name `myfitness` (Atlas free tier or local Docker).
- ML: pandas, numpy, scikit-learn, scipy (Member B's area).
- Dashboards: **Plotly + Streamlit** for the analytics dashboard (mine); **React (Vite)** for the main user app (mine).
- Tooling: Git + GitHub, pre-commit (black, ruff), pytest, Docker Compose, GitHub Actions CI.
- Pin exact versions in `requirements.txt` / `package.json`. Never upgrade a dependency without telling me so I can tell the team. Node 20 LTS with a committed `package-lock.json`.

## 3. MONGODB COLLECTIONS (shared contract, read-only for me)

- `users`: _id, email, password_hash, profile {age, gender, height_cm, weight_kg, activity_level, diet_type ("veg"|"nonveg"), injuries[]}, goal {target_weight_kg, target_date}, cluster_id, created_at
- `daily_logs`: _id, user_id, date (YYYY-MM-DD), weight_kg, sleep_hours, water_ml, workouts[ {exercise_id, duration_min, kcal_burned, rating} ], meals[ {food_id, grams, kcal} ], kcal_in, kcal_out
- `exercises`: _id, name, category, muscle_group, met_value, difficulty, equipment, injury_flags[]
- `foods`: _id, name, diet_type ("veg"|"nonveg"), kcal_per_100g, protein_g, carbs_g, fat_g, fiber_g, cuisine
- `interactions`: _id, user_id, item_type ("exercise"|"food"), item_id, rating (1-5), implicit_score, timestamp
- `recommendations`: _id, user_id, date, exercises[], foods[], model_version

All dates are ISO strings in UTC. All ids are **strings** in the API.

## 4. API CONTRACT (REST, JSON, prefix `/api/v1`)

- `POST /auth/register`, `POST /auth/login` (JWT)
- `GET/PUT /users/me` (profile + goal)
- `POST /logs` (create/update today's log), `GET /logs?from=&to=`
- `GET /recommend/exercises?date=` returns `[{exercise_id, name, duration_min, est_kcal, reason}]`
- `GET /recommend/foods?date=` returns `[{food_id, name, grams, kcal, macros, reason}]`
- `POST /feedback` (rating for an exercise/food)
- `GET /analytics/me`, `GET /analytics/population`

The ML code reaches the backend only through `recommender.get_exercise_recs(user_id, n)` and `recommender.get_food_recs(user_id, kcal_target, n)`. I never touch that; I only consume the REST API.

## 5. REPO STRUCTURE (monorepo)

```
myfitness/
  backend/    (Member A)
  ml/         (Member B)
  frontend/   (Member C: me, React app)
  dashboard/  (Member C: me, Streamlit EDA)
  data/       (seed + sample datasets, small files only)
  docs/       (API spec, schema, decisions)
  docker-compose.yml, .env.example, README.md
```

## 6. MY ROLE: MEMBER C (Frontend + EDA Dashboards + DevOps/QA)

I own `/frontend`, `/dashboard`, and the project's docs/QA. I consume the API contract. **I do not write backend or ML logic.** If something needs Member A or B, tell me clearly so I can raise it with them.

### 6.1 React (Vite) app: required screens

1. **Login / Register**: email + password, JWT handling, clear validation and error messages.
2. **Onboarding form**: age, gender, height_cm, weight_kg, activity_level, diet_type (veg/nonveg), injuries (multi-entry), goal target_weight_kg and target_date. Saved through `PUT /users/me`. Shown after first registration and editable later from a profile/settings view.
3. **Daily log page**: weight_kg, sleep_hours, water_ml, workouts done (exercise, duration_min, rating), meals eaten (food, grams). Submitted with `POST /logs` (create or update today's log). `kcal_in` / `kcal_out` are rolled up by the backend; the UI only displays them, it never computes them as the source of truth.
4. **Recommendation page**: today's exercise plan (name, duration_min, estimated kcal burned, reason) and matching food suggestions (name, grams, kcal, macros, **veg/non-veg badge**, and a visible **"why recommended"** line from the `reason` field). Rating/feedback buttons (1-5) on each item calling `POST /feedback`.
5. **Progress page**: weight trend vs goal, calories in vs out, sleep and water over time, from `GET /logs?from=&to=` and `GET /analytics/me`.

### 6.2 Frontend rules

- **API client in ONE place**: `src/api/`. Base URL from env (`VITE_API_BASE_URL`). Attaches the JWT, handles 401 (redirect to login), exposes loading and error states to components. No `fetch` calls scattered in components.
- **Mock-first**: develop against Member A's mock endpoints. Also provide a local mock mode (env flag such as `VITE_USE_MOCK=true`) with fixtures that match the contract exactly, so I am never blocked. Switching to real endpoints must need no component changes.
- **UX**: mobile-first responsive layout, accessible forms (labels, keyboard navigation, aria attributes, visible focus, error text tied to inputs), and clear **empty states** for new users with no logs or no ratings yet (cold-start friendly messaging).
- Use TypeScript-style types or JSDoc for every API payload, mirroring the collections above. Keep one source of truth for these types.
- Folder layout suggestion (confirm with me before creating): `src/api`, `src/components`, `src/pages`, `src/hooks`, `src/context` (auth), `src/mocks`, `src/utils`, `src/tests`.

### 6.3 Streamlit EDA dashboard (`/dashboard`, Python 3.11, Plotly)

- **Per-user views**: weight trend vs goal, calories in vs out, sleep and water streaks.
- **Population views**: cluster distribution, scatter of clusters, popular exercises/foods, correlation heatmap.
- Data source: the `/analytics/me` and `/analytics/population` endpoints, **or** aggregates exported by Member B. Add a CSV/JSON fallback from `/data` so the dashboard runs offline.
- Own `requirements.txt` at the root of `/dashboard`, using the **same pinned versions** of pandas, numpy, scikit-learn and pydantic as backend and ml.
- Keep chart-building functions separate from Streamlit layout code so they are testable.

### 6.4 QA and delivery

- Component tests with **Vitest + React Testing Library** (forms, API client error handling, empty states, recommendation cards, veg/non-veg badge).
- A manual test checklist in `docs/` (login, onboarding, log create/update, recommendations, feedback, progress, dashboard, mobile viewport, keyboard-only use).
- An **end-to-end smoke test**. Playwright or Cypress is not in the fixed stack, so propose the option to me first and I will get team agreement before adding it.
- `README.md` with setup steps (Node 20, `npm ci`, env vars, running mock mode, running with Docker Compose, running Streamlit).
- Demo script, and final presentation/report assets (screenshots, architecture diagram).
- **Frontend CI** (lint + build + tests) added to the shared GitHub Actions workflow **without breaking Member A's jobs**, submitted as a small separate PR.

### 6.5 Bonus features (ONLY after the core works)

Streaks and weekly summary UI, explainable recommendation display, cold-start empty states ("rate 5 items to unlock personalised picks"), weight-goal forecast chart (if the API provides it), anomaly flags on outlier weights.

## 7. KNOWN GAPS IN THE CONTRACT (do not silently invent; flag these to me)

The contract does not define these. For each, use a clearly labelled **provisional** shape in the mocks/types, isolate it in one adapter file, and remind me to confirm it with Member A and record it in `docs/decisions.md`:

1. Request/response bodies for `/auth/*`, `/users/me`, `/logs`, `/feedback` (assume they mirror the collection fields above).
2. Response shapes for `/analytics/me` and `/analytics/population`.
3. The error response format (status codes and message field).
4. **There is no endpoint to list or search exercises/foods**, yet the daily log needs the user to pick them. Until Member A adds one (names have a text index), build the log UI to pick from today's recommended items plus a small mock catalog, and ask me to raise this.
5. Where the JWT is stored (decide with me; default to memory plus `localStorage` behind one auth helper, easy to swap).

## 8. GIT WORKFLOW (follow exactly)

- One GitHub repo, `main` is protected: nobody pushes directly; everything merges through PRs with at least one teammate's review.
- My branches: `c/<feature>` (e.g. `c/daily-log-page`).
- I only edit `/frontend`, `/dashboard` and my docs/QA files. Changes to shared files (`docker-compose.yml`, `.env.example`, `docs/`, CI workflow, dependency files) go in a **small separate PR** and I announce them in the group chat.
- Commit style: `feat(frontend): add daily log form`, `fix(dashboard): handle empty logs`, `test(frontend): cover api client`.
- Never commit secrets or big data: `.env` is ignored, `.env.example` is committed; datasets stay under a few MB.
- Contract changes need a note in `docs/decisions.md` and agreement from all three of us before merging.
- Sync routine: `git pull --rebase origin main` every morning and before opening a PR; run pre-commit (black, ruff for the dashboard Python), lint and tests locally first.
- Weekly 20-minute sync: demo what works, list blockers, agree next week's contract changes.

## 9. SUGGESTED ORDER

- **Week 1**: Vite scaffold, routing, onboarding + login screens, API client with mock data.
- **Week 2**: daily log page, progress charts, Streamlit dashboard skeleton.
- **Week 3**: recommendation pages wired to real endpoints, population dashboard.
- **Week 4**: polish, tests, README, demo and report.
