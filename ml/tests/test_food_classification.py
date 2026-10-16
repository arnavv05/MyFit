import json
import re
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"

NONVEG_KEYWORD_PATTERN = re.compile(
    r"\b(egg|eggs|chicken|fish|mutton|prawn|prawns|beef|pork|meat|salmon|tuna|turkey|lamb|bacon|shrimp|tilapia|quail)\b",
    re.IGNORECASE,
)


def test_foods_catalog_size_and_sync():
    """Verify foods.csv and foods.json exist, have at least 150 items, and have matching counts."""
    csv_path = DATA_DIR / "foods.csv"
    json_path = DATA_DIR / "foods.json"

    assert csv_path.exists(), "data/foods.csv does not exist"
    assert json_path.exists(), "data/foods.json does not exist"

    df = pd.read_csv(csv_path)
    with open(json_path, "r", encoding="utf-8") as f:
        json_items = json.load(f)

    assert len(df) >= 150, f"Expected at least 150 foods in CSV, got {len(df)}"
    assert (
        len(json_items) >= 150
    ), f"Expected at least 150 foods in JSON, got {len(json_items)}"
    assert len(df) == len(
        json_items
    ), "foods.csv and foods.json row counts do not match"


def test_diet_type_validity():
    """Verify every food item has diet_type exactly 'veg' or 'nonveg' with no nulls."""
    df = pd.read_csv(DATA_DIR / "foods.csv")
    assert "diet_type" in df.columns, "diet_type column missing from foods.csv"

    invalid_rows = df[~df["diet_type"].isin(["veg", "nonveg"])]
    assert invalid_rows.empty, f"Found invalid diet_type entries: {invalid_rows[['_id', 'name', 'diet_type']].to_dict(orient='records')}"


def test_no_nonveg_keywords_in_veg_foods():
    """Verify that no food tagged as 'veg' contains non-veg keywords (chicken, fish, egg, etc.)."""
    df = pd.read_csv(DATA_DIR / "foods.csv")
    veg_foods = df[df["diet_type"] == "veg"]

    misclassified = []
    for _, row in veg_foods.iterrows():
        name = str(row["name"])
        match = NONVEG_KEYWORD_PATTERN.search(name)
        if match:
            misclassified.append(
                {
                    "id": row["_id"],
                    "name": name,
                    "keyword": match.group(0),
                    "diet_type": row["diet_type"],
                }
            )

    assert (
        not misclassified
    ), f"Found non-veg foods misclassified as veg: {misclassified}"


def test_veg_user_hard_filter():
    """Verify that calling get_food_recs for a veg user NEVER returns nonveg items."""
    from recommender import get_food_recs

    # Test with user who is veg
    recs = get_food_recs(user_id="usr_demo_student", kcal_target=450.0, n=5)
    assert len(recs) > 0, "No food recommendations returned"

    df_foods = pd.read_csv(DATA_DIR / "foods.csv").set_index("_id")
    for r in recs:
        food_id = r["food_id"]
        if food_id in df_foods.index:
            catalog_dt = df_foods.loc[food_id, "diet_type"]
            assert (
                catalog_dt == "veg"
            ), f"Veg user received non-veg food {food_id} ({r['name']})!"
        assert (
            r.get("diet_type") == "veg"
        ), f"Recommendation item diet_type expected 'veg', got {r.get('diet_type')}"
