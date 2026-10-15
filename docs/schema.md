# Database & Schema Specifications

This document defines the MongoDB database models, collection structures, index strategies, and Pydantic validation schemas for the **Myfitness** application.

---

## 1. Database & Collections

- **Database Name**: `myfitness` (configured via `MONGODB_DB_NAME`)
- **Engine**: MongoDB Atlas / MongoDB 6.0+
- **ORM / ODM**: Asynchronous Motor (`AsyncIOMotorClient`) with Pydantic v2 validation.

### Collection Indexing Strategy

| Collection | Key / Field | Type | Properties | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `email` | B-Tree | `unique: true` | Prevents duplicate user accounts |
| `daily_logs` | `(user_id, date)` | Compound B-Tree | `unique: true` | Enforces one canonical log per user per day |
| `daily_logs` | `user_id` | Single B-Tree | `background: true` | Fast chronological user log retrieval |
| `exercises` | `name`, `category` | Text Index | `weights: {name: 10, category: 5}` | Full-text catalog search (`/exercises?q=`) |
| `foods` | `name`, `category` | Text Index | `weights: {name: 10, category: 5}` | Full-text catalog search (`/foods?q=`) |
| `interactions` | `(user_id, item_id)` | Compound B-Tree | `background: true` | Fast collaborative filtering feedback queries |

---

## 2. Core Pydantic Schemas

### 2.1 User Profile & Goals

```python
class UserProfile(BaseModel):
    age: int = Field(..., ge=10, le=120)
    gender: Literal["male", "female", "other"]
    height_cm: float = Field(..., gt=50, lt=300)
    weight_kg: float = Field(..., gt=20, lt=500)
    activity_level: Literal[
        "sedentary",
        "lightly_active",
        "moderately_active",
        "very_active",
        "extra_active",
    ]
    dietary_preference: Literal["veg", "nonveg", "any"]
    injuries: list[str] = Field(default_factory=list)


class UserGoal(BaseModel):
    target_weight_kg: float = Field(..., gt=20, lt=500)
    target_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    primary_goal: Literal[
        "weight_loss", "muscle_gain", "maintenance", "endurance"
    ]
```

### 2.2 Daily Logging

```python
class WorkoutItem(BaseModel):
    exercise_id: str
    duration_min: float = Field(..., gt=0, le=360)
    kcal_burned: float = Field(..., ge=0)
    notes: Optional[str] = None


class MealItem(BaseModel):
    food_id: str
    grams: float = Field(..., gt=0, le=3000)
    kcal: float = Field(..., ge=0)
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]


class DailyLogCreate(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    weight_kg: Optional[float] = Field(None, gt=20, lt=500)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    water_ml: Optional[float] = Field(None, ge=0, le=10000)
    workouts: list[WorkoutItem] = Field(default_factory=list)
    meals: list[MealItem] = Field(default_factory=list)
```

### 2.3 Catalogs & Datasets

- **`Exercise` Schema**:
  - `id`: Unique string (`ex_001` .. `ex_060`)
  - `name`: Exercise title
  - `category`: `cardio`, `strength`, `flexibility`, `mobility`
  - `met`: Metabolic Equivalent of Task score (e.g. `8.0` for vigorous running)
  - `injury_flags`: Semicolon-separated contraindicated injuries (`knee`, `wrist`, `lower_back`, `shoulder`)
  - `equipment`: `bodyweight`, `dumbbells`, `barbell`, `machine`, etc.

- **`Food` Schema**:
  - `id`: Unique string (`fd_001` .. `fd_060`)
  - `name`: Food title
  - `category`: `grain`, `protein`, `dairy`, `fruit`, `vegetable`
  - `is_veg`: Boolean flag (`true` = vegetarian compliant, `false` = non-vegetarian)
  - `kcal_per_100g`: Caloric density per 100g
  - `macros`: `{ protein_g, carbs_g, fat_g, fiber_g }`

---

## 3. Nutrition Formulas

### Mifflin-St Jeor BMR Equation
$$\text{BMR}_{\text{male}} = 10 \times \text{weight (kg)} + 6.25 \times \text{height (cm)} - 5 \times \text{age (yr)} + 5$$
$$\text{BMR}_{\text{female}} = 10 \times \text{weight (kg)} + 6.25 \times \text{height (cm)} - 5 \times \text{age (yr)} - 161$$

### Total Daily Energy Expenditure (TDEE)
$$\text{TDEE} = \text{BMR} \times \text{Activity Multiplier}$$
- `sedentary`: $1.20$
- `lightly_active`: $1.375$
- `moderately_active`: $1.55$
- `very_active`: $1.725$
- `extra_active`: $1.90$

### Calorie Burn Calculation (Compendium of Physical Activities)
$$\text{Burn (kcal)} = \text{MET} \times \text{weight (kg)} \times \frac{\text{duration (min)}}{60}$$
