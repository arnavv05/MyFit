import uuid
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.api.deps import get_current_user
from backend.app.db.mongodb import get_database
from backend.app.schemas.all_schemas import DailyLogCreateRequest, DailyLogResponse

router = APIRouter(prefix="/logs", tags=["Daily Logs"])


@router.post("", response_model=DailyLogResponse)
async def create_or_update_daily_log(
    payload: DailyLogCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Create or update daily log for a specified date.
    Calculates kcal_in from meals and kcal_out from workouts.
    """
    user_id = current_user["_id"]
    user_weight = (
        payload.weight_kg or current_user.get("profile", {}).get("weight_kg") or 70.0
    )

    workouts_data = []
    for w in payload.workouts:
        w_dict = w.model_dump()
        if not w_dict.get("kcal_burned") or w_dict["kcal_burned"] <= 0:
            w_dict["kcal_burned"] = round(
                5.0 * user_weight * (w.duration_min / 60.0), 2
            )
        workouts_data.append(w_dict)

    meals_data = []
    for m in payload.meals:
        m_dict = m.model_dump()
        if not m_dict.get("kcal") or m_dict["kcal"] <= 0:
            m_dict["kcal"] = round(m.grams * 1.5, 2)
        meals_data.append(m_dict)

    # Calculate kcal_in and kcal_out rollups
    kcal_in = sum(m["kcal"] for m in meals_data)
    kcal_out = sum(w["kcal_burned"] for w in workouts_data)

    existing_log = await db["daily_logs"].find_one(
        {"user_id": user_id, "date": payload.date}
    )

    doc_data = {
        "user_id": user_id,
        "date": payload.date,
        "weight_kg": payload.weight_kg,
        "sleep_hours": payload.sleep_hours,
        "water_ml": payload.water_ml,
        "workouts": workouts_data,
        "meals": meals_data,
        "kcal_in": round(kcal_in, 2),
        "kcal_out": round(kcal_out, 2),
    }

    if existing_log:
        await db["daily_logs"].update_one(
            {"_id": existing_log["_id"]}, {"$set": doc_data}
        )
        doc_data["_id"] = existing_log["_id"]
    else:
        log_id = str(uuid.uuid4())
        doc_data["_id"] = log_id
        await db["daily_logs"].insert_one(doc_data)

    # If any workout has a rating, persist it to interactions for recommender adaptation
    from datetime import datetime, timezone

    for w in workouts_data:
        if w.get("rating") is not None:
            await db["interactions"].update_one(
                {
                    "user_id": user_id,
                    "item_type": "exercise",
                    "item_id": w["exercise_id"],
                },
                {
                    "$set": {
                        "user_id": user_id,
                        "item_type": "exercise",
                        "item_id": w["exercise_id"],
                        "rating": int(w["rating"]),
                        "implicit_score": float(w["rating"]),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    "$setOnInsert": {"_id": str(uuid.uuid4())},
                },
                upsert=True,
            )

    return DailyLogResponse(**doc_data)


@router.get("", response_model=list[DailyLogResponse])
async def get_daily_logs(
    from_date: str | None = Query(
        None, alias="from", description="Start date (YYYY-MM-DD)"
    ),
    to_date: str | None = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Retrieve daily logs within an optional date range [from, to]."""
    user_id = current_user["_id"]
    query = {"user_id": user_id}

    date_filter = {}
    if from_date:
        date_filter["$gte"] = from_date
    if to_date:
        date_filter["$lte"] = to_date
    if date_filter:
        query["date"] = date_filter

    cursor = db["daily_logs"].find(query).sort("date", 1)
    logs = await cursor.to_list(length=1000)

    return [DailyLogResponse(**log) for log in logs]
