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
    DailyCaloriePoint,
    DailySummary,
    ForecastResult,
    PopulationAnalyticsResponse,
    UserAnalyticsResponse,
    WeeklySummary,
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


def _compute_streaks(log_dates: list[str]) -> tuple[int, int]:
    """Calculate current streak and best streak.

    Current streak counts consecutive days ending today or yesterday (active streak).
    Best streak counts the maximum consecutive run ever recorded.
    """
    if not log_dates:
        return 0, 0
    unique_dates = sorted(set(log_dates))
    date_objs: list[date] = []
    for d in unique_dates:
        try:
            date_objs.append(date.fromisoformat(d))
        except Exception:
            pass
    if not date_objs:
        return 0, 0

    # Best streak calculation
    best_streak = 1
    current_run = 1
    for i in range(1, len(date_objs)):
        if (date_objs[i] - date_objs[i - 1]).days == 1:
            current_run += 1
            if current_run > best_streak:
                best_streak = current_run
        elif (date_objs[i] - date_objs[i - 1]).days > 1:
            current_run = 1

    # Current streak calculation
    today = date.today()
    yesterday = today - timedelta(days=1)
    date_set = set(date_objs)

    streak = 0
    if today in date_set:
        check = today
        while check in date_set:
            streak += 1
            check -= timedelta(days=1)
    elif yesterday in date_set:
        check = yesterday
        while check in date_set:
            streak += 1
            check -= timedelta(days=1)
    else:
        streak = 0

    return streak, max(best_streak, streak)


def _compute_streak(log_dates: list[str]) -> int:
    """Legacy helper returning current streak."""
    curr, _ = _compute_streaks(log_dates)
    return curr


# ---------------------------------------------------------------------------
# Core User Analytics Builder
# ---------------------------------------------------------------------------


async def _build_user_analytics(
    user: dict,
    db: AsyncIOMotorDatabase,
) -> UserAnalyticsResponse:
    """Aggregate individual user progress fresh from storage."""
    user_id = user["_id"]

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
    curr_streak, best_streak = _compute_streaks(log_dates)

    # Per-day calories in vs out
    calories_in_vs_out = [
        DailyCaloriePoint(
            date=log["date"],
            kcal_in=round(float(log.get("kcal_in", 0.0)), 1),
            kcal_out=round(float(log.get("kcal_out", 0.0)), 1),
            net_kcal=round(
                float(log.get("kcal_in", 0.0)) - float(log.get("kcal_out", 0.0)), 1
            ),
        )
        for log in logs
    ]

    # Today summary
    today_str = date.today().isoformat()
    today_log = next((entry for entry in logs if entry.get("date") == today_str), None)
    today_summary = None
    if today_log:
        today_summary = DailySummary(
            date=today_str,
            weight_kg=today_log.get("weight_kg"),
            kcal_in=round(float(today_log.get("kcal_in", 0.0)), 1),
            kcal_out=round(float(today_log.get("kcal_out", 0.0)), 1),
            net_kcal=round(
                float(today_log.get("kcal_in", 0.0))
                - float(today_log.get("kcal_out", 0.0)),
                1,
            ),
            workouts_count=len(today_log.get("workouts", [])),
            meals_count=len(today_log.get("meals", [])),
            sleep_hours=today_log.get("sleep_hours"),
            water_ml=today_log.get("water_ml"),
        )

    # 7-day rolling summary
    seven_days_ago = (date.today() - timedelta(days=6)).isoformat()
    recent_logs = [entry for entry in logs if entry.get("date", "") >= seven_days_ago]
    weekly_in = sum(float(entry.get("kcal_in", 0.0)) for entry in recent_logs)
    weekly_out = sum(float(entry.get("kcal_out", 0.0)) for entry in recent_logs)
    weekly_workouts = sum(len(entry.get("workouts", [])) for entry in recent_logs)
    days_logged_week = len(recent_logs)
    weekly_summary = WeeklySummary(
        total_kcal_in=round(weekly_in, 1),
        total_kcal_out=round(weekly_out, 1),
        avg_daily_kcal_in=round(weekly_in / days_logged_week, 1)
        if days_logged_week
        else 0.0,
        avg_daily_kcal_out=round(weekly_out / days_logged_week, 1)
        if days_logged_week
        else 0.0,
        workouts_completed=weekly_workouts,
        days_logged=days_logged_week,
    )

    # Goal Progress Calculation
    goal = user.get("goal", {})
    target_weight = goal.get("target_weight_kg")
    goal_progress_pct = 0.0
    if target_weight and weight_history:
        init_weight = weight_history[0].weight_kg
        curr_weight = weight_history[-1].weight_kg
        total_delta = abs(init_weight - target_weight)
        if total_delta > 0.05:
            if init_weight > target_weight:
                progress = init_weight - curr_weight
            else:
                progress = curr_weight - init_weight
            goal_progress_pct = round(
                max(0.0, min(100.0, (progress / total_delta) * 100.0)), 1
            )
        elif abs(curr_weight - target_weight) <= 0.5:
            goal_progress_pct = 100.0

    # ------------------------------------------------------------------
    # ML-powered fields
    # ------------------------------------------------------------------
    goal_forecast: ForecastResult | None = None
    weight_anomalies: list[WeightAnomaly] = []

    from ml.recommender.data_access import InMemoryDataAccess

    in_memory_da = InMemoryDataAccess(user=user, logs=logs)

    if _forecast_fn is not None:
        try:
            raw = _forecast_fn(user_id=user_id, data_access=in_memory_da)
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
            raw_anomalies = _anomaly_fn(user_id=user_id, data_access=in_memory_da)
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
        current_streak_days=curr_streak,
        best_streak_days=best_streak,
        streak=curr_streak,
        calories_in_vs_out=calories_in_vs_out,
        today_summary=today_summary,
        weekly_summary=weekly_summary,
        goal_progress_pct=goal_progress_pct,
        goal_forecast=goal_forecast,
        weight_anomalies=weight_anomalies,
    )


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
    """Aggregate individual user progress fresh from storage on every request."""
    return await _build_user_analytics(current_user, db)


@router.get(
    "/user/{user_id}",
    response_model=UserAnalyticsResponse,
    summary="User progress analytics by user ID (dashboard and internal analytics)",
)
async def get_analytics_for_user_id(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Fetch user progress analytics by user ID directly."""
    user_doc = await db["users"].find_one({"_id": user_id})
    if not user_doc:
        from ml.recommender.data_access import CsvDataAccess

        user_doc = CsvDataAccess().get_user(user_id) or {
            "_id": user_id,
            "profile": {},
            "goal": {},
        }
    return await _build_user_analytics(user_doc, db)


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
