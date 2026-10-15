import json
from pathlib import Path
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.db.mongodb import get_database
from backend.app.schemas.all_schemas import CatalogResponse, ExerciseItem, FoodItem

router = APIRouter(tags=["Catalog"])


@router.get("/catalog", response_model=CatalogResponse)
async def get_catalog(
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Retrieve catalog of exercises and foods for logging selection.
    If database catalog is empty, seamlessly falls back to /data JSON files.
    """
    exercises_cur = db["exercises"].find({})
    exercises = await exercises_cur.to_list(length=200)

    foods_cur = db["foods"].find({})
    foods = await foods_cur.to_list(length=200)

    # Fallback to local data/ json files if collections are empty
    data_dir = Path(__file__).resolve().parents[4] / "data"

    if not exercises:
        ex_file = data_dir / "exercises.json"
        if ex_file.exists():
            with open(ex_file, "r", encoding="utf-8") as f:
                exercises = json.load(f)

    if not foods:
        food_file = data_dir / "foods.json"
        if food_file.exists():
            with open(food_file, "r", encoding="utf-8") as f:
                foods = json.load(f)

    return CatalogResponse(
        exercises=[ExerciseItem(**e) for e in exercises],
        foods=[FoodItem(**f) for f in foods],
    )
