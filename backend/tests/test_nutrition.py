from backend.app.schemas.all_schemas import UserProfile, UserGoal
from backend.app.services.nutrition import (
    calculate_bmr,
    calculate_tdee,
    calculate_daily_calorie_target,
    calculate_met_calories,
)


def test_bmr_calculation_male():
    profile = UserProfile(
        age=25,
        gender="male",
        height_cm=180.0,
        weight_kg=80.0,
        activity_level="sedentary",
        diet_type="nonveg",
        injuries=[],
    )
    # BMR = 10 * 80 + 6.25 * 180 - 5 * 25 + 5 = 800 + 1125 - 125 + 5 = 1805.0
    bmr = calculate_bmr(profile)
    assert bmr == 1805.0


def test_bmr_calculation_female():
    profile = UserProfile(
        age=30,
        gender="female",
        height_cm=165.0,
        weight_kg=60.0,
        activity_level="moderately_active",
        diet_type="veg",
        injuries=[],
    )
    # BMR = 10 * 60 + 6.25 * 165 - 5 * 30 - 161 = 600 + 1031.25 - 150 - 161 = 1320.25
    bmr = calculate_bmr(profile)
    assert bmr == 1320.25


def test_tdee_calculation():
    profile = UserProfile(
        age=25,
        gender="male",
        height_cm=180.0,
        weight_kg=80.0,
        activity_level="sedentary",  # multiplier 1.2
        diet_type="nonveg",
        injuries=[],
    )
    tdee = calculate_tdee(profile)
    assert tdee == round(1805.0 * 1.2, 2)


def test_met_calories_calculation():
    # 3.8 MET, 80kg, 30 min (0.5 hours) -> 3.8 * 80 * 0.5 = 152.0
    kcal = calculate_met_calories(met=3.8, weight_kg=80.0, duration_min=30.0)
    assert kcal == 152.0


def test_daily_calorie_target_safe_floor():
    profile = UserProfile(
        age=25,
        gender="male",
        height_cm=160.0,
        weight_kg=55.0,
        activity_level="sedentary",
        diet_type="veg",
        injuries=[],
    )
    # Extreme deficit requested
    goal = UserGoal(target_weight_kg=40.0, target_date="2026-10-15")
    target = calculate_daily_calorie_target(profile, goal)
    # Must respect male minimum floor of 1500 kcal
    assert target >= 1500.0
