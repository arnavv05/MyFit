from datetime import datetime
from typing import Literal
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
    injuries: list[str] = Field(default_factory=list, description="Injuries or physical limitations")


class UserGoal(BaseModel):
    target_weight_kg: float = Field(..., gt=20, lt=500, description="Target weight in kilograms")
    target_date: str = Field(..., description="Target date in ISO format YYYY-MM-DD")


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Plaintext password, min 6 characters")
    profile: UserProfile | None = None
    goal: UserGoal | None = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
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
    duration_min: float = Field(..., gt=0)
    kcal_burned: float = Field(default=0.0, ge=0)
    rating: int | None = Field(default=None, ge=1, le=5)


class MealLogEntry(BaseModel):
    food_id: str
    grams: float = Field(..., gt=0)
    kcal: float = Field(default=0.0, ge=0)


class CatalogResponse(BaseModel):
    exercises: list[ExerciseItem] = Field(default_factory=list)
    foods: list[FoodItem] = Field(default_factory=list)


class DailyLogCreateRequest(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date formatted as YYYY-MM-DD")
    weight_kg: float | None = Field(default=None, gt=20, lt=500)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    water_ml: float | None = Field(default=None, ge=0)
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
    grams: float
    kcal: float
    macros: FoodMacros
    reason: str


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
