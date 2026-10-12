from datetime import datetime
from fastapi import APIRouter, Depends, Query
from backend.app.api.deps import get_current_user
from backend.app.schemas.all_schemas import (
    ExerciseRecItem,
    FoodRecItem,
    UserProfile,
    UserGoal,
)
from backend.app.services.nutrition import calculate_daily_calorie_target
from backend.app.services.recommender_service import recommender_service

router = APIRouter(prefix="/recommend", tags=["Recommendations"])


@router.get("/exercises", response_model=list[ExerciseRecItem])
async def recommend_exercises(
    date: str | None = Query(None, description="Recommendation target date YYYY-MM-DD"),
    limit: int = Query(3, ge=1, le=10, description="Number of recommendations"),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve personalized exercise recommendations for the authenticated user.
    Calls recommender package interface: recommender.get_exercise_recs(user_id, n).
    """
    user_id = current_user["_id"]
    # Interface call
    recs = recommender_service.get_exercise_recs(user_id=user_id, n=limit)
    return recs


@router.get("/foods", response_model=list[FoodRecItem])
async def recommend_foods(
    date: str | None = Query(None, description="Recommendation target date YYYY-MM-DD"),
    limit: int = Query(3, ge=1, le=10, description="Number of recommendations"),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve personalized food recommendations tailored to caloric deficit/target.
    Calls recommender package interface: recommender.get_food_recs(user_id, kcal_target, n).
    """
    user_id = current_user["_id"]
    profile = UserProfile(**current_user["profile"])
    goal = UserGoal(**current_user["goal"])

    # Calculate personalized calorie target for the recommender
    kcal_target = calculate_daily_calorie_target(profile, goal)

    # Interface call
    recs = recommender_service.get_food_recs(user_id=user_id, kcal_target=kcal_target, n=limit)
    return recs
