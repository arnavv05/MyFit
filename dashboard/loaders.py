import json
from pathlib import Path
import pandas as pd  # type: ignore[import-untyped]


# Why: Path(__file__).resolve() ensures loading works regardless of the terminal's current working directory.
BASE_DIR = Path(__file__).resolve().parent.parent / "data" / "eda_aggregates"


def load_demographics() -> dict:
    """Load demographic distribution metrics and ratios."""
    with open(BASE_DIR / "demographics_distribution.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_correlations() -> pd.DataFrame:
    """Load Pearson correlation matrix of health metrics."""
    return pd.read_csv(BASE_DIR / "correlations_matrix.csv", index_col=0)


def load_daily_metrics() -> dict:
    """Load summary baseline statistics for sleep and water intake."""
    with open(BASE_DIR / "daily_metrics_summary.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_exercise_popularity() -> pd.DataFrame:
    """Load exercise catalog with interaction counts and ratings."""
    return pd.read_csv(BASE_DIR / "exercise_popularity_summary.csv")


def load_food_macros() -> pd.DataFrame:
    """Load average macronutrients comparison between vegetarian and non-vegetarian foods."""
    return pd.read_csv(BASE_DIR / "food_macros_summary.csv")


def load_users_sample(max_rows: int = 500) -> pd.DataFrame:
    """Load a sample of users with cluster assignments for cluster scatter visualization."""
    users_csv = Path(__file__).resolve().parent.parent / "data" / "users.csv"
    if users_csv.exists():
        df = pd.read_csv(users_csv)
        # Ensure cluster column exists and is categorical
        if "cluster_id" in df.columns:
            df["cluster_id"] = df["cluster_id"].fillna(0).astype(int).astype(str)
        if len(df) > max_rows:
            return df.sample(n=max_rows, random_state=42)
        return df
    return pd.DataFrame()


def load_popular_foods(top_n: int = 15) -> pd.DataFrame:
    """Load food items ranked by interaction count from interactions and food catalog."""
    data_dir = Path(__file__).resolve().parent.parent / "data"
    interactions_csv = data_dir / "interactions.csv"
    foods_json = data_dir / "foods.json"

    if interactions_csv.exists() and foods_json.exists():
        try:
            with open(foods_json, "r", encoding="utf-8") as f:
                foods = json.load(f)
            food_map = {item["_id"]: item["name"] for item in foods}

            df_int = pd.read_csv(interactions_csv)
            food_ints = df_int[df_int["item_type"] == "food"]
            counts = food_ints["item_id"].value_counts().reset_index()
            counts.columns = ["food_id", "interaction_count"]
            counts["name"] = counts["food_id"].map(food_map).fillna(counts["food_id"])
            return counts.head(top_n)
        except Exception:
            pass

    return pd.DataFrame()
