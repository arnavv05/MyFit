"""Recommendation routes: GET /recommend/exercises, GET /recommend/foods."""

import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.api.deps import get_current_user
from backend.app.db.mongodb import get_database
from backend.app.schemas.all_schemas import (
    ExerciseRecItem,
    FoodMacros,
    FoodRecItem,
    UserProfile,
    UserGoal,
)
from backend.app.services.nutrition import (
    calculate_daily_calorie_target,
    calculate_tdee,
)
from backend.app.services.recommender_service import recommender_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommend", tags=["Recommendations"])


async def _store_recommendation(
    db: AsyncIOMotorDatabase,
    user_id: str,
    rec_type: str,
    items: list,
) -> None:
    """Persist recommendation result to recommendations collection."""
    doc = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "rec_type": rec_type,
        "items": [
            item.model_dump() if hasattr(item, "model_dump") else dict(item)
            for item in items
        ],
        "model_version": recommender_service.model_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "is_mock": recommender_service.is_mock,
    }
    await db["recommendations"].insert_one(doc)


@router.get(
    "/exercises",
    response_model=list[ExerciseRecItem],
    summary="Personalised exercise recommendations",
    responses={
        200: {"description": "List of recommended exercises"},
        401: {"description": "Not authenticated"},
    },
)
async def recommend_exercises(
    date: str | None = Query(
        None, description="Target date (YYYY-MM-DD, informational)"
    ),
    limit: int = Query(3, ge=1, le=10, description="Number of recommendations"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Get personalised exercise recommendations.

    Calls `recommender.get_exercise_recs(user_id, n, target_burn_kcal)` where
    `target_burn_kcal` is derived from the user's TDEE and goal (as documented in
    ml/README.md).

    Results are stored in the **recommendations** collection with `model_version`.
    """
    user_id = current_user["_id"]

    # Compute daily calorie target → use TDEE surplus as burn target
    try:
        profile = UserProfile(**current_user["profile"])
        _ = UserGoal(**current_user["goal"])
        target_burn_kcal = (
            calculate_tdee(profile) * 0.20
        )  # 20% of TDEE as workout burn target
    except Exception:
        target_burn_kcal = 350.0

    recs = recommender_service.get_exercise_recs(
        user_id=user_id,
        n=limit,
        target_burn_kcal=target_burn_kcal,
        user_dict=current_user,
        date=date,
    )

    # Strict Safety Filter: ensure no exercise flagged for the user's injuries is recommended
    injuries = [
        str(i).lower().strip()
        for i in current_user.get("profile", {}).get("injuries", [])
        if str(i).strip()
    ]
    if injuries:
        catalog_exercises = await db["exercises"].find({}).to_list(length=200)
        ex_flag_map = {
            e["_id"]: [
                str(f).lower().strip()
                for f in e.get("injury_flags", [])
                if str(f).strip()
            ]
            for e in catalog_exercises
        }
        filtered = [
            r
            for r in recs
            if not any(inj in ex_flag_map.get(r.exercise_id, []) for inj in injuries)
        ]
        if len(filtered) < len(recs):
            for e in catalog_exercises:
                if len(filtered) >= limit:
                    break
                flags = [
                    str(f).lower().strip()
                    for f in e.get("injury_flags", [])
                    if str(f).strip()
                ]
                if not any(inj in flags for inj in injuries) and not any(
                    r.exercise_id == e["_id"] for r in filtered
                ):
                    filtered.append(
                        ExerciseRecItem(
                            exercise_id=e["_id"],
                            name=e["name"],
                            duration_min=30.0,
                            est_kcal=140.0,
                            reason=f"Joint-friendly exercise safe for your {', '.join(injuries)} recovery",
                        )
                    )
            recs = filtered

    await _store_recommendation(db, user_id, "exercise", recs)
    logger.info(
        "exercise recs user=%s n=%d is_mock=%s model=%s",
        user_id,
        len(recs),
        recommender_service.is_mock,
        recommender_service.model_version,
    )
    return recs


@router.get(
    "/foods",
    response_model=list[FoodRecItem],
    summary="Personalised food recommendations",
    responses={
        200: {"description": "List of recommended foods"},
        401: {"description": "Not authenticated"},
    },
)
async def recommend_foods(
    date: str | None = Query(
        None, description="Target date (YYYY-MM-DD, informational)"
    ),
    limit: int = Query(3, ge=1, le=10, description="Number of recommendations"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Get personalised food recommendations calibrated to the user's calorie target.

    Calls `recommender.get_food_recs(user_id, kcal_target, n)`.

    Results are stored in the **recommendations** collection with `model_version`.
    """
    user_id = current_user["_id"]
    profile = UserProfile(**current_user["profile"])
    goal = UserGoal(**current_user["goal"])

    kcal_target = calculate_daily_calorie_target(profile, goal)

    recs = recommender_service.get_food_recs(
        user_id=user_id,
        kcal_target=kcal_target,
        n=limit,
        user_dict=current_user,
        date=date,
    )

    # Strict Safety Filter: ensure veg user only receives veg-safe food items
    diet_type = current_user.get("profile", {}).get("diet_type", "veg")
    if diet_type == "veg":
        catalog_foods = await db["foods"].find({}).to_list(length=200)
        food_diet_map = {f["_id"]: f.get("diet_type", "veg") for f in catalog_foods}
        filtered = [r for r in recs if food_diet_map.get(r.food_id, "veg") == "veg"]
        if len(filtered) < len(recs):
            for f in catalog_foods:
                if len(filtered) >= limit:
                    break
                if f.get("diet_type") == "veg" and not any(
                    r.food_id == f["_id"] for r in filtered
                ):
                    grams = 150.0
                    kcal_100g = max(float(f.get("kcal_per_100g", 100)), 20.0)
                    factor = grams / 100.0
                    filtered.append(
                        FoodRecItem(
                            food_id=f["_id"],
                            name=f["name"],
                            diet_type="veg",
                            grams=grams,
                            kcal=round(kcal_100g * factor, 1),
                            macros=FoodMacros(
                                protein_g=round(
                                    float(f.get("protein_g", 0)) * factor, 1
                                ),
                                carbs_g=round(float(f.get("carbs_g", 0)) * factor, 1),
                                fat_g=round(float(f.get("fat_g", 0)) * factor, 1),
                                fiber_g=round(float(f.get("fiber_g", 0)) * factor, 1),
                            ),
                            reason="Wholesome vegetarian choice supporting your daily target",
                        )
                    )
        recs = filtered

    await _store_recommendation(db, user_id, "food", recs)
    logger.info(
        "food recs user=%s kcal_target=%.1f n=%d is_mock=%s",
        user_id,
        kcal_target,
        len(recs),
        recommender_service.is_mock,
    )
    return recs
