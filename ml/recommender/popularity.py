"""Popularity baseline module for exercises and foods.

Provides global popularity as well as cluster-specific popularity.
Serves as the cold-start fallback (fewer than 5 ratings) and strong baseline.
Strictly respects injury constraints and veg/nonveg hard filtering.
"""

from typing import Any

from recommender.data_access import BaseDataAccess


def get_popular_exercises(
    data_access: BaseDataAccess,
    user_injuries: list[str] | None = None,
    cluster_user_ids: list[str] | None = None,
    n: int = 5,
) -> list[dict[str, Any]]:
    """Compute top popular exercises filtered by user injuries."""
    exercises_df = data_access.get_exercises()
    if exercises_df.empty:
        return []

    interactions_df = data_access.get_interactions(item_type="exercise")
    user_injuries = [
        inj.lower().strip() for inj in (user_injuries or []) if inj.strip()
    ]

    # Filter out exercises that conflict with user injuries
    def parse_injury_flags(val) -> list[str]:
        if isinstance(val, (list, tuple, set)):
            return [str(f).strip().lower() for f in val if str(f).strip()]
        if not val:
            return []
        val_str = str(val).strip("[]'\" ")
        import re

        tokens = re.split(r"[,;|]", val_str)
        return [
            t.strip().strip("'\"").lower()
            for t in tokens
            if t.strip() and t.strip().lower() != "none"
        ]

    def is_exercise_safe(row) -> bool:
        flags = parse_injury_flags(row.get("injury_flags", ""))
        return not any(inj in flags for inj in user_injuries)

    safe_exercises = exercises_df[exercises_df.apply(is_exercise_safe, axis=1)]
    if safe_exercises.empty:
        safe_exercises = exercises_df

    # Calculate popularity scores
    if not interactions_df.empty:
        if cluster_user_ids:
            cluster_interactions = interactions_df[
                interactions_df["user_id"].isin(cluster_user_ids)
            ]
            if not cluster_interactions.empty:
                interactions_df = cluster_interactions

        # Weighted score = count * avg_rating
        stats = (
            interactions_df.groupby("item_id")
            .agg(
                count=("rating", "count"),
                avg_rating=("rating", "mean"),
            )
            .reset_index()
        )

        safe_exercises = safe_exercises.merge(
            stats, left_on="_id", right_on="item_id", how="left"
        )
        safe_exercises["count"] = safe_exercises["count"].fillna(0)
        safe_exercises["avg_rating"] = safe_exercises["avg_rating"].fillna(3.5)
        safe_exercises["score"] = safe_exercises["count"] * safe_exercises["avg_rating"]
        safe_exercises = safe_exercises.sort_values(
            by=["score", "avg_rating"], ascending=False
        )

    records = safe_exercises.head(n).to_dict(orient="records")
    return records


def get_popular_foods(
    data_access: BaseDataAccess,
    diet_type: str = "veg",
    cluster_user_ids: list[str] | None = None,
    n: int = 5,
) -> list[dict[str, Any]]:
    """Compute top popular foods strictly respecting veg hard filter."""
    foods_df = data_access.get_foods()
    if foods_df.empty:
        return []

    # HARD FILTER: veg users must NEVER receive nonveg foods
    if diet_type.lower() == "veg":
        valid_foods = foods_df[foods_df["diet_type"] == "veg"]
    else:
        valid_foods = foods_df

    interactions_df = data_access.get_interactions(item_type="food")

    if not interactions_df.empty:
        if cluster_user_ids:
            cluster_interactions = interactions_df[
                interactions_df["user_id"].isin(cluster_user_ids)
            ]
            if not cluster_interactions.empty:
                interactions_df = cluster_interactions

        stats = (
            interactions_df.groupby("item_id")
            .agg(
                count=("rating", "count"),
                avg_rating=("rating", "mean"),
            )
            .reset_index()
        )

        valid_foods = valid_foods.merge(
            stats, left_on="_id", right_on="item_id", how="left"
        )
        valid_foods["count"] = valid_foods["count"].fillna(0)
        valid_foods["avg_rating"] = valid_foods["avg_rating"].fillna(3.5)
        valid_foods["score"] = valid_foods["count"] * valid_foods["avg_rating"]
        valid_foods = valid_foods.sort_values(
            by=["score", "avg_rating"], ascending=False
        )

    records = valid_foods.head(n).to_dict(orient="records")
    return records
