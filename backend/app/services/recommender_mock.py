from backend.app.schemas.all_schemas import ExerciseRecItem, FoodRecItem, FoodMacros


def get_exercise_recs(user_id: str, n: int = 3) -> list[ExerciseRecItem]:
    """Mock interface for Member B's recommender package.

    Returns fixed fallback exercise recommendations to ensure Member C
    remains unblocked.
    """
    mock_exercises = [
        ExerciseRecItem(
            exercise_id="ex_bodyweight_squats",
            name="Bodyweight Squats",
            duration_min=20.0,
            est_kcal=120.0,
            reason="Popular among users with similar fitness goals in your cluster",
        ),
        ExerciseRecItem(
            exercise_id="ex_pushups",
            name="Standard Pushups",
            duration_min=15.0,
            est_kcal=75.0,
            reason="High engagement and suitable for your upper-body focus",
        ),
        ExerciseRecItem(
            exercise_id="ex_cycling_leisure",
            name="Stationary Cycling (Moderate)",
            duration_min=30.0,
            est_kcal=180.0,
            reason="Low-impact cardio matching your current activity level",
        ),
    ]
    return mock_exercises[:n]


def get_food_recs(user_id: str, kcal_target: float, n: int = 3) -> list[FoodRecItem]:
    """Mock interface for Member B's recommender package.

    Returns fixed fallback food recommendations aligned with user diet and target.
    """
    mock_foods = [
        FoodRecItem(
            food_id="food_oatmeal",
            name="Rolled Oatmeal with Water",
            grams=200.0,
            kcal=136.0,
            macros=FoodMacros(protein_g=4.8, carbs_g=24.0, fat_g=2.8, fiber_g=3.4),
            reason="High-fiber complex carb ideal for clean energy replenishment",
        ),
        FoodRecItem(
            food_id="food_paneer",
            name="Paneer (Cottage Cheese)",
            grams=150.0,
            kcal=397.5,
            macros=FoodMacros(protein_g=27.45, carbs_g=1.8, fat_g=31.2, fiber_g=0.0),
            reason="High-protein vegetarian option favored by similar profiles",
        ),
        FoodRecItem(
            food_id="food_brown_rice",
            name="Cooked Brown Rice",
            grams=200.0,
            kcal=222.0,
            macros=FoodMacros(protein_g=5.2, carbs_g=46.0, fat_g=1.8, fiber_g=3.6),
            reason="Balanced macro recovery staple matching your daily target",
        ),
    ]
    return mock_foods[:n]
