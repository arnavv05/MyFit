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

    # Calculate kcal_in and kcal_out rollups
    kcal_in = sum(m.kcal for m in payload.meals)
    kcal_out = sum(w.kcal_burned for w in payload.workouts)

    existing_log = await db["daily_logs"].find_one({"user_id": user_id, "date": payload.date})

    doc_data = {
        "user_id": user_id,
        "date": payload.date,
        "weight_kg": payload.weight_kg,
        "sleep_hours": payload.sleep_hours,
        "water_ml": payload.water_ml,
        "workouts": [w.model_dump() for w in payload.workouts],
        "meals": [m.model_dump() for m in payload.meals],
        "kcal_in": round(kcal_in, 2),
        "kcal_out": round(kcal_out, 2),
    }

    if existing_log:
        await db["daily_logs"].update_one({"_id": existing_log["_id"]}, {"$set": doc_data})
        doc_data["_id"] = existing_log["_id"]
    else:
        log_id = str(uuid.uuid4())
        doc_data["_id"] = log_id
        await db["daily_logs"].insert_one(doc_data)

    return DailyLogResponse(**doc_data)


@router.get("", response_model=list[DailyLogResponse])
async def get_daily_logs(
    from_date: str | None = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
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
