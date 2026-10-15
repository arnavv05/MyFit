from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.api.deps import get_current_user
from backend.app.db.mongodb import get_database
from backend.app.schemas.all_schemas import FeedbackRequest, FeedbackResponse

router = APIRouter(tags=["Interactions & Feedback"])


@router.post(
    "/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED
)
async def submit_feedback(
    payload: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Log user rating (1-5) for an exercise or food item to interactions collection.
    Computes an implicit score to fuel collaborative filtering ML models.
    """
    user_id = current_user["_id"]

    # Verify item exists in master collections
    target_collection = "exercises" if payload.item_type == "exercise" else "foods"
    item = await db[target_collection].find_one({"_id": payload.item_id})
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{payload.item_type.capitalize()} item with ID '{payload.item_id}' not found.",
        )

    interaction_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    # Implicit score normalized between 0.2 and 1.0 based on 1-5 rating
    implicit_score = round(payload.rating / 5.0, 2)

    doc = {
        "_id": interaction_id,
        "user_id": user_id,
        "item_type": payload.item_type,
        "item_id": payload.item_id,
        "rating": payload.rating,
        "implicit_score": implicit_score,
        "timestamp": now_iso,
    }

    await db["interactions"].insert_one(doc)

    return FeedbackResponse(**doc)
