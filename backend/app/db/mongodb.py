from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.app.core.config import settings


try:
    import certifi

    _CA_FILE = certifi.where()
except Exception:
    _CA_FILE = None


class MongoDBManager:
    """Manages Async Motor MongoDB client and database connections."""

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


db_manager = MongoDBManager()


async def connect_to_mongo() -> None:
    """Initialize MongoDB client and connect to database."""
    import asyncio
    import logging

    kwargs = {"serverSelectionTimeoutMS": 4000}
    if _CA_FILE:
        kwargs["tlsCAFile"] = _CA_FILE
    db_manager.client = AsyncIOMotorClient(settings.MONGODB_URI, **kwargs)
    db_manager.db = db_manager.client[settings.MONGODB_DB_NAME]
    try:
        await asyncio.wait_for(init_db_indexes(db_manager.db), timeout=3.0)
    except Exception as e:
        logging.getLogger(__name__).warning(
            "Index initialization deferred (MongoDB not immediately reachable): %s", e
        )



async def close_mongo_connection() -> None:
    """Close MongoDB connection gracefully."""
    if db_manager.client is not None:
        db_manager.client.close()
        db_manager.client = None
        db_manager.db = None


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency helper to get active database instance."""
    if db_manager.db is None:
        raise RuntimeError(
            "Database not initialized. Ensure connect_to_mongo() was executed."
        )
    return db_manager.db


async def init_db_indexes(db: AsyncIOMotorDatabase) -> None:
    """Ensure indexes conform to shared specifications:
    - users: unique email
    - daily_logs: unique (user_id, date)
    - exercises: text index on name
    - foods: text index on name
    - interactions: compound (user_id, item_type, item_id)
    """
    # users: email unique
    await db["users"].create_index("email", unique=True)

    # daily_logs: compound unique index on (user_id, date)
    await db["daily_logs"].create_index([("user_id", 1), ("date", 1)], unique=True)

    # exercises: text index on name
    await db["exercises"].create_index([("name", "text")])

    # foods: text index on name
    await db["foods"].create_index([("name", "text")])

    # interactions: index for querying by user or item
    await db["interactions"].create_index([("user_id", 1), ("item_type", 1)])
