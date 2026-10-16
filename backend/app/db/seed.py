"""Seed script: idempotent (safe to run multiple times).

Loads:
  1. exercises     – from data/exercises.json (with bulk_write)
  2. foods         – from data/foods.json (with bulk_write)
  3. users         – demo user + synthetic users from data/users.csv
  4. daily_logs    – sample logs for demo user + sampled logs from data/daily_logs.csv
  5. interactions  – sample interactions + sampled interactions from data/interactions.csv

Also ensures all database indexes are created.
"""

import asyncio
import csv
import json
import logging
import random
import sys
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

# Make sure the package root is on the path when run as a script
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.config import settings  # noqa: E402
from backend.app.core.security import get_password_hash  # noqa: E402
from backend.app.db.mongodb import init_db_indexes  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

DATA_DIR = ROOT / "data"

CSV_MAX_USERS = 200
CSV_MAX_LOGS = 500
CSV_MAX_INTERACTIONS = 1000

RANDOM_SEED = 42


async def seed_exercises(db) -> int:
    """Upsert exercises from data/exercises.json."""
    exercises_file = DATA_DIR / "exercises.json"
    if not exercises_file.exists():
        logger.warning("exercises.json not found at %s – skipping.", exercises_file)
        return 0
    with open(exercises_file, "r", encoding="utf-8") as f:
        exercises = json.load(f)
    if not exercises:
        return 0
    ops = [
        UpdateOne({"_id": item["_id"]}, {"$set": item}, upsert=True)
        for item in exercises
    ]
    await db["exercises"].bulk_write(ops, ordered=False)
    logger.info("Loaded %d exercises.", len(exercises))
    return len(exercises)


async def seed_foods(db) -> int:
    """Upsert foods from data/foods.json."""
    foods_file = DATA_DIR / "foods.json"
    if not foods_file.exists():
        logger.warning("foods.json not found at %s – skipping.", foods_file)
        return 0
    with open(foods_file, "r", encoding="utf-8") as f:
        foods = json.load(f)
    if not foods:
        return 0
    ops = [
        UpdateOne({"_id": item["_id"]}, {"$set": item}, upsert=True) for item in foods
    ]
    await db["foods"].bulk_write(ops, ordered=False)
    logger.info("Loaded %d foods.", len(foods))
    return len(foods)


async def seed_demo_user(db) -> dict:
    """Upsert the fixed demo/grader user."""
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
    await db["users"].update_one(
        {"email": demo_user["email"]}, {"$set": demo_user}, upsert=True
    )
    logger.info("Demo user: %s / password123", demo_user["email"])
    return demo_user


