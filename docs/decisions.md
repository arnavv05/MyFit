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

## 3. Provisional Shapes (Pending Member A Confirmation)

> [!NOTE]
> The following schemas are provisionally implemented in the frontend mock layer. Member C will confirm them with Member A.

### 3.1 Analytics (`/analytics/me` and `/analytics/population`)
- `GET /analytics/me`:
  ```json
  {
    "streak_days": 5,
    "total_workouts": 14,
    "weight_change_kg": -1.2,
    "calorie_target": 2100,
    "avg_sleep_hours": 7.4,
    "avg_water_ml": 2400,
    "history": [
      {
        "date": "2026-10-10",
        "weight_kg": 72.4,
        "kcal_in": 2050,
        "kcal_out": 2200,
        "sleep_hours": 7.0,
        "water_ml": 2200
      }
    ]
  }
  ```
- `GET /analytics/population`:
  ```json
  {
    "cluster_count": 4,
    "clusters": [
      {
        "cluster_id": 0,
        "name": "Sedentary Weight Loss",
        "user_count": 45,
        "avg_age": 28,
        "avg_weight": 84
      }
    ],
    "popular_exercises": [
      { "name": "Push-ups", "count": 120 }
    ],
    "popular_foods": [
      { "name": "Oatmeal", "count": 98 }
    ]
  }
  ```

### 3.2 Error Responses
- FastAPI Standard HTTP exception:
  ```json
  {
    "detail": "Descriptive error message"
  }
  ```

### 3.3 Catalog Search / Listing Gap
- **Issue**: Contract currently lacks `GET /exercises` and `GET /foods` to search or pick items for logging.
- **Frontend Fallback**: The Daily Log screen will provide items from today's recommendations plus a built-in search catalog.
- **Action for Member A**: Propose adding `GET /exercises?q=` and `GET /foods?q=` endpoints with MongoDB text search.
