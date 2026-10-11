"""Exercise Recommender module.

Hybrid recommender combining:
1. User-item collaborative filtering (cosine similarity).
2. Cold-start fallback via cluster popularity (<5 interactions).
3. Hard safety filtering for user injuries.
4. Calorie burn estimation using MET formula with realistic duration allocation.
5. Explainable 'reason' metadata for each recommendation.

Output matches exact API contract expected by Member A's backend:
[
  {
    "exercise_id": str,
    "name": str,
    "duration_min": int,
    "est_kcal": float,
    "reason": str
  }
]
"""

from typing import Any

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from recommender.calories import DEFAULT_TARGET_BURN_KCAL, allocate_exercise_durations
from recommender.clustering import predict_cluster
from recommender.data_access import BaseDataAccess, get_data_access
from recommender.popularity import get_popular_exercises


def recommend_exercises_for_user(
    user_id: str,
    n: int = 4,
    data_access: BaseDataAccess | None = None,
    target_burn_kcal: float = DEFAULT_TARGET_BURN_KCAL,
) -> list[dict[str, Any]]:
    """Generate top-N exercise recommendations for a user."""
    da = data_access or get_data_access()
    user = da.get_user(user_id)

    # Handle unknown user edge case
    if not user:
        weight_kg = 70.0
        injuries = []
        cluster_id = None
        cluster_label = "General Fitness"
    else:
        profile = user.get("profile", {})
        weight_kg = float(profile.get("weight_kg", 70.0))
        injuries = [str(i).lower().strip() for i in profile.get("injuries", []) if str(i).strip()]
        logs = da.get_user_logs(user_id, limit=14)
        cluster_info = predict_cluster(user, logs)
        cluster_id = cluster_info["cluster_id"]
        cluster_label = cluster_info["cluster_label"]

    exercises_df = da.get_exercises()
    if exercises_df.empty:
        return []

    # Map exercise injuries
    def is_safe(row) -> bool:
        flags_str = str(row.get("injury_flags", ""))
        flags = [f.strip().lower() for f in flags_str.split(";") if f.strip() and f.strip() != "none"]
        return not any(inj in flags for inj in injuries)

    safe_exercises_df = exercises_df[exercises_df.apply(is_safe, axis=1)].copy()
    if safe_exercises_df.empty:
        safe_exercises_df = exercises_df.copy()

    interactions_df = da.get_interactions(item_type="exercise")
    user_interactions = interactions_df[interactions_df["user_id"] == user_id] if not interactions_df.empty else pd.DataFrame()

    candidate_exercises = []

    # Collaborative filtering check: requires at least 5 ratings for warm CF
    if len(user_interactions) >= 5:
        # Build user-item interaction matrix
        pivot = interactions_df.pivot_table(index="user_id", columns="item_id", values="rating").fillna(0)
        if user_id in pivot.index:
            user_ratings = pivot.loc[[user_id]]
            # Cosine similarity between users
            user_sim = cosine_similarity(user_ratings, pivot)[0]
            sim_series = pd.Series(user_sim, index=pivot.index).drop(index=user_id, errors="ignore")
            top_similar_users = sim_series.nlargest(15).index

            # Score candidates based on similar users' ratings
            sub_pivot = pivot.loc[top_similar_users]
            cf_scores = sub_pivot.mean(axis=0)

            # Filter already rated items
            already_done = user_interactions["item_id"].tolist()
            candidate_ids = [ex_id for ex_id in cf_scores.index if ex_id not in already_done and ex_id in safe_exercises_df["_id"].values]

            top_cf_ids = pd.Series(cf_scores[candidate_ids]).nlargest(n).index.tolist()
            for ex_id in top_cf_ids:
                row = safe_exercises_df[safe_exercises_df["_id"] == ex_id].iloc[0]
                candidate_exercises.append({
                    "exercise_id": str(row["_id"]),
                    "name": str(row["name"]),
                    "met_value": float(row["met_value"]),
                    "reason": "Recommended based on workouts loved by members with similar training profiles",
                })

    # Cold start or fallback if CF yields fewer than N
    if len(candidate_exercises) < n:
        needed = n - len(candidate_exercises)
        popular_items = get_popular_exercises(
            data_access=da,
            user_injuries=injuries,
            n=needed + len(candidate_exercises) + 5,
        )

        existing_ids = {c["exercise_id"] for c in candidate_exercises}
        for pop_item in popular_items:
            ex_id = str(pop_item["_id"])
            if ex_id not in existing_ids:
                reason = (
                    f"Top rated for your '{cluster_label}' cluster and safe for your joint/injury profile"
                    if cluster_id is not None
                    else "Popular core workout safe for your activity level"
                )
                candidate_exercises.append({
                    "exercise_id": ex_id,
                    "name": str(pop_item["name"]),
                    "met_value": float(pop_item["met_value"]),
                    "reason": reason,
                })
                existing_ids.add(ex_id)
                if len(candidate_exercises) >= n:
                    break

    # Calculate MET-based durations and calorie burn
    candidates_to_allocate = candidate_exercises[:n]
    allocated = allocate_exercise_durations(
        candidates_to_allocate,
        target_kcal_burn=target_burn_kcal,
        weight_kg=weight_kg,
    )

    # Format output according to exact API contract
    final_recs = []
    for item in allocated:
        final_recs.append({
            "exercise_id": item["exercise_id"],
            "name": item["name"],
            "duration_min": int(item["duration_min"]),
            "est_kcal": float(item["est_kcal"]),
            "reason": item["reason"],
        })

    return final_recs
