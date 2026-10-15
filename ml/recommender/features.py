"""User feature extraction module for clustering and profiling.

Features engineered:
1. age: User's age in years.
2. bmi: Body Mass Index (weight_kg / (height_m ** 2)).
3. activity_numeric: Ordinal mapping of activity level (1 to 4).
4. goal_delta: target_weight_kg - weight_kg (<0 for weight loss, >0 for weight gain).
5. avg_sleep: Average logged sleep hours (defaults to 7.0 if unrecorded).
6. avg_workout_min: Average daily workout minutes from historical logs.
"""

import json
from typing import Any

import numpy as np
import pandas as pd

FEATURE_NAMES = [
    "age",
    "bmi",
    "activity_numeric",
    "goal_delta",
    "avg_sleep",
    "avg_workout_min",
]

ACTIVITY_MAP = {
    "sedentary": 1.0,
    "lightly_active": 2.0,
    "moderately_active": 3.0,
    "very_active": 4.0,
}


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate Body Mass Index (BMI)."""
    if height_cm <= 0 or weight_kg <= 0:
        return 22.0
    height_m = height_cm / 100.0
    return round(weight_kg / (height_m**2), 2)


def extract_features_from_dict(
    user: dict[str, Any], logs: list[dict[str, Any]] | None = None
) -> np.ndarray:
    """Extract 1D feature vector for a given user dictionary matching the MongoDB schema.

    Handles edge cases like missing fields and empty logs.
    """
    profile = user.get("profile", {})
    goal = user.get("goal", {})

    age = float(profile.get("age", 28))
    height_cm = float(profile.get("height_cm", 170.0))
    weight_kg = float(profile.get("weight_kg", 70.0))
    activity_str = str(profile.get("activity_level", "sedentary")).lower()
    activity_numeric = ACTIVITY_MAP.get(activity_str, 2.0)

    target_weight_kg = float(goal.get("target_weight_kg", weight_kg))
    goal_delta = target_weight_kg - weight_kg
    bmi = calculate_bmi(weight_kg, height_cm)

    # Process logs if available
    avg_sleep = 7.0
    avg_workout_min = 0.0

    if logs and len(logs) > 0:
        sleep_vals = [
            float(log_item.get("sleep_hours", 7.0))
            for log_item in logs
            if "sleep_hours" in log_item and pd.notna(log_item["sleep_hours"])
        ]
        if sleep_vals:
            avg_sleep = float(np.mean(sleep_vals))

        workout_durations = []
        for log_item in logs:
            workouts_field = log_item.get("workouts", [])
            if isinstance(workouts_field, str):
                try:
                    workouts_field = json.loads(workouts_field)
                except (json.JSONDecodeError, TypeError, ValueError):
                    workouts_field = []
            if isinstance(workouts_field, list):
                total_min = sum(
                    float(w.get("duration_min", 0))
                    for w in workouts_field
                    if isinstance(w, dict)
                )
                workout_durations.append(total_min)
        if workout_durations:
            avg_workout_min = float(np.mean(workout_durations))

    return np.array(
        [age, bmi, activity_numeric, goal_delta, avg_sleep, avg_workout_min],
        dtype=float,
    )


def build_feature_dataframe(
    users_df: pd.DataFrame, logs_df: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Build a complete feature matrix DataFrame from users and daily logs."""
    # Precompute per-user log aggregates if logs provided
    user_sleep_map = {}
    user_workout_map = {}

    if logs_df is not None and not logs_df.empty:
        # Sleep aggregate
        sleep_grp = logs_df.groupby("user_id")["sleep_hours"].mean()
        user_sleep_map = sleep_grp.to_dict()

        # Workout duration aggregate
        def compute_row_workout_min(workouts_val):
            if pd.isna(workouts_val):
                return 0.0
            if isinstance(workouts_val, str):
                try:
                    workouts_val = json.loads(workouts_val)
                except (json.JSONDecodeError, TypeError, ValueError):
                    return 0.0
            if isinstance(workouts_val, list):
                return sum(
                    float(w.get("duration_min", 0))
                    for w in workouts_val
                    if isinstance(w, dict)
                )
            return 0.0

        if "workouts" in logs_df.columns:
            temp_df = logs_df.copy()
            temp_df["total_workout_min"] = temp_df["workouts"].apply(
                compute_row_workout_min
            )
            workout_grp = temp_df.groupby("user_id")["total_workout_min"].mean()
            user_workout_map = workout_grp.to_dict()

    feature_rows = []
    user_ids = []

    for _, row in users_df.iterrows():
        uid = str(row["_id"])
        user_ids.append(uid)

        age = float(row.get("age", 28))
        height_cm = float(row.get("height_cm", 170.0))
        weight_kg = float(row.get("weight_kg", 70.0))
        activity_str = str(row.get("activity_level", "sedentary")).lower()
        activity_numeric = ACTIVITY_MAP.get(activity_str, 2.0)

        target_weight = (
            float(row.get("target_weight_kg", weight_kg))
            if pd.notna(row.get("target_weight_kg"))
            else weight_kg
        )
        goal_delta = target_weight - weight_kg
        bmi = calculate_bmi(weight_kg, height_cm)

        avg_sleep = user_sleep_map.get(uid, 7.0)
        avg_workout_min = user_workout_map.get(uid, 0.0)

        feature_rows.append(
            {
                "user_id": uid,
                "age": age,
                "bmi": bmi,
                "activity_numeric": activity_numeric,
                "goal_delta": goal_delta,
                "avg_sleep": avg_sleep,
                "avg_workout_min": avg_workout_min,
            }
        )

    return pd.DataFrame(feature_rows)
