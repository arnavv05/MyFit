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
