# Architecture & API Decisions

This document records shared architectural choices, API contracts, and provisional schemas for the **Myfitness** project.
Any changes to shared contracts require team consensus (Members A, B, and C) before merging to `main`.

---

## 1. Roles & Scope Boundary
- **Member A**: Backend API (FastAPI + MongoDB `myfitness`), Authentication (JWT), Database schemas.
- **Member B**: Machine Learning models (Collaborative Filtering, K-Means clustering, calorie estimation).
- **Member C**: Frontend application (`/frontend`, React + Vite) & Analytics dashboard (`/dashboard`, Streamlit + Plotly).

---

## 2. Shared MongoDB Collections & API Shapes

Base API Prefix: `/api/v1`

### 2.1 Authentication (`/auth`)
- `POST /auth/register`
  - **Request**: `{ "email": "user@example.com", "password": "securepassword", "profile": {...}, "goal": {...} }`
  - **Response**: `UserResponse` object (user only — **no token**). Frontend adapter immediately calls `POST /auth/login` to obtain a token.
- `POST /auth/login`
  - **Request**: `{ "email": "user@example.com", "password": "securepassword" }`
  - **Response**: `{ "access_token": "string", "token_type": "bearer" }` — no `user_id`.
- **JWT Storage**: Stored in `localStorage` behind an auth helper service (`src/api/authStorage.js`) to allow seamless migration to httpOnly cookies if needed.

### 2.2 User Profile & Goals (`/users/me`)
- `GET /users/me`
- `PUT /users/me`
  - **Body**:
    ```json
    {
      "profile": {
        "age": 22,
        "gender": "male",
        "height_cm": 175,
        "weight_kg": 72.5,
        "activity_level": "moderately_active",
        "diet_type": "veg",
        "injuries": ["knee"]
      },
      "goal": {
        "target_weight_kg": 68.0,
        "target_date": "2026-12-31"
      }
    }
    ```
  - **Note**: `activity_level` values: `sedentary | lightly_active | moderately_active | very_active | extra_active`

### 2.3 Daily Logs (`/logs`)
- `POST /logs` (Create or update today's log)
  - **Body**:
    ```json
    {
      "date": "2026-10-11",
      "weight_kg": 72.3,
      "sleep_hours": 7.5,
      "water_ml": 2500,
      "workouts": [
        {
          "exercise_id": "ex_101",
          "duration_min": 30,
          "kcal_burned": 178,
          "rating": 4
        }
      ],
      "meals": [
        {
          "food_id": "fd_201",
          "grams": 200,
          "kcal": 260
        }
      ]
    }
    ```
  - **⚠ CORRECTION (was wrong in earlier version of this doc):** `kcal_burned` and `kcal` are **required** and must be computed by the **frontend** before POSTing. Formula: `kcal_burned = MET × weight_kg × (duration_min / 60)`; `kcal = kcal_per_100g × grams / 100`. The server only sums them — it does not compute them.
  - **Response**: Full `daily_log` object with `kcal_in` (sum of meal kcal) and `kcal_out` (sum of workout kcal_burned).
- `GET /logs?from=YYYY-MM-DD&to=YYYY-MM-DD`: Array of daily log records.

### 2.4 Recommendations (`/recommend`)
- `GET /recommend/exercises?date=YYYY-MM-DD`
  - **Response**:
    ```json
    [
      {
        "exercise_id": "ex_101",
        "name": "Brisk Walking",
        "duration_min": 30,
        "est_kcal": 150,
        "reason": "Low impact match for your knee injury limitation"
      }
    ]
    ```
- `GET /recommend/foods?date=YYYY-MM-DD`
  - **Response**:
    ```json
    [
      {
        "food_id": "fd_201",
        "name": "Tofu Stir-fry",
        "diet_type": "veg",
        "grams": 250,
        "kcal": 320,
        "macros": { "protein_g": 22, "carbs_g": 18, "fat_g": 12, "fiber_g": 5 },
        "reason": "High protein vegetarian recovery replenishment"
      }
    ]
    ```

### 2.5 Feedback (`/feedback`)
- `POST /feedback`
  - **Body**:
    ```json
    {
      "item_type": "exercise",
      "item_id": "ex_101",
      "rating": 5
    }
    ```

---

## 3. Ratified Architecture Decisions & Updates

### 3.1 Analytics (`/analytics/me` and `/analytics/population`)
- **Status**: **RATIFIED & IMPLEMENTED**
- `GET /analytics/me`: Provides personal metrics including active workout count, streak days, weight trends, and automated anomaly warnings for rapid fluctuations (>1.5kg/week or high calorie deficit).
- `GET /analytics/population`: Provides population-level metrics across all active users: K-Means cluster distributions (3 fitness archetypes), diet ratios, and overall popular workouts and foods.

### 3.2 Catalog Search Endpoints
- **Status**: **RATIFIED & IMPLEMENTED**
- `GET /exercises?q=&category=`: Supports live text filtering across name and category with MongoDB text indexing.
- `GET /foods?q=&is_veg=&category=`: Supports live search and strict dietary preference filtering.

### 3.3 Error Handling & UX Contract
- **Status**: **RATIFIED & IMPLEMENTED**
- Standardized HTTP status codes (201 Created for register/feedback, 200 OK for standard fetches, 401 Unauthorized for expired/missing JWT, 409 Conflict for duplicate emails, 422 Unprocessable Entity for schema validation failures).
- Frontend never displays raw stack traces; standard friendly alert toasts and banners are presented. On 401, client automatically clears session and transitions to `/login`.

### 3.4 Isolated Streamlit Environment
- **Status**: **RATIFIED & IMPLEMENTED**
- To prevent dependency pinning collisions between FastAPI/Starlette and Streamlit, the Streamlit dashboard runs in an isolated `dashboard/.venv`.
- Both environments cleanly communicate over HTTP to `/api/v1` with a seamless fallback to local EDA aggregates (`data/eda_aggregates/`) when the API is offline.

### 3.5 Additive Schema Extensions & Personalization (Fix Iteration October 2026)
- **Status**: **RATIFIED & IMPLEMENTED**
- **Food `diet_type` Tagging**: Added `diet_type: "veg" | "nonveg"` to `FoodRecItem`, catalog responses, and seed data. Strict hard-filter applied at both ML engine level and backend API router level.
- **Recommender Context Passing**: `get_exercise_recs` and `get_food_recs` accept optional `user_dict` and `date` for seamless personalization for newly registered MongoDB users without CSV synchronization delay. Incorporates dynamic cluster prediction, joint safety exclusion, and interaction rating adaptation ($\le 2$ excluded, $\ge 4$ boosted).
- **Time-Series Analytics**: `UserAnalyticsResponse` includes additive fields `calories_in_vs_out` (daily per-day In vs Out balance), `today_summary`, `weekly_summary`, `current_streak_days`, `best_streak_days`, and `goal_progress_pct`.
- **Direct User Telemetry Route**: Added `GET /analytics/user/{user_id}` allowing admin and dashboard telemetry resolution via user ID or JWT Bearer token.

