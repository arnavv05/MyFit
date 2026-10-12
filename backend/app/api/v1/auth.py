from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.db.mongodb import get_database
from backend.app.schemas.all_schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegisterRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Register a new user with profile and goal."""
    existing_user = await db["users"].find_one({"email": payload.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    user_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    doc = {
        "_id": user_id,
        "email": payload.email,
        "password_hash": get_password_hash(payload.password),
        "profile": payload.profile.model_dump(),
        "goal": payload.goal.model_dump(),
        "cluster_id": None,
        "created_at": now_iso,
    }

    await db["users"].insert_one(doc)

    return UserResponse(
        _id=user_id,
        email=payload.email,
        profile=payload.profile,
        goal=payload.goal,
        cluster_id=None,
        created_at=now_iso,
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    payload: UserLoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Authenticate with email and password to receive JWT token."""
    user = await db["users"].find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user["_id"], "email": user["email"]})
    return TokenResponse(access_token=token)
