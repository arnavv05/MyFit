from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.api.deps import get_current_user
from backend.app.db.mongodb import get_database

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/me")
async def get_user_analytics(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Aggregate individual user progress:
    - Total workouts completed
    - Total active calories burned
    - Total calories consumed
    - Average sleep and water intake
    - Weight history trajectory
    """
    user_id = current_user["_id"]

    logs_cursor = db["daily_logs"].find({"user_id": user_id}).sort("date", 1)
    logs = await logs_cursor.to_list(length=365)

    total_logs = len(logs)
    total_kcal_in = sum(log.get("kcal_in", 0.0) for log in logs)
    total_kcal_out = sum(log.get("kcal_out", 0.0) for log in logs)
    total_workouts = sum(len(log.get("workouts", [])) for log in logs)

    valid_sleep = [log["sleep_hours"] for log in logs if log.get("sleep_hours") is not None]
    avg_sleep = round(sum(valid_sleep) / len(valid_sleep), 1) if valid_sleep else None

    valid_water = [log["water_ml"] for log in logs if log.get("water_ml") is not None]
    avg_water = round(sum(valid_water) / len(valid_water), 1) if valid_water else None

    weight_history = [
        {"date": log["date"], "weight_kg": log["weight_kg"]}
        for log in logs
        if log.get("weight_kg") is not None
    ]

    return {
        "user_id": user_id,
        "total_days_logged": total_logs,
        "total_workouts_completed": total_workouts,
        "total_kcal_in": round(total_kcal_in, 2),
        "total_kcal_out": round(total_kcal_out, 2),
        "avg_sleep_hours": avg_sleep,
        "avg_water_ml": avg_water,
        "weight_history": weight_history,
    }


@router.get("/population")
async def get_population_analytics(
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Aggregate overall user population metrics:
    - Total registered users
    - Gender & diet type distribution
    - Average user height and weight
    - Global log engagement summary
    """
    total_users = await db["users"].count_documents({})
    total_logs = await db["daily_logs"].count_documents({})

    pipeline = [
        {
            "$group": {
                "_id": None,
                "avg_weight": {"$avg": "$profile.weight_kg"},
                "avg_height": {"$avg": "$profile.height_cm"},
                "avg_age": {"$avg": "$profile.age"},
            }
        }
    ]
    agg_result = await db["users"].aggregate(pipeline).to_list(length=1)
    stats = agg_result[0] if agg_result else {}

    # Diet preference distribution
    diet_pipeline = [{"$group": {"_id": "$profile.diet_type", "count": {"$sum": 1}}}]
    diet_dist = await db["users"].aggregate(diet_pipeline).to_list(length=10)

    # Activity level distribution
    activity_pipeline = [{"$group": {"_id": "$profile.activity_level", "count": {"$sum": 1}}}]
    activity_dist = await db["users"].aggregate(activity_pipeline).to_list(length=10)

    return {
        "total_users": total_users,
        "total_logs_recorded": total_logs,
        "average_age": round(stats.get("avg_age", 0.0), 1) if stats else 0.0,
        "average_weight_kg": round(stats.get("avg_weight", 0.0), 1) if stats else 0.0,
        "average_height_cm": round(stats.get("avg_height", 0.0), 1) if stats else 0.0,
        "diet_distribution": {item["_id"]: item["count"] for item in diet_dist if item.get("_id")},
        "activity_distribution": {item["_id"]: item["count"] for item in activity_dist if item.get("_id")},
    }