async def seed_synthetic_users(db) -> int:
    """Load synthetic users from data/users.csv."""
    users_csv = DATA_DIR / "users.csv"
    if not users_csv.exists():
        logger.info("users.csv not found – skipping synthetic users.")
        return 0

    rng = random.Random(RANDOM_SEED)
    rows: list[dict] = []
    with open(users_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if CSV_MAX_USERS and len(rows) > CSV_MAX_USERS:
        rows = rng.sample(rows, CSV_MAX_USERS)

    ops = []
    for row in rows:
        user_id = row.get("_id") or row.get("user_id", "")
        if not user_id:
            continue

        cluster_id_raw = row.get("cluster_id") or row.get("cluster", "")
        try:
            cluster_id = int(float(cluster_id_raw)) if cluster_id_raw else None
        except (ValueError, TypeError):
            cluster_id = None

        injuries_raw = row.get("injuries", "")
        injuries = (
            [i.strip() for i in injuries_raw.split(",") if i.strip()]
            if injuries_raw
            else []
        )

        doc = {
            "_id": user_id,
            "email": row.get("email", f"{user_id}@myfitness.synthetic"),
            "password_hash": row.get("password_hash")
            or get_password_hash("synthetic_pw"),
            "profile": {
                "age": int(float(row.get("age", 25))),
                "gender": row.get("gender", "male"),
                "height_cm": float(row.get("height_cm", 170)),
                "weight_kg": float(row.get("weight_kg", 70)),
                "activity_level": row.get("activity_level", "moderately_active"),
                "diet_type": row.get("diet_type", "veg"),
                "injuries": injuries,
            },
            "goal": {
                "target_weight_kg": float(row.get("target_weight_kg", 65)),
                "target_date": row.get("target_date", "2026-12-31"),
            },
            "cluster_id": cluster_id,
            "created_at": row.get("created_at", "2026-01-01T00:00:00Z"),
        }
        ops.append(UpdateOne({"_id": user_id}, {"$set": doc}, upsert=True))

    if ops:
        await db["users"].bulk_write(ops, ordered=False)
    logger.info("Loaded %d synthetic users from users.csv.", len(ops))
    return len(ops)


async def seed_demo_logs(db, demo_user: dict) -> int:
    """Upsert 5 fixed sample daily logs for the demo user."""
    sample_logs = [
        {
            "_id": "log_demo_001",
            "user_id": demo_user["_id"],
            "date": "2026-10-10",
            "weight_kg": 74.5,
            "sleep_hours": 7.5,
            "water_ml": 2500,
            "workouts": [
                {
                    "exercise_id": "ex_004",
                    "duration_min": 20,
                    "kcal_burned": 95,
                    "rating": 5,
                }
            ],
            "meals": [{"food_id": "fd_001", "grams": 200, "kcal": 136}],
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
                {
                    "exercise_id": "ex_009",
                    "duration_min": 30,
                    "kcal_burned": 180,
                    "rating": 4,
                }
            ],
            "meals": [{"food_id": "fd_020", "grams": 150, "kcal": 397}],
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
                {
                    "exercise_id": "ex_012",
                    "duration_min": 25,
                    "kcal_burned": 150,
                    "rating": 5,
                }
            ],
            "meals": [{"food_id": "fd_002", "grams": 200, "kcal": 222}],
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
                {
                    "exercise_id": "ex_021",
                    "duration_min": 15,
                    "kcal_burned": 75,
                    "rating": 4,
                }
            ],
            "meals": [{"food_id": "fd_001", "grams": 250, "kcal": 170}],
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
                {
                    "exercise_id": "ex_004",
                    "duration_min": 25,
                    "kcal_burned": 120,
                    "rating": 5,
                }
            ],
            "meals": [{"food_id": "fd_020", "grams": 200, "kcal": 530}],
            "kcal_in": 2050.0,
            "kcal_out": 2400.0,
        },
    ]

    ops = [
        UpdateOne(
            {"user_id": log["user_id"], "date": log["date"]},
            {"$set": log},
            upsert=True,
        )
        for log in sample_logs
    ]
    await db["daily_logs"].bulk_write(ops, ordered=False)
    logger.info("Loaded %d demo daily logs.", len(sample_logs))
    return len(sample_logs)


