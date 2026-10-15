from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.api.deps import get_current_user
from backend.app.db.mongodb import get_database
from backend.app.schemas.all_schemas import UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
):
    """Retrieve profile and goal for current authenticated user."""
    return UserResponse(**current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    payload: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Update profile and/or goal for current authenticated user."""
    update_data = {}
    if payload.profile is not None:
        p_dict = payload.profile.model_dump()
        norm_map = {
            "light": "lightly_active",
            "moderate": "moderately_active",
            "active": "very_active",
        }
        p_dict["activity_level"] = norm_map.get(
            p_dict["activity_level"], p_dict["activity_level"]
        )
        update_data["profile"] = p_dict
    if payload.goal is not None:
        update_data["goal"] = payload.goal.model_dump()

    if update_data:
        await db["users"].update_one(
            {"_id": current_user["_id"]}, {"$set": update_data}
        )
        updated = await db["users"].find_one({"_id": current_user["_id"]})
        if updated:
            current_user = updated
        else:
            current_user.update(update_data)

    return UserResponse(**current_user)
