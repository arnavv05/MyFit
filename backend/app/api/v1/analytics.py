"""Analytics routes: GET /analytics/me, GET /analytics/population."""

import logging
import sys
from datetime import date, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.api.deps import get_current_user
from backend.app.db.mongodb import get_database
from backend.app.schemas.all_schemas import (
    ForecastResult,
    PopulationAnalyticsResponse,
    UserAnalyticsResponse,
    WeightAnomaly,
    WeightPoint,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ---------------------------------------------------------------------------
# Helpers: load recommender functions with graceful fallback
# ---------------------------------------------------------------------------


def _load_ml():
    """Try to import the real recommender package; return (forecast_fn, anomaly_fn) or Nones."""
    try:
        import recommender as _rec  # installed via pip install -e ml/

        return _rec.forecast_goal_date, _rec.detect_weight_anomalies
    except ImportError:
        # Try adding ml/ to path (dev mode)
        ml_path = str(Path(__file__).resolve().parents[4] / "ml")
        if ml_path not in sys.path:
            sys.path.insert(0, ml_path)
        try:
            import recommender as _rec  # type: ignore

            return _rec.forecast_goal_date, _rec.detect_weight_anomalies
        except Exception as exc:
            logger.warning(
                "ML package unavailable for analytics (%s). Skipping forecast/anomaly.",
                exc,
            )
            return None, None


_forecast_fn, _anomaly_fn = _load_ml()


# ---------------------------------------------------------------------------
# Streak helper
# ---------------------------------------------------------------------------


def _compute_streak(log_dates: list[str]) -> int:
    """Count consecutive days ending on or before today."""
    if not log_dates:
        return 0
    today = date.today()
    # Walk back from today
    streak = 0
    check = today
    date_set = set(log_dates)
    while check.isoformat() in date_set:
        streak += 1
        check -= timedelta(days=1)
    return streak


# ---------------------------------------------------------------------------
# GET /analytics/me
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=UserAnalyticsResponse,
    summary="Personal progress analytics",
    responses={401: {"description": "Not authenticated"}},
)
async def get_user_analytics(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Aggregate individual user progress.

    Fields:
    - **calories in/out** totals and averages
    - **streak** – consecutive days with a log entry ending today
    - **weight_history** – chronological weight entries
    - **goal_forecast** – Ridge-regression goal-date forecast *(ML package)*
    - **weight_anomalies** – day-to-day spike detection *(ML package)*
    """
    user_id = current_user["_id"]

    logs_cursor = db["daily_logs"].find({"user_id": user_id}).sort("date", 1)
    logs = await logs_cursor.to_list(length=730)  # ~2 years max

    total_logs = len(logs)
    total_kcal_in = sum(log.get("kcal_in", 0.0) for log in logs)
    total_kcal_out = sum(log.get("kcal_out", 0.0) for log in logs)
    total_workouts = sum(len(log.get("workouts", [])) for log in logs)

    valid_sleep = [
        log["sleep_hours"] for log in logs if log.get("sleep_hours") is not None
    ]
    avg_sleep = round(sum(valid_sleep) / len(valid_sleep), 1) if valid_sleep else None

    valid_water = [log["water_ml"] for log in logs if log.get("water_ml") is not None]
    avg_water = round(sum(valid_water) / len(valid_water), 1) if valid_water else None

    weight_history = [
        WeightPoint(date=log["date"], weight_kg=log["weight_kg"])
        for log in logs
        if log.get("weight_kg") is not None
    ]

    log_dates = [log["date"] for log in logs]
    streak = _compute_streak(log_dates)

    # ------------------------------------------------------------------
    # ML-powered fields
    # ------------------------------------------------------------------
    goal_forecast: ForecastResult | None = None
    weight_anomalies: list[WeightAnomaly] = []

    if _forecast_fn is not None:
        try:
            raw = _forecast_fn(user_id=user_id)
            goal_forecast = ForecastResult(
                expected_date=raw.get("expected_date"),
                days_remaining=raw.get("days_remaining"),
                weekly_rate_kg=raw.get("weekly_rate_kg"),
                on_track=raw.get("on_track"),
                message=raw.get("message", ""),
            )
        except Exception as exc:
            logger.warning("forecast_goal_date failed for user %s: %s", user_id, exc)

    if _anomaly_fn is not None:
        try:
            raw_anomalies = _anomaly_fn(user_id=user_id)
            weight_anomalies = [
                WeightAnomaly(
                    date=a["date"],
                    weight_kg=a["weight_kg"],
                    reason=a.get("reason", ""),
                )
                for a in raw_anomalies
            ]
        except Exception as exc:
            logger.warning(
                "detect_weight_anomalies failed for user %s: %s", user_id, exc
            )

    return UserAnalyticsResponse(
        user_id=user_id,
        total_days_logged=total_logs,
        total_workouts_completed=total_workouts,
        total_kcal_in=round(total_kcal_in, 2),
        total_kcal_out=round(total_kcal_out, 2),
        avg_sleep_hours=avg_sleep,
        avg_water_ml=avg_water,
        weight_history=weight_history,
        current_streak_days=streak,
        goal_forecast=goal_forecast,
        weight_anomalies=weight_anomalies,
    )


# ---------------------------------------------------------------------------
# GET /analytics/population  (no auth required – public aggregate)
# ---------------------------------------------------------------------------


@router.get(
    "/population",
    response_model=PopulationAnalyticsResponse,
    summary="Population-level fitness statistics",
)
async def get_population_analytics(
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Aggregate overall user population metrics:
    - gender / diet / activity / **cluster** distributions
    - average age, weight, height
    - **popular exercises and foods** (by interaction count)
    """
    total_users = await db["users"].count_documents({})
    total_logs = await db["daily_logs"].count_documents({})

    # Aggregate averages
    agg_result = (
        await db["users"]
        .aggregate(
            [
                {
                    "$group": {
                        "_id": None,
                        "avg_weight": {"$avg": "$profile.weight_kg"},
                        "avg_height": {"$avg": "$profile.height_cm"},
                        "avg_age": {"$avg": "$profile.age"},
                    }
                }
            ]
        )
        .to_list(length=1)
    )
    stats = agg_result[0] if agg_result else {}

    # Diet distribution
    diet_dist = {
        item["_id"]: item["count"]
        for item in await db["users"]
        .aggregate([{"$group": {"_id": "$profile.diet_type", "count": {"$sum": 1}}}])
        .to_list(length=10)
        if item.get("_id")
    }

    # Activity distribution
    activity_dist = {
        item["_id"]: item["count"]
        for item in await db["users"]
        .aggregate(
            [{"$group": {"_id": "$profile.activity_level", "count": {"$sum": 1}}}]
        )
        .to_list(length=20)
        if item.get("_id")
    }

    # Cluster distribution
    cluster_dist: dict[str, int] = {}
    raw_clusters = (
        await db["users"]
        .aggregate([{"$group": {"_id": "$cluster_id", "count": {"$sum": 1}}}])
        .to_list(length=20)
    )
    for item in raw_clusters:
        if item.get("_id") is not None:
            cluster_dist[str(item["_id"])] = item["count"]

    # Popular exercises (top 5 by interaction count)
    pop_ex_pipeline = [
        {"$match": {"item_type": "exercise"}},
        {
            "$group": {
                "_id": "$item_id",
                "count": {"$sum": 1},
                "avg_rating": {"$avg": "$rating"},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]
    popular_exercises = [
        {
            "exercise_id": i["_id"],
            "interactions": i["count"],
            "avg_rating": round(i.get("avg_rating") or 0, 2),
        }
        for i in await db["interactions"].aggregate(pop_ex_pipeline).to_list(length=5)
    ]

    # Popular foods (top 5)
    pop_food_pipeline = [
        {"$match": {"item_type": "food"}},
        {
            "$group": {
                "_id": "$item_id",
                "count": {"$sum": 1},
                "avg_rating": {"$avg": "$rating"},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]
    popular_foods = [
        {
            "food_id": i["_id"],
            "interactions": i["count"],
            "avg_rating": round(i.get("avg_rating") or 0, 2),
        }
        for i in await db["interactions"].aggregate(pop_food_pipeline).to_list(length=5)
    ]

    return PopulationAnalyticsResponse(
        total_users=total_users,
        total_logs_recorded=total_logs,
        average_age=round(stats.get("avg_age") or 0.0, 1),
        average_weight_kg=round(stats.get("avg_weight") or 0.0, 1),
        average_height_cm=round(stats.get("avg_height") or 0.0, 1),
        diet_distribution=diet_dist,
        activity_distribution=activity_dist,
        cluster_distribution=cluster_dist,
        popular_exercises=popular_exercises,
        popular_foods=popular_foods,
    )
