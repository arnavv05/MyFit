"""Auth routes: POST /auth/register, POST /auth/login."""

from datetime import datetime, timezone
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from backend.app.db.mongodb import get_database
from backend.app.schemas.all_schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])

# Activity-level normalisation (handles short form sent by older frontend)
_NORM_ACTIVITY = {
    "light": "lightly_active",
    "moderate": "moderately_active",
    "active": "very_active",
}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
async def register_user(
    payload: UserRegisterRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Register a new user account.

    - Returns **201** with the new user profile (no password hash).
    - Returns **409** if the email is already taken.
    """
    existing_user = await db["users"].find_one({"email": payload.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    if payload.profile is not None:
        profile_dict = payload.profile.model_dump()
        profile_dict["activity_level"] = _NORM_ACTIVITY.get(
            profile_dict["activity_level"], profile_dict["activity_level"]
        )
    else:
        profile_dict = {
            "age": 21,
            "gender": "male",
            "height_cm": 175.0,
            "weight_kg": 72.0,
            "activity_level": "moderately_active",
            "diet_type": "veg",
            "injuries": [],
        }

    if payload.goal is not None:
        goal_dict = payload.goal.model_dump()
    else:
        goal_dict = {
            "target_weight_kg": 68.0,
            "target_date": "2026-12-31",
        }

    doc = {
        "_id": user_id,
        "email": payload.email,
        "password_hash": get_password_hash(payload.password),  # never returned
        "profile": profile_dict,
        "goal": goal_dict,
        "cluster_id": None,
        "created_at": now_iso,
    }

    await db["users"].insert_one(doc)
    logger.info("Registered new user id=%s email=%s", user_id, payload.email)

    return UserResponse(
        _id=user_id,
        email=payload.email,
        profile=profile_dict,
        goal=goal_dict,
        cluster_id=None,
        created_at=now_iso,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain a JWT access token",
    responses={
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error"},
    },
)
async def login_user(
    payload: UserLoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Authenticate with email and password.

    Returns a **Bearer** JWT token valid for `ACCESS_TOKEN_EXPIRE_MINUTES`.
    """
    user = await db["users"].find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user["_id"], "email": user["email"]})
    logger.info("Login successful user_id=%s", user["_id"])
    return TokenResponse(access_token=token)
