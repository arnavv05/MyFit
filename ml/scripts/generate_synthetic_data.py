"""Synthetic Data Generator for Myfitness ML module.

Generates realistic users, daily logs, and user-item interactions
with fixed random seed (42) adhering strictly to MongoDB schemas:
- users: age, gender, height_cm, weight_kg, activity_level, diet_type ("veg"|"nonveg"), injuries, goal
- daily_logs: date, weight_kg, sleep_hours, water_ml, kcal_in, kcal_out, workouts, meals
- interactions: user_id, item_type ("exercise"|"food"), item_id, rating (1-5), implicit_score (0.0-1.0), timestamp

Key realism constraints:
1. Veg users NEVER interact with non-veg foods.
2. Users with injuries avoid or rarely interact with contraindicated exercises.
3. Daily weight drift is physically correlated with calorie balance (kcal_in - kcal_out).
4. Timestamps span 60 days to enable realistic time-based train/test splits.
5. Total file size is compact (<4 MB).
"""

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Set paths
SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = ML_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

RANDOM_SEED = 42


def generate_datasets(num_users: int = 1200, days_history: int = 21) -> None:
    """Generate synthetic users, daily logs, and interactions."""
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # 1. Load exercises and foods
    exercises_df = pd.read_csv(DATA_DIR / "exercises.csv")
    foods_df = pd.read_csv(DATA_DIR / "foods.csv")

    veg_foods = foods_df[foods_df["diet_type"] == "veg"]["_id"].tolist()
    nonveg_foods = foods_df[foods_df["diet_type"] == "nonveg"]["_id"].tolist()
    all_exercise_ids = exercises_df["_id"].tolist()

    # Pre-map exercise injury flags
    exercise_injuries = {}
    exercise_met = {}
    for _, row in exercises_df.iterrows():
        flags = [
            f.strip().lower()
            for f in str(row["injury_flags"]).split(";")
            if f.strip() and f.strip().lower() != "none"
        ]
        exercise_injuries[row["_id"]] = flags
        exercise_met[row["_id"]] = float(row["met_value"])

    # Food kcal map
    food_kcal_per_100g = {
        row["_id"]: float(row["kcal_per_100g"]) for _, row in foods_df.iterrows()
    }

    # Activity levels & factors
    activity_levels = [
        "sedentary",
        "lightly_active",
        "moderately_active",
        "very_active",
    ]
    injury_pool = ["knee", "shoulder", "back", "wrist", "ankle"]

    start_date = datetime(2026, 8, 1, tzinfo=timezone.utc)

    users_records = []
    daily_logs_records = []
    interactions_records = []

    interaction_id_counter = 1
    log_id_counter = 1

    print(f"Generating {num_users} users with {days_history} days history...")

    for i in range(1, num_users + 1):
        user_id = f"usr_{i:04d}"
        email = f"user_{i:04d}@example.com"
        gender = "female" if random.random() < 0.48 else "male"
        age = int(np.random.normal(30, 8))
        age = max(18, min(65, age))

        if gender == "male":
            height_cm = round(float(np.random.normal(175, 7)), 1)
            base_weight = round(float(np.random.normal(78, 12)), 1)
        else:
            height_cm = round(float(np.random.normal(162, 6)), 1)
            base_weight = round(float(np.random.normal(65, 10)), 1)

        base_weight = max(45.0, min(140.0, base_weight))
        height_cm = max(145.0, min(205.0, height_cm))

        activity = random.choices(activity_levels, weights=[0.35, 0.35, 0.20, 0.10])[0]
        # ~45% veg (typical for Indian / wellness population)
        diet_type = "veg" if random.random() < 0.45 else "nonveg"

        # Injuries: 25% chance of 1-2 injuries
        user_injuries = []
        if random.random() < 0.25:
            user_injuries = random.sample(
                injury_pool, k=1 if random.random() < 0.8 else 2
            )

        # Goal weight
        # 60% want weight loss, 25% maintain, 15% muscle/weight gain
        goal_type = random.choices(
            ["loss", "maintain", "gain"], weights=[0.60, 0.25, 0.15]
        )[0]
        if goal_type == "loss":
            target_weight = round(base_weight - random.uniform(3.0, 10.0), 1)
        elif goal_type == "gain":
            target_weight = round(base_weight + random.uniform(2.0, 6.0), 1)
        else:
            target_weight = base_weight

        target_date = (start_date + timedelta(days=90)).strftime("%Y-%m-%d")
        created_at = (start_date - timedelta(days=random.randint(1, 10))).isoformat()

        # BMR approximation (Mifflin-St Jeor)
        if gender == "male":
            bmr = 10 * base_weight + 6.25 * height_cm - 5 * age + 5
        else:
            bmr = 10 * base_weight + 6.25 * height_cm - 5 * age - 161

        activity_multipliers = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
        }
        tdee = bmr * activity_multipliers[activity]

        # Target deficit or surplus
        if goal_type == "loss":
            daily_target_balance = -400.0  # kcal deficit
        elif goal_type == "gain":
            daily_target_balance = +300.0  # kcal surplus
        else:
            daily_target_balance = 0.0

        users_records.append(
            {
                "_id": user_id,
                "email": email,
                "password_hash": "dummy_hash_for_test",
                "age": age,
                "gender": gender,
                "height_cm": height_cm,
                "weight_kg": base_weight,
                "activity_level": activity,
                "diet_type": diet_type,
                "injuries": ";".join(user_injuries),
                "target_weight_kg": target_weight,
                "target_date": target_date,
                "cluster_id": None,
                "created_at": created_at,
            }
        )

        # Generate Daily Logs & Interactions
        current_weight = base_weight
        num_logs = random.randint(days_history - 5, days_history)

        # Available foods for user based on diet_type
        user_food_pool = veg_foods if diet_type == "veg" else (veg_foods + nonveg_foods)

        # Available exercises (preferred exercises that don't violate injuries)
        safe_exercises = [
            ex_id
            for ex_id in all_exercise_ids
            if not any(inj in exercise_injuries[ex_id] for inj in user_injuries)
        ]
        if not safe_exercises:
            safe_exercises = all_exercise_ids

        # Track user's favorite items to simulate CF preferences
        user_fav_exercises = random.sample(
            safe_exercises, k=min(4, len(safe_exercises))
        )
        user_fav_foods = random.sample(user_food_pool, k=min(8, len(user_food_pool)))

        for day_idx in range(num_logs):
            log_date = start_date + timedelta(days=day_idx)
            date_str = log_date.strftime("%Y-%m-%d")

            sleep_hours = round(float(np.random.normal(7.0, 0.9)), 1)
            sleep_hours = max(4.0, min(10.5, sleep_hours))

            water_ml = int(np.random.normal(2400, 450))
            water_ml = max(1000, min(4500, water_ml))

            # Calorie intake vs out
            balance_noise = np.random.normal(0, 150)
            actual_balance = daily_target_balance + balance_noise
            # Workout minutes
            workout_prob = (
                0.85 if activity in ["moderately_active", "very_active"] else 0.55
            )
            did_workout = random.random() < workout_prob

            workout_burn = 0.0
            log_workouts = []
            if did_workout:
                # pick 1-2 exercises
                ex_chosen = random.sample(
                    user_fav_exercises if random.random() < 0.75 else safe_exercises,
                    k=random.choice([1, 2]),
                )
                for ex_id in ex_chosen:
                    dur_min = random.choice([20, 30, 45, 60])
                    met = exercise_met.get(ex_id, 4.0)
                    kcal_burned = round(met * current_weight * (dur_min / 60.0), 1)
                    workout_burn += kcal_burned
                    rating = random.choices(
                        [3, 4, 5, 2, 1], weights=[0.25, 0.45, 0.20, 0.07, 0.03]
                    )[0]
                    log_workouts.append(
                        {
                            "exercise_id": ex_id,
                            "duration_min": dur_min,
                            "kcal_burned": kcal_burned,
                            "rating": rating,
                        }
                    )

                    # Log interaction
                    interactions_records.append(
                        {
                            "_id": f"int_{interaction_id_counter:07d}",
                            "user_id": user_id,
                            "item_type": "exercise",
                            "item_id": ex_id,
                            "rating": rating,
                            "implicit_score": round(
                                min(1.0, dur_min / 60.0 * (rating / 5.0)), 2
                            ),
                            "timestamp": (
                                log_date + timedelta(hours=random.randint(6, 18))
                            ).isoformat(),
                        }
                    )
                    interaction_id_counter += 1

            kcal_out = round(tdee + workout_burn, 1)
            kcal_in = round(kcal_out + actual_balance, 1)
            kcal_in = max(1000.0, kcal_in)

            # Select 2-3 logged meals
            meal_items = random.sample(
                user_fav_foods if random.random() < 0.75 else user_food_pool,
                k=random.choice([2, 3]),
            )
            log_meals = []
            for fd_id in meal_items:
                grams = float(random.choice([100, 150, 200, 250]))
                fd_kcal = round(
                    food_kcal_per_100g.get(fd_id, 120.0) * (grams / 100.0), 1
                )
                log_meals.append({"food_id": fd_id, "grams": grams, "kcal": fd_kcal})

                # Food interaction
                food_rating = random.choices(
                    [4, 5, 3, 2, 1], weights=[0.40, 0.35, 0.18, 0.05, 0.02]
                )[0]
                interactions_records.append(
                    {
                        "_id": f"int_{interaction_id_counter:07d}",
                        "user_id": user_id,
                        "item_type": "food",
                        "item_id": fd_id,
                        "rating": food_rating,
                        "implicit_score": round(food_rating / 5.0, 2),
                        "timestamp": (
                            log_date + timedelta(hours=random.randint(8, 21))
                        ).isoformat(),
                    }
                )
                interaction_id_counter += 1

            # Weight physics: 7700 kcal ~= 1 kg body mass
            weight_delta_kg = actual_balance / 7700.0
            # Water weight noise
            water_noise = np.random.normal(0, 0.1)
            current_weight = round(current_weight + weight_delta_kg + water_noise, 2)

            daily_logs_records.append(
                {
                    "_id": f"log_{log_id_counter:07d}",
                    "user_id": user_id,
                    "date": date_str,
                    "weight_kg": current_weight,
                    "sleep_hours": sleep_hours,
                    "water_ml": water_ml,
                    "workouts": json.dumps(log_workouts),
                    "meals": json.dumps(log_meals),
                    "kcal_in": kcal_in,
                    "kcal_out": kcal_out,
                }
            )
            log_id_counter += 1

    # Convert to DataFrames and save
    users_df = pd.DataFrame(users_records)
    daily_logs_df = pd.DataFrame(daily_logs_records)
    interactions_df = pd.DataFrame(interactions_records)

    users_df.to_csv(DATA_DIR / "users.csv", index=False)
    daily_logs_df.to_csv(DATA_DIR / "daily_logs.csv", index=False)
    interactions_df.to_csv(DATA_DIR / "interactions.csv", index=False)

    print("Datasets successfully generated:")
    print(f"- Users: {len(users_df)} rows ({DATA_DIR / 'users.csv'})")
    print(f"- Daily Logs: {len(daily_logs_df)} rows ({DATA_DIR / 'daily_logs.csv'})")
    print(
        f"- Interactions: {len(interactions_df)} rows ({DATA_DIR / 'interactions.csv'})"
    )


if __name__ == "__main__":
    generate_datasets()
