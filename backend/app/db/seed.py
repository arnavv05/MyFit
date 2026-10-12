import asyncio
import json
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.core.config import settings


async def seed_data() -> None:
    """Reads datasets from /data and upserts into MongoDB."""
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    print(f"Connecting to MongoDB at {settings.MONGODB_URI} (db: {settings.MONGODB_DB_NAME})...")

    # Seed exercises
    exercises_file = data_dir / "exercises.json"
    if exercises_file.exists():
        with open(exercises_file, "r", encoding="utf-8") as f:
            exercises = json.load(f)
        for item in exercises:
            await db["exercises"].update_one({"_id": item["_id"]}, {"$set": item}, upsert=True)
        print(f"Loaded {len(exercises)} exercises.")

    # Seed foods
    foods_file = data_dir / "foods.json"
    if foods_file.exists():
        with open(foods_file, "r", encoding="utf-8") as f:
            foods = json.load(f)
        for item in foods:
            await db["foods"].update_one({"_id": item["_id"]}, {"$set": item}, upsert=True)
        print(f"Loaded {len(foods)} foods.")

    client.close()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed_data())
