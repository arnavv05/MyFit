"""Food Recommender module.

Upgraded Personal & Varied Food Recommender combining:
1. Strict dietary safety filtering (HARD CONSTRAINT: veg users NEVER get nonveg items).
2. Goal-specific macro-fit scoring (protein-first for muscle building & fat loss).
3. Live user feedback adaptation (ratings 1-2 excluded, ratings 4-5 boosted).
4. Balanced meal plan composition across meal roles (Protein Main, Healthy Staple, Recovery Snack).
5. Non-veg prioritization: non-veg users actively receive high-protein non-veg choices.
6. Calorie-target constrained serving allocation (total kcal lands within ~10% of kcal_target).
7. Seeded daily rotation (deterministic variety across different days).
8. Explainable 'reason' metadata and diet_type tags.

Output matches exact API contract expected by Member A's backend:
[
  {
    "food_id": str,
    "name": str,
    "diet_type": str,
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

import hashlib
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from recommender.data_access import BaseDataAccess, get_data_access


# Helper to classify foods into balanced meal plan slots
def classify_meal_role(name: str, diet_type: str) -> str:
    """Classify a food item into a role: 'protein_main', 'staple_grain', or 'snack_recovery'."""
    name_lower = name.lower()

    # Non-veg mains
    if diet_type == "nonveg":
        if any(
            w in name_lower
            for w in [
                "chicken",
                "fish",
                "salmon",
                "tuna",
                "mutton",
                "prawn",
                "turkey",
                "tilapia",
                "egg",
                "omelette",
                "shrimp",
            ]
        ):
            return "protein_main"

    # Veg protein mains
    if any(
        w in name_lower
        for w in [
            "paneer",
            "tofu",
            "soya",
            "dal",
            "rajma",
            "chole",
            "chickpea",
            "lentil",
            "edamame",
        ]
    ):
        return "protein_main"

    # Staples & Grains
    if any(
        w in name_lower
        for w in [
            "rice",
            "roti",
            "chapati",
            "oat",
            "oats",
            "quinoa",
            "poha",
            "upma",
            "idli",
            "dosa",
            "bread",
            "pasta",
            "dalia",
            "khichdi",
            "thepla",
            "paratha",
            "potato",
            "noodles",
        ]
    ):
        return "staple_grain"

    # Snacks, Salads & Recovery
    return "snack_recovery"


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

    def _compute_item_cf_score(
        self, candidate_id: str, user_rated: dict[str, float]
    ) -> tuple[float, str | None]:
        """Compute item-based CF score from items the user rated favorably."""
        if (
            self._item_sim_matrix is None
            or candidate_id not in self._item_sim_matrix.index
        ):
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
        user_dict: dict[str, Any] | None = None,
        date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Recommend N food items replenishing kcal_target, strictly adhering to diet_type."""
        if not self._fitted:
            self.fit()

        user = user_dict or self.da.get_user(user_id)

        # 1. Extract user profile constraints
        diet_type = "veg"
        goal_type = "maintain"
        if user:
            profile = user.get("profile", {})
            diet_type = str(profile.get("diet_type", "veg")).lower().strip()
            goal = user.get("goal", {})
            target_weight = float(
                goal.get("target_weight_kg", profile.get("weight_kg", 70.0))
            )
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

        # 3. User Feedback & Ratings
        fresh_user_interactions = self.da.get_user_interactions(
            user_id, item_type="food"
        )
        user_rated_map: dict[str, float] = {}
        if not fresh_user_interactions.empty:
            user_rated_map = dict(
                zip(
                    fresh_user_interactions["item_id"],
                    fresh_user_interactions["rating"],
                )
            )
        elif not self.interactions_df.empty:
            cached_history = self.interactions_df[
                self.interactions_df["user_id"] == user_id
            ]
            if not cached_history.empty:
                user_rated_map = dict(
                    zip(cached_history["item_id"], cached_history["rating"])
                )

        # Exclude foods the user disliked (1-2 stars)
        disliked_foods = {
            f_id for f_id, rating in user_rated_map.items() if rating <= 2
        }
        eligible_df = eligible_df[~eligible_df["_id"].isin(disliked_foods)].copy()
        if eligible_df.empty:
            eligible_df = (
                self.foods_df[self.foods_df["diet_type"] == "veg"].copy()
                if diet_type == "veg"
                else self.foods_df.copy()
            )

        # 4. Scoring: Macro-Fit, Collaborative Filtering, and Persona Relevance
        seed_str = f"{user_id}:{date or 'today'}"
        seed_val = int(hashlib.md5(seed_str.encode("utf-8")).hexdigest(), 16) % (10**8)
        rng = np.random.default_rng(seed_val)

        name_map = dict(zip(self.foods_df["_id"], self.foods_df["name"]))

        def compute_item_score(row: pd.Series) -> tuple[float, str]:
            f_id = str(row["_id"])
            item_dt = str(row.get("diet_type", "veg"))
            _name = str(row["name"])
            kcal_100g = max(float(row.get("kcal_per_100g", 100)), 20.0)
            protein_100g = float(row.get("protein_g", 0.0))
            fiber_100g = float(row.get("fiber_g", 0.0))
            protein_density = (protein_100g / kcal_100g) * 100.0

            # Macro-fit score
            if goal_type in ["loss", "gain"]:
                macro_score = protein_density * 1.5 + fiber_100g * 0.4
            else:
                macro_score = protein_density * 1.0 + fiber_100g * 0.5 + 2.0

            # Item-CF score
            cf_score, anchor_id = self._compute_item_cf_score(f_id, user_rated_map)

            # Boost if nonveg user getting nonveg protein source
            nonveg_priority_boost = 0.0
            if diet_type == "nonveg" and item_dt == "nonveg":
                nonveg_priority_boost = 1.2

            # Boost for items rated 4-5 stars
            affinity_boost = 0.0
            if f_id in user_rated_map and user_rated_map[f_id] >= 4:
                affinity_boost = 1.0
            elif anchor_id and user_rated_map.get(anchor_id, 0) >= 4:
                affinity_boost = 0.6

            # Controlled rotation jitter per user + date
            jitter = rng.uniform(-0.3, 0.3)

            norm_macro = min(5.0, max(1.0, macro_score / 4.0))
            composite = (
                (0.50 * norm_macro)
                + (0.50 * cf_score)
                + nonveg_priority_boost
                + affinity_boost
                + jitter
            )

            # Explainable reason
            if anchor_id and anchor_id in name_map:
                anchor_name = name_map[anchor_id]
                reason = f"Personalized {item_dt} recovery choice, similar to {anchor_name} that you liked"
            elif item_dt == "nonveg":
                reason = f"Lean high-protein non-veg food ({protein_100g}g/100g) powering your {goal_type} goal"
            elif protein_100g >= 12.0:
                reason = f"High-protein {item_dt} food ({protein_100g}g/100g) ideal for post-workout muscle recovery"
            elif fiber_100g >= 4.0:
                reason = f"High-fiber complex {item_dt} staple providing slow-digesting clean energy"
            else:
                reason = (
                    f"Wholesome {item_dt} option balanced for your daily calorie target"
                )

            return composite, reason

        eligible_df["meal_role"] = eligible_df.apply(
            lambda r: classify_meal_role(
                str(r["name"]), str(r.get("diet_type", "veg"))
            ),
            axis=1,
        )

        scored_records = []
        for _, row in eligible_df.iterrows():
            score, reason = compute_item_score(row)
            scored_records.append(
                {
                    "food_id": str(row["_id"]),
                    "name": str(row["name"]),
                    "diet_type": str(row.get("diet_type", "veg")),
                    "meal_role": row["meal_role"],
                    "row": row,
                    "score": score,
                    "reason": reason,
                }
            )

        # Group candidates by role
        roles = ["protein_main", "staple_grain", "snack_recovery"]
        role_candidates: dict[str, list[dict[str, Any]]] = {r: [] for r in roles}
        for item in scored_records:
            role_candidates[item["meal_role"]].append(item)

        for r in roles:
            role_candidates[r].sort(key=lambda x: x["score"], reverse=True)

        # 5. Balanced Selection across Roles
        selected_candidates: list[dict[str, Any]] = []

        if n == 3:
            # Pick 1 from each role for optimal nutrition balance
            for r in roles:
                cands = role_candidates[r]
                if cands:
                    selected_candidates.append(cands[0])
        else:
            # For other n, pick round-robin from available roles
            role_ptrs = {r: 0 for r in roles}
            while len(selected_candidates) < n:
                added = False
                for r in roles:
                    ptr = role_ptrs[r]
                    cands = role_candidates[r]
                    if ptr < len(cands) and len(selected_candidates) < n:
                        selected_candidates.append(cands[ptr])
                        role_ptrs[r] += 1
                        added = True
                if not added:
                    break

        # Fallback if roles didn't have enough items
        if len(selected_candidates) < n:
            all_sorted = sorted(scored_records, key=lambda x: x["score"], reverse=True)
            for item in all_sorted:
                if len(selected_candidates) >= n:
                    break
                if item not in selected_candidates:
                    selected_candidates.append(item)

        # 6. Serving Size (grams) Allocation to land within ~10% of kcal_target
        safe_target = max(100.0, float(kcal_target))

        # Role calorie weighting: Protein Main gets 40%, Staple gets 35%, Snack gets 25%
        role_weights = {
            "protein_main": 0.40,
            "staple_grain": 0.35,
            "snack_recovery": 0.25,
        }

        recs = []
        for idx, item in enumerate(selected_candidates):
            row = item["row"]
            role = item["meal_role"]
            weight_ratio = role_weights.get(
                role, 1.0 / max(1, len(selected_candidates))
            )
            if len(selected_candidates) != 3:
                weight_ratio = 1.0 / len(selected_candidates)

            target_item_kcal = safe_target * weight_ratio

            kcal_100g = max(float(row["kcal_per_100g"]), 20.0)
            protein_100g = float(row.get("protein_g", 0.0))
            carbs_100g = float(row.get("carbs_g", 0.0))
            fat_100g = float(row.get("fat_g", 0.0))
            fiber_100g = float(row.get("fiber_g", 0.0))

            # Grams needed to provide target_item_kcal
            raw_grams = (target_item_kcal / kcal_100g) * 100.0
            # Sensible bounds: 30g to 350g, rounded to nearest 5g
            grams = float(max(30.0, min(350.0, round(raw_grams / 5.0) * 5.0)))

            factor = grams / 100.0
            item_kcal = round(kcal_100g * factor, 1)
            macros = {
                "protein_g": round(protein_100g * factor, 1),
                "carbs_g": round(carbs_100g * factor, 1),
                "fat_g": round(fat_100g * factor, 1),
                "fiber_g": round(fiber_100g * factor, 1),
            }

            recs.append(
                {
                    "food_id": str(item["food_id"]),
                    "name": str(item["name"]),
                    "diet_type": str(item["diet_type"]),
                    "grams": grams,
                    "kcal": item_kcal,
                    "macros": macros,
                    "reason": str(item["reason"]),
                }
            )

        return recs


# Cached engine instance
_food_engine: HybridFoodRecommender | None = None


def recommend_foods_for_user(
    user_id: str,
    kcal_target: float = 400.0,
    n: int = 3,
    data_access: BaseDataAccess | None = None,
    user_dict: dict[str, Any] | None = None,
    date: str | None = None,
) -> list[dict[str, Any]]:
    """Public function routing to HybridFoodRecommender with user context and date support."""
    global _food_engine
    da = data_access or get_data_access()
    if _food_engine is None or _food_engine.da is not da:
        _food_engine = HybridFoodRecommender(da)
        _food_engine.fit()

    return _food_engine.recommend(
        user_id=user_id,
        kcal_target=kcal_target,
        n=n,
        user_dict=user_dict,
        date=date,
    )
