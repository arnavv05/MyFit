"""Food Recommender module.

Upgraded Day 2 Recommender combining:
1. Strict dietary safety filtering (HARD CONSTRAINT: veg users NEVER get nonveg items).
2. Item-based collaborative filtering (cosine similarity between foods rated by users).
3. Goal-specific macro-fit scoring (protein-first for muscle building & fat loss).
4. Calorie-target constrained serving allocation (total kcal lands close to kcal_target).
5. Explainable 'reason' metadata for each item.

Output matches exact API contract expected by Member A's backend:
[
  {
    "food_id": str,
    "name": str,
    "grams": float,
    "kcal": float,
    "macros": {
      "protein_g": float,
      "carbs_g": float,
      "fat_g": float,
      "fiber_g": float
    },
    "reason": str
  }
]
"""

from typing import Any

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from recommender.data_access import BaseDataAccess, get_data_access


class HybridFoodRecommender:
    """Hybrid item-based CF and macro-fit recommender for foods."""

    def __init__(self, data_access: BaseDataAccess) -> None:
        self.da = data_access
        self.foods_df = self.da.get_foods()
        self.interactions_df = self.da.get_interactions(item_type="food")
        self._item_sim_matrix: pd.DataFrame | None = None
        self._fitted = False

    def fit(self) -> "HybridFoodRecommender":
        """Fit item-item similarity matrix across food interactions."""
        if self.interactions_df.empty or self.foods_df.empty:
            self._fitted = True
            return self

        pivot = self.interactions_df.pivot_table(
            index="user_id",
            columns="item_id",
            values="rating",
            aggfunc="mean",
        ).fillna(0.0)

        # Transpose so rows are food items
        item_vectors = pivot.T
        if len(item_vectors) > 1:
            sim_array = cosine_similarity(item_vectors)
            self._item_sim_matrix = pd.DataFrame(
                sim_array,
                index=item_vectors.index,
                columns=item_vectors.index,
            )

        self._fitted = True
        return self

    def _compute_item_cf_score(self, candidate_id: str, user_rated: dict[str, float]) -> tuple[float, str | None]:
        """Compute item-based CF score from items the user rated favorably."""
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
        kcal_target: float = 400.0,
        n: int = 3,
    ) -> list[dict[str, Any]]:
        """Recommend N food items replenishing kcal_target, strictly adhering to diet_type."""
        if not self._fitted:
            self.fit()

        user = self.da.get_user(user_id)

        # 1. Extract user profile constraints
        diet_type = "veg"
        goal_type = "maintain"
        if user:
            profile = user.get("profile", {})
            diet_type = str(profile.get("diet_type", "veg")).lower()
            goal = user.get("goal", {})
            target_weight = float(goal.get("target_weight_kg", profile.get("weight_kg", 70.0)))
            current_weight = float(profile.get("weight_kg", 70.0))
            if target_weight < current_weight:
                goal_type = "loss"
            elif target_weight > current_weight:
                goal_type = "gain"

        if self.foods_df.empty:
            return []

        # 2. HARD SAFETY FILTER: Vegetarian users MUST NEVER receive nonveg foods
        if diet_type == "veg":
            eligible_df = self.foods_df[self.foods_df["diet_type"] == "veg"].copy()
        else:
            eligible_df = self.foods_df.copy()

        # 3. Macro-Fit Score
        def compute_macro_score(row: pd.Series) -> float:
            kcal_100g = max(float(row.get("kcal_per_100g", 100)), 20.0)
            protein_100g = float(row.get("protein_g", 0.0))
            fiber_100g = float(row.get("fiber_g", 0.0))
            protein_density = (protein_100g / kcal_100g) * 100.0

            if goal_type in ["loss", "gain"]:
                # High protein priority for muscle sparing or building
                return protein_density * 1.8 + fiber_100g * 0.4
            # Balanced nutrition
            return protein_density * 1.0 + fiber_100g * 0.5 + 2.0

        eligible_df["macro_score"] = eligible_df.apply(compute_macro_score, axis=1)

        # 4. User Interaction History & CF Scoring
        user_history = pd.DataFrame()
        if not self.interactions_df.empty:
            user_history = self.interactions_df[self.interactions_df["user_id"] == user_id]

        user_rated_map = {}
        if not user_history.empty:
            user_rated_map = dict(zip(user_history["item_id"], user_history["rating"]))

        scored_candidates = []
        name_map = dict(zip(self.foods_df["_id"], self.foods_df["name"]))

        for _, row in eligible_df.iterrows():
            f_id = str(row["_id"])
            macro_score = float(row["macro_score"])

            # Item-CF score
            cf_score, anchor_id = self._compute_item_cf_score(f_id, user_rated_map)

            # Combined score: 60% macro fit (normalized), 40% CF score
            norm_macro = min(5.0, max(1.0, macro_score / 4.0))
            combined_score = 0.55 * norm_macro + 0.45 * cf_score

            if anchor_id and anchor_id in name_map:
                anchor_name = name_map[anchor_id]
                reason = f"Personalized {row['diet_type']} recovery choice, similar to {anchor_name} that you liked"
            elif float(row.get("protein_g", 0.0)) >= 10.0:
                reason = f"High-protein {row['diet_type']} food ({row['protein_g']}g/100g) ideal for post-workout muscle recovery"
            else:
                reason = f"Wholesome {row['diet_type']} meal providing clean energy to hit your daily calorie target"

            scored_candidates.append({
                "food_id": f_id,
                "name": str(row["name"]),
                "row": row,
                "score": combined_score,
                "reason": reason,
            })

        # Sort and pick top diverse candidates
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        selected_candidates = scored_candidates[:n]

        # 5. Serving Size (grams) Allocation to land close to kcal_target
        safe_target = max(100.0, float(kcal_target))
        kcal_per_item = safe_target / max(1, len(selected_candidates))

        recs = []
        for item in selected_candidates:
            row = item["row"]
            kcal_100g = max(float(row["kcal_per_100g"]), 20.0)
            protein_100g = float(row.get("protein_g", 0.0))
            carbs_100g = float(row.get("carbs_g", 0.0))
            fat_100g = float(row.get("fat_g", 0.0))
            fiber_100g = float(row.get("fiber_g", 0.0))

            # Grams needed to provide kcal_per_item
            raw_grams = (kcal_per_item / kcal_100g) * 100.0
            grams = float(max(25.0, min(350.0, round(raw_grams / 10.0) * 10.0)))

            factor = grams / 100.0
            item_kcal = round(kcal_100g * factor, 1)
            macros = {
                "protein_g": round(protein_100g * factor, 1),
                "carbs_g": round(carbs_100g * factor, 1),
                "fat_g": round(fat_100g * factor, 1),
                "fiber_g": round(fiber_100g * factor, 1),
            }

            recs.append({
                "food_id": str(item["food_id"]),
                "name": str(item["name"]),
                "grams": grams,
                "kcal": item_kcal,
                "macros": macros,
                "reason": str(item["reason"]),
            })

        return recs


# Cached engine instance
_food_engine: HybridFoodRecommender | None = None


def recommend_foods_for_user(
    user_id: str,
    kcal_target: float = 400.0,
    n: int = 3,
    data_access: BaseDataAccess | None = None,
) -> list[dict[str, Any]]:
    """Public function routing to HybridFoodRecommender."""
    global _food_engine
    da = data_access or get_data_access()
    if _food_engine is None or _food_engine.da is not da:
        _food_engine = HybridFoodRecommender(da)
        _food_engine.fit()

    return _food_engine.recommend(user_id=user_id, kcal_target=kcal_target, n=n)
