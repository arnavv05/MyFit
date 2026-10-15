import asyncio
import json
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.core.config import settings
from backend.app.core.security import get_password_hash


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

    # Seed demo user
    demo_user = {
        "_id": "usr_demo_student",
        "email": "student@myfitness.edu",
        "password_hash": get_password_hash("password123"),
        "profile": {
            "age": 21,
            "gender": "male",
            "height_cm": 176.0,
            "weight_kg": 73.5,
            "activity_level": "moderately_active",
            "diet_type": "veg",
            "injuries": ["knee"],
        },
        "goal": {
            "target_weight_kg": 69.0,
            "target_date": "2026-12-31",
        },
        "cluster_id": 2,
        "created_at": "2026-09-01T00:00:00Z",
    }
    await db["users"].update_one({"email": demo_user["email"]}, {"$set": demo_user}, upsert=True)
    print(f"Loaded demo user: {demo_user['email']} (password: password123)")

    # Seed sample daily logs for demo user
    sample_logs = [
        {
            "_id": "log_demo_001",
            "user_id": demo_user["_id"],
            "date": "2026-10-10",
            "weight_kg": 74.5,
            "sleep_hours": 7.5,
            "water_ml": 2500,
            "workouts": [
                {"exercise_id": "ex_pushups", "duration_min": 20, "kcal_burned": 95, "rating": 5}
            ],
            "meals": [
                {"food_id": "food_oatmeal", "grams": 200, "kcal": 136}
            ],
            "kcal_in": 1850.0,
            "kcal_out": 2200.0,
        },
        {
            "_id": "log_demo_002",
            "user_id": demo_user["_id"],
            "date": "2026-10-11",
            "weight_kg": 74.2,
            "sleep_hours": 8.0,
            "water_ml": 2800,
            "workouts": [
                {"exercise_id": "ex_cycling_leisure", "duration_min": 30, "kcal_burned": 180, "rating": 4}
            ],
            "meals": [
                {"food_id": "food_paneer", "grams": 150, "kcal": 397}
            ],
            "kcal_in": 1950.0,
            "kcal_out": 2300.0,
        },
        {
            "_id": "log_demo_003",
            "user_id": demo_user["_id"],
            "date": "2026-10-12",
            "weight_kg": 74.0,
            "sleep_hours": 7.0,
            "water_ml": 3000,
            "workouts": [
                {"exercise_id": "ex_bodyweight_squats", "duration_min": 25, "kcal_burned": 150, "rating": 5}
            ],
            "meals": [
                {"food_id": "food_brown_rice", "grams": 200, "kcal": 222}
            ],
            "kcal_in": 2000.0,
            "kcal_out": 2350.0,
        },
        {
            "_id": "log_demo_004",
            "user_id": demo_user["_id"],
            "date": "2026-10-13",
            "weight_kg": 73.8,
            "sleep_hours": 7.8,
            "water_ml": 2600,
            "workouts": [
                {"exercise_id": "ex_plank", "duration_min": 15, "kcal_burned": 75, "rating": 4}
            ],
            "meals": [
                {"food_id": "food_oatmeal", "grams": 250, "kcal": 170}
            ],
            "kcal_in": 1900.0,
            "kcal_out": 2250.0,
        },
        {
            "_id": "log_demo_005",
            "user_id": demo_user["_id"],
            "date": "2026-10-14",
            "weight_kg": 73.5,
            "sleep_hours": 8.2,
            "water_ml": 3100,
            "workouts": [
                {"exercise_id": "ex_pushups", "duration_min": 25, "kcal_burned": 120, "rating": 5}
            ],
            "meals": [
                {"food_id": "food_paneer", "grams": 200, "kcal": 530}
            ],
            "kcal_in": 2050.0,
            "kcal_out": 2400.0,
        },
    ]

    for log in sample_logs:
        await db["daily_logs"].update_one(
            {"user_id": log["user_id"], "date": log["date"]},
            {"$set": log},
            upsert=True,
        )
    print(f"Loaded {len(sample_logs)} daily logs for demo user.")

    # Seed sample interactions
    sample_interactions = [
        {
            "_id": "int_demo_001",
            "user_id": demo_user["_id"],
            "item_type": "exercise",
            "item_id": "ex_pushups",
            "rating": 5,
            "implicit_score": 1.0,
            "timestamp": "2026-10-14T10:00:00Z",
        },
        {
            "_id": "int_demo_002",
            "user_id": demo_user["_id"],
            "item_type": "food",
            "item_id": "food_oatmeal",
            "rating": 4,
            "implicit_score": 0.8,
            "timestamp": "2026-10-14T11:00:00Z",
        },
    ]
    for interaction in sample_interactions:
        await db["interactions"].update_one(
            {"_id": interaction["_id"]},
            {"$set": interaction},
            upsert=True,
        )
    print(f"Loaded {len(sample_interactions)} sample interactions.")

    client.close()
    print("Database seed complete.")


if __name__ == "__main__":
    asyncio.run(seed_data())
