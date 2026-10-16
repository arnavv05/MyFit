"""Shared Pydantic v2 schemas for the Myfitness API (all collections)."""

from typing import Any, Literal
from pydantic import BaseModel, EmailStr, Field


# ==========================================
# USERS
# ==========================================
class UserProfile(BaseModel):
    age: int = Field(..., ge=10, le=120, description="Age in years")
    gender: Literal["male", "female", "other"] = Field(..., description="Gender")
    height_cm: float = Field(..., gt=50, lt=300, description="Height in centimeters")
    weight_kg: float = Field(..., gt=20, lt=500, description="Weight in kilograms")
    activity_level: Literal[
        "sedentary",
        "light",
        "lightly_active",
        "moderate",
        "moderately_active",
        "active",
        "very_active",
        "extra_active",
    ] = Field(..., description="Activity level for TDEE calculation")
    diet_type: Literal["veg", "nonveg"] = Field(..., description="Dietary preference")
    injuries: list[str] = Field(
        default_factory=list, description="Injuries or physical limitations"
    )


class UserGoal(BaseModel):
    target_weight_kg: float = Field(
        ..., gt=20, lt=500, description="Target weight in kilograms"
    )
    target_date: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Target date in ISO format YYYY-MM-DD",
    )


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        ..., min_length=6, description="Plaintext password, min 6 characters"
    )
    profile: UserProfile | None = None
    goal: UserGoal | None = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User profile returned to the client. Never includes password_hash."""

    id: str = Field(..., alias="_id")
    email: EmailStr
    profile: UserProfile
    goal: UserGoal
    cluster_id: int | None = None
    created_at: str

    model_config = {"populate_by_name": True}


class UserUpdateRequest(BaseModel):
    profile: UserProfile | None = None
    goal: UserGoal | None = None


# ==========================================
# EXERCISES & FOODS (Master Collections)
# ==========================================
class ExerciseItem(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    category: str
    muscle_group: str
    met_value: float = Field(..., gt=0, description="Metabolic Equivalent of Task")
    difficulty: str
    equipment: str
    injury_flags: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class FoodMacros(BaseModel):
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0.0


class FoodItem(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    diet_type: Literal["veg", "nonveg"]
    kcal_per_100g: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0.0
    cuisine: str = "general"

    model_config = {"populate_by_name": True}


# ==========================================
# DAILY LOGS
# ==========================================
class WorkoutLogEntry(BaseModel):
    exercise_id: str
    duration_min: float = Field(
        ..., gt=0, le=480, description="Duration in minutes (max 8 h)"
    )
    kcal_burned: float = Field(default=0.0, ge=0)
    rating: int | None = Field(default=None, ge=1, le=5)


class MealLogEntry(BaseModel):
    food_id: str
    grams: float = Field(..., gt=0, le=5000, description="Portion in grams (max 5 kg)")
    kcal: float = Field(default=0.0, ge=0)


class CatalogResponse(BaseModel):
    exercises: list[ExerciseItem] = Field(default_factory=list)
    foods: list[FoodItem] = Field(default_factory=list)


class DailyLogCreateRequest(BaseModel):
    date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date formatted as YYYY-MM-DD"
    )
    weight_kg: float | None = Field(
        default=None, gt=20, lt=500, description="Body weight (kg)"
    )
    sleep_hours: float | None = Field(
        default=None, ge=0, le=24, description="Sleep hours (0-24)"
    )
    water_ml: float | None = Field(
        default=None, ge=0, le=10000, description="Water intake (ml, max 10 L)"
    )
    workouts: list[WorkoutLogEntry] = Field(default_factory=list)
    meals: list[MealLogEntry] = Field(default_factory=list)


class DailyLogResponse(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    date: str
    weight_kg: float | None = None
    sleep_hours: float | None = None
    water_ml: float | None = None
    workouts: list[WorkoutLogEntry] = Field(default_factory=list)
    meals: list[MealLogEntry] = Field(default_factory=list)
    kcal_in: float = 0.0
    kcal_out: float = 0.0

    model_config = {"populate_by_name": True}


# ==========================================
# RECOMMENDATIONS
# ==========================================
class ExerciseRecItem(BaseModel):
    exercise_id: str
    name: str
    duration_min: float
    est_kcal: float
    reason: str


class FoodRecItem(BaseModel):
    food_id: str
    name: str
    diet_type: Literal["veg", "nonveg"] = "veg"
    grams: float
    kcal: float
    macros: FoodMacros
    reason: str


class RecommendationRecord(BaseModel):
    """Stored record in the recommendations collection."""

    id: str = Field(..., alias="_id")
    user_id: str
    rec_type: Literal["exercise", "food"]
    items: list[dict[str, Any]]
    model_version: str
    generated_at: str

    model_config = {"populate_by_name": True, "protected_namespaces": ()}


# ==========================================
# INTERACTIONS & FEEDBACK
# ==========================================
class FeedbackRequest(BaseModel):
    item_type: Literal["exercise", "food"]
    item_id: str
    rating: int = Field(..., ge=1, le=5)


class FeedbackResponse(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    item_type: Literal["exercise", "food"]
    item_id: str
    rating: int
    implicit_score: float
    timestamp: str

    model_config = {"populate_by_name": True}


# ==========================================
# ANALYTICS
# ==========================================
class WeightPoint(BaseModel):
    date: str
    weight_kg: float


class ForecastResult(BaseModel):
    expected_date: str | None = None
    days_remaining: int | None = None
    weekly_rate_kg: float | None = None
    on_track: bool | None = None
    message: str = ""


class WeightAnomaly(BaseModel):
    date: str
    weight_kg: float
    reason: str


class DailyCaloriePoint(BaseModel):
    date: str
    kcal_in: float = 0.0
    kcal_out: float = 0.0
    net_kcal: float = 0.0


class DailySummary(BaseModel):
    date: str
    weight_kg: float | None = None
    kcal_in: float = 0.0
    kcal_out: float = 0.0
    net_kcal: float = 0.0
    workouts_count: int = 0
    meals_count: int = 0
    sleep_hours: float | None = None
    water_ml: float | None = None


class WeeklySummary(BaseModel):
    total_kcal_in: float = 0.0
    total_kcal_out: float = 0.0
    avg_daily_kcal_in: float = 0.0
    avg_daily_kcal_out: float = 0.0
    workouts_completed: int = 0
    days_logged: int = 0


class UserAnalyticsResponse(BaseModel):
    user_id: str
    total_days_logged: int
    total_workouts_completed: int
    total_kcal_in: float
    total_kcal_out: float
    avg_sleep_hours: float | None
    avg_water_ml: float | None
    weight_history: list[WeightPoint]
    # Streak: consecutive days logged
    current_streak_days: int = 0
    best_streak_days: int = 0
    streak: int = 0  # alias for backward compatibility
    # Time-series and summary rollups
    calories_in_vs_out: list[DailyCaloriePoint] = Field(default_factory=list)
    today_summary: DailySummary | None = None
    weekly_summary: WeeklySummary | None = None
    goal_progress_pct: float = 0.0
    # ML-powered fields (from recommender package)
    goal_forecast: ForecastResult | None = None
    weight_anomalies: list[WeightAnomaly] = Field(default_factory=list)


class PopulationAnalyticsResponse(BaseModel):
    total_users: int
    total_logs_recorded: int
    average_age: float
    average_weight_kg: float
    average_height_cm: float
    diet_distribution: dict[str, int]
    activity_distribution: dict[str, int]
    cluster_distribution: dict[str, int] = Field(default_factory=dict)
    popular_exercises: list[dict[str, Any]] = Field(default_factory=list)
    popular_foods: list[dict[str, Any]] = Field(default_factory=list)
