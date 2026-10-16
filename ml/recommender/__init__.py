"""Myfitness Recommender Package.

This package exposes the official Python interface for Member A's FastAPI backend:
- `get_exercise_recs(user_id: str, n: int = 4)`
- `get_food_recs(user_id: str, kcal_target: float = 400.0, n: int = 3)`
- `model_version: str`
- `predict_cluster(user_dict: dict, logs: list[dict] = None)`

All return structures conform strictly to the Myfitness shared API contract.
"""

from typing import Any

from pydantic import BaseModel, Field

from recommender.anomaly import detect_daily_log_anomalies, detect_weight_anomalies
from recommender.clustering import predict_cluster
from recommender.config import MODEL_VERSION
from recommender.data_access import BaseDataAccess, get_data_access
from recommender.exercise_recs import recommend_exercises_for_user
from recommender.food_recs import recommend_foods_for_user
from recommender.forecast import forecast_goal_date

# Public version string
model_version: str = MODEL_VERSION


# Pydantic v2 schemas for validation
class MacroBreakdown(BaseModel):
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float


class ExerciseRecommendation(BaseModel):
    exercise_id: str
    name: str
    duration_min: int = Field(ge=1)
    est_kcal: float = Field(ge=0.0)
    reason: str


class FoodRecommendation(BaseModel):
    food_id: str
    name: str
    diet_type: str = "veg"
    grams: float = Field(gt=0.0)
    kcal: float = Field(ge=0.0)
    macros: MacroBreakdown
    reason: str


def get_exercise_recs(
    user_id: str,
    n: int = 4,
    data_access: BaseDataAccess | None = None,
    target_burn_kcal: float = 350.0,
    user_dict: dict[str, Any] | None = None,
    date: str | None = None,
) -> list[dict[str, Any]]:
    """Return top-N exercise recommendations matching the shared API contract.

    Args:
        user_id: Unique string identifier of the user.
        n: Number of recommendations to return (default 4).
        data_access: Optional custom DataAccess instance (default uses configured factory).
        target_burn_kcal: Optional daily workout burn target in kcal (default 350.0).
        user_dict: Optional user context dict from MongoDB or auth session.
        date: Optional date string for daily variety rotation.

    Returns:
        List of dicts: [{exercise_id, name, duration_min, est_kcal, reason}]
    """
    raw_recs = recommend_exercises_for_user(
        user_id=user_id,
        n=n,
        data_access=data_access,
        target_burn_kcal=target_burn_kcal,
        user_dict=user_dict,
        date=date,
    )
    # Validate each item through Pydantic model and return as JSON-serializable plain dict
    validated = [ExerciseRecommendation(**item).model_dump() for item in raw_recs]
    return validated


def get_food_recs(
    user_id: str,
    kcal_target: float = 400.0,
    n: int = 3,
    data_access: BaseDataAccess | None = None,
    user_dict: dict[str, Any] | None = None,
    date: str | None = None,
) -> list[dict[str, Any]]:
    """Return top-N food recommendations matching the shared API contract.

    Args:
        user_id: Unique string identifier of the user.
        kcal_target: Daily or post-workout calorie replenishment target.
        n: Number of food recommendations to return (default 3).
        data_access: Optional custom DataAccess instance.
        user_dict: Optional user context dict from MongoDB or auth session.
        date: Optional date string for daily variety rotation.

    Returns:
        List of dicts: [{food_id, name, diet_type, grams, kcal, macros: {...}, reason}]
    """
    raw_recs = recommend_foods_for_user(
        user_id=user_id,
        kcal_target=kcal_target,
        n=n,
        data_access=data_access,
        user_dict=user_dict,
        date=date,
    )
    # Validate each item through Pydantic model and return as JSON-serializable plain dict
    validated = [FoodRecommendation(**item).model_dump() for item in raw_recs]
    return validated


__all__ = [
    "BaseDataAccess",
    "ExerciseRecommendation",
    "FoodRecommendation",
    "MacroBreakdown",
    "detect_daily_log_anomalies",
    "detect_weight_anomalies",
    "forecast_goal_date",
    "get_data_access",
    "get_exercise_recs",
    "get_food_recs",
    "model_version",
    "predict_cluster",
]
