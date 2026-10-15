# Myfitness REST API Specification

Base URL: `http://localhost:8000/api/v1`  
Interactive OpenAPI UI: `http://localhost:8000/docs`  
ReDoc UI: `http://localhost:8000/redoc`

All authenticated endpoints require the header:  
`Authorization: Bearer <jwt_access_token>`

---

## 1. Authentication Endpoints

### 1.1 Register
- **Path**: `POST /auth/register`
- **Status**: `201 Created`
- **Request**:
  ```json
  {
    "email": "student@example.com",
    "password": "strongPassword123"
  }
  ```
- **Response**:
  ```json
  {
    "id": "673f...",
    "email": "student@example.com",
    "created_at": "2026-10-15T12:00:00Z"
  }
  ```

### 1.2 Login
- **Path**: `POST /auth/login`
- **Status**: `200 OK`
- **Request**:
  ```json
  {
    "email": "student@example.com",
    "password": "strongPassword123"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

---

## 2. User Profile & Onboarding

### 2.1 Get Current Profile
- **Path**: `GET /users/me`
- **Auth**: Required
- **Status**: `200 OK`
- **Response**: Full `UserOut` object containing `profile` and `goal`.

### 2.2 Update Profile / Onboard
- **Path**: `PUT /users/me`
- **Auth**: Required
- **Status**: `200 OK`
- **Request**:
  ```json
  {
    "profile": {
      "age": 24,
      "gender": "female",
      "height_cm": 165.0,
      "weight_kg": 62.0,
      "activity_level": "moderately_active",
      "dietary_preference": "veg",
      "injuries": ["knee"]
    },
    "goal": {
      "target_weight_kg": 58.0,
      "target_date": "2026-12-31",
      "primary_goal": "weight_loss"
    }
  }
  ```

---

## 3. Daily Logging

### 3.1 Submit Daily Log
- **Path**: `POST /logs`
- **Auth**: Required
- **Status**: `200 OK` / `201 Created`
- **Request**:
  ```json
  {
    "date": "2026-10-15",
    "weight_kg": 62.0,
    "sleep_hours": 7.5,
    "water_ml": 2500,
    "workouts": [
      {
        "exercise_id": "ex_001",
        "duration_min": 30,
        "kcal_burned": 150.0
      }
    ],
    "meals": [
      {
        "food_id": "fd_001",
        "grams": 200,
        "kcal": 260.0,
        "meal_type": "lunch"
      }
    ]
  }
  ```

### 3.2 Query Daily Logs
- **Path**: `GET /logs?from=2026-10-01&to=2026-10-15`
- **Auth**: Required
- **Status**: `200 OK`
- **Response**: Array of `DailyLogOut` objects.

---

## 4. Catalogs & Search

### 4.1 Search Exercises Catalog
- **Path**: `GET /exercises?q=squat&category=strength`
- **Status**: `200 OK`
- **Query Params**: `q` (optional text search), `category` (optional filter)
- **Response**: List of `ExerciseItem` objects.

### 4.2 Search Foods Catalog
- **Path**: `GET /foods?q=paneer&is_veg=true`
- **Status**: `200 OK`
- **Query Params**: `q` (optional text search), `is_veg` (boolean filter), `category`
- **Response**: List of `FoodItem` objects.

---

## 5. ML Recommendations

### 5.1 Exercise Recommendations
- **Path**: `GET /recommend/exercises?limit=5`
- **Auth**: Required
- **Status**: `200 OK`
- **Response**:
  ```json
  [
    {
      "exercise_id": "ex_004",
      "name": "Stationary Cycling (Light)",
      "duration_min": 30.0,
      "est_kcal": 140.0,
      "reason": "Popular core workout safe for your activity level."
    }
  ]
  ```

### 5.2 Food Recommendations
- **Path**: `GET /recommend/foods?limit=5`
- **Auth**: Required
- **Status**: `200 OK`
- **Response**:
  ```json
  [
    {
      "food_id": "fd_015",
      "name": "Soya Chunks (Dry)",
      "is_veg": true,
      "grams": 170.0,
      "kcal": 586.5,
      "macros": {
        "protein_g": 88.4,
        "carbs_g": 56.1,
        "fat_g": 0.8,
        "fiber_g": 22.1
      },
      "reason": "High-protein veg food (52.0g/100g) ideal for post-workout recovery."
    }
  ]
  ```

### 5.3 Submit Feedback / Ratings
- **Path**: `POST /feedback`
- **Auth**: Required
- **Status**: `201 Created`
- **Request**:
  ```json
  {
    "item_type": "exercise",
    "item_id": "ex_004",
    "rating": 5
  }
  ```

---

## 6. Analytics

### 6.1 Personal Progress & Telemetry
- **Path**: `GET /analytics/me`
- **Auth**: Required
- **Status**: `200 OK`
- **Response**: Contains streaks, weight history, workout count, and anomaly signals.

### 6.2 Population Analytics
- **Path**: `GET /analytics/population`
- **Status**: `200 OK`
- **Response**: Total users, cluster distributions, diet ratios, and top exercises/foods.
