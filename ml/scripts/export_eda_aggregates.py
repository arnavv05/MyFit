"""Export EDA figures and statistical aggregates for Member C's Streamlit dashboard.

Produces documented CSV and JSON artifacts in data/eda_aggregates/:
- demographics_distribution.json: Age groups, BMI categories, activity levels, diet distribution.
- correlations_matrix.csv: Pearson correlation between weight change, sleep, water, workouts, calorie balance.
- daily_metrics_summary.json: Mean, std, and percentiles for sleep, water, and workout metrics.
- exercise_popularity_summary.csv: Exercise engagement and rating distributions.
- food_macros_summary.csv: Calorie density and macro distributions by diet_type.
- README.md: Integration documentation for Member C.
"""

import json
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = ML_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = DATA_DIR / "eda_aggregates"


def export_aggregates() -> None:
    print(f"Exporting EDA aggregates to {OUTPUT_DIR}...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    users_df = pd.read_csv(DATA_DIR / "users.csv")
    logs_df = pd.read_csv(DATA_DIR / "daily_logs.csv")
    exercises_df = pd.read_csv(DATA_DIR / "exercises.csv")
    foods_df = pd.read_csv(DATA_DIR / "foods.csv")
    interactions_df = pd.read_csv(DATA_DIR / "interactions.csv")

    # 1. Demographics Distribution
    bmi_vals = users_df["weight_kg"] / ((users_df["height_cm"] / 100.0) ** 2)
    bmi_categories = (
        pd.cut(
            bmi_vals,
            bins=[0, 18.5, 24.9, 29.9, 100],
            labels=["underweight", "normal", "overweight", "obese"],
        )
        .value_counts(normalize=True)
        .to_dict()
    )

    demographics = {
        "total_users": len(users_df),
        "gender_ratio": users_df["gender"].value_counts().to_dict(),
        "diet_type_ratio": users_df["diet_type"].value_counts().to_dict(),
        "activity_level_ratio": users_df["activity_level"].value_counts().to_dict(),
        "bmi_categories_pct": {
            k: round(float(v) * 100, 2) for k, v in bmi_categories.items()
        },
        "age_distribution": {
            "mean": round(float(users_df["age"].mean()), 1),
            "median": round(float(users_df["age"].median()), 1),
            "std": round(float(users_df["age"].std()), 1),
            "min": int(users_df["age"].min()),
            "max": int(users_df["age"].max()),
        },
    }

    with open(
        OUTPUT_DIR / "demographics_distribution.json", "w", encoding="utf-8"
    ) as f:
        json.dump(demographics, f, indent=2)

    # 2. Daily Log Correlations & Statistics
    # Calculate daily calorie balance
    logs_df["calorie_balance"] = logs_df["kcal_in"] - logs_df["kcal_out"]

    # Calculate user-level weight change
    logs_sorted = logs_df.sort_values(["user_id", "date"])
    first_weights = logs_sorted.groupby("user_id")["weight_kg"].first()
    last_weights = logs_sorted.groupby("user_id")["weight_kg"].last()
    weight_changes = (last_weights - first_weights).rename("net_weight_change_kg")

    user_means = (
        logs_sorted.groupby("user_id")
        .agg(
            {
                "sleep_hours": "mean",
                "water_ml": "mean",
                "calorie_balance": "mean",
                "kcal_in": "mean",
                "kcal_out": "mean",
            }
        )
        .join(weight_changes)
    )

    corr_matrix = user_means.corr().round(4)
    corr_matrix.to_csv(OUTPUT_DIR / "correlations_matrix.csv")

    daily_summary = {
        "sleep_hours": {
            "mean": round(float(logs_df["sleep_hours"].mean()), 2),
            "std": round(float(logs_df["sleep_hours"].std()), 2),
            "q25": round(float(logs_df["sleep_hours"].quantile(0.25)), 2),
            "q70": round(float(logs_df["sleep_hours"].quantile(0.70)), 2),
        },
        "water_ml": {
            "mean": round(float(logs_df["water_ml"].mean()), 1),
            "std": round(float(logs_df["water_ml"].std()), 1),
            "median": round(float(logs_df["water_ml"].median()), 1),
        },
        "calorie_balance_mean": round(float(logs_df["calorie_balance"].mean()), 1),
        "total_logs": len(logs_df),
    }

    with open(OUTPUT_DIR / "daily_metrics_summary.json", "w", encoding="utf-8") as f:
        json.dump(daily_summary, f, indent=2)

    # 3. Exercise Popularity & Category Aggregates
    ex_interactions = interactions_df[interactions_df["item_type"] == "exercise"]
    ex_stats = (
        ex_interactions.groupby("item_id")
        .agg(
            interaction_count=("rating", "count"),
            average_rating=("rating", "mean"),
        )
        .reset_index()
    )

    ex_summary = exercises_df.merge(
        ex_stats, left_on="_id", right_on="item_id", how="left"
    )
    ex_summary["interaction_count"] = (
        ex_summary["interaction_count"].fillna(0).astype(int)
    )
    ex_summary["average_rating"] = ex_summary["average_rating"].fillna(0.0).round(2)
    ex_summary = ex_summary.sort_values(by="interaction_count", ascending=False)
    ex_summary.to_csv(OUTPUT_DIR / "exercise_popularity_summary.csv", index=False)

    # 4. Food Macro Distributions
    food_summary = (
        foods_df.groupby("diet_type")
        .agg(
            item_count=("_id", "count"),
            avg_kcal_100g=("kcal_per_100g", "mean"),
            avg_protein_g=("protein_g", "mean"),
            avg_carbs_g=("carbs_g", "mean"),
            avg_fat_g=("fat_g", "mean"),
            avg_fiber_g=("fiber_g", "mean"),
        )
        .round(2)
        .reset_index()
    )
    food_summary.to_csv(OUTPUT_DIR / "food_macros_summary.csv", index=False)

    # 5. Write Documentation for Member C
    readme_content = """# EDA Aggregates for Dashboard (Member C)

These precomputed statistical aggregates are generated by Member B for direct consumption in the **Streamlit Analytics Dashboard** (`/dashboard`).

---

## 📊 File Catalog

1. `demographics_distribution.json`:
   - User base breakdown: total count, gender breakdown, diet type ratio (veg vs non-veg), activity levels, and BMI classification percentages.
   - Ideal for: Population demographic pie charts and summary stat KPI cards.

2. `correlations_matrix.csv`:
   - Pearson correlation matrix across: `net_weight_change_kg`, `sleep_hours`, `water_ml`, `calorie_balance`, `kcal_in`, `kcal_out`.
   - Ideal for: Heatmap in Streamlit showing how caloric deficit and sleep drive weight loss.

3. `daily_metrics_summary.json`:
   - Summary statistics (mean, std, quartiles) for daily sleep and hydration volume.
   - Ideal for: Benchmark distribution curves and habit tracker baselines.

4. `exercise_popularity_summary.csv`:
   - List of all exercises with category, MET value, difficulty, total interaction count, and average user rating.
   - Ideal for: "Most Popular Workouts" bar chart and category breakdown.

5. `food_macros_summary.csv`:
   - Mean macronutrient breakdown comparing Vegetarian vs Non-Vegetarian food items.
   - Ideal for: Macro balance comparison charts.

---

## 💡 Example Streamlit Usage

```python
import streamlit as st
import pandas as pd
import json

# Load demographics
with open("data/eda_aggregates/demographics_distribution.json") as f:
    demo = json.load(f)

st.metric("Total Active Users", demo["total_users"])
st.metric("Avg Age", demo["age_distribution"]["mean"])

# Load correlations
corr_df = pd.read_csv("data/eda_aggregates/correlations_matrix.csv", index_col=0)
st.write("Correlation Heatmap", corr_df)
```
"""

    with open(OUTPUT_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("EDA aggregates successfully exported!")


if __name__ == "__main__":
    export_aggregates()