async def seed_csv_logs(db) -> int:
    """Load a sample of synthetic logs from data/daily_logs.csv."""
    logs_csv = DATA_DIR / "daily_logs.csv"
    if not logs_csv.exists():
        logger.info("daily_logs.csv not found – skipping synthetic logs.")
        return 0

    rng = random.Random(RANDOM_SEED)
    rows: list[dict] = []
    with open(logs_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if CSV_MAX_LOGS and len(rows) > CSV_MAX_LOGS:
        rows = rng.sample(rows, CSV_MAX_LOGS)

    # Get set of all valid user IDs in one quick query to avoid orphan logs
    valid_users = set(await db["users"].distinct("_id"))

    ops = []
    for row in rows:
        user_id = row.get("user_id", "")
        date_val = row.get("date", "")
        if not user_id or not date_val:
            continue
        if user_id not in valid_users:
            continue

        workouts = []
        if row.get("workouts"):
            try:
                workouts = json.loads(row["workouts"])
            except Exception:
                workouts = []

        meals = []
        if row.get("meals"):
            try:
                meals = json.loads(row["meals"])
            except Exception:
                meals = []

        doc_id = row.get("_id") or f"log_{user_id}_{date_val}".replace("-", "")
        doc = {
            "_id": doc_id,
            "user_id": user_id,
            "date": date_val,
            "weight_kg": float(row["weight_kg"]) if row.get("weight_kg") else None,
            "sleep_hours": float(row["sleep_hours"])
            if row.get("sleep_hours")
            else None,
            "water_ml": float(row["water_ml"]) if row.get("water_ml") else None,
            "workouts": workouts,
            "meals": meals,
            "kcal_in": float(row["kcal_in"]) if row.get("kcal_in") else 0.0,
            "kcal_out": float(row["kcal_out"]) if row.get("kcal_out") else 0.0,
        }
        ops.append(
            UpdateOne(
                {"user_id": user_id, "date": date_val},
                {"$setOnInsert": doc},
                upsert=True,
            )
        )

    if ops:
        result = await db["daily_logs"].bulk_write(ops, ordered=False)
        inserted = result.upserted_count
    else:
        inserted = 0

    logger.info("Upserted %d synthetic daily logs.", len(ops))
    return inserted


async def seed_demo_interactions(db, demo_user: dict) -> int:
    """Upsert fixed demo interactions."""
    sample_interactions = [
        {
            "_id": "int_demo_001",
            "user_id": demo_user["_id"],
            "item_type": "exercise",
            "item_id": "ex_004",
            "rating": 5,
            "implicit_score": 1.0,
            "timestamp": "2026-10-14T10:00:00Z",
        },
        {
            "_id": "int_demo_002",
            "user_id": demo_user["_id"],
            "item_type": "food",
            "item_id": "fd_001",
            "rating": 4,
            "implicit_score": 0.8,
            "timestamp": "2026-10-14T11:00:00Z",
        },
    ]
    ops = [
        UpdateOne({"_id": item["_id"]}, {"$set": item}, upsert=True)
        for item in sample_interactions
    ]
    await db["interactions"].bulk_write(ops, ordered=False)
    logger.info("Loaded %d demo interactions.", len(sample_interactions))
    return len(sample_interactions)


async def seed_csv_interactions(db) -> int:
    """Load a sample of synthetic interactions from data/interactions.csv."""
    interactions_csv = DATA_DIR / "interactions.csv"
    if not interactions_csv.exists():
        logger.info("interactions.csv not found – skipping.")
        return 0

    rng = random.Random(RANDOM_SEED)
    rows: list[dict] = []
    with open(interactions_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if CSV_MAX_INTERACTIONS and len(rows) > CSV_MAX_INTERACTIONS:
        rows = rng.sample(rows, CSV_MAX_INTERACTIONS)

    ops = []
    for row in rows:
        user_id = row.get("user_id", "")
        item_id = row.get("item_id", row.get("exercise_id", row.get("food_id", "")))
        if not user_id or not item_id:
            continue

        item_type = row.get("item_type", "exercise")
        try:
            rating = int(float(row.get("rating", 3)))
        except (ValueError, TypeError):
            rating = 3
        implicit_score = round(rating / 5.0, 2)

        doc_id = row.get("_id") or f"int_{user_id}_{item_id}".replace("-", "_")
        doc = {
            "_id": doc_id,
            "user_id": user_id,
            "item_type": item_type,
            "item_id": item_id,
            "rating": rating,
            "implicit_score": implicit_score,
            "timestamp": row.get("timestamp", "2026-01-01T00:00:00Z"),
        }
        ops.append(UpdateOne({"_id": doc_id}, {"$setOnInsert": doc}, upsert=True))

    if ops:
        await db["interactions"].bulk_write(ops, ordered=False)
    logger.info("Loaded %d synthetic interactions.", len(ops))
    return len(ops)


async def seed_data() -> None:
    """Main entry point: connect → index → seed all collections → close."""
    logger.info("Connecting to MongoDB db=%s", settings.MONGODB_DB_NAME)
    try:
        import certifi

        ca_file = certifi.where()
    except Exception:
        ca_file = None

    kwargs = {"tlsCAFile": ca_file} if ca_file else {}
    client = AsyncIOMotorClient(settings.MONGODB_URI, **kwargs)
    db = client[settings.MONGODB_DB_NAME]

    try:
        logger.info("Ensuring database indexes...")
        await init_db_indexes(db)
        await seed_exercises(db)
        await seed_foods(db)
        demo_user = await seed_demo_user(db)
        await seed_synthetic_users(db)
        await seed_demo_logs(db, demo_user)
        await seed_csv_logs(db)
        await seed_demo_interactions(db, demo_user)
        await seed_csv_interactions(db)
        logger.info("✅ Database seed complete.")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_data())
