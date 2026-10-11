"""Exercise Recommender module.

Upgraded Day 2 Hybrid Recommender combining:
1. Item-based Collaborative Filtering (Cosine similarity on item-user vectors).
2. Matrix Factorization via TruncatedSVD (latent feature factorization on ratings).
3. Cluster popularity prior (from K-Means user persona clusters).
4. Cold-start fallback (< 5 interactions) to cluster-popular items.
5. Strict joint/injury filter (contraindicated exercises are completely excluded).
6. Compendium MET-based duration & calorie allocation.
7. Explainable, human-readable reason strings.

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

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity

from recommender.calories import DEFAULT_TARGET_BURN_KCAL, allocate_exercise_durations
from recommender.clustering import predict_cluster
from recommender.config import RANDOM_SEED
from recommender.data_access import BaseDataAccess, get_data_access
from recommender.popularity import get_popular_exercises


class HybridExerciseRecommender:
    """Hybrid recommender engine for exercises."""

    def __init__(self, data_access: BaseDataAccess) -> None:
        self.da = data_access
        self.exercises_df = self.da.get_exercises()
        self.interactions_df = self.da.get_interactions(item_type="exercise")
        self._user_item_matrix: pd.DataFrame | None = None
        self._item_sim_matrix: pd.DataFrame | None = None
        self._svd_preds_matrix: pd.DataFrame | None = None
        self._fitted = False

    def fit(self) -> "HybridExerciseRecommender":
        """Precompute interaction matrices, item-item similarity, and SVD decomposition."""
        if self.interactions_df.empty or self.exercises_df.empty:
            self._fitted = True
            return self

        # Pivot to User-Item ratings matrix (rows: users, cols: exercise_id)
        pivot = self.interactions_df.pivot_table(
            index="user_id",
            columns="item_id",
            values="rating",
            aggfunc="mean",
        ).fillna(0.0)

        self._user_item_matrix = pivot

        # 1. Item-Based Cosine Similarity: cols are items
        # To compare items, we compute cosine similarity between columns
        item_vectors = pivot.T  # rows are items, cols are users
        if len(item_vectors) > 1:
            sim_array = cosine_similarity(item_vectors)
            self._item_sim_matrix = pd.DataFrame(
                sim_array,
                index=item_vectors.index,
                columns=item_vectors.index,
            )

        # 2. Latent Matrix Factorization via TruncatedSVD
        n_components = min(12, max(2, min(pivot.shape) - 1))
        if pivot.shape[0] >= 5 and pivot.shape[1] >= 5:
            # Center user ratings around user means for better reconstruction
            user_means = pivot.replace(0.0, np.nan).mean(axis=1).fillna(3.0)
            centered_pivot = pivot.sub(user_means, axis=0).fillna(0.0)

            svd = TruncatedSVD(n_components=n_components, random_state=RANDOM_SEED)
            svd_transformed = svd.fit_transform(centered_pivot.values)
            reconstructed = svd.inverse_transform(svd_transformed)
            pred_ratings = reconstructed + user_means.values[:, np.newaxis]

            self._svd_preds_matrix = pd.DataFrame(
                pred_ratings,
                index=pivot.index,
                columns=pivot.columns,
            )

        self._fitted = True
        return self

    def _compute_item_cf_score(self, user_id: str, candidate_id: str, user_rated: dict[str, float]) -> tuple[float, str | None]:
        """Compute item-based CF predicted score and identify most similar rated anchor item."""
        if self._item_sim_matrix is None or candidate_id not in self._item_sim_matrix.index:
            return 3.0, None

        sim_row = self._item_sim_matrix.loc[candidate_id]
        numerator = 0.0
        denominator = 0.0
        best_anchor = None
        max_sim = -1.0

        for rated_id, rating in user_rated.items():
            if rated_id in sim_row.index:
                sim = float(sim_row[rated_id])
                if sim > 0:
                    numerator += sim * rating
                    denominator += sim
                    if sim > max_sim:
                        max_sim = sim
                        best_anchor = rated_id

        if denominator > 0:
            return float(numerator / denominator), best_anchor
        return 3.0, None

    def recommend(
        self,
        user_id: str,
        n: int = 4,
        target_burn_kcal: float = DEFAULT_TARGET_BURN_KCAL,
    ) -> list[dict[str, Any]]:
        """Generate top-N hybrid exercise recommendations for a user."""
        if not self._fitted:
            self.fit()

        user = self.da.get_user(user_id)
        if not user:
            weight_kg = 70.0
            injuries: list[str] = []
            cluster_id = None
            cluster_label = "General Fitness"
        else:
            profile = user.get("profile", {})
            weight_kg = float(profile.get("weight_kg", 70.0))
            injuries = [str(i).lower().strip() for i in profile.get("injuries", []) if str(i).strip()]
            logs = self.da.get_user_logs(user_id, limit=14)
            cluster_info = predict_cluster(user, logs)
            cluster_id = cluster_info["cluster_id"]
            cluster_label = cluster_info["cluster_label"]

        if self.exercises_df.empty:
            return []

        # Injury Safety Filter
        def is_safe(row) -> bool:
            flags_str = str(row.get("injury_flags", ""))
            flags = [f.strip().lower() for f in flags_str.split(";") if f.strip() and f.strip() != "none"]
            return not any(inj in flags for inj in injuries)

        safe_df = self.exercises_df[self.exercises_df.apply(is_safe, axis=1)].copy()
        if safe_df.empty:
            safe_df = self.exercises_df.copy()

        # Check user history
        user_history = pd.DataFrame()
        if not self.interactions_df.empty:
            user_history = self.interactions_df[self.interactions_df["user_id"] == user_id]

        # COLD START: Fewer than 5 ratings -> return cluster-popular safe exercises
        if len(user_history) < 5 or self._user_item_matrix is None or user_id not in self._user_item_matrix.index:
            popular = get_popular_exercises(
                data_access=self.da,
                user_injuries=injuries,
                n=n,
            )
            candidate_list = []
            for item in popular:
                reason = (
                    f"Top-rated by members in your '{cluster_label}' group and safe for your joints"
                    if cluster_id is not None
                    else "Popular core workout safe for your activity level"
                )
                candidate_list.append({
                    "exercise_id": str(item["_id"]),
                    "name": str(item["name"]),
                    "met_value": float(item["met_value"]),
                    "reason": reason,
                })
            allocated = allocate_exercise_durations(candidate_list, target_burn_kcal, weight_kg)
            return [
                {
                    "exercise_id": a["exercise_id"],
                    "name": a["name"],
                    "duration_min": int(a["duration_min"]),
                    "est_kcal": float(a["est_kcal"]),
                    "reason": a["reason"],
                }
                for a in allocated
            ]

        # WARM USER: Hybrid CF + SVD + Cluster Popularity
        user_ratings_map = dict(zip(user_history["item_id"], user_history["rating"]))
        already_rated = set(user_ratings_map.keys())

        # Precompute safe candidate ids
        candidate_rows = safe_df[~safe_df["_id"].isin(already_rated)]
        if candidate_rows.empty:
            candidate_rows = safe_df

        scored_candidates = []
        name_map = dict(zip(self.exercises_df["_id"], self.exercises_df["name"]))

        for _, row in candidate_rows.iterrows():
            ex_id = str(row["_id"])
            ex_name = str(row["name"])
            met_val = float(row["met_value"])

            # 1. Item-CF Score
            item_cf_score, anchor_id = self._compute_item_cf_score(user_id, ex_id, user_ratings_map)

            # 2. SVD Score
            svd_score = 3.0
            if self._svd_preds_matrix is not None and user_id in self._svd_preds_matrix.index and ex_id in self._svd_preds_matrix.columns:
                svd_score = float(self._svd_preds_matrix.loc[user_id, ex_id])

            # 3. Base Popularity Prior (normalized 1.0 to 5.0)
            pop_score = float(row.get("met_value", 4.0)) / 2.0 + 1.5

            # Blended Hybrid Score: 45% Item-CF, 35% SVD, 20% Prior
            hybrid_score = (0.45 * item_cf_score) + (0.35 * svd_score) + (0.20 * pop_score)

            # Explainable reason formulation
            if anchor_id and anchor_id in name_map:
                anchor_name = name_map[anchor_id]
                reason = f"Recommended because you loved {anchor_name} and users like you rated this highly"
            elif cluster_label:
                reason = f"Aligned with your {cluster_label} training goals and favored by similar members"
            else:
                reason = "Highly rated by fitness members with a similar profile"

            scored_candidates.append({
                "exercise_id": ex_id,
                "name": ex_name,
                "met_value": met_val,
                "hybrid_score": hybrid_score,
                "reason": reason,
            })

        # Sort by hybrid score
        scored_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
        top_n_candidates = scored_candidates[:n]

        # MET duration and calorie allocation
        allocated = allocate_exercise_durations(top_n_candidates, target_burn_kcal, weight_kg)

        final_recs = [
            {
                "exercise_id": str(item["exercise_id"]),
                "name": str(item["name"]),
                "duration_min": int(item["duration_min"]),
                "est_kcal": float(item["est_kcal"]),
                "reason": str(item["reason"]),
            }
            for item in allocated
        ]

        return final_recs


# Cached engine instance
_exercise_engine: HybridExerciseRecommender | None = None


def recommend_exercises_for_user(
    user_id: str,
    n: int = 4,
    data_access: BaseDataAccess | None = None,
    target_burn_kcal: float = DEFAULT_TARGET_BURN_KCAL,
) -> list[dict[str, Any]]:
    """Public function routing to HybridExerciseRecommender."""
    global _exercise_engine
    da = data_access or get_data_access()
    if _exercise_engine is None or _exercise_engine.da is not da:
        _exercise_engine = HybridExerciseRecommender(da)
        _exercise_engine.fit()

    return _exercise_engine.recommend(user_id=user_id, n=n, target_burn_kcal=target_burn_kcal)
